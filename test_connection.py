# test_connection.py (mac-ready, IPv6 aware)
import os, sys, socket, urllib.parse
import psycopg2, pandas as pd, requests
from dotenv import load_dotenv

load_dotenv()
PG_CONN = os.getenv("PG_CONN","")
SUPABASE_URL = os.getenv("SUPABASE_URL","")

def host_from_conn(s):
    p = urllib.parse.urlparse(s.replace("postgresql://","http://",1))
    return p.hostname

def can_resolve(host):
    try:
        # getaddrinfo mengembalikan IPv4/IPv6; cukup bukti DNS OK
        info = socket.getaddrinfo(host, None)
        fams = {i[0] for i in info}
        return True, ("IPv6" if socket.AF_INET6 in fams else "IPv4/IPv6"), info[0][4][0]
    except Exception as e:
        return False, str(e), None

print("PG_CONN:", PG_CONN or "(missing)")
print("SUPABASE_URL:", SUPABASE_URL or "(missing)")

host = host_from_conn(PG_CONN) if PG_CONN else None
print("DB Host:", host)

ok, fam, ip = can_resolve(host) if host else (False,"no-host",None)
if not ok:
    print("❌ DNS gagal:", fam)
    sys.exit(1)
print(f"🌐 DNS OK → {ip} ({fam})")

# optional ping REST untuk validasi project ref
if SUPABASE_URL:
    try:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/", timeout=10)
        print("REST ping:", SUPABASE_URL, "→", r.status_code)
    except Exception as e:
        print("REST ping gagal:", e)

print("\n=== PostgreSQL connect ===")
try:
    with psycopg2.connect(PG_CONN) as conn:
        cur = conn.cursor()
        cur.execute("select current_database(), current_user, version();")
        print("✅", cur.fetchone())
        try:
            df = pd.read_sql_query("select count(*) n from core.employees;", conn)
            print("core.employees rows:", int(df.loc[0,"n"]))
        except Exception as e:
            print("ℹ️  core.employees belum ada / belum terisi:", e)
except Exception as e:
    print("❌ Connect error:", e)
    print("Tips: pastikan ?sslmode=require, dan IPv6 port 5432 tidak diblok firewall/router.")
    sys.exit(1)