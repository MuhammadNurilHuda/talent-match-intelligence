"""
db.py
-----
Menangani koneksi ke database Supabase (PostgreSQL).

Fungsi utama:
- `get_engine()` -> mengembalikan SQLAlchemy Engine tunggal (lazy-loaded).
- Menggunakan PG_CONN dari `.env`.
"""

from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()
PG_CONN = os.getenv("PG_CONN")

_engine = None
def get_engine():
    global _engine
    if _engine is None:
        if not PG_CONN:
            raise RuntimeError("PG_CONN missing in .env")
        _engine = create_engine(PG_CONN, pool_pre_ping=True)
    return _engine