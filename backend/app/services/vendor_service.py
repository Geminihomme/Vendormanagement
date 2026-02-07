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
from sqlalchemy import func, or_

from app.models.vendor import Vendor
from app.schemas.vendor import VendorCreate, VendorUpdate


def get_vendors(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    status: str | None = None,
    category: str | None = None,
    sort_by: str = "name",
    sort_order: str = "asc",
):
    """
    Get a list of vendors from the database with optional search, filtering, and sorting.

    HOW DATABASE SEARCH WORKS (The Library Analogy):
    ================================================
    Imagine a librarian searching for books. You could:
    1. Pull EVERY book off the shelf and check each title (slow — "full table scan")
    2. Look in the card catalog first, then go straight to the right shelf (fast — "indexed search")

    SQL databases work the same way. When we do:
        WHERE name ILIKE '%acme%'
    The database checks each row's name column for "acme" (case-insensitive).

    ILIKE = case-insensitive LIKE. So "Acme", "ACME", and "acme" all match.
    The % symbols are wildcards: %acme% means "anything, then acme, then anything."

    With an INDEX on the name column, the database can skip irrelevant rows faster.
    Without an index, it checks every single row (like reading every book title).

    SORTING:
    ORDER BY tells the database to sort results before returning them.
    It's like telling the librarian: "Give me the results alphabetically by name."

    Parameters:
    - search: Text to search for in name, email, or description
    - status: Filter by vendor status (e.g., "active", "pending")
    - category: Filter by vendor category (e.g., "IT Services")
    - sort_by: Which column to sort by (name, created_at, status, category)
    - sort_order: "asc" (A→Z, oldest first) or "desc" (Z→A, newest first)
    """
    query = db.query(Vendor)

    # --- SEARCH ---
    # Search across multiple fields at once using OR.
    # "Find vendors where name contains 'acme' OR email contains 'acme' OR description..."
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Vendor.name.ilike(search_pattern),
                Vendor.email.ilike(search_pattern),
                Vendor.description.ilike(search_pattern),
                Vendor.category.ilike(search_pattern),
                Vendor.city.ilike(search_pattern),
            )
        )

    # --- FILTERS ---
    # These are exact matches, like "show me only active vendors."
    if status:
        query = query.filter(Vendor.status == status)
    if category:
        query = query.filter(Vendor.category == category)

    # --- SORTING ---
    # Map the sort_by parameter to the actual database column.
    sort_columns = {
        "name": Vendor.name,
        "email": Vendor.email,
        "category": Vendor.category,
        "status": Vendor.status,
        "created_at": Vendor.created_at,
        "updated_at": Vendor.updated_at,
    }
    sort_column = sort_columns.get(sort_by, Vendor.name)

    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    return query.offset(skip).limit(limit).all()


def get_vendor_categories(db: Session) -> list[str]:
    """
    Get all unique categories currently used by vendors.
    This powers the category dropdown filter on the frontend.

    The SQL is: SELECT DISTINCT category FROM vendors WHERE category IS NOT NULL
    """
    results = (
        db.query(Vendor.category)
        .filter(Vendor.category.isnot(None), Vendor.category != "")
        .distinct()
        .order_by(Vendor.category)
        .all()
    )
    return [r[0] for r in results]


def count_vendors(
    db: Session,
    search: str | None = None,
    status: str | None = None,
    category: str | None = None,
) -> int:
    """
    Count vendors matching the current filters (without loading all data).
    Used for showing "Showing 12 of 47 vendors" on the page.

    COUNT is fast because the database just counts rows without reading
    all the actual data. It's like counting folders in a drawer without
    opening each one.
    """
    query = db.query(func.count(Vendor.id))

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Vendor.name.ilike(search_pattern),
                Vendor.email.ilike(search_pattern),
                Vendor.description.ilike(search_pattern),
                Vendor.category.ilike(search_pattern),
                Vendor.city.ilike(search_pattern),
            )
        )
    if status:
        query = query.filter(Vendor.status == status)
    if category:
        query = query.filter(Vendor.category == category)

    return query.scalar()


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
