"""
RISK ASSESSMENT SCHEMAS
=========================
Data shapes for the risk scoring system.

RiskScoreResponse — Full breakdown for one vendor (the "credit report")
RiskDashboardItem — Summary for the dashboard table (one row per vendor)
RiskSummary — Overall counts (how many low/medium/high/critical vendors)
RiskAlert — A triggered alert when a vendor exceeds the threshold
"""

from datetime import datetime

from pydantic import BaseModel


class RiskFactorDetail(BaseModel):
    """One factor in the risk breakdown — like one section of a credit report."""
    name: str              # "Contract Value"
    score: float           # 16.0
    max_score: float       # 25.0
    description: str       # "Total contract value is $150,000 (high exposure)"


class RiskScoreResponse(BaseModel):
    """Full risk report for one vendor — the detailed credit report."""
    vendor_id: int
    vendor_name: str
    overall_score: float            # 0-100
    risk_level: str                 # "low", "medium", "high", "critical"
    factors: list[RiskFactorDetail]  # Breakdown of each scoring category
    calculated_at: datetime | None = None

    model_config = {"from_attributes": True}


class RiskDashboardItem(BaseModel):
    """One row in the risk dashboard table — the quick overview."""
    vendor_id: int
    vendor_name: str
    category: str | None = None
    status: str
    overall_score: float
    risk_level: str
    contract_count: int = 0
    total_contract_value: float = 0
    overdue_payments: int = 0
    expiring_soon: int = 0          # contracts expiring within 90 days


class RiskSummary(BaseModel):
    """Dashboard header stats — how many vendors in each risk bracket."""
    low: int = 0
    medium: int = 0
    high: int = 0
    critical: int = 0
    total: int = 0
    average_score: float = 0


class RiskAlert(BaseModel):
    """A triggered risk alert — when a vendor crosses the threshold."""
    vendor_id: int
    vendor_name: str
    risk_level: str
    overall_score: float
    alert_reason: str             # "Score increased from 45 to 78"
    triggered_at: datetime
