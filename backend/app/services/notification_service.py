"""
NOTIFICATION SERVICE (The "Assistant" Who Checks Contracts)
=============================================================
This is the BRAIN of our alert system. It answers the question:
"Which contracts are expiring soon, and do we need to alert anyone?"

HOW IT WORKS (step-by-step):
1. Look at today's date
2. Check every active contract's end_date
3. Calculate: how many days until it expires?
4. If it's within 30, 60, or 90 days — create a notification
5. But ONLY if we haven't already created one for that threshold

THE DUPLICATE CHECK IS CRUCIAL:
Without it, the system would send "30 days left!" emails EVERY DAY
for 30 straight days. Nobody wants that. We check: "Did we already
send a 30-day alert for this contract?" If yes, skip it.

REAL-WORLD ANALOGY:
Your assistant checks the lease calendar every morning.
On day 90, they put a green sticky note on your desk: "Heads up."
On day 60, they add a yellow one: "Getting closer."
On day 30, they add a red one: "Action needed!"
But they don't put a SECOND green note on day 89.
"""

from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.contract import Contract, ContractStatus
from app.models.notification import Notification, NotificationType


# The thresholds we check, in order of urgency.
# Each tuple is: (days_before_expiry, notification_type, urgency_label)
ALERT_THRESHOLDS = [
    (90, NotificationType.NINETY_DAY, "90 days"),
    (60, NotificationType.SIXTY_DAY, "60 days"),
    (30, NotificationType.THIRTY_DAY, "30 days"),
]


def check_expiring_contracts(db: Session) -> list[dict]:
    """
    The main function that runs daily. Scans all active contracts
    and creates notifications for any expiring within 30/60/90 days.

    Returns a list of newly created notifications (for logging/testing).

    HOW THE DATE MATH WORKS:
    - Today is Jan 1, 2026
    - Contract end_date is Feb 15, 2026
    - Days until expiry = (Feb 15 - Jan 1) = 45 days
    - 45 is <= 60, so we trigger a 60-day alert
    - 45 is NOT <= 30, so no 30-day alert yet
    """
    today = date.today()
    new_notifications = []

    # Get all contracts that:
    # 1. Have an end_date set (some contracts might not)
    # 2. Are in an "active" or "pending_approval" status
    #    (no point alerting about drafts or already-terminated contracts)
    active_contracts = db.query(Contract).filter(
        Contract.end_date.isnot(None),
        Contract.status.in_([
            ContractStatus.ACTIVE.value,
            ContractStatus.PENDING_APPROVAL.value,
        ])
    ).all()

    for contract in active_contracts:
        days_remaining = (contract.end_date - today).days

        # Skip contracts that have already expired
        # (we handle those separately below)
        if days_remaining < 0:
            # Check if we already sent an expired alert
            _create_expired_notification(db, contract, days_remaining, new_notifications)
            continue

        # Check each threshold: 90, 60, 30 days
        for threshold_days, notif_type, label in ALERT_THRESHOLDS:
            if days_remaining <= threshold_days:
                # Have we already sent THIS type of alert for THIS contract?
                existing = db.query(Notification).filter(
                    and_(
                        Notification.contract_id == contract.id,
                        Notification.notification_type == notif_type.value,
                    )
                ).first()

                if not existing:
                    # No duplicate — create the notification!
                    vendor_name = contract.vendor.name if contract.vendor else "Unknown Vendor"
                    owner_email = (contract.created_by.email
                                   if contract.created_by else None)

                    notification = Notification(
                        contract_id=contract.id,
                        notification_type=notif_type.value,
                        days_until_expiry=days_remaining,
                        message=(
                            f"Contract \"{contract.title}\" with {vendor_name} "
                            f"expires in {days_remaining} days "
                            f"(end date: {contract.end_date.strftime('%B %d, %Y')}). "
                            f"Please review for renewal."
                        ),
                        is_read=False,
                        email_sent=False,
                        recipient_email=owner_email,
                    )

                    db.add(notification)
                    new_notifications.append({
                        "contract_id": contract.id,
                        "contract_title": contract.title,
                        "vendor_name": vendor_name,
                        "type": notif_type.value,
                        "days_remaining": days_remaining,
                        "recipient_email": owner_email,
                    })

    db.commit()
    return new_notifications


def _create_expired_notification(
    db: Session, contract: Contract, days_remaining: int, results: list
):
    """Create an 'expired' notification if we haven't already."""
    existing = db.query(Notification).filter(
        and_(
            Notification.contract_id == contract.id,
            Notification.notification_type == NotificationType.EXPIRED.value,
        )
    ).first()

    if not existing:
        vendor_name = contract.vendor.name if contract.vendor else "Unknown Vendor"
        owner_email = (contract.created_by.email if contract.created_by else None)

        notification = Notification(
            contract_id=contract.id,
            notification_type=NotificationType.EXPIRED.value,
            days_until_expiry=days_remaining,
            message=(
                f"Contract \"{contract.title}\" with {vendor_name} "
                f"has EXPIRED (end date was {contract.end_date.strftime('%B %d, %Y')}). "
                f"Immediate action required."
            ),
            is_read=False,
            email_sent=False,
            recipient_email=owner_email,
        )
        db.add(notification)
        results.append({
            "contract_id": contract.id,
            "contract_title": contract.title,
            "vendor_name": vendor_name,
            "type": NotificationType.EXPIRED.value,
            "days_remaining": days_remaining,
            "recipient_email": owner_email,
        })


def get_all_notifications(
    db: Session, unread_only: bool = False, skip: int = 0, limit: int = 100
) -> list[dict]:
    """
    Get notifications for the dashboard.
    Optionally filter to only unread notifications.
    Returns newest first (most urgent on top).
    """
    query = db.query(Notification)

    if unread_only:
        query = query.filter(Notification.is_read == False)  # noqa: E712

    notifications = (
        query
        .order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [_enrich_notification(n) for n in notifications]


def get_unread_count(db: Session) -> int:
    """How many unread notifications exist? Shown as a badge count."""
    return db.query(Notification).filter(
        Notification.is_read == False  # noqa: E712
    ).count()


def mark_as_read(db: Session, notification_ids: list[int]) -> int:
    """
    Mark one or more notifications as read.
    Returns how many were actually updated.
    """
    updated = db.query(Notification).filter(
        Notification.id.in_(notification_ids)
    ).update({"is_read": True}, synchronize_session="fetch")
    db.commit()
    return updated


def get_upcoming_renewals(db: Session) -> list[dict]:
    """
    Get all active contracts with end dates, sorted by soonest expiring first.
    This powers the "Upcoming Renewals" dashboard.

    Unlike notifications (which are one-time alerts), this is a LIVE VIEW
    that always shows current data. Think of it as looking at the calendar
    directly, not at the sticky notes your assistant left.
    """
    today = date.today()

    contracts = (
        db.query(Contract)
        .filter(
            Contract.end_date.isnot(None),
            Contract.status.in_([
                ContractStatus.ACTIVE.value,
                ContractStatus.PENDING_APPROVAL.value,
            ])
        )
        .order_by(Contract.end_date.asc())  # Soonest first
        .all()
    )

    results = []
    for contract in contracts:
        days_remaining = (contract.end_date - today).days
        vendor_name = contract.vendor.name if contract.vendor else "Unknown"

        # Determine urgency level for the UI to color-code
        if days_remaining < 0:
            urgency = "expired"
        elif days_remaining <= 30:
            urgency = "critical"     # Red
        elif days_remaining <= 60:
            urgency = "warning"      # Orange/Yellow
        elif days_remaining <= 90:
            urgency = "attention"    # Blue
        else:
            urgency = "normal"       # Green/Gray

        results.append({
            "contract_id": contract.id,
            "contract_title": contract.title,
            "contract_number": contract.contract_number,
            "vendor_id": contract.vendor_id,
            "vendor_name": vendor_name,
            "value": contract.value,
            "end_date": contract.end_date,
            "days_remaining": days_remaining,
            "urgency": urgency,
            "status": contract.status,
        })

    return results


def _enrich_notification(notification: Notification) -> dict:
    """
    Convert a Notification model to a dict with extra info.
    Adds contract_title and vendor_name by following relationships.
    """
    contract = notification.contract
    return {
        "id": notification.id,
        "contract_id": notification.contract_id,
        "contract_title": contract.title if contract else None,
        "vendor_name": (contract.vendor.name
                        if contract and contract.vendor else None),
        "notification_type": notification.notification_type,
        "days_until_expiry": notification.days_until_expiry,
        "message": notification.message,
        "is_read": notification.is_read,
        "email_sent": notification.email_sent,
        "recipient_email": notification.recipient_email,
        "created_at": notification.created_at,
    }
