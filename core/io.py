"""
io.py
-----
Lapisan input/output data: mengeksekusi query dan membentuk dataset siap analisis.

Fungsi penting:
- `read_sql(q)`                       : jalankan query SQL dan kembalikan DataFrame (dengan error context).
- `fetch_perf_latest()`               : ambil rating performa terbaru per karyawan (window function, bukan idxmax).
- `fetch_competency_wide_latest()`    : pivot kompetensi (latest per employee_id,pillar_code) -> 1 baris per karyawan.
- `fetch_dim_comp_labels()`           : ambil label pilar dari tabel dimensi.
- `fetch_employees_org_min()`         : ambil subset kolom employees untuk konteks (opsional untuk slicing).
- `fetch_for_competency_eda()`        : bundler data untuk EDA kompetensi.
- `fetch_papi_wide()`                 : pivot PAPI dari long -> wide (kolom = scale_code).
- `fetch_psych()`                     : ambil psikometri (iq, gtq, tiki, pauli, faxtor, disc, mbti).
- `fetch_for_psych_eda()`             : bundler data untuk EDA psikometrik.

Catatan:
- Implementasi "latest" memakai window function SQL agar robust untuk tipe data/tie dan tidak bergantung ke idxmax.
- Semua pembacaan SQL memakai pembungkus `read_sql` yang menambahkan konteks error agar mudah debug.
"""

from typing import Dict
import pandas as pd
from sqlalchemy import text
from .db import get_engine
from . import queries as Q


def read_sql(q: str) -> pd.DataFrame:
    """
    Jalankan query dan kembalikan DataFrame.
    Jika gagal, raise ulang dengan menambahkan potongan query untuk memudahkan debug.
    """
    eng = get_engine()
    try:
        with eng.begin() as con:
            return pd.read_sql(text(q), con)
    except Exception as e:
        snippet = q.strip().replace("\n", " ")
        if len(snippet) > 180:
            snippet = snippet[:180] + "..."
        raise RuntimeError(f"read_sql() failed for query: {snippet}") from e


def fetch_perf_latest() -> pd.DataFrame:
    """
    Ambil rating performa terbaru per employee_id menggunakan window function (rn=1).
    Kolom hasil: employee_id, year, rating
    """
    q = """
    WITH ranked AS (
        SELECT employee_id, year, rating,
               ROW_NUMBER() OVER (PARTITION BY employee_id ORDER BY year DESC, rating DESC) AS rn
        FROM core.performance_yearly
    )
    SELECT employee_id, year, rating
    FROM ranked
    WHERE rn = 1;
    """
    return read_sql(q)


def fetch_competency_wide_latest() -> pd.DataFrame:
    """
    Ambil skor kompetensi terbaru per (employee_id, pillar_code) lalu pivot ke wide.
    Kolom hasil: employee_id + setiap pillar_code menjadi kolom.
    """
    q = """
    WITH ranked AS (
        SELECT employee_id, pillar_code, score, year,
               ROW_NUMBER() OVER (
                   PARTITION BY employee_id, pillar_code
                   ORDER BY year DESC, score DESC
               ) AS rn
        FROM core.competencies_yearly
    )
    SELECT employee_id, pillar_code, score
    FROM ranked
    WHERE rn = 1;
    """
    last = read_sql(q)
    wide = last.pivot(index="employee_id", columns="pillar_code", values="score").reset_index()
    wide.columns.name = None
    return wide


def fetch_dim_comp_labels() -> pd.DataFrame:
    try:
        return read_sql(Q.Q_DIM_COMP_PILLARS)
    except Exception:
        return pd.DataFrame(columns=["pillar_code", "pillar_label"])


def fetch_employees_org_min() -> pd.DataFrame:
    return read_sql(Q.Q_EMP_ORG)


def fetch_for_competency_eda() -> Dict[str, pd.DataFrame]:
    return {
        "perf_latest": fetch_perf_latest(),
        "competency_latest_wide": fetch_competency_wide_latest(),
        "dim_comp_labels": fetch_dim_comp_labels(),
        "employees": fetch_employees_org_min(),
    }


def fetch_papi_wide() -> pd.DataFrame:
    """
    Ambil PAPI dalam format long dan pivot menjadi wide (kolom = scale_code).
    """
    df = read_sql(Q.Q_PAPI)  # pastikan Q.Q_PAPI ada di core/queries.py
    if df.empty:
        return pd.DataFrame(columns=["employee_id"])
    wide = df.pivot(index="employee_id", columns="scale_code", values="score").reset_index()
    wide.columns.name = None
    return wide


def fetch_psych() -> pd.DataFrame:
    """
    Ambil profil psikometrik dari core.profiles_psych.
    Kolom yang diharapkan (berdasarkan skema kamu): employee_id, pauli, faxtor, disc, disc_word, mbti, iq, gtq, tiki
    """
    return read_sql(Q.Q_PSYCH)  # pastikan Q.Q_PSYCH ada di core/queries.py

def fetch_for_psych_eda() -> Dict[str, pd.DataFrame]:
    return {
        "perf_latest": fetch_perf_latest(),
        "papi_wide": fetch_papi_wide(),
        "psych": fetch_psych(),
    }

def fetch_strengths() -> pd.DataFrame:
    return read_sql("SELECT employee_id, rank, theme FROM core.strengths;")

def fetch_for_strengths_eda() -> dict:
    return {
        "perf_latest": fetch_perf_latest(),
        "strengths": fetch_strengths(),
    }

def fetch_employees_org() -> pd.DataFrame:
    return read_sql("SELECT * FROM mart.v_employees_org;")

def fetch_for_contextual_eda() -> dict:
    return {
        "perf_latest": fetch_perf_latest(),
        "employees_org": fetch_employees_org(),
    }

def fetch_profiles_psych_full() -> pd.DataFrame:
    q = """
    SELECT
      employee_id,
      pauli, faxtor,
      disc, disc_word,
      mbti,
      iq, gtq, tiki
    FROM core.profiles_psych;
    """
    return read_sql(q)