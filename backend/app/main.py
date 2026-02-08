"""
MAIN APPLICATION ENTRY POINT
==============================
This is where our FastAPI application starts. Think of it as the front door
to our backend. Every request from the frontend comes through here first.

WHY this file matters:
- It creates the FastAPI "app" that handles all web requests
- It sets up CORS (security rules for who can talk to our backend)
- It connects all our API routes (URLs) to the app
- It creates the database tables when the app first starts

HOW it fits in:
Browser -> main.py (routes request) -> api/vendors.py (handles it) -> database
"""

import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import CORS_ORIGINS, ENVIRONMENT

# Set up logging so background jobs can print messages.
# Think of logging as the app writing in its diary -- helpful for debugging.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

from app.database import engine, Base
from app.api import auth, vendors, users, contracts, notifications, payments, approvals, risk, reports, currency

# Import all models so SQLAlchemy knows about them when creating tables.
# Without these imports, the tables wouldn't be created.
import app.models.vendor       # noqa: F401
import app.models.user         # noqa: F401
import app.models.contract     # noqa: F401
import app.models.notification # noqa: F401
import app.models.payment      # noqa: F401
import app.models.approval     # noqa: F401
import app.models.risk_assessment  # noqa: F401
import app.models.exchange_rate    # noqa: F401

# LIFESPAN: What happens when the app starts up and shuts down.
# This is where we start and stop the background scheduler.
# Think of it as the "opening" and "closing" procedures for a store:
# - Opening: turn on lights, unlock doors, START THE SCHEDULER
# - Closing: lock doors, turn off lights, STOP THE SCHEDULER
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs on app startup and shutdown."""
    # --- STARTUP ---
    from app.scheduler import start_scheduler
    start_scheduler()
    yield
    # --- SHUTDOWN ---
    from app.scheduler import stop_scheduler
    stop_scheduler()


# Create the FastAPI application.
# This is our "app" - the central object that everything connects to.
app = FastAPI(
    title="Vendor Management Platform",
    description="API for managing vendors, contracts, and compliance",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS = Cross-Origin Resource Sharing.
# By default, a browser blocks requests from one website to another
# (security feature). Our React frontend needs to talk to our backend,
# so we explicitly allow it.
# In development: allows http://localhost:3000
# In production: set the CORS_ORIGINS environment variable to your real domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],   # Allow GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],   # Allow any headers
)

# Create all database tables when the app starts.
# In a production app, you'd use Alembic migrations instead,
# but this is simpler for getting started.
Base.metadata.create_all(bind=engine)

# Seed default exchange rates (USD, EUR, GBP) on first run.
# Like stocking the currency exchange board on opening day.
from app.database import SessionLocal
from app.services.currency_service import seed_exchange_rates
_seed_db = SessionLocal()
seed_exchange_rates(_seed_db)
_seed_db.close()

# Register all API routes. Each line tells FastAPI:
# "Any request starting with /api/X should be handled by module X."
# The tags help organize the auto-generated API docs at /docs
# Auth routes are PUBLIC (no login required to register or log in!)
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])

# All other routes require authentication (handled in each route via Depends)
app.include_router(vendors.router, prefix="/api/vendors", tags=["vendors"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(contracts.router, prefix="/api/contracts", tags=["contracts"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(payments.router, prefix="/api/payments", tags=["payments"])
app.include_router(approvals.router, prefix="/api/approvals", tags=["approvals"])
app.include_router(risk.router, prefix="/api/risk", tags=["risk"])
app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(currency.router, prefix="/api/currency", tags=["currency"])

# Serve uploaded files (PDFs, etc.) as static files.
# When someone visits /uploads/contracts/abc123.pdf, FastAPI serves the file
# directly from the uploads/contracts/ folder on disk.
# This is how the browser downloads contract documents.
UPLOAD_DIR = Path(__file__).resolve().parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


@app.get("/")
def root():
    """
    A simple health check endpoint.
    If you visit http://localhost:8000/ and see this message,
    the backend is running correctly.
    """
    return {"message": "Vendor Management API is running"}


@app.get("/health")
def health_check():
    """
    Health check endpoint used by monitoring tools and Docker
    to verify the application is alive and responding.
    """
    return {"status": "healthy"}
