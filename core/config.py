"""
config.py
---------
Memuat konfigurasi environment project.

Fungsi utama:
- Memuat variabel koneksi dari file `.env` (PG_CONN, SUPABASE_URL, SUPABASE_KEY).
- Menyediakan fungsi `validate_env()` untuk memastikan variabel penting tersedia.
"""

import os
from dotenv import load_dotenv

load_dotenv()

PG_CONN = os.getenv("PG_CONN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def validate_env():
    missing = [k for k,v in {
        "PG_CONN": PG_CONN,
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_KEY": SUPABASE_KEY,
    }.items() if not v]
    if missing:
        raise RuntimeError(f"Missing env vars: {', '.join(missing)}")