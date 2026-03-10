"""
CONTRACT SCHEMAS (Data Validation)
=====================================
These schemas control what data goes in and out for contract-related API calls.

KEY DESIGN DECISIONS:

1. ContractCreate requires vendor_id (which vendor is this contract with?)
   but created_by_id is optional (set automatically from the logged-in user later).

2. ContractResponse includes NESTED objects: instead of just returning
   vendor_id=1, it returns the full vendor name and the creator's name.
   This saves the frontend from making extra API calls.

EXAMPLE:
Without nesting, the frontend gets: {"vendor_id": 1, "created_by_id": 2}
  -> Frontend must make 2 MORE requests to get vendor name and user name.

With nesting, the frontend gets:
  {
    "vendor_id": 1,
    "vendor_name": "Acme IT Solutions",
    "created_by_id": 2,
    "created_by_name": "Sarah Chen"
  }
  -> Everything needed in ONE response. Much faster.
"""

from datetime import datetime, date
from pydantic import BaseModel, Field, field_validator

# The only currencies our system accepts.
# Adding a currency here also requires adding it to the exchange_rates table.
VALID_CURRENCIES = {"USD", "EUR", "GBP"}


class ContractCreate(BaseModel):
    """
    Schema for CREATING a new contract.
    vendor_id is required -- every contract must be tied to a vendor.
    """
    title: str = Field(..., min_length=1, max_length=255, description="Contract title")
    description: str | None = Field(None, description="Detailed description")
    contract_number: str | None = Field(None, max_length=100, description="e.g., CNT-2025-001")
    vendor_id: int = Field(..., description="ID of the vendor this contract is with")
    created_by_id: int | None = Field(None, description="ID of the user creating this")
    value: float | None = Field(None, ge=0, description="Contract value (must be >= 0)")
    # ge=0 means "greater than or equal to 0" -- no negative contracts!
    currency: str = Field("USD", max_length=3, description="Currency code: USD, EUR, or GBP")
    start_date: date | None = Field(None, description="When the contract begins")
    end_date: date | None = Field(None, description="When the contract expires")
    status: str = Field("draft", description="Contract status")
    document_url: str | None = Field(None, max_length=500, description="Link to contract document")

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        code = v.upper()
        if code not in VALID_CURRENCIES:
            raise ValueError(f"Unsupported currency: {v}. Must be one of: {', '.join(sorted(VALID_CURRENCIES))}")
        return code


class ContractUpdate(BaseModel):
    """
    Schema for UPDATING an existing contract.
    All fields optional -- only send what changed.
    """
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    contract_number: str | None = Field(None, max_length=100)
    vendor_id: int | None = None
    value: float | None = Field(None, ge=0)
    currency: str | None = Field(None, max_length=3)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str | None) -> str | None:
        if v is None:
            return v
        code = v.upper()
        if code not in VALID_CURRENCIES:
            raise ValueError(f"Unsupported currency: {v}. Must be one of: {', '.join(sorted(VALID_CURRENCIES))}")
        return code
    start_date: date | None = None
    end_date: date | None = None
    status: str | None = Field(None, max_length=20)
    document_url: str | None = Field(None, max_length=500)


class ContractResponse(BaseModel):
    """
    Schema for RETURNING contract data.
    Includes vendor_name and created_by_name so the frontend
    doesn't need to make extra API calls to look up those names.
    """
    id: int
    title: str
    description: str | None = None
    contract_number: str | None = None
    vendor_id: int
    vendor_name: str | None = None        # Convenience: the vendor's name
    created_by_id: int | None = None
    created_by_name: str | None = None    # Convenience: the creator's name
    value: float | None = None
    currency: str = "USD"
    start_date: date | None = None
    end_date: date | None = None
    status: str
    document_url: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
