"""
CURRENCY API ROUTES (The Exchange Rate Board)
================================================
These endpoints let users view and manage exchange rates,
update their preferred display currency, and convert amounts.

ENDPOINTS:
  GET  /api/currency/rates                -> View all exchange rates
  PUT  /api/currency/rates/{code}         -> Update a rate (admin only)
  GET  /api/currency/convert              -> Convert an amount between currencies
  PUT  /api/currency/preference           -> Set your preferred display currency

REAL-WORLD ANALOGY:
Think of these like the controls on an international shopping website:
- /rates = the currency exchange board in the airport
- /convert = the calculator next to the board
- /preference = clicking "Show prices in EUR" in your account settings
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.user import User
from app.services import currency_service

router = APIRouter()


# --- Schemas for this module ---

class ExchangeRateResponse(BaseModel):
    """One row from the exchange rate board."""
    currency_code: str
    rate_to_usd: float
    updated_at: str | None = None

    model_config = {"from_attributes": True}


class RateUpdate(BaseModel):
    """Used by admins to update an exchange rate."""
    rate_to_usd: float = Field(..., gt=0, description="New rate: 1 unit of this currency = X USD")


class ConvertRequest(BaseModel):
    """Query params for currency conversion."""
    amount: float
    from_currency: str
    to_currency: str


class ConvertResponse(BaseModel):
    """Result of a currency conversion."""
    original_amount: float
    original_currency: str
    converted_amount: float
    converted_currency: str
    rate_used: str  # Human-readable rate description


class CurrencyPreference(BaseModel):
    """Used to set a user's preferred display currency."""
    preferred_currency: str = Field(..., max_length=3, description="Currency code: USD, EUR, or GBP")


# --- Endpoints ---

@router.get("/rates", response_model=list[ExchangeRateResponse])
def get_exchange_rates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all exchange rates.
    This is the "price board" — shows how much each currency is worth in USD.
    """
    # Ensure rates are seeded on first access
    currency_service.seed_exchange_rates(db)
    return currency_service.get_all_rates(db)


@router.put("/rates/{currency_code}", response_model=ExchangeRateResponse)
def update_exchange_rate(
    currency_code: str,
    update: RateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an exchange rate (admin/manager only).
    Like the currency exchange clerk updating the price board.
    """
    if current_user.role not in ("admin", "manager"):
        raise HTTPException(status_code=403, detail="Only admins and managers can update exchange rates")

    rate = currency_service.update_rate(db, currency_code, update.rate_to_usd)
    if not rate:
        raise HTTPException(status_code=404, detail=f"Currency '{currency_code}' not found")
    return rate


@router.get("/convert")
def convert_amount(
    amount: float,
    from_currency: str = "USD",
    to_currency: str = "EUR",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Convert an amount between two currencies.
    Like using the calculator at the airport exchange counter.

    Example: /api/currency/convert?amount=100&from_currency=USD&to_currency=EUR
    """
    rates = currency_service.get_rates_dict(db)

    from_upper = from_currency.upper()
    to_upper = to_currency.upper()

    if from_upper not in rates:
        raise HTTPException(status_code=400, detail=f"Unknown currency: {from_currency}")
    if to_upper not in rates:
        raise HTTPException(status_code=400, detail=f"Unknown currency: {to_currency}")

    converted = currency_service.convert(amount, from_upper, to_upper, rates)

    return {
        "original_amount": amount,
        "original_currency": from_upper,
        "converted_amount": converted,
        "converted_currency": to_upper,
        "rate_used": f"1 {from_upper} = {round(rates[from_upper] / rates[to_upper], 4)} {to_upper}",
    }


@router.put("/preference")
def update_currency_preference(
    pref: CurrencyPreference,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Set your preferred display currency.
    Like clicking "Show prices in EUR" on an international website.
    All analytics and dashboards will convert to this currency.
    """
    code = pref.preferred_currency.upper()
    if code not in currency_service.SUPPORTED_CURRENCIES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported currency: {code}. Supported: {currency_service.SUPPORTED_CURRENCIES}"
        )

    current_user.preferred_currency = code
    db.commit()
    db.refresh(current_user)

    return {
        "message": f"Display currency updated to {code}",
        "preferred_currency": code,
    }


@router.get("/supported")
def get_supported_currencies(current_user: User = Depends(get_current_user)):
    """
    List all supported currencies with their symbols.
    Used by the frontend to populate currency dropdown menus.
    """
    return [
        {"code": "USD", "name": "US Dollar", "symbol": "$"},
        {"code": "EUR", "name": "Euro", "symbol": "\u20ac"},
        {"code": "GBP", "name": "British Pound", "symbol": "\u00a3"},
    ]
