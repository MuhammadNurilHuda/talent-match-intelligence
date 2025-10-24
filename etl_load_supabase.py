# etl_load_supabase.py
import os
import sys
import csv
import psycopg2
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PG_CONN = os.getenv("PG_CONN")
STAGING_DIR = Path("staging_csv")

TABLE_FILES = [
    ("staging.talent_variable_tv_talent_g", "talent_variable_tv_talent_g.csv"),
    ("staging.dim_companies", "dim_companies.csv"),
    ("staging.dim_areas", "dim_areas.csv"),
    ("staging.dim_positions", "dim_positions.csv"),
    ("staging.dim_departments", "dim_departments.csv"),
    ("staging.dim_divisions", "dim_divisions.csv"),
    ("staging.dim_directorates", "dim_directorates.csv"),
    ("staging.dim_grades", "dim_grades.csv"),
    ("staging.dim_education", "dim_education.csv"),
    ("staging.dim_majors", "dim_majors.csv"),
    ("staging.dim_competency_pillars", "dim_competency_pillars.csv"),
    ("staging.employees", "employees.csv"),
    ("staging.profiles_psych", "profiles_psych.csv"),
    ("staging.papi_scores", "papi_scores.csv"),
    ("staging.strengths", "strengths.csv"),
    ("staging.performance_yearly", "performance_yearly.csv"),
    ("staging.competencies_yearly", "competencies_yearly.csv"),
]

DDL_STAGING = """
CREATE SCHEMA IF NOT EXISTS staging;

-- kamus TV/TGV
CREATE TABLE IF NOT EXISTS staging.talent_variable_tv_talent_g (
  test_as_talent_variable_tv TEXT, subtest TEXT, meaning TEXT, behavior_example TEXT,
  talent_group_variable_tgv TEXT, note TEXT
);

-- dims (single column: name)
CREATE TABLE IF NOT EXISTS staging.dim_companies(name TEXT);
CREATE TABLE IF NOT EXISTS staging.dim_areas(name TEXT);
CREATE TABLE IF NOT EXISTS staging.dim_positions(name TEXT);
CREATE TABLE IF NOT EXISTS staging.dim_departments(name TEXT);
CREATE TABLE IF NOT EXISTS staging.dim_divisions(name TEXT);
CREATE TABLE IF NOT EXISTS staging.dim_directorates(name TEXT);
CREATE TABLE IF NOT EXISTS staging.dim_grades(name TEXT);
CREATE TABLE IF NOT EXISTS staging.dim_education(name TEXT);
CREATE TABLE IF NOT EXISTS staging.dim_majors(name TEXT);

-- competency pillar
CREATE TABLE IF NOT EXISTS staging.dim_competency_pillars(pillar_code TEXT, pillar_label TEXT);

-- core-like staging
CREATE TABLE IF NOT EXISTS staging.employees(
  employee_id TEXT, fullname TEXT, nip TEXT, company TEXT, area TEXT, position TEXT,
  department TEXT, division TEXT, directorate TEXT, grade TEXT, education TEXT,
  major TEXT, years_of_service_months TEXT
);

CREATE TABLE IF NOT EXISTS staging.profiles_psych(
  employee_id TEXT, pauli TEXT, faxtor TEXT, disc TEXT, disc_word TEXT, mbti TEXT,
  iq TEXT, gtq TEXT, tiki TEXT
);

CREATE TABLE IF NOT EXISTS staging.papi_scores(
  employee_id TEXT, scale_code TEXT, score TEXT
);

CREATE TABLE IF NOT EXISTS staging.strengths(
  employee_id TEXT, rank TEXT, theme TEXT
);

CREATE TABLE IF NOT EXISTS staging.performance_yearly(
  employee_id TEXT, rating TEXT, year TEXT
);

CREATE TABLE IF NOT EXISTS staging.competencies_yearly(
  employee_id TEXT, score TEXT, pillar_code TEXT, year TEXT
);
"""

def copy_csv(conn, table, csv_path: Path):
    with conn.cursor() as cur, csv_path.open("r", newline="", encoding="utf-8") as f:
        # use COPY FROM STDIN for speed
        sql = f"COPY {table} FROM STDIN WITH (FORMAT CSV, HEADER TRUE)"
        cur.copy_expert(sql, f)
    conn.commit()

def count_rows(conn, table):
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {table};")
        return cur.fetchone()[0]

def main():
    if not PG_CONN:
        print("❌ PG_CONN not set. Check your .env")
        sys.exit(1)
    if not STAGING_DIR.exists():
        print(f"❌ Folder {STAGING_DIR} tidak ditemukan.")
        sys.exit(1)

    with psycopg2.connect(PG_CONN) as conn:
        print("✅ Connected to Postgres")
        with conn.cursor() as cur:
            cur.execute(DDL_STAGING)
        conn.commit()
        print("📐 Schema & staging tables ensured.")

        for table, fname in TABLE_FILES:
            csv_path = STAGING_DIR / fname
            if not csv_path.exists():
                print(f"⚠️  Skip {table}: file {fname} tidak ada.")
                continue
            # truncate sebelum load agar idempotent
            with conn.cursor() as cur:
                cur.execute(f"TRUNCATE TABLE {table};")
            conn.commit()

            print(f"⬆️  Loading {fname} → {table} ...")
            copy_csv(conn, table, csv_path)
            n = count_rows(conn, table)
            print(f"   ✅ {table}: {n} rows")

    print("\n🎉 Selesai bulk load ke schema staging.")
    print("Next: jalankan transform staging → core (02_transform_core.sql)")

if __name__ == "__main__":
    main()
