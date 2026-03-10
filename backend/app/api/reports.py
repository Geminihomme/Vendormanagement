"""
REPORTS API ROUTES (The Download Center)
==========================================
These endpoints generate and serve downloadable report files.

ENDPOINTS:
  --- CSV Exports (raw data) ---
  GET /api/reports/vendors/csv       -> Download vendors as CSV
  GET /api/reports/contracts/csv     -> Download contracts as CSV
  GET /api/reports/payments/csv      -> Download payments as CSV

  --- Excel Reports (formatted, multi-sheet) ---
  GET /api/reports/spend/excel       -> Vendor spend report (.xlsx)
  GET /api/reports/expiry/excel      -> Contract expiration report (.xlsx)
  GET /api/reports/risk/excel        -> Risk assessment report (.xlsx)

HOW FILE DOWNLOADS WORK:
==========================
Normal API responses send JSON (data as text). File downloads are different:

1. We set special headers telling the browser "this is a FILE, not a web page"
2. The Content-Type header says WHAT kind of file (CSV or Excel)
3. The Content-Disposition header says the FILENAME and tells the browser to download

When the browser sees these headers, instead of showing the data on screen,
it pops up the "Save As" dialog. It's like when you click "Print to PDF" —
the data gets packaged into a file for you.

EXAMPLE HEADERS:
  Content-Type: text/csv
  Content-Disposition: attachment; filename="vendors_2026-02-08.csv"
  (The browser sees "attachment" and downloads instead of displaying)
"""

from datetime import date

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import report_service
from app.auth import get_current_user
from app.models.user import User

router = APIRouter()

# Helper to build a filename with today's date
def _dated(name: str, ext: str) -> str:
    return f"{name}_{date.today().isoformat()}.{ext}"


# ===================================================================
# CSV EXPORTS — Raw data, universal compatibility
# ===================================================================

@router.get("/vendors/csv")
def export_vendors_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download all vendors as a CSV file."""
    csv_content = report_service.generate_vendors_csv(db)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{_dated("vendors", "csv")}"'
        },
    )


@router.get("/contracts/csv")
def export_contracts_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download all contracts as a CSV file."""
    csv_content = report_service.generate_contracts_csv(db)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{_dated("contracts", "csv")}"'
        },
    )


@router.get("/payments/csv")
def export_payments_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Download all payments as a CSV file."""
    csv_content = report_service.generate_payments_csv(db)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{_dated("payments", "csv")}"'
        },
    )


# ===================================================================
# EXCEL REPORTS — Formatted, multi-sheet, professional-looking
# ===================================================================

@router.get("/spend/excel")
def export_spend_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Download the Vendor Spend Report as Excel.
    Contains 4 sheets: Summary, By Vendor, Monthly Trend, All Payments.
    """
    excel_bytes = report_service.generate_spend_report_excel(db)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{_dated("spend_report", "xlsx")}"'
        },
    )


@router.get("/expiry/excel")
def export_expiry_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Download the Contract Expiration Report as Excel.
    Contains 2 sheets: Expiring Soon (90 days), All Contracts.
    Rows are color-coded by urgency.
    """
    excel_bytes = report_service.generate_contract_expiry_report_excel(db)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{_dated("contract_expiry_report", "xlsx")}"'
        },
    )


@router.get("/risk/excel")
def export_risk_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Download the Risk Assessment Report as Excel.
    Contains 2 sheets: Risk Summary (counts), Detailed Scores (every vendor).
    High-risk rows are highlighted.
    """
    excel_bytes = report_service.generate_risk_report_excel(db)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{_dated("risk_report", "xlsx")}"'
        },
    )
