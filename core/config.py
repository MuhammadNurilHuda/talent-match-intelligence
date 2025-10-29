"""
config.py
----------
This module handles environment configuration for the Talent Match Intelligence project.

Responsibilities:
- Load critical environment variables from the `.env` file.
- Expose constants for PostgreSQL and Supabase connections.
- Validate that all required variables are available before use.

Usage:
Import this module and call `validate_env()` at application startup to ensure
all environment configurations are correctly set.
"""

import os
from dotenv import load_dotenv

# Load environment variables from the `.env` file into the system environment.
load_dotenv()

# PostgreSQL connection string for database access.
PG_CONN = os.getenv("PG_CONN")
# Supabase project URL for API communication.
SUPABASE_URL = os.getenv("SUPABASE_URL")
# Supabase service or anonymous key used for authentication.
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def validate_env():
    """
    Ensure that all required environment variables are defined.

    Checks:
        - PG_CONN: Database connection string.
        - SUPABASE_URL: Base URL of the Supabase project.
        - SUPABASE_KEY: API key for Supabase access.

    Raises:
        RuntimeError: If one or more of the required environment variables are missing.
    """
    # Identify which required variables are missing or undefined.
    missing = [k for k,v in {
        "PG_CONN": PG_CONN,
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_KEY": SUPABASE_KEY,
    }.items() if not v]
    # Raise an error listing all missing environment variables for easier debugging.
    if missing:
        raise RuntimeError(f"Missing env vars: {', '.join(missing)}")