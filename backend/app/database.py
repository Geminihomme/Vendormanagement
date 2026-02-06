"""
DATABASE CONNECTION
===================
This file sets up the connection between our Python code and PostgreSQL.

Think of it like setting up a phone line between two offices:
- Our Python code is one office
- PostgreSQL (the database) is the other office
- SQLAlchemy is the phone system that lets them talk

WHY we need this:
Without a database connection, our app would lose all data every time it restarts.
The database stores vendor information permanently.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# The DATABASE_URL tells Python where to find PostgreSQL.
# Format: postgresql://username:password@host:port/database_name
# We read it from an environment variable so we don't hardcode passwords.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://vendorapp:vendorpass@localhost:5432/vendormanagement"
)

# The "engine" is the actual connection to the database.
# Think of it as opening the phone line.
engine = create_engine(DATABASE_URL)

# A "session" is a single conversation with the database.
# Each time someone makes an API request, we open a session,
# do our work, and then close it.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# This is the "base class" that all our database tables will inherit from.
# It's like a template that says "everything that extends me is a database table."
class Base(DeclarativeBase):
    pass


def get_db():
    """
    This function provides a database session to our API endpoints.

    It uses a pattern called a "generator" (the yield keyword):
    1. Opens a database session
    2. Lets the API endpoint use it
    3. Closes it when done (even if there was an error)

    This prevents "connection leaks" (leaving phone lines open forever).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
