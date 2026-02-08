"""
RISK SCORING ENGINE (The "Credit Bureau")
============================================
This service calculates risk scores for vendors by analyzing their
contracts, payments, and compliance status.

THE ALGORITHM (step by step):
==============================
For each vendor, we calculate 4 factor scores and add them up:

STEP 1 — CONTRACT VALUE SCORE (0-25 points)
  "How much money is at stake?"
  Like checking the total loan amount on a credit report.
  - Look at ALL active contracts for this vendor
  - Add up their values
  - Higher total = higher risk (more to lose if something goes wrong)

STEP 2 — EXPIRY SCORE (0-25 points)
  "Are contracts about to expire?"
  Like checking if someone has bills coming due soon.
  - Count contracts expiring within 30, 60, and 90 days
  - More expiring soon = higher risk (potential service disruptions)

STEP 3 — COMPLIANCE/DOCUMENTATION SCORE (0-25 points)
  "Are all the papers in order?"
  Like checking if someone has all their financial records.
  - Count contracts that are missing uploaded documents
  - More missing docs = higher risk (can't prove agreements)

STEP 4 — PAYMENT HEALTH SCORE (0-25 points)
  "Do they get paid on time?"
  Like checking payment history on a credit report.
  - Count overdue payments for this vendor
  - Compare to total payments
  - Higher overdue ratio = higher risk

TOTAL = Step1 + Step2 + Step3 + Step4 (0-100)

Then map the total to a risk level:
  0-25:   LOW
  26-50:  MEDIUM
  51-75:  HIGH
  76-100: CRITICAL

WHY THESE SPECIFIC THRESHOLDS?
The thresholds are based on common business risk management practices.
They can be tuned: a conservative company might set "high risk" at 40+,
while a startup might accept up to 60 before flagging.
"""

import logging
from datetime import datetime, date

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.vendor import Vendor
from app.models.contract import Contract
from app.models.payment import Payment
from app.models.risk_assessment import RiskAssessment, RiskLevel
from app.services.currency_service import convert, get_rates_dict

logger = logging.getLogger(__name__)

# --- SCORING THRESHOLDS ---
# Each factor is scored 0-25 (total max = 100)
MAX_FACTOR_SCORE = 25.0

# Contract value thresholds — always measured in USD for consistency.
# All contract values are converted to USD before comparison, regardless
# of what currency they were entered in.
VALUE_THRESHOLDS = [
    (200_000, 25),   # Over $200K  → 25 points (maximum risk)
    (100_000, 20),   # $100K-$200K → 20 points
    (50_000, 16),    # $50K-$100K  → 16 points
    (10_000, 8),     # $10K-$50K   → 8 points
    (0, 0),          # Under $10K  → 0 points (minimal risk)
]

# Risk level brackets
RISK_BRACKETS = [
    (76, RiskLevel.CRITICAL),
    (51, RiskLevel.HIGH),
    (26, RiskLevel.MEDIUM),
    (0, RiskLevel.LOW),
]

# Alert threshold — scores at or above this trigger an alert
ALERT_THRESHOLD = 51


def calculate_vendor_risk(db: Session, vendor_id: int) -> dict:
    """
    Calculate the full risk score for a single vendor.

    Returns a dict with:
    - overall_score, risk_level
    - Individual factor scores + human-readable descriptions
    - A list of factor details for the dashboard breakdown

    This is the MAIN FUNCTION — everything else feeds into it.
    """
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        return None

    # Gather data for scoring
    contracts = db.query(Contract).filter(Contract.vendor_id == vendor_id).all()
    payments = db.query(Payment).filter(Payment.vendor_id == vendor_id).all()
    rates = get_rates_dict(db)

    # Calculate each factor
    value_result = _score_contract_value(contracts, rates)
    expiry_result = _score_contract_expiry(contracts)
    compliance_result = _score_compliance(contracts)
    payment_result = _score_payment_health(payments)

    # Sum up
    overall = (
        value_result["score"]
        + expiry_result["score"]
        + compliance_result["score"]
        + payment_result["score"]
    )
    overall = min(overall, 100.0)  # Cap at 100

    # Determine risk level
    risk_level = _get_risk_level(overall)

    # Save/update in database
    _save_assessment(
        db, vendor_id, overall, risk_level,
        value_result["score"], expiry_result["score"],
        compliance_result["score"], payment_result["score"],
    )

    return {
        "vendor_id": vendor_id,
        "vendor_name": vendor.name,
        "overall_score": round(overall, 1),
        "risk_level": risk_level.value,
        "factors": [
            {
                "name": "Contract Value",
                "score": round(value_result["score"], 1),
                "max_score": MAX_FACTOR_SCORE,
                "description": value_result["description"],
            },
            {
                "name": "Contract Expiry",
                "score": round(expiry_result["score"], 1),
                "max_score": MAX_FACTOR_SCORE,
                "description": expiry_result["description"],
            },
            {
                "name": "Compliance & Documentation",
                "score": round(compliance_result["score"], 1),
                "max_score": MAX_FACTOR_SCORE,
                "description": compliance_result["description"],
            },
            {
                "name": "Payment Health",
                "score": round(payment_result["score"], 1),
                "max_score": MAX_FACTOR_SCORE,
                "description": payment_result["description"],
            },
        ],
        "calculated_at": datetime.utcnow().isoformat(),
    }


def calculate_all_risks(db: Session) -> list[dict]:
    """
    Recalculate risk scores for ALL vendors.
    Used by the scheduler or the "Recalculate All" button.
    """
    vendors = db.query(Vendor).all()
    results = []
    for vendor in vendors:
        result = calculate_vendor_risk(db, vendor.id)
        if result:
            results.append(result)
    return results


def get_risk_dashboard(db: Session) -> list[dict]:
    """
    Get all vendors with their risk scores for the dashboard table.
    Joins vendor data with cached risk assessments.
    Sorted by score descending (highest risk first).
    """
    vendors = db.query(Vendor).all()
    rates = get_rates_dict(db)
    dashboard_items = []

    for vendor in vendors:
        # Get cached assessment or calculate fresh
        assessment = (
            db.query(RiskAssessment)
            .filter(RiskAssessment.vendor_id == vendor.id)
            .first()
        )

        contracts = db.query(Contract).filter(Contract.vendor_id == vendor.id).all()
        # Convert all contract values to USD for consistent comparison
        total_value = sum(
            convert(c.value or 0, getattr(c, "currency", "USD") or "USD", "USD", rates)
            for c in contracts
        )
        overdue_count = (
            db.query(Payment)
            .filter(Payment.vendor_id == vendor.id, Payment.status == "overdue")
            .count()
        )

        today = date.today()
        expiring_soon = sum(
            1 for c in contracts
            if c.end_date and c.status == "active"
            and 0 <= (c.end_date - today).days <= 90
        )

        dashboard_items.append({
            "vendor_id": vendor.id,
            "vendor_name": vendor.name,
            "category": vendor.category,
            "status": vendor.status,
            "overall_score": round(assessment.overall_score, 1) if assessment else 0,
            "risk_level": assessment.risk_level.value if assessment else "low",
            "contract_count": len(contracts),
            "total_contract_value": round(total_value, 2),
            "overdue_payments": overdue_count,
            "expiring_soon": expiring_soon,
        })

    # Sort: highest risk first
    dashboard_items.sort(key=lambda x: x["overall_score"], reverse=True)
    return dashboard_items


def get_risk_summary(db: Session) -> dict:
    """
    Get counts for each risk bracket — powers the dashboard header cards.
    """
    assessments = db.query(RiskAssessment).all()

    summary = {
        "low": 0, "medium": 0, "high": 0, "critical": 0,
        "total": 0, "average_score": 0,
    }

    total_score = 0
    for a in assessments:
        summary[a.risk_level.value] += 1
        summary["total"] += 1
        total_score += a.overall_score

    if summary["total"] > 0:
        summary["average_score"] = round(total_score / summary["total"], 1)

    return summary


def get_risk_alerts(db: Session) -> list[dict]:
    """
    Get all vendors whose risk score exceeds the alert threshold.
    These are the vendors that need immediate attention.
    """
    high_risk = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.overall_score >= ALERT_THRESHOLD)
        .order_by(RiskAssessment.overall_score.desc())
        .all()
    )

    alerts = []
    for assessment in high_risk:
        vendor = db.query(Vendor).filter(Vendor.id == assessment.vendor_id).first()
        if vendor:
            alerts.append({
                "vendor_id": vendor.id,
                "vendor_name": vendor.name,
                "risk_level": assessment.risk_level.value,
                "overall_score": round(assessment.overall_score, 1),
                "alert_reason": _build_alert_reason(assessment),
                "triggered_at": assessment.updated_at.isoformat() if assessment.updated_at else None,
            })

    return alerts


# ===================================================================
# PRIVATE SCORING FUNCTIONS
# ===================================================================

def _score_contract_value(contracts: list, rates: dict[str, float]) -> dict:
    """
    FACTOR 1: Contract Value Score (0-25)

    How much total money is at stake with this vendor?

    MULTI-CURRENCY: Since contracts can be in USD, EUR, or GBP,
    we convert every value to USD before summing. This is like
    a bank converting all loans to one currency before assessing
    total exposure. A €100K contract is roughly $108K, not $100K.
    """
    active_contracts = [c for c in contracts if c.status in ("active", "pending_approval")]

    # Convert each contract value to USD for consistent scoring
    total_value_usd = 0.0
    for c in active_contracts:
        if c.value:
            currency = getattr(c, "currency", "USD") or "USD"
            total_value_usd += convert(c.value, currency, "USD", rates)

    score = 0
    for threshold, points in VALUE_THRESHOLDS:
        if total_value_usd >= threshold:
            score = points
            break

    if not active_contracts:
        desc = "No active contracts"
    else:
        desc = (
            f"Total contract value: ${total_value_usd:,.0f} USD equivalent across "
            f"{len(active_contracts)} active contract(s)"
        )

    return {"score": score, "description": desc}


def _score_contract_expiry(contracts: list) -> dict:
    """
    FACTOR 2: Contract Expiry Score (0-25)

    Are contracts about to expire? Expiring contracts mean potential
    service disruptions if not renewed in time.

    ANALOGY: If your car insurance expires next week and you haven't
    renewed it, that's a HIGH risk of driving uninsured. Same idea:
    vendor contracts expiring soon = risk of service gaps.
    """
    today = date.today()
    active_contracts = [c for c in contracts if c.status == "active" and c.end_date]

    expiring_30 = 0
    expiring_60 = 0
    expiring_90 = 0
    expired = 0

    for c in active_contracts:
        days_left = (c.end_date - today).days
        if days_left < 0:
            expired += 1
        elif days_left <= 30:
            expiring_30 += 1
        elif days_left <= 60:
            expiring_60 += 1
        elif days_left <= 90:
            expiring_90 += 1

    # Score based on worst case
    if expired > 0:
        score = 25
        desc = f"{expired} expired contract(s) — immediate action needed"
    elif expiring_30 > 0:
        score = 22
        desc = f"{expiring_30} contract(s) expiring within 30 days"
    elif expiring_60 > 0:
        score = 16
        desc = f"{expiring_60} contract(s) expiring within 60 days"
    elif expiring_90 > 0:
        score = 8
        desc = f"{expiring_90} contract(s) expiring within 90 days"
    else:
        score = 0
        desc = "No contracts expiring soon"

    return {"score": score, "description": desc}


def _score_compliance(contracts: list) -> dict:
    """
    FACTOR 3: Compliance & Documentation Score (0-25)

    Are all contracts properly documented? Missing documents mean
    we can't prove our agreements if disputes arise.

    ANALOGY: Imagine renting an apartment without a lease.
    If the landlord raises rent, you have no proof of the original terms.
    Missing contract documents = same kind of vulnerability.
    """
    if not contracts:
        return {"score": 0, "description": "No contracts to evaluate"}

    total = len(contracts)
    missing_docs = sum(1 for c in contracts if not c.document_url)
    missing_ratio = missing_docs / total

    if missing_ratio == 0:
        score = 0
        desc = f"All {total} contract(s) have uploaded documents"
    elif missing_ratio <= 0.25:
        score = 8
        desc = f"{missing_docs} of {total} contract(s) missing documents"
    elif missing_ratio <= 0.5:
        score = 14
        desc = f"{missing_docs} of {total} contract(s) missing documents"
    elif missing_ratio <= 0.75:
        score = 20
        desc = f"{missing_docs} of {total} contract(s) missing documents — most need attention"
    else:
        score = 25
        desc = f"{missing_docs} of {total} contract(s) have no documents — critical compliance gap"

    return {"score": score, "description": desc}


def _score_payment_health(payments: list) -> dict:
    """
    FACTOR 4: Payment Health Score (0-25)

    Are there overdue payments? A vendor with many overdue invoices
    suggests either a billing problem or a strained relationship.

    ANALOGY: Your credit score drops hard if you miss payments.
    Similarly, overdue payments to a vendor signals financial stress
    or relationship issues.
    """
    if not payments:
        return {"score": 0, "description": "No payment history"}

    total = len(payments)
    overdue = sum(1 for p in payments if p.status == "overdue")
    overdue_ratio = overdue / total

    if overdue == 0:
        score = 0
        desc = f"All {total} payment(s) in good standing"
    elif overdue_ratio <= 0.1:
        score = 6
        desc = f"{overdue} of {total} payment(s) overdue — minor concern"
    elif overdue_ratio <= 0.25:
        score = 12
        desc = f"{overdue} of {total} payment(s) overdue"
    elif overdue_ratio <= 0.5:
        score = 20
        desc = f"{overdue} of {total} payment(s) overdue — significant concern"
    else:
        score = 25
        desc = f"{overdue} of {total} payment(s) overdue — critical payment issues"

    return {"score": score, "description": desc}


def _get_risk_level(score: float) -> RiskLevel:
    """Map a numeric score to a risk level bracket."""
    for threshold, level in RISK_BRACKETS:
        if score >= threshold:
            return level
    return RiskLevel.LOW


def _save_assessment(
    db: Session, vendor_id: int, overall: float, risk_level: RiskLevel,
    value_score: float, expiry_score: float,
    compliance_score: float, payment_score: float,
):
    """Save or update the cached risk assessment in the database."""
    assessment = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.vendor_id == vendor_id)
        .first()
    )

    if assessment:
        assessment.overall_score = overall
        assessment.risk_level = risk_level
        assessment.contract_value_score = value_score
        assessment.expiry_score = expiry_score
        assessment.compliance_score = compliance_score
        assessment.payment_score = payment_score
        assessment.updated_at = datetime.utcnow()
    else:
        assessment = RiskAssessment(
            vendor_id=vendor_id,
            overall_score=overall,
            risk_level=risk_level,
            contract_value_score=value_score,
            expiry_score=expiry_score,
            compliance_score=compliance_score,
            payment_score=payment_score,
        )
        db.add(assessment)

    db.commit()


def _build_alert_reason(assessment: RiskAssessment) -> str:
    """Build a human-readable alert reason from the factor scores."""
    reasons = []
    if assessment.contract_value_score >= 16:
        reasons.append("high contract exposure")
    if assessment.expiry_score >= 16:
        reasons.append("contracts expiring soon")
    if assessment.compliance_score >= 14:
        reasons.append("missing documentation")
    if assessment.payment_score >= 12:
        reasons.append("overdue payments")

    if not reasons:
        reasons.append("elevated overall risk")

    return f"Risk score {assessment.overall_score:.0f}/100 — {', '.join(reasons)}"
