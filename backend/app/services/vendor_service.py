"""
VENDOR SERVICE (Business Logic)
=================================
This file contains the actual operations we perform on vendor data:
creating, reading, updating, and deleting (called "CRUD" operations).

WHAT IS A SERVICE LAYER?
It's the middleman between the API routes and the database.
- API route says: "Someone wants to create a vendor"
- Service says: "OK, I'll validate and save it to the database"

WHY separate this from the API routes?
1. Organization: API routes handle HTTP stuff, services handle business logic
2. Reusability: Multiple routes can use the same service function
3. Testing: Easier to test business logic separately from HTTP handling

HOW it fits in:
API Route (receives request) -> Service (does the work) -> Database (stores data)
"""

from sqlalchemy.orm import Session

from app.models.vendor import Vendor
from app.schemas.vendor import VendorCreate, VendorUpdate


def get_vendors(db: Session, skip: int = 0, limit: int = 100):
    """
    Get a list of vendors from the database.

    'skip' and 'limit' enable pagination:
    - skip=0, limit=10 = first 10 vendors
    - skip=10, limit=10 = next 10 vendors
    This prevents loading thousands of records at once.
    """
    return db.query(Vendor).offset(skip).limit(limit).all()


def get_vendor(db: Session, vendor_id: int):
    """
    Get a single vendor by their ID.
    Returns None if no vendor with that ID exists.
    """
    return db.query(Vendor).filter(Vendor.id == vendor_id).first()


def create_vendor(db: Session, vendor: VendorCreate):
    """
    Create a new vendor in the database.

    Steps:
    1. Convert the schema (validated input) into a database model
    2. Add it to the session (like putting it in a shopping cart)
    3. Commit (like checking out - actually saves to database)
    4. Refresh (reload from database to get the auto-generated ID)
    """
    db_vendor = Vendor(**vendor.model_dump())
    db.add(db_vendor)
    db.commit()
    db.refresh(db_vendor)
    return db_vendor


def update_vendor(db: Session, vendor_id: int, vendor_update: VendorUpdate):
    """
    Update an existing vendor's information.

    We use 'exclude_unset=True' so that only the fields the user
    actually sent get updated. If they only sent {"phone": "555-1234"},
    we won't accidentally set name, email, etc. to None.
    """
    db_vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not db_vendor:
        return None

    update_data = vendor_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_vendor, field, value)

    db.commit()
    db.refresh(db_vendor)
    return db_vendor


def delete_vendor(db: Session, vendor_id: int):
    """
    Delete a vendor from the database.
    Returns True if the vendor was found and deleted, False if not found.
    """
    db_vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not db_vendor:
        return False

    db.delete(db_vendor)
    db.commit()
    return True
