"""
PAYMENT SERVICE (The Accountant)
==================================
Handles all payment CRUD operations AND the analytics calculations.

HOW ANALYTICS WORK (The "Spreadsheet Formulas" of Databases):
================================================================
When you want to know "total spent per vendor," you're doing the same
thing as the SUM() function in a spreadsheet. The database version:

Spreadsheet:                    Database (SQL):
=SUM(B2:B100)                   SELECT SUM(amount) FROM payments
=SUMIF(A:A,"Acme",B:B)          SELECT SUM(amount) FROM payments WHERE vendor_id=1
Subtotals by vendor              SELECT vendor_id, SUM(amount) GROUP BY vendor_id

SQLAlchemy lets us write these queries in Python instead of raw SQL:
  db.query(func.sum(Payment.amount)).filter(Payment.vendor_id == 1)

MULTI-CURRENCY ANALYTICS:
===========================
Since payments can be in different currencies (USD, EUR, GBP), we can't
just SUM them directly — that would be like adding dollars and euros.

Instead, we convert each payment to the user's DISPLAY currency first,
then sum. Think of it like a currency exchange at the airport:
before counting your total, you exchange all your leftover bills into
one currency so you can add them up.

KEY ANALYTICS WE CALCULATE:
1. Total spend per vendor    (GROUP BY vendor_id, convert amounts)
2. Monthly spend over time   (GROUP BY year, month, convert amounts)
3. Overall spend summary     (SUM, COUNT, AVG — all in display currency)
"""

import calendar
from datetime import date
from sqlalchemy import func, extract
from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.models.vendor import Vendor
from app.models.contract import Contract
from app.schemas.payment import PaymentCreate, PaymentUpdate
from app.services.currency_service import convert, get_rates_dict


def get_payments(db: Session, skip: int = 0, limit: int = 100) -> list[dict]:
    """Get all payments, newest first."""
    payments = (
        db.query(Payment)
        .order_by(Payment.payment_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [_enrich_payment(p) for p in payments]


def get_payment(db: Session, payment_id: int) -> dict | None:
    """Get a single payment by ID."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if payment:
        return _enrich_payment(payment)
    return None


def get_vendor_payments(db: Session, vendor_id: int) -> list[dict]:
    """Get all payments for a specific vendor."""
    payments = (
        db.query(Payment)
        .filter(Payment.vendor_id == vendor_id)
        .order_by(Payment.payment_date.desc())
        .all()
    )
    return [_enrich_payment(p) for p in payments]


def create_payment(db: Session, payment: PaymentCreate) -> dict:
    """Record a new payment."""
    db_payment = Payment(**payment.model_dump())
    db.add(db_payment)
    db.commit()
    db.refresh(db_payment)
    return _enrich_payment(db_payment)


def update_payment(db: Session, payment_id: int, payment_update: PaymentUpdate) -> dict | None:
    """Update an existing payment."""
    db_payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not db_payment:
        return None

    update_data = payment_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_payment, field, value)

    db.commit()
    db.refresh(db_payment)
    return _enrich_payment(db_payment)


def delete_payment(db: Session, payment_id: int) -> bool:
    """Delete a payment record."""
    db_payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not db_payment:
        return False
    db.delete(db_payment)
    db.commit()
    return True


# ====================================================================
# ANALYTICS FUNCTIONS (The "Spreadsheet Formulas")
# ====================================================================

def get_spend_by_vendor(db: Session, display_currency: str = "USD") -> list[dict]:
    """
    Calculate total spending PER VENDOR, converted to display_currency.

    THIS IS LIKE A PIVOT TABLE IN EXCEL:
    If your spreadsheet has columns: [Vendor, Amount]
    A pivot table would group by Vendor and SUM the Amount column.

    MULTI-CURRENCY TWIST:
    Since each payment might be in a different currency (like getting
    receipts in USD, EUR, and GBP from a business trip), we can't
    just SUM them directly. We convert each to the target currency first.
    """
    rates = get_rates_dict(db)

    # Get all paid payments (we need individual rows for currency conversion)
    payments = (
        db.query(Payment)
        .filter(Payment.status == "paid")
        .all()
    )

    # Group by vendor and convert as we go
    vendor_totals: dict[int, dict] = {}
    for p in payments:
        vid = p.vendor_id
        converted = convert(p.amount, getattr(p, "currency", "USD"), display_currency, rates)

        if vid not in vendor_totals:
            vendor_totals[vid] = {
                "total": 0.0,
                "count": 0,
                "last_date": None,
            }

        vendor_totals[vid]["total"] += converted
        vendor_totals[vid]["count"] += 1
        last = vendor_totals[vid]["last_date"]
        if last is None or p.payment_date > last:
            vendor_totals[vid]["last_date"] = p.payment_date

    summaries = []
    for vid, data in vendor_totals.items():
        vendor = db.query(Vendor).filter(Vendor.id == vid).first()
        summaries.append({
            "vendor_id": vid,
            "vendor_name": vendor.name if vendor else "Unknown",
            "total_spent": round(data["total"], 2),
            "payment_count": data["count"],
            "average_payment": round(data["total"] / data["count"], 2) if data["count"] else 0,
            "last_payment_date": data["last_date"],
            "display_currency": display_currency,
        })

    # Sort by total spent descending (biggest spender first)
    summaries.sort(key=lambda x: x["total_spent"], reverse=True)
    return summaries


def get_monthly_spend(db: Session, year: int | None = None, display_currency: str = "USD") -> list[dict]:
    """
    Calculate total spending PER MONTH, converted to display_currency.

    THIS IS LIKE A MONTHLY BANK STATEMENT:
    "January: 15,000 EUR (5 payments)"
    "February: 12,000 EUR (3 payments)"

    MULTI-CURRENCY NOTE:
    We fetch individual payments and convert each one before summing
    by month, rather than using SQL SUM() directly. This is like
    exchanging each receipt into EUR before adding up your monthly total.
    """
    rates = get_rates_dict(db)

    query = db.query(Payment).filter(Payment.status == "paid")
    if year:
        query = query.filter(extract('year', Payment.payment_date) == year)

    payments = query.all()

    # Group by (year, month) and convert amounts
    monthly_buckets: dict[tuple[int, int], dict] = {}
    for p in payments:
        yr = p.payment_date.year
        mo = p.payment_date.month
        key = (yr, mo)
        converted = convert(p.amount, getattr(p, "currency", "USD"), display_currency, rates)

        if key not in monthly_buckets:
            monthly_buckets[key] = {"total": 0.0, "count": 0}
        monthly_buckets[key]["total"] += converted
        monthly_buckets[key]["count"] += 1

    # Sort by date and build results
    monthly_data = []
    for (yr, mo) in sorted(monthly_buckets.keys()):
        data = monthly_buckets[(yr, mo)]
        monthly_data.append({
            "year": yr,
            "month": mo,
            "month_name": calendar.month_name[mo],
            "total_spent": round(data["total"], 2),
            "payment_count": data["count"],
            "display_currency": display_currency,
        })

    return monthly_data


def get_spend_summary(db: Session, display_currency: str = "USD") -> dict:
    """
    Overall spending summary — the "executive report," converted to display_currency.

    Like the TOTAL row at the bottom of a spreadsheet:
    Total Spent: 250,000 EUR
    Number of Payments: 47
    Average Payment: 5,319.15 EUR
    Number of Vendors: 8
    """
    rates = get_rates_dict(db)

    payments = db.query(Payment).filter(Payment.status == "paid").all()

    total = 0.0
    vendor_ids = set()
    for p in payments:
        total += convert(p.amount, getattr(p, "currency", "USD"), display_currency, rates)
        vendor_ids.add(p.vendor_id)

    count = len(payments)

    return {
        "total_spent": round(total, 2),
        "payment_count": count,
        "average_payment": round(total / count, 2) if count else 0,
        "vendor_count": len(vendor_ids),
        "display_currency": display_currency,
    }


def get_vendor_monthly_spend(db: Session, vendor_id: int, display_currency: str = "USD") -> list[dict]:
    """
    Monthly spending for a SPECIFIC vendor, converted to display_currency.
    Used to show the line chart on a vendor's detail page.
    """
    rates = get_rates_dict(db)

    payments = (
        db.query(Payment)
        .filter(Payment.vendor_id == vendor_id, Payment.status == "paid")
        .all()
    )

    monthly_buckets: dict[tuple[int, int], dict] = {}
    for p in payments:
        yr = p.payment_date.year
        mo = p.payment_date.month
        key = (yr, mo)
        converted = convert(p.amount, getattr(p, "currency", "USD"), display_currency, rates)

        if key not in monthly_buckets:
            monthly_buckets[key] = {"total": 0.0, "count": 0}
        monthly_buckets[key]["total"] += converted
        monthly_buckets[key]["count"] += 1

    return [
        {
            "year": yr,
            "month": mo,
            "month_name": calendar.month_name[mo],
            "total_spent": round(data["total"], 2),
            "payment_count": data["count"],
            "display_currency": display_currency,
        }
        for (yr, mo), data in sorted(monthly_buckets.items())
    ]


def _enrich_payment(payment: Payment) -> dict:
    """Add vendor_name, contract_title, and currency to a payment."""
    return {
        "id": payment.id,
        "vendor_id": payment.vendor_id,
        "vendor_name": payment.vendor.name if payment.vendor else None,
        "contract_id": payment.contract_id,
        "contract_title": payment.contract.title if payment.contract else None,
        "amount": payment.amount,
        "currency": getattr(payment, "currency", "USD"),
        "payment_date": payment.payment_date,
        "invoice_number": payment.invoice_number,
        "description": payment.description,
        "status": payment.status,
        "payment_method": payment.payment_method,
        "created_at": payment.created_at,
        "updated_at": payment.updated_at,
    }
