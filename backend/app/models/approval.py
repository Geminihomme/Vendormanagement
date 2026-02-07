"""
APPROVAL DATABASE MODEL (The Paper Trail)
============================================
This tracks every approval request in the system.

WHAT IS AN APPROVAL?
Think of it like a formal request form. When someone wants to add a new
vendor or finalize a contract, they can't just do it on their own —
they need a manager's stamp of approval.

THE WORKFLOW (like a document moving through office trays):

    ┌──────────┐      ┌──────────┐      ┌──────────┐
    │ PENDING  │ ───→ │ APPROVED │ ───→ │  ACTIVE  │
    │ (inbox)  │      │ (stamped)│      │ (done!)  │
    └──────────┘      └──────────┘      └──────────┘
         │
         └──────────→ ┌──────────┐
                      │ REJECTED │
                      │ (denied) │
                      └──────────┘

1. PENDING:  Someone submitted a request. It's sitting in the manager's
             inbox, waiting for review.
2. APPROVED: A manager reviewed it and said "Yes, this is good."
             The vendor/contract gets activated.
3. REJECTED: A manager reviewed it and said "No, not this one."
             The vendor/contract stays inactive.

WHAT WE TRACK:
- WHAT needs approval (vendor or contract)
- WHO requested it (the submitter)
- WHO reviewed it (the approver)
- WHEN each step happened
- WHY it was approved or rejected (the comment)

This creates a full audit trail — if anyone asks "who approved vendor X
and why?", we have the answer.

RELATIONSHIPS:
An Approval links to:
- A User who requested it (the submitter)
- A User who reviewed it (the approver)
- Either a Vendor OR a Contract (the thing being approved)
"""

import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship

from app.database import Base


class ApprovalStatus(str, enum.Enum):
    """
    The three possible states of an approval request.

    PENDING = "sitting in the inbox" — no one has reviewed it yet
    APPROVED = "stamped with a green checkmark" — good to go
    REJECTED = "stamped with a red X" — not approved
    """
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalType(str, enum.Enum):
    """
    What kind of thing needs approval.
    We might add more types later (e.g., payment approval).

    VENDOR = a new vendor being added to the system
    CONTRACT = a new contract being finalized
    """
    VENDOR = "vendor"
    CONTRACT = "contract"


class Approval(Base):
    """
    The Approvals table — stores every approval request.

    EXAMPLE DATA:
    | id | type     | entity_id | status   | requested_by | reviewed_by | comment            |
    |----|----------|-----------|----------|--------------|-------------|---------------------|
    | 1  | vendor   | 5         | approved | 3 (Lisa)     | 2 (Mike)    | "Verified, LGTM"   |
    | 2  | contract | 12        | pending  | 3 (Lisa)     | NULL        | NULL                |
    | 3  | vendor   | 8         | rejected | 3 (Lisa)     | 1 (Sarah)   | "Duplicate vendor"  |
    """

    __tablename__ = "approvals"

    # --- PRIMARY KEY ---
    id = Column(Integer, primary_key=True, index=True)

    # --- WHAT NEEDS APPROVAL ---

    # Type of entity: "vendor" or "contract"
    approval_type = Column(
        Enum(ApprovalType),
        nullable=False,
    )

    # The ID of the vendor or contract being approved.
    # We use a plain integer instead of a foreign key because it could
    # reference EITHER the vendors table OR the contracts table.
    entity_id = Column(Integer, nullable=False)

    # Human-readable title (e.g., "Acme Corp" or "Acme IT Support Contract")
    # Stored here so the inbox can show it without extra database lookups.
    entity_title = Column(String(255), nullable=False)

    # --- CURRENT STATUS ---
    status = Column(
        Enum(ApprovalStatus),
        nullable=False,
        default=ApprovalStatus.PENDING,
    )

    # --- WHO IS INVOLVED ---

    # Who submitted this request (the person who created the vendor/contract)
    requested_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    requested_by = relationship("User", foreign_keys=[requested_by_id])

    # Who reviewed it (NULL until someone approves/rejects)
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])

    # --- COMMENTS ---
    # The reviewer's explanation for their decision
    # Required for rejections (must explain why), optional for approvals
    comment = Column(Text, nullable=True)

    # --- TIMESTAMPS ---
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
