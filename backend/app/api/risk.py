"""
RISK ASSESSMENT API ROUTES (The Risk Dashboard Backend)
=========================================================
These endpoints power the Risk Dashboard and alert system.

ENDPOINTS:
  GET  /api/risk/dashboard          -> All vendors with risk scores (table data)
  GET  /api/risk/summary            -> Counts per risk level (stat cards)
  GET  /api/risk/alerts             -> Vendors exceeding the risk threshold
  GET  /api/risk/vendor/{id}        -> Detailed risk report for one vendor
  POST /api/risk/recalculate        -> Recalculate all vendor risk scores
  POST /api/risk/vendor/{id}/recalculate -> Recalculate one vendor's score

THE USER JOURNEY:
=================
1. Manager opens /risk → sees summary cards (2 low, 5 medium, 1 high, 1 critical)
2. Table shows all vendors sorted by risk (highest first)
3. Manager clicks a vendor → sees the detailed breakdown
   (contract value: 25/25, expiry: 16/25, compliance: 20/25, payments: 11/25)
4. Clicks "Recalculate" to refresh scores after changes
5. Alerts tab shows vendors exceeding the threshold with reasons

WHEN DO SCORES UPDATE?
- Automatically when you visit the dashboard (if scores don't exist yet)
- When you click "Recalculate All" (for manual refresh)
- Scores are cached in the database for fast loading
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import risk_service
from app.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/summary")
def get_risk_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get risk level counts for the dashboard header cards.
    Returns: {"low": 5, "medium": 3, "high": 2, "critical": 1, "total": 11, "average_score": 34.2}
    """
    return risk_service.get_risk_summary(db)


@router.get("/dashboard")
def get_risk_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all vendors with their risk scores for the dashboard table.
    Sorted by risk score descending (most risky first).
    Each item includes: vendor info, score, level, contract count, overdue payments.
    """
    return risk_service.get_risk_dashboard(db)


@router.get("/alerts")
def get_risk_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all vendors whose risk score exceeds the alert threshold (51+).
    These are the HIGH and CRITICAL risk vendors that need attention.
    Each alert includes: vendor, score, level, and a human-readable reason.
    """
    return risk_service.get_risk_alerts(db)


@router.get("/vendor/{vendor_id}")
def get_vendor_risk(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the detailed risk breakdown for a single vendor.
    Shows each factor's score with explanations — like a full credit report.
    Also recalculates the score live (not from cache) for accuracy.
    """
    result = risk_service.calculate_vendor_risk(db, vendor_id)
    if not result:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return result


@router.post("/recalculate")
def recalculate_all_risks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Recalculate risk scores for ALL vendors.

    This is the "Refresh All" button. It recalculates every vendor's score
    based on current data and saves the results to the database.

    Use this after:
    - Uploading new contract documents (compliance score changes)
    - Recording payments (payment health changes)
    - Contracts expiring (expiry score changes)
    """
    results = risk_service.calculate_all_risks(db)
    return {
        "message": f"Recalculated risk scores for {len(results)} vendors",
        "vendors_assessed": len(results),
        "results": results,
    }


@router.post("/vendor/{vendor_id}/recalculate")
def recalculate_vendor_risk(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Recalculate risk score for a single vendor and return the new result."""
    result = risk_service.calculate_vendor_risk(db, vendor_id)
    if not result:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return result
