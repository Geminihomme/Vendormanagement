"""
RISK ASSESSMENT DATABASE MODEL (The Vendor "Credit Report")
==============================================================
This stores the calculated risk score and breakdown for each vendor.

WHAT IS A RISK ASSESSMENT?
Think of it like a credit report for a vendor. Just like a bank checks
your credit score before giving you a loan, we check a vendor's risk
score before trusting them with our business.

THE SCORE (0-100):
==================
0-25:   LOW RISK    (green)  — Like an 800+ credit score. Everything is solid.
26-50:  MEDIUM RISK (yellow) — Some concerns. Keep an eye on it.
51-75:  HIGH RISK   (orange) — Multiple red flags. Needs attention.
76-100: CRITICAL    (red)    — Like a 400 credit score. Take immediate action.

THE FACTORS:
============
Just like a credit score has categories (payment history 35%, amounts 30%, etc.),
our risk score is built from weighted factors:

1. CONTRACT VALUE (25 points max)
   How much money is at stake? Higher value = higher risk.
   - Under $10K:  0 points
   - $10K-$50K:   8 points
   - $50K-$200K:  16 points
   - Over $200K:  25 points

2. CONTRACT EXPIRY (25 points max)
   Are contracts about to expire? Gaps = disruption risk.
   - No contracts expiring soon:  0 points
   - Expiring in 60-90 days:     8 points
   - Expiring in 30-60 days:     16 points
   - Expiring within 30 days:    25 points

3. COMPLIANCE/DOCUMENTATION (25 points max)
   Missing documents = we can't prove our agreements.
   - All contracts have documents:  0 points
   - Some missing:                  12 points
   - Most missing:                  20 points
   - No documents at all:           25 points

4. PAYMENT HEALTH (25 points max)
   Are there overdue payments? Like checking if someone pays their bills.
   - No overdue payments:   0 points
   - Some overdue:          12 points
   - Many overdue:          20 points
   - Mostly overdue:        25 points

Total: 0-100 points (sum of all factors)

WHY STORE IT?
We CACHE the calculated score in the database so:
1. We don't recalculate it on every page load (performance)
2. We can track how risk changes over time (trend analysis)
3. We can query "show me all high-risk vendors" efficiently
"""

import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship

from app.database import Base


class RiskLevel(str, enum.Enum):
    """
    Risk levels — like credit score brackets:
    - LOW:      Everything is fine (credit score 750+)
    - MEDIUM:   Some concerns (credit score 650-749)
    - HIGH:     Red flags (credit score 550-649)
    - CRITICAL: Urgent action needed (credit score below 550)
    """
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskAssessment(Base):
    """
    Cached risk score for a vendor — recalculated periodically.

    EXAMPLE DATA:
    | vendor_id | overall_score | risk_level | contract_value_score | expiry_score | compliance_score | payment_score |
    |-----------|---------------|------------|---------------------|--------------|-----------------|---------------|
    | 5         | 72            | high       | 25                  | 16           | 20              | 11            |
    | 8         | 12            | low        | 8                   | 0            | 0               | 4             |
    """

    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True)

    # Which vendor this assessment belongs to
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False, unique=True, index=True)
    vendor = relationship("Vendor", backref="risk_assessment")

    # --- THE SCORES ---
    overall_score = Column(Float, nullable=False, default=0)     # 0-100
    risk_level = Column(
        Enum(RiskLevel),
        nullable=False,
        default=RiskLevel.LOW,
    )

    # Individual factor scores (each 0-25)
    contract_value_score = Column(Float, nullable=False, default=0)
    expiry_score = Column(Float, nullable=False, default=0)
    compliance_score = Column(Float, nullable=False, default=0)
    payment_score = Column(Float, nullable=False, default=0)

    # Human-readable breakdown explaining WHY the score is what it is
    # Stored as a text summary so the dashboard can show it immediately
    details = Column(Text, nullable=True)

    # Timestamps
    calculated_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
