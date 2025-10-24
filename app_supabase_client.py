# app_supabase_client.py
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise SystemExit("Missing SUPABASE_URL or SUPABASE_KEY in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# contoh: baca 5 baris dari tabel yang sudah diexpose via REST
# (di Supabase, buat view REST-friendly: mis. view core_employees untuk expose kolom aman)
print("=== Sample query (limit 5) ===")
resp = supabase.table("core_employees").select("*").limit(5).execute()
print(resp)
