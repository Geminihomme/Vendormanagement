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
  GET    /api/vendors/        -> List all vendors
  POST   /api/vendors/        -> Create a new vendor
  GET    /api/vendors/{id}    -> Get one vendor by ID
  PUT    /api/vendors/{id}    -> Update a vendor
  DELETE /api/vendors/{id}    -> Delete a vendor

HOW it fits in:
This is the "front desk" of our backend. The frontend only talks to these
routes. The routes delegate the real work to the service layer.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.vendor import VendorCreate, VendorUpdate, VendorResponse
from app.services import vendor_service

# A "router" groups related endpoints together.
# All routes in this file will be prefixed with /api/vendors (set in main.py).
router = APIRouter()


@router.get("/", response_model=list[VendorResponse])
def list_vendors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get a list of all vendors.

    The 'Depends(get_db)' part is called "dependency injection" --
    FastAPI automatically provides a database session to this function.
    We don't have to create or manage it ourselves.

    Example: GET /api/vendors/?skip=0&limit=10
    """
    vendors = vendor_service.get_vendors(db, skip=skip, limit=limit)
    return vendors


@router.post("/", response_model=VendorResponse, status_code=201)
def create_vendor(vendor: VendorCreate, db: Session = Depends(get_db)):
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
def get_vendor(vendor_id: int, db: Session = Depends(get_db)):
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
def delete_vendor(vendor_id: int, db: Session = Depends(get_db)):
    """
    Delete a vendor.

    status_code=204 means "No Content" -- the deletion was successful
    and there's nothing to return.
    """
    success = vendor_service.delete_vendor(db, vendor_id)
    if not success:
        raise HTTPException(status_code=404, detail="Vendor not found")
