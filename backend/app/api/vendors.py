"""
VENDOR API ROUTES (Endpoints)
===============================
This file defines the URLs that the frontend can call to work with vendors.

WHAT IS AN API ROUTE?
An API route is a URL + an action. When the frontend needs data, it sends
an HTTP request to one of these URLs. The most common actions are:

- GET    = "Give me data"          (like reading a book)
- POST   = "Save this new data"    (like writing a new page)
- PUT    = "Update existing data"  (like editing a page)
- DELETE = "Remove this data"      (like tearing out a page)

THE ROUTES WE DEFINE:
  GET    /api/vendors/             -> List vendors (with search, filter, sort)
  GET    /api/vendors/categories   -> Get all unique categories (for filter dropdown)
  GET    /api/vendors/count        -> Count vendors matching filters
  POST   /api/vendors/             -> Create a new vendor
  GET    /api/vendors/{id}         -> Get one vendor by ID
  PUT    /api/vendors/{id}         -> Update a vendor
  DELETE /api/vendors/{id}         -> Delete a vendor

HOW it fits in:
This is the "front desk" of our backend. The frontend only talks to these
routes. The routes delegate the real work to the service layer.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.vendor import VendorCreate, VendorUpdate, VendorResponse
from app.services import vendor_service
from app.auth import get_current_user
from app.models.user import User

# A "router" groups related endpoints together.
# All routes in this file will be prefixed with /api/vendors (set in main.py).
router = APIRouter()


@router.get("/", response_model=list[VendorResponse])
def list_vendors(
    skip: int = 0,
    limit: int = 100,
    search: str | None = Query(None, description="Search by name, email, description, category, or city"),
    status: str | None = Query(None, description="Filter by status (active, pending, etc.)"),
    category: str | None = Query(None, description="Filter by category"),
    sort_by: str = Query("name", description="Sort by: name, email, category, status, created_at, updated_at"),
    sort_order: str = Query("asc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a list of vendors with optional search, filtering, and sorting.

    HOW QUERY PARAMETERS WORK:
    The frontend adds filters to the URL:
      GET /api/vendors/?search=acme&status=active&sort_by=name&sort_order=asc

    FastAPI reads each ?key=value pair and passes them as function arguments.

    Example combinations:
      /api/vendors/?search=IT                          -> search in name/email/description
      /api/vendors/?status=active&category=IT Services -> active IT vendors only
      /api/vendors/?sort_by=created_at&sort_order=desc -> newest vendors first
    """
    vendors = vendor_service.get_vendors(
        db, skip=skip, limit=limit,
        search=search, status=status, category=category,
        sort_by=sort_by, sort_order=sort_order,
    )
    return vendors


@router.get("/categories", response_model=list[str])
def get_vendor_categories(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get all unique vendor categories.
    Used to populate the category filter dropdown on the frontend.
    Returns: ["IT Services", "Office Supplies", "Consulting", ...]
    """
    return vendor_service.get_vendor_categories(db)


@router.get("/count")
def get_vendor_count(
    search: str | None = None,
    status: str | None = None,
    category: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the count of vendors matching the current filters.
    Used for "Showing X of Y vendors" without loading all data.
    """
    total = vendor_service.count_vendors(db)
    filtered = vendor_service.count_vendors(db, search=search, status=status, category=category)
    return {"total": total, "filtered": filtered}


@router.post("/", response_model=VendorResponse, status_code=201)
def create_vendor(vendor: VendorCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Create a new vendor.

    The frontend sends a JSON body like:
    {
        "name": "Acme Corp",
        "email": "contact@acme.com",
        "category": "IT Services"
    }

    FastAPI automatically validates this against VendorCreate schema.
    If validation fails, it returns a 422 error with details.

    status_code=201 means "Created" -- tells the frontend it was successful.
    """
    return vendor_service.create_vendor(db, vendor)


@router.get("/{vendor_id}", response_model=VendorResponse)
def get_vendor(vendor_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Get a single vendor by their ID.

    The {vendor_id} in the URL path becomes a function parameter.
    Example: GET /api/vendors/42 -> vendor_id=42

    If the vendor doesn't exist, we return a 404 "Not Found" error.
    """
    vendor = vendor_service.get_vendor(db, vendor_id)
    if vendor is None:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


@router.put("/{vendor_id}", response_model=VendorResponse)
def update_vendor(
    vendor_id: int,
    vendor_update: VendorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing vendor.

    You only need to send the fields you want to change:
    PUT /api/vendors/42  with body {"phone": "555-1234"}
    """
    vendor = vendor_service.update_vendor(db, vendor_id, vendor_update)
    if vendor is None:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor


@router.delete("/{vendor_id}", status_code=204)
def delete_vendor(vendor_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Delete a vendor.

    status_code=204 means "No Content" -- the deletion was successful
    and there's nothing to return.
    """
    success = vendor_service.delete_vendor(db, vendor_id)
    if not success:
        raise HTTPException(status_code=404, detail="Vendor not found")
