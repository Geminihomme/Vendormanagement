"""
CONTRACT API ROUTES
=====================
URLs the frontend calls to manage contracts.

ENDPOINTS:
  GET    /api/contracts/               -> List all contracts
  POST   /api/contracts/               -> Create a new contract
  GET    /api/contracts/{id}           -> Get one contract
  PUT    /api/contracts/{id}           -> Update a contract
  DELETE /api/contracts/{id}           -> Delete a contract
  GET    /api/contracts/vendor/{id}    -> Get all contracts for a specific vendor

EXTRA VALIDATION:
When creating a contract, we verify the vendor_id points to a real vendor.
This gives a friendly error message instead of a cryptic database error.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.contract import ContractCreate, ContractUpdate, ContractResponse
from app.services import contract_service
from app.services import vendor_service

router = APIRouter()


@router.get("/", response_model=list[ContractResponse])
def list_contracts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all contracts. Includes vendor and creator names."""
    return contract_service.get_contracts(db, skip=skip, limit=limit)


@router.post("/", response_model=ContractResponse, status_code=201)
def create_contract(contract: ContractCreate, db: Session = Depends(get_db)):
    """
    Create a new contract.

    Validates that the vendor exists before creating.
    If vendor_id=999 but no vendor 999 exists, returns a 404 error.
    """
    # Make sure the vendor exists
    vendor = vendor_service.get_vendor(db, contract.vendor_id)
    if not vendor:
        raise HTTPException(
            status_code=404,
            detail=f"Vendor with id {contract.vendor_id} not found"
        )

    return contract_service.create_contract(db, contract)


@router.get("/{contract_id}", response_model=ContractResponse)
def get_contract(contract_id: int, db: Session = Depends(get_db)):
    """Get a single contract by ID."""
    contract = contract_service.get_contract(db, contract_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract


@router.put("/{contract_id}", response_model=ContractResponse)
def update_contract(
    contract_id: int,
    contract_update: ContractUpdate,
    db: Session = Depends(get_db),
):
    """Update an existing contract."""
    contract = contract_service.update_contract(db, contract_id, contract_update)
    if contract is None:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract


@router.delete("/{contract_id}", status_code=204)
def delete_contract(contract_id: int, db: Session = Depends(get_db)):
    """Delete a contract."""
    success = contract_service.delete_contract(db, contract_id)
    if not success:
        raise HTTPException(status_code=404, detail="Contract not found")


@router.get("/vendor/{vendor_id}", response_model=list[ContractResponse])
def get_vendor_contracts(vendor_id: int, db: Session = Depends(get_db)):
    """
    Get all contracts for a specific vendor.

    This is used on the vendor detail page to show:
    "Here are all the contracts we have with Acme IT Solutions."
    """
    return contract_service.get_contracts_by_vendor(db, vendor_id)
