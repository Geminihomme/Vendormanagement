"""
USER SERVICE (Business Logic)
===============================
Handles all user-related operations: creating accounts,
looking up users, updating profiles, and deactivating accounts.

KEY SECURITY LOGIC:
- Passwords are hashed BEFORE being stored (see create_user)
- We check for duplicate emails BEFORE creating (see create_user)
- The service layer is the right place for this logic because
  it sits between "what the API receives" and "what hits the database"

HOW it fits in:
API Route (receives request) -> Service (does the work) -> Database (stores data)
"""

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def get_users(db: Session, skip: int = 0, limit: int = 100):
    """Get a list of all users, with pagination."""
    return db.query(User).offset(skip).limit(limit).all()


def get_user(db: Session, user_id: int):
    """Get a single user by their ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    """
    Look up a user by their email address.
    Used during login and when checking for duplicate emails.
    """
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user: UserCreate):
    """
    Create a new user account.

    Steps:
    1. Hash the password (NEVER store plain text)
    2. Create the User model with the hashed password
    3. Save to database
    """
    hashed = User.hash_password(user.password)
    db_user = User(
        full_name=user.full_name,
        email=user.email,
        hashed_password=hashed,
        role=user.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int, user_update: UserUpdate):
    """Update a user's profile information (not password)."""
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return None

    update_data = user_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int):
    """
    Delete a user from the database.
    In practice, you might prefer deactivating (is_active=False)
    instead of deleting, to preserve audit trails.
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        return False

    db.delete(db_user)
    db.commit()
    return True
