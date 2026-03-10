"""
PRODUCTION CONFIGURATION
=========================
This file centralizes ALL configuration for the backend.

WHY THIS EXISTS:
In development, we use simple defaults (weak passwords, localhost URLs).
In production, we MUST use strong secrets, real database URLs, etc.

HOW IT WORKS:
Every setting is read from an ENVIRONMENT VARIABLE first.
If the variable isn't set, it falls back to a development default.
When you deploy, you set these environment variables on your hosting platform.

Think of it like a restaurant's recipe card:
- The recipe says "add salt to taste"
- At home, you use table salt (development)
- At the restaurant, the chef uses Maldon sea salt (production)
- Same recipe, different ingredients depending on the environment.
"""

import os


# --- ENVIRONMENT ---
# "production" or "development" — controls security behaviors
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# --- DATABASE ---
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://vendorapp:vendorpass@localhost:5432/vendormanagement",
)

# --- SECURITY ---
# JWT secret key: In production, this MUST be a long random string.
# Generate one with: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "dev-secret-key-change-in-production-please",
)

# How long login sessions last (in hours)
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))

# --- CORS ---
# Which frontend URLs are allowed to call our API.
# In development: http://localhost:3000
# In production: your real domain like https://vendorapp.com
# Separate multiple origins with commas: https://app.example.com,https://example.com
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000",
).split(",")

# --- FILE UPLOADS ---
# Maximum upload size in bytes (default: 10 MB)
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", str(10 * 1024 * 1024)))
