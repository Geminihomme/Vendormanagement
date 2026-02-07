"""
PAYMENT SCHEMAS (Data Validation)
====================================
Controls what payment data looks like when it goes in and out of the API.

KEY DESIGN:
- PaymentCreate requires vendor_id and amount (who did we pay, how much?)
- PaymentResponse includes vendor_name and contract_title so the
  frontend doesn't need extra API calls
- Analytics schemas define the shape of aggregated data (totals, monthly)
"""

from datetime import datetime, date
from pydantic import BaseModel, Field


class PaymentCreate(BaseModel):
    """Schema for recording a new payment."""
    vendor_id: int = Field(..., description="Which vendor was paid")
    contract_id: int | None = Field(None, description="Which contract this is for (optional)")
    amount: float = Field(..., gt=0, description="Payment amount in dollars (must be > 0)")
    payment_date: date = Field(..., description="When the payment was made")
    invoice_number: str | None = Field(None, max_length=100, description="Invoice/reference number")
    description: str | None = Field(None, description="What was this payment for?")
    status: str = Field("paid", description="Payment status")
    payment_method: str | None = Field(None, description="How the payment was made")


class PaymentUpdate(BaseModel):
    """Schema for updating a payment. All fields optional."""
    vendor_id: int | None = None
    contract_id: int | None = None
    amount: float | None = Field(None, gt=0)
    payment_date: date | None = None
    invoice_number: str | None = Field(None, max_length=100)
    description: str | None = None
    status: str | None = None
    payment_method: str | None = None


class PaymentResponse(BaseModel):
    """Schema for returning payment data."""
    id: int
    vendor_id: int
    vendor_name: str | None = None        # Convenience: "Acme IT Solutions"
    contract_id: int | None = None
    contract_title: str | None = None     # Convenience: "Annual IT Support"
    amount: float
    payment_date: date
    invoice_number: str | None = None
    description: str | None = None
    status: str
    payment_method: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class VendorSpendSummary(BaseModel):
    """
    How much we've spent with a specific vendor.

    ANALOGY - Excel Pivot Table:
    This is like using a pivot table in Excel to group payments by vendor
    and calculate the SUM, COUNT, and AVG for each group.
    """
    vendor_id: int
    vendor_name: str
    total_spent: float           # SUM of all payments
    payment_count: int           # COUNT of payments
    average_payment: float       # AVG payment amount
    last_payment_date: date | None = None  # Most recent payment


class MonthlySpend(BaseModel):
    """
    Total spending for a specific month.

    ANALOGY - Monthly Bank Statement:
    Like looking at your bank statement month by month:
    "January: $15,000, February: $12,000, March: $18,000..."
    """
    year: int
    month: int
    month_name: str              # "January", "February", etc.
    total_spent: float
    payment_count: int
