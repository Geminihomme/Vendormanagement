"""
CONTRACT API ROUTES
=====================
URLs the frontend calls to manage contracts.

ENDPOINTS:
  GET    /api/contracts/                        -> List all contracts
  POST   /api/contracts/                        -> Create a new contract
  GET    /api/contracts/{id}                    -> Get one contract
  PUT    /api/contracts/{id}                    -> Update a contract
  DELETE /api/contracts/{id}                    -> Delete a contract
  GET    /api/contracts/vendor/{id}             -> Get all contracts for a vendor
  POST   /api/contracts/{id}/upload-document    -> Upload a PDF to a contract

FILE UPLOAD CONCEPT:
Normal API calls send JSON (text data). File uploads are different:
- The browser sends "multipart/form-data" instead of JSON
- This format can carry BOTH text fields AND binary file data
- Think of it as a package with separate compartments for each piece

FastAPI handles this with UploadFile, which gives us:
- file.filename: the original file name (e.g., "contract_2025.pdf")
- file.content_type: what kind of file (e.g., "application/pdf")
- file.read(): the actual file bytes
"""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.contract import ContractCreate, ContractUpdate, ContractResponse
from app.services import contract_service
from app.services import vendor_service

router = APIRouter()

# Where uploaded files are saved on the server's filesystem.
UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads" / "contracts"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Security: only allow these file types. Without this check, someone
# could upload a malicious .exe file. Always validate file types!
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB limit


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


@router.post("/{contract_id}/upload-document", response_model=ContractResponse)
async def upload_contract_document(
    contract_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a document (PDF, etc.) and attach it to a contract.

    HOW THIS WORKS step-by-step:
    1. Frontend sends the file as multipart/form-data
    2. FastAPI receives it as an UploadFile object
    3. We validate the file type and size (security!)
    4. We generate a UNIQUE filename (prevents collisions & path attacks)
    5. We save the file bytes to the uploads/contracts/ folder
    6. We update the contract's document_url field in the database
    7. We return the updated contract

    WHY A UNIQUE FILENAME?
    If two people upload "contract.pdf", they'd overwrite each other.
    Using uuid (a random ID like "a8f3b2c4-...") guarantees unique names.
    It also prevents "path traversal" attacks where a malicious filename
    like "../../etc/passwd" could read system files.
    """
    # --- SECURITY CHECK 1: Does the contract exist? ---
    contract = contract_service.get_contract(db, contract_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="Contract not found")

    # --- SECURITY CHECK 2: Is the file type allowed? ---
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{file_ext}' not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # --- SECURITY CHECK 3: Is the file too large? ---
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)} MB"
        )

    # --- SAVE THE FILE ---
    # Generate a unique filename: "a8f3b2c4-1234-5678-9abc-def012345678.pdf"
    unique_name = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_name

    with open(file_path, "wb") as f:
        f.write(contents)

    # --- UPDATE THE CONTRACT ---
    # Store the URL path (not the filesystem path) so the browser can access it.
    # The browser will request: http://localhost:8000/uploads/contracts/abc123.pdf
    document_url = f"/uploads/contracts/{unique_name}"

    updated = contract_service.update_contract(
        db, contract_id,
        ContractUpdate(document_url=document_url)
    )
    return updated
