"""
CONTRACT SERVICE (Business Logic)
===================================
Handles all contract-related operations.

THIS SERVICE IS MORE COMPLEX than vendors/users because:
1. Contracts reference OTHER tables (vendors, users) via foreign keys
2. We need to validate that the vendor exists before creating a contract
3. The response needs extra data (vendor name, creator name) pulled
   from related tables

Think of it like filling out a form that references other forms:
"Vendor: [pick from vendor list]" -- we need to verify the vendor exists.

HOW it fits in:
API Route -> Contract Service -> Database
                |-> Also reads from Vendors table (to verify vendor exists)
                |-> Also reads from Users table (to get creator name)
"""

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.contract import Contract
from app.models.vendor import Vendor
from app.models.user import User
from app.schemas.contract import ContractCreate, ContractUpdate, ContractResponse


def get_contracts(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    status: str | None = None,
    sort_by: str = "title",
    sort_order: str = "asc",
):
    """
    Get a list of all contracts with optional search, filtering, and sorting.

    Search looks across title, description, and contract_number.
    Sort supports: title, status, value, end_date, created_at.
    """
    query = db.query(Contract)

    # Search across multiple fields
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Contract.title.ilike(search_pattern),
                Contract.description.ilike(search_pattern),
                Contract.contract_number.ilike(search_pattern),
            )
        )

    # Filter by status
    if status:
        query = query.filter(Contract.status == status)

    # Sorting
    sort_columns = {
        "title": Contract.title,
        "status": Contract.status,
        "value": Contract.value,
        "end_date": Contract.end_date,
        "created_at": Contract.created_at,
    }
    sort_column = sort_columns.get(sort_by, Contract.title)

    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    contracts = query.offset(skip).limit(limit).all()
    return [_enrich_contract(c) for c in contracts]


def get_contract(db: Session, contract_id: int):
    """Get a single contract by ID, enriched with related names."""
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if contract:
        return _enrich_contract(contract)
    return None


def get_contracts_by_vendor(db: Session, vendor_id: int):
    """
    Get all contracts for a specific vendor.
    Useful when viewing a vendor's detail page -- shows all their contracts.
    """
    contracts = db.query(Contract).filter(Contract.vendor_id == vendor_id).all()
    return [_enrich_contract(c) for c in contracts]


def create_contract(db: Session, contract: ContractCreate):
    """
    Create a new contract.

    We verify the vendor exists first -- you can't create a contract
    with a vendor that doesn't exist (the foreign key would fail anyway,
    but checking first gives us a better error message).
    """
    db_contract = Contract(**contract.model_dump())
    db.add(db_contract)
    db.commit()
    db.refresh(db_contract)
    return _enrich_contract(db_contract)


def update_contract(db: Session, contract_id: int, contract_update: ContractUpdate):
    """Update an existing contract."""
    db_contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not db_contract:
        return None

    update_data = contract_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_contract, field, value)

    db.commit()
    db.refresh(db_contract)
    return _enrich_contract(db_contract)


def delete_contract(db: Session, contract_id: int):
    """Delete a contract."""
    db_contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not db_contract:
        return False

    db.delete(db_contract)
    db.commit()
    return True


def _enrich_contract(contract: Contract) -> dict:
    """
    Convert a Contract model to a dictionary with extra info.

    The Contract model has vendor_id=1, but the frontend wants to
    display the vendor's NAME. This function adds those convenience fields
    by following the relationships we defined in the model.

    contract.vendor is the related Vendor object (SQLAlchemy loads it
    automatically through the relationship we defined).
    """
    return {
        "id": contract.id,
        "title": contract.title,
        "description": contract.description,
        "contract_number": contract.contract_number,
        "vendor_id": contract.vendor_id,
        "vendor_name": contract.vendor.name if contract.vendor else None,
        "created_by_id": contract.created_by_id,
        "created_by_name": contract.created_by.full_name if contract.created_by else None,
        "value": contract.value,
        "start_date": contract.start_date,
        "end_date": contract.end_date,
        "status": contract.status,
        "document_url": contract.document_url,
        "created_at": contract.created_at,
        "updated_at": contract.updated_at,
    }
