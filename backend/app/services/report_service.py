"""
REPORT SERVICE (The Report Printer)
======================================
This service generates downloadable reports in CSV and Excel formats.

HOW REPORT GENERATION WORKS:
==============================
Think of it like using a printer at the office:

1. GATHER DATA: Pull records from the database (like pulling files from a cabinet)
2. FORMAT: Arrange the data into rows and columns (like filling out a spreadsheet)
3. PACKAGE: Save it as a file (CSV or Excel)
4. DELIVER: Send the file to the user's browser (automatic download)

FILE FORMAT DIFFERENCES:
=========================
CSV (Comma-Separated Values):
  - Plain text file: "Name,Email,Status\nAcme,acme@co.com,active"
  - Opens in ANY spreadsheet app (Excel, Google Sheets, Numbers)
  - Tiny file size
  - No formatting (no bold, no colors)
  - Best for: importing data into other systems, raw data analysis

Excel (.xlsx):
  - Formatted spreadsheet with styled headers, column widths, number formatting
  - Multiple sheets in one file (e.g., "Summary" + "Details")
  - Supports bold headers, currency formatting, date formatting
  - Best for: sharing with colleagues, professional-looking reports

WHEN TO USE WHICH:
  CSV  → "I need to import this into another system" or "Just give me the raw data"
  Excel → "I need to email this to my boss" or "I want it to look polished"
"""

import csv
import io
import logging
from datetime import date, datetime

from sqlalchemy.orm import Session
from sqlalchemy import func
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, numbers

from app.models.vendor import Vendor
from app.models.contract import Contract
from app.models.payment import Payment
from app.models.risk_assessment import RiskAssessment

logger = logging.getLogger(__name__)


# ===================================================================
# CSV GENERATORS
# ===================================================================

def generate_vendors_csv(db: Session) -> str:
    """
    Export all vendors as CSV.
    Each row = one vendor. Columns = all vendor fields.
    """
    vendors = db.query(Vendor).order_by(Vendor.name).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        "ID", "Name", "Email", "Phone", "Website", "Category",
        "Status", "Tax ID", "City", "State", "Country", "Created"
    ])

    # Data rows
    for v in vendors:
        writer.writerow([
            v.id, v.name, v.email, v.phone or "", v.website or "",
            v.category or "", v.status, v.tax_id or "",
            v.city or "", v.state or "", v.country or "",
            v.created_at.strftime("%Y-%m-%d") if v.created_at else "",
        ])

    return output.getvalue()


def generate_contracts_csv(db: Session) -> str:
    """Export all contracts as CSV with vendor names."""
    contracts = (
        db.query(Contract, Vendor.name)
        .outerjoin(Vendor, Contract.vendor_id == Vendor.id)
        .order_by(Contract.end_date)
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "ID", "Title", "Contract Number", "Vendor", "Value", "Currency",
        "Start Date", "End Date", "Status", "Has Document", "Created"
    ])

    for contract, vendor_name in contracts:
        writer.writerow([
            contract.id, contract.title, contract.contract_number or "",
            vendor_name or "", f"{contract.value:.2f}" if contract.value else "0.00",
            getattr(contract, "currency", "USD") or "USD",
            str(contract.start_date) if contract.start_date else "",
            str(contract.end_date) if contract.end_date else "",
            contract.status, "Yes" if contract.document_url else "No",
            contract.created_at.strftime("%Y-%m-%d") if contract.created_at else "",
        ])

    return output.getvalue()


def generate_payments_csv(db: Session) -> str:
    """Export all payments as CSV with vendor and contract names."""
    payments = (
        db.query(Payment, Vendor.name, Contract.title)
        .outerjoin(Vendor, Payment.vendor_id == Vendor.id)
        .outerjoin(Contract, Payment.contract_id == Contract.id)
        .order_by(Payment.payment_date.desc())
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "ID", "Vendor", "Contract", "Amount", "Currency", "Payment Date",
        "Invoice Number", "Status", "Payment Method", "Description"
    ])

    for payment, vendor_name, contract_title in payments:
        writer.writerow([
            payment.id, vendor_name or "", contract_title or "",
            f"{float(payment.amount):.2f}", getattr(payment, "currency", "USD") or "USD",
            str(payment.payment_date),
            payment.invoice_number or "", payment.status,
            payment.payment_method or "", payment.description or "",
        ])

    return output.getvalue()


# ===================================================================
# EXCEL REPORT GENERATORS
# ===================================================================

def _style_header_row(ws, col_count: int):
    """Apply professional styling to the header row of a worksheet."""
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="1A1A2E", end_color="1A1A2E", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center")

    for col in range(1, col_count + 1):
        cell = ws.cell(row=1, column=col)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align


def _auto_column_widths(ws):
    """Auto-size columns based on content length."""
    for column_cells in ws.columns:
        max_length = 0
        column_letter = column_cells[0].column_letter
        for cell in column_cells:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
        ws.column_dimensions[column_letter].width = min(max_length + 4, 40)


def generate_spend_report_excel(db: Session) -> bytes:
    """
    VENDOR SPEND REPORT (Excel)
    =============================
    A professional multi-sheet report with:
    - Sheet 1: "Summary" — Overall spending stats
    - Sheet 2: "By Vendor" — Total spend per vendor (sorted highest first)
    - Sheet 3: "Monthly" — Month-by-month spending trend
    - Sheet 4: "All Payments" — Every payment record

    This is the report you'd email to the CFO.
    """
    wb = Workbook()

    # --- SHEET 1: SUMMARY ---
    ws_summary = wb.active
    ws_summary.title = "Summary"

    # Overall stats
    total_spent = db.query(func.sum(Payment.amount)).filter(Payment.status == "paid").scalar() or 0
    payment_count = db.query(func.count(Payment.id)).filter(Payment.status == "paid").scalar() or 0
    vendor_count = db.query(func.count(func.distinct(Payment.vendor_id))).scalar() or 0
    avg_payment = total_spent / payment_count if payment_count > 0 else 0

    ws_summary.append(["Vendor Spend Report"])
    ws_summary.append(["Generated", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")])
    ws_summary.append([])
    ws_summary.append(["Metric", "Value"])
    ws_summary.append(["Total Spent", total_spent])
    ws_summary.append(["Total Payments", payment_count])
    ws_summary.append(["Average Payment", avg_payment])
    ws_summary.append(["Vendors with Payments", vendor_count])

    # Style the title
    ws_summary["A1"].font = Font(bold=True, size=16)
    ws_summary.column_dimensions["A"].width = 25
    ws_summary.column_dimensions["B"].width = 20
    for row in range(5, 9):
        ws_summary.cell(row=row, column=2).number_format = numbers.FORMAT_NUMBER_COMMA_SEPARATED1

    # --- SHEET 2: BY VENDOR ---
    ws_vendor = wb.create_sheet("By Vendor")
    ws_vendor.append(["Vendor", "Total Spent", "Payment Count", "Average Payment"])
    _style_header_row(ws_vendor, 4)

    vendor_spend = (
        db.query(
            Vendor.name,
            func.sum(Payment.amount).label("total"),
            func.count(Payment.id).label("count"),
            func.avg(Payment.amount).label("avg"),
        )
        .join(Vendor, Payment.vendor_id == Vendor.id)
        .filter(Payment.status == "paid")
        .group_by(Vendor.name)
        .order_by(func.sum(Payment.amount).desc())
        .all()
    )

    for name, total, count, avg in vendor_spend:
        ws_vendor.append([name, float(total or 0), count, float(avg or 0)])

    # Format currency columns
    for row in ws_vendor.iter_rows(min_row=2, min_col=2, max_col=4):
        for cell in row:
            cell.number_format = numbers.FORMAT_NUMBER_COMMA_SEPARATED1

    _auto_column_widths(ws_vendor)

    # --- SHEET 3: MONTHLY ---
    ws_monthly = wb.create_sheet("Monthly Trend")
    ws_monthly.append(["Year", "Month", "Total Spent", "Payment Count"])
    _style_header_row(ws_monthly, 4)

    from sqlalchemy import extract
    monthly = (
        db.query(
            extract("year", Payment.payment_date).label("year"),
            extract("month", Payment.payment_date).label("month"),
            func.sum(Payment.amount).label("total"),
            func.count(Payment.id).label("count"),
        )
        .filter(Payment.status == "paid")
        .group_by("year", "month")
        .order_by("year", "month")
        .all()
    )

    for year, month, total, count in monthly:
        ws_monthly.append([int(year), int(month), float(total or 0), count])

    for row in ws_monthly.iter_rows(min_row=2, min_col=3, max_col=3):
        for cell in row:
            cell.number_format = numbers.FORMAT_NUMBER_COMMA_SEPARATED1

    _auto_column_widths(ws_monthly)

    # --- SHEET 4: ALL PAYMENTS ---
    ws_payments = wb.create_sheet("All Payments")
    ws_payments.append([
        "Date", "Vendor", "Contract", "Amount", "Currency", "Invoice #",
        "Status", "Method", "Description"
    ])
    _style_header_row(ws_payments, 9)

    payments = (
        db.query(Payment, Vendor.name, Contract.title)
        .outerjoin(Vendor, Payment.vendor_id == Vendor.id)
        .outerjoin(Contract, Payment.contract_id == Contract.id)
        .order_by(Payment.payment_date.desc())
        .all()
    )

    for payment, vendor_name, contract_title in payments:
        ws_payments.append([
            payment.payment_date.strftime("%Y-%m-%d") if payment.payment_date else "",
            vendor_name or "", contract_title or "",
            float(payment.amount), getattr(payment, "currency", "USD") or "USD",
            payment.invoice_number or "",
            payment.status, payment.payment_method or "",
            payment.description or "",
        ])

    for row in ws_payments.iter_rows(min_row=2, min_col=4, max_col=4):
        for cell in row:
            cell.number_format = numbers.FORMAT_NUMBER_COMMA_SEPARATED1

    _auto_column_widths(ws_payments)

    # Save to bytes
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def generate_contract_expiry_report_excel(db: Session) -> bytes:
    """
    CONTRACT EXPIRATION REPORT (Excel)
    =====================================
    Shows all contracts sorted by end date (soonest first).
    Highlights expired and soon-to-expire contracts.
    Two sheets: "Expiring Soon" (within 90 days) and "All Contracts".
    """
    wb = Workbook()
    today = date.today()

    # Gather all contracts with vendor names
    contracts = (
        db.query(Contract, Vendor.name)
        .outerjoin(Vendor, Contract.vendor_id == Vendor.id)
        .order_by(Contract.end_date)
        .all()
    )

    headers = [
        "Title", "Contract #", "Vendor", "Value", "Currency",
        "Start Date", "End Date", "Days Remaining",
        "Status", "Urgency"
    ]

    def _urgency(end_dt):
        if not end_dt:
            return "unknown", 0
        days = (end_dt - today).days
        if days < 0:
            return "EXPIRED", days
        elif days <= 30:
            return "CRITICAL", days
        elif days <= 60:
            return "WARNING", days
        elif days <= 90:
            return "ATTENTION", days
        else:
            return "OK", days

    # Colors for urgency
    fills = {
        "EXPIRED": PatternFill(start_color="F8D7DA", end_color="F8D7DA", fill_type="solid"),
        "CRITICAL": PatternFill(start_color="F8D7DA", end_color="F8D7DA", fill_type="solid"),
        "WARNING": PatternFill(start_color="FFF3CD", end_color="FFF3CD", fill_type="solid"),
        "ATTENTION": PatternFill(start_color="CCE5FF", end_color="CCE5FF", fill_type="solid"),
    }

    def _write_contracts(ws, contract_list):
        ws.append(headers)
        _style_header_row(ws, len(headers))

        for contract, vendor_name in contract_list:
            urgency, days = _urgency(contract.end_date)
            row_idx = ws.max_row + 1
            ws.append([
                contract.title, contract.contract_number or "",
                vendor_name or "", float(contract.value or 0),
                getattr(contract, "currency", "USD") or "USD",
                str(contract.start_date) if contract.start_date else "",
                str(contract.end_date) if contract.end_date else "",
                days, contract.status, urgency,
            ])
            # Color the row by urgency
            if urgency in fills:
                for col in range(1, len(headers) + 1):
                    ws.cell(row=row_idx, column=col).fill = fills[urgency]

        _auto_column_widths(ws)

    # --- SHEET 1: EXPIRING SOON (within 90 days) ---
    ws_expiring = wb.active
    ws_expiring.title = "Expiring Soon"

    expiring = [
        (c, v) for c, v in contracts
        if c.end_date and c.status == "active"
        and (c.end_date - today).days <= 90
    ]
    _write_contracts(ws_expiring, expiring)

    if not expiring:
        ws_expiring.append([])
        ws_expiring.append(["No contracts expiring within 90 days."])

    # --- SHEET 2: ALL CONTRACTS ---
    ws_all = wb.create_sheet("All Contracts")
    _write_contracts(ws_all, contracts)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


def generate_risk_report_excel(db: Session) -> bytes:
    """
    RISK ASSESSMENT REPORT (Excel)
    =================================
    Shows all vendors with their risk scores and factor breakdowns.
    Two sheets: "Risk Summary" and "Detailed Scores".
    """
    wb = Workbook()

    # Gather risk data
    assessments = (
        db.query(RiskAssessment, Vendor.name, Vendor.category, Vendor.status)
        .join(Vendor, RiskAssessment.vendor_id == Vendor.id)
        .order_by(RiskAssessment.overall_score.desc())
        .all()
    )

    # Risk level colors
    risk_fills = {
        "critical": PatternFill(start_color="F8D7DA", end_color="F8D7DA", fill_type="solid"),
        "high": PatternFill(start_color="FFE0CC", end_color="FFE0CC", fill_type="solid"),
        "medium": PatternFill(start_color="FFF3CD", end_color="FFF3CD", fill_type="solid"),
    }

    # --- SHEET 1: SUMMARY ---
    ws_summary = wb.active
    ws_summary.title = "Risk Summary"

    ws_summary.append(["Risk Assessment Report"])
    ws_summary.append(["Generated", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")])
    ws_summary.append([])
    ws_summary["A1"].font = Font(bold=True, size=16)

    # Count by level
    level_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    for a, *_ in assessments:
        level_counts[a.risk_level.value] += 1

    ws_summary.append(["Risk Level", "Vendor Count"])
    ws_summary.append(["Critical", level_counts["critical"]])
    ws_summary.append(["High", level_counts["high"]])
    ws_summary.append(["Medium", level_counts["medium"]])
    ws_summary.append(["Low", level_counts["low"]])
    ws_summary.append(["Total", sum(level_counts.values())])

    ws_summary.column_dimensions["A"].width = 20
    ws_summary.column_dimensions["B"].width = 15

    # --- SHEET 2: DETAILED SCORES ---
    ws_detail = wb.create_sheet("Detailed Scores")

    headers = [
        "Vendor", "Category", "Status", "Overall Score", "Risk Level",
        "Contract Value", "Expiry", "Compliance", "Payment Health"
    ]
    ws_detail.append(headers)
    _style_header_row(ws_detail, len(headers))

    for assessment, vendor_name, category, status in assessments:
        row_idx = ws_detail.max_row + 1
        ws_detail.append([
            vendor_name, category or "", status,
            round(assessment.overall_score, 1),
            assessment.risk_level.value.upper(),
            round(assessment.contract_value_score, 1),
            round(assessment.expiry_score, 1),
            round(assessment.compliance_score, 1),
            round(assessment.payment_score, 1),
        ])
        # Color high-risk rows
        level = assessment.risk_level.value
        if level in risk_fills:
            for col in range(1, len(headers) + 1):
                ws_detail.cell(row=row_idx, column=col).fill = risk_fills[level]

    _auto_column_widths(ws_detail)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()
