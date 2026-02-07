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

KEY ANALYTICS WE CALCULATE:
1. Total spend per vendor    (GROUP BY vendor_id)
2. Monthly spend over time   (GROUP BY year, month)
3. Overall spend summary     (SUM, COUNT, AVG across all payments)
"""

import calendar
from datetime import date
from sqlalchemy import func, extract
from sqlalchemy.orm import Session

from app.models.payment import Payment
from app.models.vendor import Vendor
from app.models.contract import Contract
from app.schemas.payment import PaymentCreate, PaymentUpdate


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

def get_spend_by_vendor(db: Session) -> list[dict]:
    """
    Calculate total spending PER VENDOR.

    THIS IS LIKE A PIVOT TABLE IN EXCEL:
    If your spreadsheet has columns: [Vendor, Amount]
    A pivot table would group by Vendor and SUM the Amount column.

    The SQL equivalent:
        SELECT vendor_id, SUM(amount), COUNT(*), AVG(amount), MAX(payment_date)
        FROM payments
        WHERE status = 'paid'
        GROUP BY vendor_id

    SQLAlchemy translation (what we write in Python):
        db.query(
            Payment.vendor_id,
            func.sum(Payment.amount),       # = Excel's SUM()
            func.count(Payment.id),         # = Excel's COUNT()
            func.avg(Payment.amount),       # = Excel's AVERAGE()
            func.max(Payment.payment_date), # = Excel's MAX()
        ).group_by(Payment.vendor_id)
    """
    results = (
        db.query(
            Payment.vendor_id,
            func.sum(Payment.amount).label("total_spent"),
            func.count(Payment.id).label("payment_count"),
            func.avg(Payment.amount).label("avg_payment"),
            func.max(Payment.payment_date).label("last_payment"),
        )
        .filter(Payment.status == "paid")
        .group_by(Payment.vendor_id)
        .order_by(func.sum(Payment.amount).desc())  # Biggest spender first
        .all()
    )

    summaries = []
    for row in results:
        vendor = db.query(Vendor).filter(Vendor.id == row.vendor_id).first()
        summaries.append({
            "vendor_id": row.vendor_id,
            "vendor_name": vendor.name if vendor else "Unknown",
            "total_spent": round(float(row.total_spent), 2),
            "payment_count": row.payment_count,
            "average_payment": round(float(row.avg_payment), 2),
            "last_payment_date": row.last_payment,
        })

    return summaries


def get_monthly_spend(db: Session, year: int | None = None) -> list[dict]:
    """
    Calculate total spending PER MONTH.

    THIS IS LIKE A MONTHLY BANK STATEMENT:
    "January: $15,000 (5 payments)"
    "February: $12,000 (3 payments)"
    "March: $18,000 (7 payments)"

    HOW EXTRACT() WORKS:
    extract('month', payment_date) pulls just the month number from a date.
    extract('year', payment_date) pulls just the year.

    It's like using MONTH() and YEAR() functions in Excel:
    =MONTH(A2) returns 1 for January, 2 for February, etc.

    The SQL equivalent:
        SELECT EXTRACT(year FROM payment_date), EXTRACT(month FROM payment_date),
               SUM(amount), COUNT(*)
        FROM payments
        WHERE status = 'paid'
        GROUP BY year, month
        ORDER BY year, month
    """
    query = (
        db.query(
            extract('year', Payment.payment_date).label("year"),
            extract('month', Payment.payment_date).label("month"),
            func.sum(Payment.amount).label("total_spent"),
            func.count(Payment.id).label("payment_count"),
        )
        .filter(Payment.status == "paid")
    )

    if year:
        query = query.filter(extract('year', Payment.payment_date) == year)

    results = (
        query
        .group_by(
            extract('year', Payment.payment_date),
            extract('month', Payment.payment_date),
        )
        .order_by(
            extract('year', Payment.payment_date),
            extract('month', Payment.payment_date),
        )
        .all()
    )

    monthly_data = []
    for row in results:
        month_num = int(row.month)
        monthly_data.append({
            "year": int(row.year),
            "month": month_num,
            "month_name": calendar.month_name[month_num],  # 1 -> "January"
            "total_spent": round(float(row.total_spent), 2),
            "payment_count": row.payment_count,
        })

    return monthly_data


def get_spend_summary(db: Session) -> dict:
    """
    Overall spending summary — the "executive report."

    Like the TOTAL row at the bottom of a spreadsheet:
    Total Spent: $250,000
    Number of Payments: 47
    Average Payment: $5,319.15
    Number of Vendors: 8
    """
    result = (
        db.query(
            func.sum(Payment.amount).label("total_spent"),
            func.count(Payment.id).label("payment_count"),
            func.avg(Payment.amount).label("avg_payment"),
        )
        .filter(Payment.status == "paid")
        .first()
    )

    vendor_count = (
        db.query(func.count(func.distinct(Payment.vendor_id)))
        .filter(Payment.status == "paid")
        .scalar()
    )

    return {
        "total_spent": round(float(result.total_spent or 0), 2),
        "payment_count": result.payment_count or 0,
        "average_payment": round(float(result.avg_payment or 0), 2),
        "vendor_count": vendor_count or 0,
    }


def get_vendor_monthly_spend(db: Session, vendor_id: int) -> list[dict]:
    """
    Monthly spending for a SPECIFIC vendor.
    Used to show the line chart on a vendor's detail page.
    """
    results = (
        db.query(
            extract('year', Payment.payment_date).label("year"),
            extract('month', Payment.payment_date).label("month"),
            func.sum(Payment.amount).label("total_spent"),
            func.count(Payment.id).label("payment_count"),
        )
        .filter(Payment.vendor_id == vendor_id, Payment.status == "paid")
        .group_by(
            extract('year', Payment.payment_date),
            extract('month', Payment.payment_date),
        )
        .order_by(
            extract('year', Payment.payment_date),
            extract('month', Payment.payment_date),
        )
        .all()
    )

    return [
        {
            "year": int(row.year),
            "month": int(row.month),
            "month_name": calendar.month_name[int(row.month)],
            "total_spent": round(float(row.total_spent), 2),
            "payment_count": row.payment_count,
        }
        for row in results
    ]


def _enrich_payment(payment: Payment) -> dict:
    """Add vendor_name and contract_title to a payment."""
    return {
        "id": payment.id,
        "vendor_id": payment.vendor_id,
        "vendor_name": payment.vendor.name if payment.vendor else None,
        "contract_id": payment.contract_id,
        "contract_title": payment.contract.title if payment.contract else None,
        "amount": payment.amount,
        "payment_date": payment.payment_date,
        "invoice_number": payment.invoice_number,
        "description": payment.description,
        "status": payment.status,
        "payment_method": payment.payment_method,
        "created_at": payment.created_at,
        "updated_at": payment.updated_at,
    }
