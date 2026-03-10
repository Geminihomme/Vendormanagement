"""
APPROVAL API ROUTES (The Manager's Inbox)
============================================
These endpoints let managers review, approve, and reject
vendor and contract submissions.

ENDPOINTS:
  GET  /api/approvals/                -> List approvals (with filters)
  GET  /api/approvals/pending         -> Just the pending ones (the inbox)
  GET  /api/approvals/summary         -> Counts: pending=3, approved=12, etc.
  GET  /api/approvals/{id}            -> Get one approval's details
  POST /api/approvals/{id}/review     -> Approve or reject

THE USER JOURNEY:
=================
1. A viewer creates a new vendor → status is "pending"
2. An approval request is automatically created → shows in manager's inbox
3. Manager opens /approvals page → sees "3 pending approvals"
4. Clicks an approval → sees details (who requested, what vendor, when)
5. Types a comment → clicks "Approve" or "Reject"
6. The vendor status changes (pending → approved or rejected)
7. Email notification goes to the person who submitted it

WHO CAN APPROVE?
Only users with "manager" or "admin" roles can approve/reject.
Viewers can submit requests but can't review them.
It's like how any employee can submit a purchase request,
but only managers can authorize purchases.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.approval import ApprovalResponse, ApprovalAction, ApprovalSummary
from app.services import approval_service
from app.services import email_service
from app.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/summary")
def get_approval_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get approval counts for the dashboard badges.
    Returns: {"pending": 3, "approved": 12, "rejected": 2, "total": 17}
    """
    return approval_service.get_approval_summary(db)


@router.get("/pending")
def get_pending_approvals(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get only PENDING approvals — the manager's inbox.
    These are the items waiting for someone to review them.
    """
    return approval_service.get_pending_approvals(db, skip=skip, limit=limit)


@router.get("/", response_model=list[ApprovalResponse])
def list_approvals(
    status: str | None = Query(None, description="Filter by status: pending, approved, rejected"),
    approval_type: str | None = Query(None, description="Filter by type: vendor, contract"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all approvals with optional filters.
    Used for the full approval history view.
    """
    return approval_service.get_all_approvals(
        db, status=status, approval_type=approval_type,
        skip=skip, limit=limit,
    )


@router.get("/{approval_id}")
def get_approval(
    approval_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single approval's full details."""
    approval = approval_service.get_approval(db, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    return approval


@router.post("/{approval_id}/review")
def review_approval(
    approval_id: int,
    body: ApprovalAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Approve or reject a pending request.

    AUTHORIZATION CHECK:
    Only managers and admins can review approvals.
    If a viewer tries, they get a 403 "Forbidden" error.

    VALIDATION:
    - Action must be "approve" or "reject"
    - Rejections must include a comment (explain why)
    - Can't review something that's already been reviewed

    WHAT HAPPENS AFTER:
    1. The approval record gets updated (status, reviewer, comment)
    2. The entity (vendor/contract) gets updated too
    3. An email is sent to the person who submitted the request
    """
    # Only managers and admins can review
    if current_user.role not in ("manager", "admin"):
        raise HTTPException(
            status_code=403,
            detail="Only managers and admins can approve or reject requests",
        )

    # Validate the action
    if body.action not in ("approve", "reject"):
        raise HTTPException(
            status_code=400,
            detail="Action must be 'approve' or 'reject'",
        )

    # Rejections must have a reason
    if body.action == "reject" and not body.comment:
        raise HTTPException(
            status_code=400,
            detail="A comment is required when rejecting (explain why)",
        )

    # Process the approval
    result = approval_service.process_approval(
        db,
        approval_id=approval_id,
        action=body.action,
        reviewer=current_user,
        comment=body.comment,
    )

    if not result:
        raise HTTPException(
            status_code=400,
            detail="Approval not found or has already been reviewed",
        )

    # Send email notification to the requester
    _notify_requester(db, result, current_user)

    return result


def _notify_requester(db: Session, approval: dict, reviewer: User):
    """
    Send an email to the person who submitted the request,
    letting them know it was approved or rejected.
    """
    requester = db.query(User).filter(User.id == approval["requested_by_id"]).first()
    if not requester:
        return

    action_word = "approved" if approval["status"] == "approved" else "rejected"
    entity_type = approval["approval_type"]
    entity_name = approval["entity_title"]
    comment = approval["comment"] or "No additional comments."

    email_service.send_approval_notification_email(
        recipient_email=requester.email,
        recipient_name=requester.full_name,
        action=action_word,
        entity_type=entity_type,
        entity_name=entity_name,
        reviewer_name=reviewer.full_name,
        comment=comment,
    )
