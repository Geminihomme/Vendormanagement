"""
USER API ROUTES
=================
URLs the frontend calls to manage users.

ENDPOINTS:
  GET    /api/users/          -> List all users
  POST   /api/users/          -> Create a new user (register)
  GET    /api/users/{id}      -> Get one user's profile
  PUT    /api/users/{id}      -> Update a user
  DELETE /api/users/{id}      -> Delete a user

SECURITY NOTE:
In a production app, most of these would require authentication
(you'd need to be logged in) and authorization (only admins can
create/delete users). We'll add that later.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.services import user_service

router = APIRouter()


@router.get("/", response_model=list[UserResponse])
def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Get all users. Passwords are NEVER included in the response."""
    return user_service.get_users(db, skip=skip, limit=limit)


@router.post("/", response_model=UserResponse, status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.

    Checks if the email is already taken first -- no duplicate accounts.
    The password is hashed by the service layer before storage.
    """
    # Check for existing email
    existing = user_service.get_user_by_email(db, user.email)
    if existing:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists"
        )

    return user_service.create_user(db, user)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a single user by ID."""
    user = user_service.get_user(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    """Update a user's profile."""
    user = user_service.update_user(db, user_id, user_update)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user."""
    success = user_service.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
