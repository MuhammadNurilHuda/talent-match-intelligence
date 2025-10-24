# etl/load_to_postgres.py
import os, psycopg2
from dotenv import load_dotenv

load_dotenv()
pg_conn = os.getenv("PG_CONN")

with psycopg2.connect(pg_conn) as conn:
    cur = conn.cursor()
    cur.execute("SELECT current_database(), current_user;")
    print("Connected:", cur.fetchone())
