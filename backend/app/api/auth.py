"""
AUTHENTICATION API ROUTES (The Front Desk)
=============================================
These endpoints handle the login/registration flow.

ENDPOINTS:
  POST /api/auth/register   -> Create a new account
  POST /api/auth/login      -> Log in and receive a JWT token
  GET  /api/auth/me         -> Get the currently logged-in user's info

THE LOGIN FLOW (step by step):
================================
1. User enters email + password on the Login page
2. Frontend sends: POST /api/auth/login {email, password}
3. Backend looks up the user by email
4. Backend verifies the password hash
5. If correct: creates a JWT token and sends it back
6. Frontend stores the token in localStorage
7. Every future request includes: Authorization: Bearer <token>
8. The "get_current_user" function checks the token on each request

WHY IS THIS SEPARATE FROM THE USERS API?
The users API is for MANAGING users (admin tasks: list, update, delete).
The auth API is for LOGGING IN (everyone does this).
Keeping them separate follows the "separation of concerns" principle:
- auth.py handles identity: "Who are you?"
- users.py handles management: "What can you do to user accounts?"
"""

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.services import user_service
from app.auth import create_access_token, get_current_user

router = APIRouter()


# --- SCHEMAS specific to auth ---

class LoginRequest(BaseModel):
    """What the frontend sends to log in."""
    email: str = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class LoginResponse(BaseModel):
    """What the backend sends back after successful login."""
    access_token: str     # The JWT token (the "wristband")
    token_type: str       # Always "bearer" — tells the frontend how to send it
    user: UserResponse    # The logged-in user's profile info


class RegisterRequest(BaseModel):
    """What the frontend sends to create an account."""
    full_name: str = Field(..., min_length=1, max_length=255, description="Your name")
    email: str = Field(..., max_length=255, description="Your email")
    password: str = Field(..., min_length=8, max_length=100, description="Password (min 8 characters)")


# --- ENDPOINTS ---

@router.post("/register", response_model=LoginResponse, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """
    Create a new account and immediately log the user in.

    WHAT HAPPENS:
    1. Check if email is already taken
    2. Hash the password (NEVER store plain text!)
    3. Save the new user to the database
    4. Create a JWT token
    5. Return the token + user profile

    The user is logged in immediately after registering (no separate login step).
    """
    # Check for duplicate email
    existing = user_service.get_user_by_email(db, body.email)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="An account with this email already exists",
        )

    # Create the user (password gets hashed in the service layer)
    user_data = UserCreate(
        full_name=body.full_name,
        email=body.email,
        password=body.password,
        role="viewer",  # New accounts start as viewers
    )
    new_user = user_service.create_user(db, user_data)

    # Create a token so they're immediately logged in
    token = create_access_token(new_user.id, new_user.email, new_user.role)

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user),
    )


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    """
    Log in with email and password.

    THE VERIFICATION PROCESS:
    1. Find the user by email
    2. If no user found → "Invalid credentials" (don't say "email not found"
       because that tells attackers which emails are registered)
    3. Verify the password hash
    4. If wrong password → "Invalid credentials" (same message — don't reveal
       whether it was the email or password that was wrong)
    5. If correct → create and return a JWT token

    SECURITY NOTE: We always return the SAME error message for both
    "wrong email" and "wrong password." If we said "email not found,"
    an attacker could use that to discover which emails are registered.
    This is called "information leakage" and it's a common vulnerability.
    """
    # Look up the user
    user = user_service.get_user_by_email(db, body.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Verify the password
    if not user.verify_password(body.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated. Contact an administrator.",
        )

    # Create and return the token
    token = create_access_token(user.id, user.email, user.role)

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Get the currently logged-in user's profile.

    This is how the frontend checks "Am I still logged in?" on page reload.
    It sends the stored token, and if valid, gets back the user's info.

    The 'Depends(get_current_user)' does all the work:
    1. Extracts the token from the request
    2. Verifies and decodes it
    3. Looks up the user in the database
    4. Returns the User object (or 401 if invalid)
    """
    return current_user
