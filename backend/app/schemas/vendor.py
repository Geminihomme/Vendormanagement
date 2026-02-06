"""
VENDOR SCHEMAS (Data Validation)
==================================
Schemas define the SHAPE of data going in and out of our API.

WHAT IS A SCHEMA?
Think of a schema as a bouncer at a club door. Before any data enters
our system, the schema checks:
- Is the name provided? (required fields)
- Is the email actually an email format?
- Are we only sending back the fields the frontend needs?

WHY WE NEED BOTH MODELS AND SCHEMAS:
- Models (vendor model) = describe the database table structure
- Schemas (this file) = describe what data the API accepts and returns

They serve different purposes:
- When creating a vendor, you shouldn't send an "id" (the database generates it)
- When reading a vendor, you want the "id" included
- The password for a user should be accepted (input) but never returned (output)

HOW it fits in:
Frontend sends JSON -> Schema validates it -> Service uses Model to save to DB
DB returns Model -> Schema formats it -> Frontend receives clean JSON
"""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class VendorCreate(BaseModel):
    """
    Schema for CREATING a new vendor.
    These are the fields the frontend must send when adding a vendor.
    Notice: no 'id' field -- the database generates that automatically.
    """
    name: str = Field(..., min_length=1, max_length=255, description="Company name")
    email: str = Field(..., max_length=255, description="Contact email")
    phone: str | None = Field(None, max_length=50, description="Phone number")
    website: str | None = Field(None, max_length=255, description="Website URL")
    description: str | None = Field(None, description="What the vendor does")
    category: str | None = Field(None, max_length=100, description="Business category")
    tax_id: str | None = Field(None, max_length=50, description="Tax ID number")
    address: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=100)
    state: str | None = Field(None, max_length=100)
    zip_code: str | None = Field(None, max_length=20)
    country: str | None = Field("US", max_length=100)


class VendorUpdate(BaseModel):
    """
    Schema for UPDATING an existing vendor.
    All fields are optional -- you only send what you want to change.
    For example, to just update the phone number, you'd send: {"phone": "555-1234"}
    """
    name: str | None = Field(None, min_length=1, max_length=255)
    email: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=50)
    website: str | None = Field(None, max_length=255)
    description: str | None = None
    category: str | None = Field(None, max_length=100)
    tax_id: str | None = Field(None, max_length=50)
    address: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=100)
    state: str | None = Field(None, max_length=100)
    zip_code: str | None = Field(None, max_length=20)
    country: str | None = Field(None, max_length=100)
    status: str | None = Field(None, max_length=20)


class VendorResponse(BaseModel):
    """
    Schema for RETURNING vendor data to the frontend.
    This includes the 'id' and timestamps that the database generates.
    This is what the frontend receives when it asks for vendor data.
    """
    id: int
    name: str
    email: str
    phone: str | None = None
    website: str | None = None
    description: str | None = None
    category: str | None = None
    tax_id: str | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    country: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
    # "from_attributes = True" tells Pydantic it's OK to read data
    # from a SQLAlchemy model object (not just a dictionary).
    # Without this, converting database results to API responses would fail.
