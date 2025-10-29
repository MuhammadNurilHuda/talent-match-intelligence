"""
db.py
-----
This module manages database connectivity to Supabase (PostgreSQL).

Responsibilities:
- Provide a singleton SQLAlchemy Engine using the connection string defined in the `.env` file.
- Ensure lazy initialization of the engine for efficient resource usage.
- Handle connection validation with `pool_pre_ping` enabled.

Usage:
Import this module and call `get_engine()` whenever a database connection is required.
The engine is initialized only once per runtime session.
"""

from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

# Load environment variables from the `.env` file into the system environment.
load_dotenv()
# PostgreSQL connection string retrieved from environment variables.
PG_CONN = os.getenv("PG_CONN")

_engine = None
def get_engine():
    """
    Retrieve a singleton SQLAlchemy Engine for database access.

    The engine is lazily instantiated only once, ensuring efficient connection reuse.
    If the environment variable `PG_CONN` is not defined, a RuntimeError is raised.

    Returns:
        sqlalchemy.engine.Engine: Active SQLAlchemy engine connected to Supabase.
    Raises:
        RuntimeError: If `PG_CONN` is missing from the environment.
    """
    global _engine
    if _engine is None:
        # Validate that the database connection string is available.
        if not PG_CONN:
            raise RuntimeError("PG_CONN missing in .env")
        # Create a new SQLAlchemy Engine with connection pre-ping to ensure connection health.
        _engine = create_engine(PG_CONN, pool_pre_ping=True)
    # Return the existing or newly created engine instance.
    return _engine