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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.api import vendors, users, contracts

# Import all models so SQLAlchemy knows about them when creating tables.
# Without these imports, the users and contracts tables wouldn't be created.
import app.models.vendor     # noqa: F401
import app.models.user       # noqa: F401
import app.models.contract   # noqa: F401

# Create the FastAPI application.
# This is our "app" - the central object that everything connects to.
app = FastAPI(
    title="Vendor Management Platform",
    description="API for managing vendors, contracts, and compliance",
    version="0.1.0",
)

# CORS = Cross-Origin Resource Sharing.
# By default, a browser blocks requests from one website to another
# (security feature). Our React frontend (localhost:3000) needs to talk
# to our backend (localhost:8000), so we explicitly allow it.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React development server
    ],
    allow_credentials=True,
    allow_methods=["*"],   # Allow GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],   # Allow any headers
)

# Create all database tables when the app starts.
# In a production app, you'd use Alembic migrations instead,
# but this is simpler for getting started.
Base.metadata.create_all(bind=engine)

# Register all API routes. Each line tells FastAPI:
# "Any request starting with /api/X should be handled by module X."
# The tags help organize the auto-generated API docs at /docs
app.include_router(vendors.router, prefix="/api/vendors", tags=["vendors"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(contracts.router, prefix="/api/contracts", tags=["contracts"])


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
