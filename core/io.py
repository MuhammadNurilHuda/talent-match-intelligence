"""
io.py
-----
Data I/O layer for the Talent Match Intelligence project.

Responsibilities:
- Execute SQL queries via SQLAlchemy engine and return clean DataFrames.
- Fetch and preprocess datasets required for EDA and Success Formula construction:
    * Performance ratings (latest per employee)
    * Competency scores (pivoted to wide format)
    * PAPI behavioral scales (wide format)
    * Psychometric profiles
    * CliftonStrengths themes
    * Employee contextual data
- Wrap SQL execution with detailed error context for easier debugging.

Notes:
- “Latest” logic uses SQL window functions for robust tie-breaking instead of pandas idxmax.
- All queries use `read_sql()` which enriches errors with query snippets.
"""

from typing import Dict
import pandas as pd
from sqlalchemy import text
from .db import get_engine
from . import queries as Q

# ---------------------------------------------------------------------------
# Core SQL Reader
# ---------------------------------------------------------------------------
def read_sql(q: str) -> pd.DataFrame:
    """
    Execute an SQL query and return the result as a pandas DataFrame.

    If execution fails, raises RuntimeError with a truncated SQL snippet
    for easier debugging.
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


# ---------------------------------------------------------------------------
# Fetch Latest Performance Ratings
# ---------------------------------------------------------------------------
def fetch_perf_latest() -> pd.DataFrame:
    """
    Retrieve the latest yearly performance rating per employee using
    a SQL window function (ROW_NUMBER).

    Returns:
        pd.DataFrame: Columns [employee_id, year, rating].
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


# ---------------------------------------------------------------------------
# Fetch Latest Competency Scores (Wide Format)
# ---------------------------------------------------------------------------
def fetch_competency_wide_latest() -> pd.DataFrame:
    """
    Retrieve the latest competency score per (employee_id, pillar_code),
    then pivot the result into wide format.

    Returns:
        pd.DataFrame: One row per employee with pillar codes as columns.
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
    # Pivot long-format competency data to wide (pillar_code → column).
    wide = last.pivot(index="employee_id", columns="pillar_code", values="score").reset_index()
    # Remove pivot column name metadata for clean DataFrame output.
    wide.columns.name = None
    return wide


# ---------------------------------------------------------------------------
# Dimension & Label Fetchers
# ---------------------------------------------------------------------------
def fetch_dim_comp_labels() -> pd.DataFrame:
    """
    Retrieve competency pillar labels from dimension table.

    Returns:
        pd.DataFrame with columns [pillar_code, pillar_label].
        Returns empty DataFrame if query fails.
    """
    try:
        return read_sql(Q.Q_DIM_COMP_PILLARS)
    except Exception:
        return pd.DataFrame(columns=["pillar_code", "pillar_label"])


# ---------------------------------------------------------------------------
# Employee Context Data
# ---------------------------------------------------------------------------
def fetch_employees_org_min() -> pd.DataFrame:
    """
    Retrieve minimal employee organizational context.

    Returns:
        pd.DataFrame subset of employees with org-level attributes.
    """
    return read_sql(Q.Q_EMP_ORG)


# ---------------------------------------------------------------------------
# Bundled Data for Competency EDA
# ---------------------------------------------------------------------------
def fetch_for_competency_eda() -> Dict[str, pd.DataFrame]:
    """
    Bundle all required datasets for competency EDA.

    Returns:
        dict of DataFrames:
            - perf_latest
            - competency_latest_wide
            - dim_comp_labels
            - employees
    """
    return {
        "perf_latest": fetch_perf_latest(),
        "competency_latest_wide": fetch_competency_wide_latest(),
        "dim_comp_labels": fetch_dim_comp_labels(),
        "employees": fetch_employees_org_min(),
    }


# ---------------------------------------------------------------------------
# PAPI Behavioral Scales
# ---------------------------------------------------------------------------
def fetch_papi_wide() -> pd.DataFrame:
    """
    Retrieve PAPI behavioral assessment in long format and pivot to wide.

    Returns:
        pd.DataFrame: Columns [employee_id] + one column per PAPI scale.
    """
    df = read_sql(Q.Q_PAPI)  # pastikan Q.Q_PAPI ada di core/queries.py
    if df.empty:
        return pd.DataFrame(columns=["employee_id"])
    # Convert long PAPI data to wide format with scale codes as columns.
    wide = df.pivot(index="employee_id", columns="scale_code", values="score").reset_index()
    wide.columns.name = None
    return wide


# ---------------------------------------------------------------------------
# Psychometric Profiles
# ---------------------------------------------------------------------------
def fetch_psych() -> pd.DataFrame:
    """
    Retrieve psychometric profile data including cognitive and personality measures.

    Expected Columns:
        employee_id, pauli, faxtor, disc, disc_word, mbti, iq, gtq, tiki
    """
    return read_sql(Q.Q_PSYCH)  # pastikan Q.Q_PSYCH ada di core/queries.py


# ---------------------------------------------------------------------------
# Bundled Data for Psychometric EDA
# ---------------------------------------------------------------------------
def fetch_for_psych_eda() -> Dict[str, pd.DataFrame]:
    """
    Bundle all required datasets for psychometric EDA.

    Returns:
        dict of DataFrames:
            - perf_latest
            - papi_wide
            - psych
    """
    return {
        "perf_latest": fetch_perf_latest(),
        "papi_wide": fetch_papi_wide(),
        "psych": fetch_psych(),
    }


# ---------------------------------------------------------------------------
# CliftonStrengths Themes
# ---------------------------------------------------------------------------
def fetch_strengths() -> pd.DataFrame:
    """
    Retrieve CliftonStrengths themes with ranks for each employee.

    Returns:
        pd.DataFrame with columns [employee_id, rank, theme].
    """
    return read_sql("SELECT employee_id, rank, theme FROM core.strengths;")


# ---------------------------------------------------------------------------
# Bundled Data for Strengths EDA
# ---------------------------------------------------------------------------
def fetch_for_strengths_eda() -> dict:
    """
    Bundle datasets for strengths-based EDA.

    Returns:
        dict with keys:
            - perf_latest
            - strengths
    """
    return {
        "perf_latest": fetch_perf_latest(),
        "strengths": fetch_strengths(),
    }


# ---------------------------------------------------------------------------
# Employee Organizational View
# ---------------------------------------------------------------------------
def fetch_employees_org() -> pd.DataFrame:
    """
    Retrieve full organizational employee view from mart schema.

    Returns:
        pd.DataFrame from mart.v_employees_org.
    """
    return read_sql("SELECT * FROM mart.v_employees_org;")


# ---------------------------------------------------------------------------
# Bundled Data for Contextual EDA
# ---------------------------------------------------------------------------
def fetch_for_contextual_eda() -> dict:
    """
    Bundle datasets for contextual (organizational) analysis.

    Returns:
        dict of DataFrames:
            - perf_latest
            - employees_org
    """
    return {
        "perf_latest": fetch_perf_latest(),
        "employees_org": fetch_employees_org(),
    }


# ---------------------------------------------------------------------------
# Full Psychometric Profile (Extended Fetch)
# ---------------------------------------------------------------------------
def fetch_profiles_psych_full() -> pd.DataFrame:
    """
    Retrieve full psychometric profile with all key cognitive and personality metrics.

    Returns:
        pd.DataFrame including:
            employee_id, pauli, faxtor, disc, disc_word, mbti, iq, gtq, tiki
    """
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