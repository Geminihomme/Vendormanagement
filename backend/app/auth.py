"""
AUTHENTICATION MODULE (The Bouncer)
======================================
This is the security guard at the entrance of our app. It handles:
1. Creating JWT tokens when someone logs in
2. Verifying tokens on every request (checking the wristband)
3. Extracting user info from tokens

WHAT IS A JWT TOKEN?
=====================
JWT stands for "JSON Web Token." Think of it as a TAMPER-PROOF wristband.

When you log in, the server creates a token that looks like:
  eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiw...

This long string is actually THREE parts separated by dots:
1. HEADER: Says "this is a JWT, signed with HS256 algorithm"
2. PAYLOAD: The actual data — user ID, email, role, expiration time
3. SIGNATURE: A cryptographic stamp proving the server created it

WHY JWT INSTEAD OF SESSIONS?
Traditional sessions store login data on the SERVER (in memory or a database).
JWTs store the data IN THE TOKEN ITSELF. This means:
- The server doesn't need to remember who's logged in
- The token is self-contained (like a passport vs. a membership card)
- It works great with APIs (our React frontend can just attach it to requests)

HOW THE SECRET KEY WORKS:
The server signs tokens with a SECRET_KEY (a password only the server knows).
If someone tries to modify a token (change their role from "viewer" to "admin"),
the signature won't match, and we'll reject it. It's like a holographic stamp
on a wristband — you can't fake it.

SECURITY BEST PRACTICES WE FOLLOW:
1. Tokens expire after 24 hours (limits damage if stolen)
2. Secret key is read from environment variable (not hardcoded)
3. Passwords are hashed (never stored as plain text)
4. Token verification happens on EVERY request to protected routes
"""

import os
from datetime import datetime, timedelta

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.config import JWT_SECRET_KEY, JWT_EXPIRE_HOURS

# --- CONFIGURATION ---

# The secret key used to sign JWT tokens.
# Read from the centralized config (which reads from environment variables).
SECRET_KEY = JWT_SECRET_KEY

# The algorithm used to sign tokens. HS256 is standard and secure.
ALGORITHM = "HS256"

# How long tokens are valid. Configurable via JWT_EXPIRE_HOURS env var.
ACCESS_TOKEN_EXPIRE_HOURS = JWT_EXPIRE_HOURS

# This tells FastAPI: "Look for a Bearer token in the Authorization header."
# When the frontend sends a request, it includes:
#   Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
# FastAPI extracts the token part automatically.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def create_access_token(user_id: int, email: str, role: str) -> str:
    """
    Create a JWT token for a user who just logged in.

    THE TOKEN CONTAINS (the "payload"):
    - sub: The user's ID (sub = "subject" — who this token is about)
    - email: Their email
    - role: Their role (admin/manager/viewer)
    - exp: When the token expires (current time + 24 hours)

    This is like writing on the wristband:
    "Name: Sarah, Ticket: VIP, Valid Until: Tomorrow 8 AM"
    """
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)

    payload = {
        "sub": str(user_id),   # "subject" — who is this token for?
        "email": email,
        "role": role,
        "exp": expire,         # expiration time
    }

    # Sign the token with our secret key
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    THIS IS THE BOUNCER FUNCTION.

    It runs on EVERY request to a protected route. It:
    1. Extracts the JWT token from the request header
    2. Decodes and verifies it (checks the signature)
    3. Looks up the user in the database
    4. Returns the User object (or raises an error)

    If the token is missing, expired, or tampered with, the user
    gets a 401 "Unauthorized" error — like being turned away at the door.

    HOW IT'S USED:
    In any route, add this as a parameter:
      def my_route(current_user: User = Depends(get_current_user)):
    FastAPI will automatically run this check before the route code runs.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode the token and extract the payload
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")

        if user_id_str is None:
            raise credentials_exception

        user_id = int(user_id_str)

    except (JWTError, ValueError):
        # JWTError: token is invalid, expired, or tampered with
        # ValueError: user_id couldn't be converted to int
        raise credentials_exception

    # Look up the user in the database
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated",
        )

    return user
