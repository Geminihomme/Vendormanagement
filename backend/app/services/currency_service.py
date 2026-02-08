"""
CURRENCY SERVICE (The Money Translator)
=========================================
This service handles converting amounts between different currencies.

REAL-WORLD ANALOGY - Buying Souvenirs Abroad:
Imagine you're shopping in London with British pounds (GBP).
You see a souvenir for 20 GBP and wonder: "How much is that in euros?"

Step 1: Convert GBP to the common language (USD)
  20 GBP * 1.27 (GBP rate) = 25.40 USD

Step 2: Convert USD to EUR
  25.40 USD / 1.08 (EUR rate) = 23.52 EUR

That's exactly what our convert() function does.
Every conversion goes THROUGH USD, like a translator who speaks
every language by first translating to English, then to the target.

WHY THROUGH USD?
If we had 5 currencies, we'd need 20 direct conversion rates
(each to every other). By going through USD, we only need 5 rates
(each to USD). It's like a hub-and-spoke airline system vs. point-to-point.

SUPPORTED CURRENCIES (for EMEA):
- USD (US Dollar)      - The base/hub currency
- EUR (Euro)           - Most of continental Europe
- GBP (British Pound)  - United Kingdom

SEEDING:
On first startup, if no rates exist, we pre-load sensible defaults.
In a production system, you'd fetch live rates from an API like
Open Exchange Rates or the European Central Bank.
"""

from sqlalchemy.orm import Session
from app.models.exchange_rate import ExchangeRate

# The three currencies we support for EMEA operations.
# These are ISO 4217 codes — the international standard for currency names.
SUPPORTED_CURRENCIES = ["USD", "EUR", "GBP"]

# Default rates: how much 1 unit of each currency is worth in USD.
# These are approximate mid-market rates. In production, you'd
# update these daily from a live exchange rate API.
DEFAULT_RATES = {
    "USD": 1.0,      # 1 USD = 1 USD (always)
    "EUR": 1.08,     # 1 EUR = 1.08 USD (the euro is worth more than the dollar)
    "GBP": 1.27,     # 1 GBP = 1.27 USD (the pound is worth even more)
}


def seed_exchange_rates(db: Session) -> None:
    """
    Pre-load default exchange rates if the table is empty.

    This is like stocking the shelves on opening day — we need SOME
    rates to work with before an admin sets real ones.
    """
    existing = db.query(ExchangeRate).count()
    if existing > 0:
        return  # Already seeded — don't overwrite admin changes

    for code, rate in DEFAULT_RATES.items():
        db.add(ExchangeRate(currency_code=code, rate_to_usd=rate))
    db.commit()


def get_all_rates(db: Session) -> list[ExchangeRate]:
    """Get all exchange rates, ordered by currency code."""
    return db.query(ExchangeRate).order_by(ExchangeRate.currency_code).all()


def get_rate(db: Session, currency_code: str) -> ExchangeRate | None:
    """Look up the rate for a specific currency."""
    return db.query(ExchangeRate).filter(
        ExchangeRate.currency_code == currency_code.upper()
    ).first()


def update_rate(db: Session, currency_code: str, new_rate: float) -> ExchangeRate | None:
    """
    Update an exchange rate. Returns the updated record, or None if not found.

    Only admins should call this — it's like updating the price board
    at the airport currency exchange.
    """
    rate = get_rate(db, currency_code)
    if not rate:
        return None
    rate.rate_to_usd = new_rate
    db.commit()
    db.refresh(rate)
    return rate


def convert(
    amount: float,
    from_currency: str,
    to_currency: str,
    rates: dict[str, float],
) -> float:
    """
    Convert an amount from one currency to another.

    HOW IT WORKS (The Airport Translator):
    1. Convert FROM currency -> USD (multiply by the FROM rate)
    2. Convert USD -> TO currency (divide by the TO rate)

    Example: Convert 100 EUR to GBP
      Step 1: 100 EUR * 1.08 = 108.00 USD
      Step 2: 108.00 USD / 1.27 = 85.04 GBP

    The "rates" dict looks like: {"USD": 1.0, "EUR": 1.08, "GBP": 1.27}
    """
    from_code = from_currency.upper()
    to_code = to_currency.upper()

    # Same currency? No conversion needed!
    if from_code == to_code:
        return amount

    from_rate = rates.get(from_code, 1.0)
    to_rate = rates.get(to_code, 1.0)

    # Step 1: Convert to USD
    amount_in_usd = amount * from_rate

    # Step 2: Convert from USD to target
    return round(amount_in_usd / to_rate, 2)


def get_rates_dict(db: Session) -> dict[str, float]:
    """
    Get all rates as a simple dictionary for quick lookups.
    Used by the convert() function.

    Returns: {"USD": 1.0, "EUR": 1.08, "GBP": 1.27}
    """
    rates = get_all_rates(db)
    return {r.currency_code: r.rate_to_usd for r in rates}
