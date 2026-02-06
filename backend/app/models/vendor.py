"""
VENDOR DATABASE MODEL
======================
This file defines the "vendor" table in our database.

WHAT IS A MODEL?
A model is a Python class that maps directly to a database table.
Each attribute (like `name`, `email`) becomes a column in the table.
Each instance of this class becomes a row in the table.

Think of it like a spreadsheet:
- The class = the spreadsheet template (column headers)
- Each object = one row of data

WHY we need this:
Instead of writing raw SQL like:
    CREATE TABLE vendors (id INTEGER, name VARCHAR, ...)
We describe the table in Python, and SQLAlchemy creates it for us.
This is safer, easier to read, and catches errors early.

HOW it fits in:
This model is used by:
- database.py: to create the actual table in PostgreSQL
- services/vendor_service.py: to read/write vendor data
- api/vendors.py: indirectly, through the service layer
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum
import enum

from app.database import Base


class VendorStatus(str, enum.Enum):
    """
    Vendors go through a lifecycle:
    - PENDING: Just submitted, needs review
    - APPROVED: Passed review, we can do business with them
    - ACTIVE: Currently working with us
    - INACTIVE: Relationship paused
    - REJECTED: Did not pass our review
    """
    PENDING = "pending"
    APPROVED = "approved"
    ACTIVE = "active"
    INACTIVE = "inactive"
    REJECTED = "rejected"


class Vendor(Base):
    """
    The Vendor table - stores all information about each vendor.

    Each vendor is a company or individual that provides goods/services to us.
    """

    # This tells SQLAlchemy what to name the table in PostgreSQL
    __tablename__ = "vendors"

    # --- COLUMNS ---
    # Each line below becomes a column in the database table.

    # Primary key: a unique ID for each vendor, auto-incremented (1, 2, 3...)
    id = Column(Integer, primary_key=True, index=True)

    # Basic information
    name = Column(String(255), nullable=False)       # Company name (required)
    email = Column(String(255), nullable=False)      # Contact email (required)
    phone = Column(String(50), nullable=True)        # Phone number (optional)
    website = Column(String(255), nullable=True)     # Website URL (optional)

    # Business details
    description = Column(Text, nullable=True)        # What the vendor does
    category = Column(String(100), nullable=True)    # e.g., "IT Services", "Office Supplies"
    tax_id = Column(String(50), nullable=True)       # Tax identification number

    # Address
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    zip_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True, default="US")

    # Status tracking
    status = Column(String(20), nullable=False, default=VendorStatus.PENDING)

    # Timestamps: automatically track when records are created and updated
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
