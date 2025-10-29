"""
test_connection.py
------------------
Cross-platform PostgreSQL & Supabase connectivity test (IPv6-aware, macOS-ready).

Responsibilities:
- Validate environment variables (PG_CONN, SUPABASE_URL).
- Resolve database host DNS (IPv4/IPv6) and print connection diagnostics.
- Optionally ping Supabase REST endpoint for project validation.
- Test PostgreSQL connectivity and verify core table presence.

Usage:
    python test_connection.py

Exit Codes:
    0 → Connection successful
    1 → DNS or database connection failure
"""
import os, sys, socket, urllib.parse
import psycopg2, pandas as pd, requests
from dotenv import load_dotenv

# Load environment variables from .env file.
load_dotenv()
PG_CONN = os.getenv("PG_CONN","")
SUPABASE_URL = os.getenv("SUPABASE_URL","")

# Extract hostname from PostgreSQL connection string.
def host_from_conn(s):
    p = urllib.parse.urlparse(s.replace("postgresql://","http://",1))
    return p.hostname

# Attempt DNS resolution for both IPv4 and IPv6 addresses.
def can_resolve(host):
    try:
        # getaddrinfo mengembalikan IPv4/IPv6; cukup bukti DNS OK
        info = socket.getaddrinfo(host, None)
        fams = {i[0] for i in info}
        return True, ("IPv6" if socket.AF_INET6 in fams else "IPv4/IPv6"), info[0][4][0]
    except Exception as e:
        return False, str(e), None

# Display loaded environment variables for quick debugging.
print("PG_CONN:", PG_CONN or "(missing)")
print("SUPABASE_URL:", SUPABASE_URL or "(missing)")

host = host_from_conn(PG_CONN) if PG_CONN else None
print("DB Host:", host)

# Validate that the database host can be resolved via DNS.
ok, fam, ip = can_resolve(host) if host else (False,"no-host",None)
if not ok:
    print("❌ DNS gagal:", fam)
    sys.exit(1)
print(f"🌐 DNS OK → {ip} ({fam})")

# Optional: Ping Supabase REST endpoint to confirm project is reachable.
if SUPABASE_URL:
    try:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/", timeout=10)
        print("REST ping:", SUPABASE_URL, "→", r.status_code)
    except Exception as e:
        print("REST ping gagal:", e)

print("\n=== PostgreSQL connect ===")
# Attempt PostgreSQL connection and basic query validation.
try:
    with psycopg2.connect(PG_CONN) as conn:
        cur = conn.cursor()
        cur.execute("select current_database(), current_user, version();")
        print("✅", cur.fetchone())
        # Optional: Check if core schema is populated (core.employees table).
        try:
            df = pd.read_sql_query("select count(*) n from core.employees;", conn)
            print("core.employees rows:", int(df.loc[0,"n"]))
        except Exception as e:
            print("ℹ️  core.employees belum ada / belum terisi:", e)
except Exception as e:
    print("❌ Connect error:", e)
    print("Tips: pastikan ?sslmode=require, dan IPv6 port 5432 tidak diblok firewall/router.")
    sys.exit(1)