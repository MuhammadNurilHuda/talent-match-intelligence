# test_connection.py
import os, sys, socket, urllib.parse
import psycopg2, pandas as pd, requests
from dotenv import load_dotenv
import socket
socket.setdefaulttimeout(10)
socket.AF_UNSPEC = socket.AF_INET  # paksa IPv4 (kadang bisa bypass)

load_dotenv()

PG_CONN = os.getenv("PG_CONN", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

print("🔗 PG_CONN:", PG_CONN or "(missing)")
print("🔗 SUPABASE_URL:", SUPABASE_URL or "(missing)")

# 1) Parse host dari PG_CONN dan cek DNS
try:
    parsed = urllib.parse.urlparse(PG_CONN.replace("postgresql://", "http://", 1))
    host = parsed.hostname
    print("🌐 Host parsed:", host)
    if not host:
        raise ValueError("Host tidak bisa diparse dari PG_CONN.")
    ip = socket.gethostbyname(host)
    print("🌐 DNS resolve OK →", ip)
except Exception as e:
    print("❌ DNS resolve gagal:", e)
    print("👉 Coba ganti DNS ke 1.1.1.1/8.8.8.8 atau test via hotspot.")
    sys.exit(1)

# 2) REST ping (cek project ref valid)
if SUPABASE_URL:
    try:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/", timeout=10)
        print("🌍 REST ping:", SUPABASE_URL, "→ status", r.status_code)
    except Exception as e:
        print("⚠️  REST ping gagal:", e)

# 3) Koneksi Postgres
print("\n=== Test koneksi PostgreSQL ===")
try:
    with psycopg2.connect(PG_CONN) as conn:
        cur = conn.cursor()
        cur.execute("SELECT current_database(), current_user, version();")
        print("✅ DB Info:", cur.fetchone())
        try:
            df = pd.read_sql_query("SELECT COUNT(*) AS n FROM core.employees;", conn)
            print("📦 core.employees rows:", int(df.loc[0, "n"]))
        except Exception as e:
            print("ℹ️  core.employees belum ada / belum terisi:", e)
except Exception as e:
    print("❌ Gagal konek ke Postgres:", e)
    print("👉 Pastikan ?sslmode=require dan port 5432 tidak diblok firewall.")
    sys.exit(1)
