"""
APPROVAL SERVICE (The Workflow Engine)
========================================
This is the brain behind the approval process. It handles:
1. Creating new approval requests (when a vendor/contract is submitted)
2. Retrieving the inbox (pending items for managers)
3. Processing approvals/rejections (updating status + the entity itself)
4. Summary stats (for the dashboard badges)

THE STATE MACHINE:
==================
An approval request is a "state machine" — it can only move through
specific states in specific ways:

    PENDING ──approve──→ APPROVED
    PENDING ──reject───→ REJECTED

Once approved or rejected, it CANNOT go back to pending.
This prevents confusion: "Wait, was this already approved or not?"

THE SIDE EFFECTS:
When an approval is APPROVED, the service also:
- Sets the vendor status to "approved" (from "pending")
- OR sets the contract status to "active" (from "pending_approval")

When an approval is REJECTED:
- Sets the vendor status to "rejected"
- OR sets the contract status to "draft" (so they can fix and resubmit)

This is called a "side effect" — approving one thing changes another.
"""

import logging
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.approval import Approval, ApprovalStatus, ApprovalType
from app.models.vendor import Vendor
from app.models.contract import Contract
from app.models.user import User

logger = logging.getLogger(__name__)


def create_approval(
    db: Session,
    approval_type: ApprovalType,
    entity_id: int,
    entity_title: str,
    requested_by_id: int,
) -> Approval:
    """
    Create a new approval request.

    Called automatically when a vendor or contract is created.
    This is like putting a form into the manager's inbox tray.

    Args:
        approval_type: "vendor" or "contract"
        entity_id: The ID of the vendor or contract
        entity_title: Human-readable name (for the inbox display)
        requested_by_id: The user who created it
    """
    approval = Approval(
        approval_type=approval_type,
        entity_id=entity_id,
        entity_title=entity_title,
        requested_by_id=requested_by_id,
        status=ApprovalStatus.PENDING,
    )
    db.add(approval)
    db.commit()
    db.refresh(approval)

    logger.info(
        f"Approval request created: {approval_type.value} '{entity_title}' "
        f"(id={entity_id}) by user {requested_by_id}"
    )
    return approval


def get_pending_approvals(db: Session, skip: int = 0, limit: int = 100) -> list[dict]:
    """
    Get all pending approval requests — the manager's inbox.

    Returns enriched data with requester names so the frontend
    can display everything without extra API calls.
    """
    approvals = (
        db.query(Approval)
        .filter(Approval.status == ApprovalStatus.PENDING)
        .order_by(Approval.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_enrich_approval(db, a) for a in approvals]


def get_all_approvals(
    db: Session,
    status: str | None = None,
    approval_type: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[dict]:
    """
    Get approvals with optional filtering by status and type.

    Used for the full approval history view:
    "Show me all rejected vendor approvals"
    """
    query = db.query(Approval)

    if status:
        query = query.filter(Approval.status == status)
    if approval_type:
        query = query.filter(Approval.approval_type == approval_type)

    approvals = (
        query.order_by(Approval.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_enrich_approval(db, a) for a in approvals]


def get_approval(db: Session, approval_id: int) -> dict | None:
    """Get a single approval by ID, enriched with user names."""
    approval = db.query(Approval).filter(Approval.id == approval_id).first()
    if not approval:
        return None
    return _enrich_approval(db, approval)


def process_approval(
    db: Session,
    approval_id: int,
    action: str,
    reviewer: User,
    comment: str | None = None,
) -> dict | None:
    """
    THE CORE FUNCTION: Process an approve or reject action.

    This is like a manager picking up a form from their inbox,
    writing a note, and stamping it APPROVED or REJECTED.

    WHAT HAPPENS:
    1. Find the approval request
    2. Verify it's still pending (can't re-approve something)
    3. Update the approval record (status, reviewer, comment, timestamp)
    4. Update the ENTITY itself (vendor → approved, contract → active)
    5. Return the updated approval

    The entity update is the KEY SIDE EFFECT — approving the request
    doesn't just change the approval record, it activates the vendor/contract.
    """
    approval = db.query(Approval).filter(Approval.id == approval_id).first()
    if not approval:
        return None

    # Can't process an already-processed approval
    if approval.status != ApprovalStatus.PENDING:
        return None

    now = datetime.utcnow()

    if action == "approve":
        approval.status = ApprovalStatus.APPROVED
        approval.reviewed_by_id = reviewer.id
        approval.comment = comment
        approval.reviewed_at = now

        # --- SIDE EFFECT: Activate the entity ---
        _activate_entity(db, approval)

        logger.info(
            f"Approval #{approval_id} APPROVED by {reviewer.full_name}: "
            f"{approval.approval_type.value} '{approval.entity_title}'"
        )

    elif action == "reject":
        approval.status = ApprovalStatus.REJECTED
        approval.reviewed_by_id = reviewer.id
        approval.comment = comment
        approval.reviewed_at = now

        # --- SIDE EFFECT: Mark entity as rejected ---
        _reject_entity(db, approval)

        logger.info(
            f"Approval #{approval_id} REJECTED by {reviewer.full_name}: "
            f"{approval.approval_type.value} '{approval.entity_title}' "
            f"Reason: {comment}"
        )
    else:
        return None  # Invalid action

    db.commit()
    db.refresh(approval)
    return _enrich_approval(db, approval)


def get_approval_summary(db: Session) -> dict:
    """
    Get counts for the dashboard badges.

    Returns: {"pending": 3, "approved": 12, "rejected": 2, "total": 17}
    """
    counts = (
        db.query(Approval.status, func.count(Approval.id))
        .group_by(Approval.status)
        .all()
    )

    summary = {"pending": 0, "approved": 0, "rejected": 0, "total": 0}
    for status, count in counts:
        summary[status.value] = count
        summary["total"] += count

    return summary


# --- PRIVATE HELPER FUNCTIONS ---


def _activate_entity(db: Session, approval: Approval):
    """
    When an approval is approved, activate the underlying entity.

    For vendors:  pending → approved
    For contracts: pending_approval → active
    """
    if approval.approval_type == ApprovalType.VENDOR:
        vendor = db.query(Vendor).filter(Vendor.id == approval.entity_id).first()
        if vendor:
            vendor.status = "approved"

    elif approval.approval_type == ApprovalType.CONTRACT:
        contract = db.query(Contract).filter(Contract.id == approval.entity_id).first()
        if contract:
            contract.status = "active"


def _reject_entity(db: Session, approval: Approval):
    """
    When an approval is rejected, mark the entity accordingly.

    For vendors:  pending → rejected
    For contracts: pending_approval → draft (so they can fix and resubmit)
    """
    if approval.approval_type == ApprovalType.VENDOR:
        vendor = db.query(Vendor).filter(Vendor.id == approval.entity_id).first()
        if vendor:
            vendor.status = "rejected"

    elif approval.approval_type == ApprovalType.CONTRACT:
        contract = db.query(Contract).filter(Contract.id == approval.entity_id).first()
        if contract:
            contract.status = "draft"


def _enrich_approval(db: Session, approval: Approval) -> dict:
    """
    Add human-readable names to an approval record.

    The database stores user IDs (numbers), but the frontend needs
    to show names like "Requested by Lisa Park, Approved by Mike Johnson."
    This function looks up those names.
    """
    requester = db.query(User).filter(User.id == approval.requested_by_id).first()
    reviewer = None
    if approval.reviewed_by_id:
        reviewer = db.query(User).filter(User.id == approval.reviewed_by_id).first()

    return {
        "id": approval.id,
        "approval_type": approval.approval_type.value,
        "entity_id": approval.entity_id,
        "entity_title": approval.entity_title,
        "status": approval.status.value,
        "requested_by_id": approval.requested_by_id,
        "requested_by_name": requester.full_name if requester else "Unknown",
        "reviewed_by_id": approval.reviewed_by_id,
        "reviewed_by_name": reviewer.full_name if reviewer else "",
        "comment": approval.comment,
        "created_at": approval.created_at.isoformat() if approval.created_at else None,
        "reviewed_at": approval.reviewed_at.isoformat() if approval.reviewed_at else None,
    }
