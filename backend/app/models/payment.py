"""
PAYMENT DATABASE MODEL (The Checkbook Register)
=================================================
This file defines the "payments" table — a record of every payment
we've made to every vendor.

REAL-WORLD ANALOGY - Your Personal Checkbook:
Every time you write a check, you record:
- WHO you paid (the vendor)
- HOW MUCH you paid (the amount)
- WHEN you paid (the date)
- WHAT it was for (description)
- Which CHECK NUMBER (invoice number)

Our payments table is exactly that, but digital.

WHY WE NEED THIS TABLE:
The vendors table tells us WHO we work with.
The contracts table tells us WHAT we agreed to.
The payments table tells us HOW MUCH we actually paid.

Together, they answer questions like:
- "How much have we paid Acme Corp this year?" (SUM of payments WHERE vendor=Acme)
- "Are we over budget on the IT contract?" (Compare payments vs. contract value)
- "Which month had the highest spending?" (GROUP BY month, ORDER BY total)

LINKING PAYMENTS TO VENDORS (AND OPTIONALLY CONTRACTS):
Each payment MUST be linked to a vendor (vendor_id is required).
A payment CAN optionally be linked to a contract (contract_id is optional)
because some payments might not be tied to a specific contract
(e.g., a one-time purchase).

EXAMPLE DATA:
| id | vendor_id | contract_id | amount    | payment_date | invoice_number | description          |
|----|-----------|-------------|-----------|--------------|----------------|----------------------|
| 1  | 1 (Acme)  | 1           | 4166.67   | 2025-01-15   | INV-2025-001   | Monthly IT support   |
| 2  | 1 (Acme)  | 1           | 4166.67   | 2025-02-15   | INV-2025-012   | Monthly IT support   |
| 3  | 2 (Clean) | 2           | 3000.00   | 2025-01-01   | CLN-Q1-2025    | Q1 cleaning service  |
| 4  | 1 (Acme)  | NULL        | 500.00    | 2025-01-20   | INV-2025-005   | Emergency laptop fix |
"""

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class PaymentStatus(str, enum.Enum):
    """
    Payment status tracking:
    - PENDING: Invoice received, not yet paid
    - PAID: Payment has been made
    - OVERDUE: Past the due date and still not paid
    - CANCELLED: Payment was cancelled (e.g., dispute)
    """
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class PaymentMethod(str, enum.Enum):
    """How the payment was made."""
    BANK_TRANSFER = "bank_transfer"
    CHECK = "check"
    CREDIT_CARD = "credit_card"
    WIRE = "wire"
    OTHER = "other"


class Payment(Base):
    """
    The Payments table — records every payment to every vendor.

    This is the raw data that powers our spend analytics.
    Think of each row as one line in a checkbook register.
    """

    __tablename__ = "payments"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # --- WHO did we pay? (Required) ---
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)

    # --- WHICH contract is this payment for? (Optional) ---
    # Some payments might not be tied to a specific contract
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=True, index=True)

    # --- HOW MUCH did we pay? ---
    amount = Column(Float, nullable=False)

    # --- WHEN did we pay? ---
    payment_date = Column(Date, nullable=False)

    # --- REFERENCE INFO ---
    invoice_number = Column(String(100), nullable=True, index=True)
    description = Column(Text, nullable=True)

    # --- STATUS & METHOD ---
    status = Column(String(20), nullable=False, default=PaymentStatus.PAID.value)
    payment_method = Column(String(20), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- RELATIONSHIPS ---
    vendor = relationship("Vendor", backref="payments")
    contract = relationship("Contract", backref="payments")
