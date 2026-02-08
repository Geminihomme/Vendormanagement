"""
USER SCHEMAS (Data Validation)
================================
These schemas control what data goes IN and OUT for user-related API calls.

IMPORTANT SECURITY PATTERN:
Notice that UserCreate ACCEPTS a password (so users can set one),
but UserResponse NEVER RETURNS the password or hash.

This is like a one-way mail slot: you can PUT mail through the slot,
but you can't reach in and take mail back out.

EXAMPLE API CALLS:

Creating a user (what you SEND):
  POST /api/users/
  {
    "full_name": "Sarah Chen",
    "email": "sarah@company.com",
    "password": "securepass123",
    "role": "admin"
  }

Getting a user (what you RECEIVE BACK):
  GET /api/users/1
  {
    "id": 1,
    "full_name": "Sarah Chen",
    "email": "sarah@company.com",
    "role": "admin",
    "is_active": true,
    "created_at": "2025-01-15T10:30:00"
  }

Notice: password is NEVER returned. It goes in but never comes out.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """
    Schema for CREATING a new user.
    This accepts a plain-text password, which the service layer
    will hash before storing in the database.
    """
    full_name: str = Field(..., min_length=1, max_length=255, description="User's display name")
    email: str = Field(..., max_length=255, description="Login email (must be unique)")
    password: str = Field(..., min_length=8, max_length=100, description="Password (min 8 chars)")
    role: str = Field("viewer", description="User role: admin, manager, or viewer")
    preferred_currency: str = Field("USD", max_length=3, description="Display currency: USD, EUR, or GBP")


class UserUpdate(BaseModel):
    """
    Schema for UPDATING an existing user.
    All fields optional. Password change is separate for security.
    """
    full_name: str | None = Field(None, min_length=1, max_length=255)
    email: str | None = Field(None, max_length=255)
    role: str | None = Field(None, max_length=20)
    is_active: bool | None = None
    preferred_currency: str | None = Field(None, max_length=3)


class UserResponse(BaseModel):
    """
    Schema for RETURNING user data.
    NEVER includes password or hashed_password -- this is critical for security.
    """
    id: int
    full_name: str
    email: str
    role: str
    is_active: bool
    preferred_currency: str = "USD"
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
