"""
NOTIFICATION & RENEWALS API ROUTES
=====================================
These endpoints power:
1. The Renewals Dashboard (upcoming contract expirations)
2. The Notification Center (alerts that were generated)
3. A manual trigger for testing (so you don't wait 30 days!)

ENDPOINTS:
  GET  /api/notifications/                  -> List all notifications
  GET  /api/notifications/unread-count      -> Get count of unread (for badge)
  POST /api/notifications/mark-read         -> Mark notifications as read
  GET  /api/notifications/upcoming-renewals -> Dashboard data (contracts by urgency)
  POST /api/notifications/check-now         -> Manually trigger the daily check (for testing!)

THE MANUAL TRIGGER IS KEY FOR TESTING:
In production, the scheduler runs at 8 AM daily.
But during development, you don't want to wait until 8 AM to test!
The /check-now endpoint runs the SAME function the scheduler would,
but immediately. It's like pressing the "test" button on a fire alarm.
"""

import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.notification import NotificationResponse, NotificationMarkRead
from app.services import notification_service, email_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/upcoming-renewals")
def get_upcoming_renewals(db: Session = Depends(get_db)):
    """
    Get all contracts sorted by expiration date (soonest first).

    This is the main data source for the Renewals Dashboard.
    Each item includes an "urgency" field:
    - "expired": Past the end date (red)
    - "critical": 0-30 days left (red)
    - "warning": 31-60 days left (orange)
    - "attention": 61-90 days left (blue)
    - "normal": 90+ days left (green)

    The frontend uses this to color-code the dashboard rows.
    """
    return notification_service.get_upcoming_renewals(db)


@router.get("/", response_model=list[NotificationResponse])
def list_notifications(
    unread_only: bool = Query(False, description="Only show unread notifications"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Get all notifications, newest first.
    Set unread_only=true to filter to just unread ones.
    """
    return notification_service.get_all_notifications(
        db, unread_only=unread_only, skip=skip, limit=limit
    )


@router.get("/unread-count")
def get_unread_count(db: Session = Depends(get_db)):
    """
    Get the number of unread notifications.

    This is used for the little red badge on the "Notifications" tab:
    🔔 Notifications (3)
    The "(3)" comes from this endpoint.
    """
    count = notification_service.get_unread_count(db)
    return {"unread_count": count}


@router.post("/mark-read")
def mark_notifications_as_read(
    body: NotificationMarkRead,
    db: Session = Depends(get_db),
):
    """
    Mark specific notifications as read.
    The frontend sends a list of notification IDs to mark.
    """
    updated = notification_service.mark_as_read(db, body.notification_ids)
    return {"marked_read": updated}


@router.post("/check-now")
def trigger_expiry_check(db: Session = Depends(get_db)):
    """
    MANUALLY run the contract expiration check.

    THIS IS YOUR TESTING TOOL!
    Instead of waiting for the 8 AM scheduled job, hit this endpoint
    to run the check immediately.

    HOW TO TEST WITHOUT WAITING 30 DAYS:
    ======================================
    1. Create a contract with an end_date that's 25 days from today
    2. Hit this endpoint: POST /api/notifications/check-now
    3. The system finds the contract (25 days <= 30-day threshold)
    4. A notification is created and an email is sent (or logged in dev mode)
    5. Check the /upcoming-renewals or / endpoint to see the results

    You can also create contracts with end dates in the past to test
    the "expired" notifications.

    EXAMPLE (using the API docs at http://localhost:8000/docs):
    1. POST /api/contracts/ with end_date = 15 days from now
    2. POST /api/notifications/check-now
    3. GET /api/notifications/ -> You'll see the notification!
    """
    logger.info("Manual expiry check triggered via API")

    # Run the same check the scheduler runs at 8 AM
    new_notifications = notification_service.check_expiring_contracts(db)

    # Send emails for any new notifications
    email_results = {"sent": 0, "failed": 0, "skipped": 0}
    if new_notifications:
        email_results = email_service.send_batch_notifications(new_notifications)

        # Mark notifications as email_sent
        from app.models.notification import Notification
        for notif_data in new_notifications:
            notif = db.query(Notification).filter(
                Notification.contract_id == notif_data["contract_id"],
                Notification.notification_type == notif_data["type"],
            ).order_by(Notification.created_at.desc()).first()

            if notif and notif_data.get("recipient_email"):
                notif.email_sent = True

        db.commit()

    return {
        "message": "Expiry check completed",
        "new_notifications": len(new_notifications),
        "notifications": new_notifications,
        "email_results": email_results,
    }
