"""
EXCHANGE RATE DATABASE MODEL (The Currency Price Board)
========================================================
This file defines the "exchange_rates" table — a record of how much
each currency is worth compared to a base currency (USD).

REAL-WORLD ANALOGY - The Airport Currency Exchange Board:
When you walk through an airport, there's a big board showing:
  USD 1.00 = EUR 0.92
  USD 1.00 = GBP 0.79
  USD 1.00 = USD 1.00

That board IS our exchange_rates table. Each row says:
"One US dollar is worth THIS MUCH in another currency."

WHY WE STORE RATES THIS WAY:
All rates are stored relative to USD (the "base currency").
To convert between ANY two currencies, we go through USD:
  EUR -> USD -> GBP

It's like connecting flights:
  You can't fly direct from a small city to another small city,
  but you can always connect through a major hub (USD).

EXAMPLE DATA:
| id | currency | rate_to_usd | updated_at          |
|----|----------|-------------|---------------------|
| 1  | USD      | 1.000000    | 2026-02-08 10:00:00 |
| 2  | EUR      | 1.080000    | 2026-02-08 10:00:00 |
| 3  | GBP      | 1.270000    | 2026-02-08 10:00:00 |

Reading the table: 1 EUR = 1.08 USD, 1 GBP = 1.27 USD.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float

from app.database import Base


class ExchangeRate(Base):
    """
    Stores exchange rates relative to USD.

    rate_to_usd means: "1 unit of this currency = X USD"
    - EUR with rate_to_usd=1.08 means: 1 EUR = 1.08 USD
    - GBP with rate_to_usd=1.27 means: 1 GBP = 1.27 USD
    - USD with rate_to_usd=1.00 means: 1 USD = 1.00 USD (always 1)
    """

    __tablename__ = "exchange_rates"

    id = Column(Integer, primary_key=True, index=True)

    # The currency code: "USD", "EUR", "GBP"
    # ISO 4217 standard — the international language for currencies
    currency_code = Column(String(3), nullable=False, unique=True, index=True)

    # How much 1 unit of this currency is worth in USD
    rate_to_usd = Column(Float, nullable=False)

    # When this rate was last updated (rates change daily in the real world)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
