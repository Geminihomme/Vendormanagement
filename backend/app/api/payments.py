"""
PAYMENT & ANALYTICS API ROUTES
=================================
These endpoints handle two things:
1. CRUD for individual payments (add, view, edit, delete payments)
2. Analytics endpoints (totals per vendor, monthly spending, summary)

ENDPOINTS:
  --- Payment CRUD ---
  GET    /api/payments/                     -> List all payments
  POST   /api/payments/                     -> Record a new payment
  GET    /api/payments/{id}                 -> Get one payment
  PUT    /api/payments/{id}                 -> Update a payment
  DELETE /api/payments/{id}                 -> Delete a payment
  GET    /api/payments/vendor/{vendor_id}   -> Get all payments for a vendor

  --- Analytics ---
  GET    /api/payments/analytics/summary           -> Overall spend summary
  GET    /api/payments/analytics/by-vendor          -> Total spend per vendor
  GET    /api/payments/analytics/monthly             -> Monthly spending over time
  GET    /api/payments/analytics/vendor/{id}/monthly -> Monthly spend for one vendor

USER JOURNEY: Adding a Payment -> Seeing It in Analytics
=========================================================
1. User goes to /analytics and clicks "Add Payment"
2. Fills out the form: vendor, amount, date, description
3. Clicks Submit → POST /api/payments/ is called
4. Backend saves the payment to the database
5. User is redirected back to /analytics
6. The page reloads, calling the analytics endpoints
7. The charts and tables now include the new payment!

It's like writing a check, putting it in the register, and then
looking at the monthly summary — your new check is automatically
included in the totals.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.payment import PaymentCreate, PaymentUpdate, PaymentResponse
from app.services import payment_service, vendor_service

router = APIRouter()


# ====================================================================
# ANALYTICS ENDPOINTS (must be before /{payment_id} to avoid conflicts)
# ====================================================================
# FastAPI matches routes top-to-bottom. If /{payment_id} came first,
# "analytics" would be treated as a payment ID and cause an error.

@router.get("/analytics/summary")
def get_spend_summary(db: Session = Depends(get_db)):
    """
    Overall spending summary: total spent, payment count, average, vendor count.
    Like the "Grand Total" row at the bottom of a spreadsheet.
    """
    return payment_service.get_spend_summary(db)


@router.get("/analytics/by-vendor")
def get_spend_by_vendor(db: Session = Depends(get_db)):
    """
    Total spending grouped by vendor, sorted by biggest spender first.
    Like a pivot table: "Acme: $50,000 | CleanCo: $12,000 | SecureIT: $8,000"
    """
    return payment_service.get_spend_by_vendor(db)


@router.get("/analytics/monthly")
def get_monthly_spend(
    year: int | None = None,
    db: Session = Depends(get_db),
):
    """
    Monthly spending over time. Optionally filter by year.
    Powers the bar/line chart on the analytics dashboard.
    """
    return payment_service.get_monthly_spend(db, year=year)


@router.get("/analytics/vendor/{vendor_id}/monthly")
def get_vendor_monthly_spend(vendor_id: int, db: Session = Depends(get_db)):
    """Monthly spending for a specific vendor. Powers the vendor drill-down chart."""
    return payment_service.get_vendor_monthly_spend(db, vendor_id)


# ====================================================================
# PAYMENT CRUD ENDPOINTS
# ====================================================================

@router.get("/", response_model=list[PaymentResponse])
def list_payments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all payments, newest first."""
    return payment_service.get_payments(db, skip=skip, limit=limit)


@router.post("/", response_model=PaymentResponse, status_code=201)
def create_payment(payment: PaymentCreate, db: Session = Depends(get_db)):
    """
    Record a new payment.
    Validates that the vendor exists before saving.
    """
    vendor = vendor_service.get_vendor(db, payment.vendor_id)
    if not vendor:
        raise HTTPException(
            status_code=404,
            detail=f"Vendor with id {payment.vendor_id} not found"
        )
    return payment_service.create_payment(db, payment)


@router.get("/vendor/{vendor_id}", response_model=list[PaymentResponse])
def get_vendor_payments(vendor_id: int, db: Session = Depends(get_db)):
    """Get all payments for a specific vendor."""
    return payment_service.get_vendor_payments(db, vendor_id)


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(payment_id: int, db: Session = Depends(get_db)):
    """Get a single payment by ID."""
    payment = payment_service.get_payment(db, payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.put("/{payment_id}", response_model=PaymentResponse)
def update_payment(
    payment_id: int,
    payment_update: PaymentUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing payment."""
    payment = payment_service.update_payment(db, payment_id, payment_update)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment


@router.delete("/{payment_id}", status_code=204)
def delete_payment(payment_id: int, db: Session = Depends(get_db)):
    """Delete a payment record."""
    success = payment_service.delete_payment(db, payment_id)
    if not success:
        raise HTTPException(status_code=404, detail="Payment not found")
