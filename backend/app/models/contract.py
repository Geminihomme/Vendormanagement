"""
CONTRACT DATABASE MODEL
========================
This file defines the "contracts" table in our database.

WHAT IS A CONTRACT?
A contract is a formal agreement between our company and a vendor.
It tracks: what we agreed to, how much it costs, when it starts/ends,
and who in our company created it.

WHY WE NEED A CONTRACTS TABLE:
Vendors are the "who." Contracts are the "what, when, and how much."
You might work with Acme IT Solutions (vendor), but you have SPECIFIC
agreements with them: "Annual IT Support, $50,000, Jan-Dec 2025."

FOREIGN KEYS (The Key Concept in This File):
============================================
A foreign key is like a reference or pointer to another table.

Imagine a sticky note on a contract that says "See Vendor #1 for details."
That sticky note IS the foreign key -- it doesn't contain the vendor's
full information, just a pointer to where it lives.

In database terms:
- vendor_id = 1 means "this contract belongs to the vendor with id=1"
- created_by_id = 2 means "this contract was created by user with id=2"

WHY foreign keys instead of copying data?
If Acme changes their email, we update it in ONE place (vendors table).
Without foreign keys, we'd have to find and update every contract that
mentions Acme -- error-prone and wasteful.

EXAMPLE DATA:
| id | title              | vendor_id | created_by_id | value    | status |
|----|--------------------|-----------|---------------|----------|--------|
| 1  | Annual IT Support  | 1 (Acme)  | 1 (Sarah)     | 50000.00 | active |
| 2  | Office Cleaning Q1 | 2 (Clean) | 2 (Mike)      | 12000.00 | draft  |
| 3  | Security Audit     | 1 (Acme)  | 1 (Sarah)     | 15000.00 | expired|

Notice vendor_id=1 appears twice: Acme has two contracts with us.
"""

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class ContractStatus(str, enum.Enum):
    """
    Contracts go through their own lifecycle:
    - DRAFT: Being written, not yet official
    - PENDING_APPROVAL: Waiting for a manager to approve
    - ACTIVE: Currently in effect
    - EXPIRED: Past the end date
    - TERMINATED: Ended early by either party
    - RENEWED: Replaced by a new contract
    """
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    RENEWED = "renewed"


class Contract(Base):
    """
    The Contracts table - stores all agreements with vendors.

    This table has TWO foreign keys:
    1. vendor_id -> links to the vendors table
    2. created_by_id -> links to the users table

    Think of it as the "bridge" between vendors and users.
    """

    __tablename__ = "contracts"

    # --- COLUMNS ---

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Basic contract info
    title = Column(String(255), nullable=False)      # e.g., "Annual IT Support Agreement"
    description = Column(Text, nullable=True)         # Detailed description of the agreement
    contract_number = Column(String(100), nullable=True, unique=True, index=True)
    # A human-readable contract ID like "CNT-2025-001".
    # unique=True: no two contracts share the same number.
    # index=True: makes searching by contract number fast.

    # --- FOREIGN KEYS ---
    # These are the "sticky notes" that point to other tables.

    # Which vendor is this contract with?
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)
    # ForeignKey("vendors.id") means: "this column must contain a value
    # that exists in the 'id' column of the 'vendors' table."
    # If you try to set vendor_id=999 but vendor 999 doesn't exist,
    # the database will reject it. This prevents "orphan" contracts.

    # Which user in our system created this contract?
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    # nullable=True because we might import old contracts where we don't
    # know who originally created them.

    # Financial details
    value = Column(Float, nullable=True)             # Total contract value
    # Float is used for simplicity. In a real financial system, you'd use
    # Decimal for exact precision (floats can have tiny rounding errors).

    # Currency — which currency the value is stored in (ISO 4217 code).
    # Like a price tag in a store: the number alone isn't enough,
    # you need to know if it's $50 or 50 or 50.
    currency = Column(String(3), nullable=False, default="USD")

    # Timeline
    start_date = Column(Date, nullable=True)         # When the contract begins
    end_date = Column(Date, nullable=True)           # When the contract expires

    # Status tracking
    status = Column(String(20), nullable=False, default=ContractStatus.DRAFT)

    # Document reference (where the actual PDF/file is stored)
    document_url = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- RELATIONSHIPS ---
    # These let us navigate between related objects in Python.

    # contract.vendor gives you the full Vendor object
    # (not just the ID, but all fields like name, email, etc.)
    vendor = relationship("Vendor", back_populates="contracts")

    # contract.created_by gives you the full User object who created this contract
    created_by = relationship("User", back_populates="contracts")
