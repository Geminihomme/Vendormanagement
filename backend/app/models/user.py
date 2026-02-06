"""
USER DATABASE MODEL
====================
This file defines the "users" table in our database.

WHAT IS A USER?
A user is someone who logs into our vendor management system.
They might be an admin who manages everything, a manager who
approves vendors, or a viewer who can only look at data.

WHY WE NEED A USERS TABLE:
Without users, anyone could access and modify vendor data.
The users table lets us:
1. Track WHO made changes (accountability)
2. Control WHAT different people can do (permissions via roles)
3. Keep the system secure (login required)

SECURITY NOTE - PASSWORD HASHING:
We NEVER store passwords as plain text. Instead, we store a "hash."
Think of hashing like a meat grinder: you can turn steak into ground beef,
but you can't turn ground beef back into steak. If someone steals our
database, they get hashes (useless) instead of actual passwords.

When a user logs in:
1. They type their password
2. We hash what they typed
3. We compare our stored hash with the new hash
4. If they match, the password is correct -- without ever storing it!

RELATIONSHIPS:
A user can create MANY contracts (one-to-many).
Think of it like an author and books -- one author can write many books.

EXAMPLE DATA:
| id | full_name     | email             | role    | is_active |
|----|---------------|-------------------|---------|-----------|
| 1  | Sarah Chen    | sarah@company.com | admin   | True      |
| 2  | Mike Johnson  | mike@company.com  | manager | True      |
| 3  | Lisa Park     | lisa@company.com  | viewer  | True      |
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
import enum
import hashlib
import os

from app.database import Base


class UserRole(str, enum.Enum):
    """
    Roles control what a user can do:
    - ADMIN: Full access -- can manage users, vendors, and contracts
    - MANAGER: Can create/edit vendors and contracts, but can't manage users
    - VIEWER: Read-only access -- can look but not touch
    """
    ADMIN = "admin"
    MANAGER = "manager"
    VIEWER = "viewer"


class User(Base):
    """
    The Users table - stores login credentials and profile info
    for everyone who uses our system.
    """

    __tablename__ = "users"

    # --- COLUMNS ---

    # Primary key: unique auto-incrementing ID
    id = Column(Integer, primary_key=True, index=True)

    # Profile information
    full_name = Column(String(255), nullable=False)       # Display name
    email = Column(String(255), nullable=False, unique=True, index=True)
    # unique=True means no two users can have the same email.
    # index=True makes lookups by email fast (we search by email on every login).

    # Authentication (login)
    hashed_password = Column(String(255), nullable=False)
    # We store the HASH of the password, never the actual password.

    # Role-based access control
    role = Column(String(20), nullable=False, default=UserRole.VIEWER)

    # Account status -- lets admins disable accounts without deleting them
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # --- RELATIONSHIP ---
    # A user can create many contracts.
    # This lets us do: user.contracts to get all contracts this user created.
    contracts = relationship("Contract", back_populates="created_by")

    # --- PASSWORD METHODS ---
    # These are "instance methods" -- functions that belong to a specific user.

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Turn a plain-text password into a hash.

        We use SHA-256 with a random "salt."
        The salt is random data mixed in so that two users with the
        same password get DIFFERENT hashes. This prevents attackers
        from using pre-computed hash tables ("rainbow tables").

        The format stored is: salt$hash
        """
        salt = os.urandom(32).hex()  # Random 32 bytes as hex string
        hash_value = hashlib.sha256((salt + password).encode()).hexdigest()
        return f"{salt}${hash_value}"

    def verify_password(self, password: str) -> bool:
        """
        Check if a given password matches this user's stored hash.

        Steps:
        1. Extract the salt from the stored hash
        2. Hash the provided password with that same salt
        3. Compare the result with the stored hash
        """
        salt, stored_hash = self.hashed_password.split("$")
        check_hash = hashlib.sha256((salt + password).encode()).hexdigest()
        return check_hash == stored_hash
