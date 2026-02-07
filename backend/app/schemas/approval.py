"""
APPROVAL SCHEMAS (The Shapes of Approval Data)
=================================================
These schemas define what data goes in and out for approval requests.

THERE ARE THREE SCHEMAS:

1. ApprovalResponse — What the frontend receives when it asks "show me
   all pending approvals." Includes everything: who requested it, when,
   what it's about, etc.

2. ApprovalAction — What the frontend sends when a manager clicks
   "Approve" or "Reject." Just the action and an optional comment.

3. ApprovalSummary — Counts for the dashboard: how many pending,
   approved, and rejected. For the little badges and stat cards.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ApprovalResponse(BaseModel):
    """
    Full approval record returned to the frontend.

    This powers each row in the "Approval Inbox" table.
    The frontend doesn't need to make separate calls to get
    the requester's name or the entity title — it's all here.
    """
    id: int
    approval_type: str          # "vendor" or "contract"
    entity_id: int              # The vendor or contract ID
    entity_title: str           # "Acme Corp" or "Acme IT Contract"
    status: str                 # "pending", "approved", or "rejected"
    requested_by_id: int
    requested_by_name: str = ""    # Convenience field: "Lisa Park"
    reviewed_by_id: int | None = None
    reviewed_by_name: str = ""     # "Mike Johnson" (empty if not reviewed yet)
    comment: str | None = None
    created_at: datetime
    reviewed_at: datetime | None = None

    model_config = {"from_attributes": True}


class ApprovalAction(BaseModel):
    """
    What the manager sends when they approve or reject.

    Examples:
      {"action": "approve", "comment": "Verified, all documents look good"}
      {"action": "reject", "comment": "Missing tax documentation, please resubmit"}
    """
    action: str = Field(
        ...,
        description="Either 'approve' or 'reject'",
    )
    comment: str | None = Field(
        None,
        max_length=1000,
        description="Explanation for the decision (required for rejections)",
    )


class ApprovalSummary(BaseModel):
    """
    Quick stats for the approval dashboard header.
    Shown as badges: "Pending (3) | Approved (12) | Rejected (2)"
    """
    pending: int = 0
    approved: int = 0
    rejected: int = 0
    total: int = 0
