"""
NOTIFICATION DATABASE MODEL
=============================
This file defines the "notifications" table in our database.

WHAT IS A NOTIFICATION?
A notification is a message the system generates to tell someone
something important happened. In our case: "Contract X expires in 30 days!"

REAL-WORLD ANALOGY:
Think of a notification like a sticky note your assistant puts on your desk.
It has:
- WHO it's for (the contract owner)
- WHAT it says ("Your contract expires in 30 days")
- WHEN it was created
- Whether you've READ IT or not

WHY WE STORE NOTIFICATIONS IN THE DATABASE:
1. We can show them on a dashboard (like an inbox)
2. We don't send duplicate alerts (we check: "did we already notify about this?")
3. We keep a history of what was sent

EXAMPLE DATA:
| id | contract_id | type         | days_until | message                           | is_read | sent_email |
|----|-------------|--------------|------------|-----------------------------------|---------|------------|
| 1  | 5           | 30_day_alert | 28         | "Annual IT Support expires in..." | False   | True       |
| 2  | 3           | 60_day_alert | 59         | "Office Cleaning Q2 expires..."   | True    | True       |
| 3  | 7           | 90_day_alert | 90         | "Security Audit expires in..."    | False   | False      |
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class NotificationType(str, enum.Enum):
    """
    The different alert thresholds we check:
    - 90_DAY: "Heads up, this contract expires in about 3 months"
    - 60_DAY: "Reminder: 2 months left on this contract"
    - 30_DAY: "Urgent: only 1 month left!"
    - EXPIRED: "This contract has passed its end date"
    """
    NINETY_DAY = "90_day_alert"
    SIXTY_DAY = "60_day_alert"
    THIRTY_DAY = "30_day_alert"
    EXPIRED = "expired_alert"


class Notification(Base):
    """
    The Notifications table — stores every alert the system generates.

    Each notification is tied to a specific contract via foreign key.
    This lets us answer: "Have we already sent a 30-day alert for contract #5?"
    """

    __tablename__ = "notifications"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Which contract triggered this alert?
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False, index=True)

    # What kind of alert? (30-day, 60-day, 90-day, or expired)
    notification_type = Column(String(20), nullable=False)

    # How many days until expiration when this notification was created?
    days_until_expiry = Column(Integer, nullable=False)

    # The human-readable message
    message = Column(Text, nullable=False)

    # Has someone viewed this notification on the dashboard?
    is_read = Column(Boolean, default=False, nullable=False)

    # Did we successfully send an email for this notification?
    email_sent = Column(Boolean, default=False, nullable=False)

    # Who should receive this notification? (could be null if no owner set)
    recipient_email = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # --- RELATIONSHIP ---
    # notification.contract gives us the full Contract object
    contract = relationship("Contract", backref="notifications")
