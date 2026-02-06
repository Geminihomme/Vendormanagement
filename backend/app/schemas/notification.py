"""
NOTIFICATION SCHEMAS (Data Validation)
========================================
These control what notification data looks like when it goes in and out of the API.

KEY DESIGN:
- NotificationResponse includes contract_title and vendor_name so the
  dashboard can display "Contract: Annual IT Support (Acme Corp) expires in 30 days"
  without making extra API calls.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class NotificationResponse(BaseModel):
    """What a notification looks like when returned by the API."""
    id: int
    contract_id: int
    contract_title: str | None = None      # Convenience: "Annual IT Support Agreement"
    vendor_name: str | None = None         # Convenience: "Acme IT Solutions"
    notification_type: str
    days_until_expiry: int
    message: str
    is_read: bool
    email_sent: bool
    recipient_email: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationMarkRead(BaseModel):
    """Schema for marking notifications as read."""
    notification_ids: list[int] = Field(..., description="List of notification IDs to mark as read")
