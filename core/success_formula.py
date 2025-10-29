"""
success_formula.py (Deprecated)
-------------------------------
This module implements the legacy Success Score (v1) and is kept solely for backward compatibility.

Status:
- DEPRECATED: Use `core.success_formula_v2` for new development and production scoring.
- This file remains to support older notebooks/scripts that still import v1 functions.

What changed in v2:
- Clear, rule-based component weighting informed by Step 1A–1D.
- Component normalization and clipping for robustness.
- Optional DISC-based bonus and improved diagnostics.

Migration:
- Replace `from core.success_formula import success_score_v1` with:
      `from core.success_formula_v2 import success_score_v2`
- Replace wrapper-based calls with the v2 equivalents from `success_formula_v2`.

Note: Code logic below is intentionally unchanged; only documentation/comments were added.
"""

from __future__ import annotations
import numpy as np
import pandas as pd

# --- Utilities: z-score, safe column selection, and min-max normalization (logic unchanged) ---
def _z(s: pd.Series) -> pd.Series:
    """Return standardized z-scores (population std, ddof=0); zeros if variance missing."""
    m = s.mean()
    sd = s.std(ddof=0)
    if pd.isna(sd) or sd == 0:
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (s - m) / sd

# Helper to enforce presence of required columns without altering upstream loaders.
def _safe_get_cols(df: pd.DataFrame, keep: list[str]) -> pd.DataFrame:
    """Select `employee_id` plus required columns; create missing ones filled with 0.0."""
    cols = ["employee_id"] + [c for c in keep if c in df.columns]
    out = df[cols].copy()
    for k in keep:
        if k not in out.columns:
            out[k] = 0.0
    return out

# Min–max scaler used by v1 API to produce [0, 1] scores for downstream evaluation.
def _minmax01(s: pd.Series) -> pd.Series:
    """Scale a Series to [0, 1]; if constant/NaN, return zeros (stable fallback)."""
    lo, hi = s.min(), s.max()
    if pd.isna(lo) or pd.isna(hi) or hi == lo:
        return pd.Series(0.0, index=s.index)
    return (s - lo) / (hi - lo)

# ---------------------- Component builders (v1, legacy) ---------------------- #
def build_competency_component(df_comp_wide: pd.DataFrame,
                               weights_comp: dict[str, float]) -> pd.DataFrame:
    """
    Build v1 competency component.

    Input:
        df_comp_wide: DataFrame with columns ['employee_id'] + competency pillars.
        weights_comp: Dict of pillar weights (will be aligned to available columns).

    Output:
        DataFrame with ['employee_id', 'comp_score'] where comp_score is a weighted
        sum of z-scored pillars (legacy v1 approach, not the v2 normalized rule).
    """
    comp_cols = [c for c in df_comp_wide.columns if c != "employee_id"]
    comp_z = df_comp_wide[comp_cols].apply(_z)
    # Align pillar weights to the columns actually present to avoid KeyErrors.
    w = pd.Series({c: weights_comp.get(c, 0.0) for c in comp_cols})
    comp_score = (comp_z * w).sum(axis=1)
    return pd.DataFrame({"employee_id": df_comp_wide["employee_id"], "comp_score": comp_score})

def build_psych_component(df_psych: pd.DataFrame,
                          df_papi_wide: pd.DataFrame,
                          weights_psych: dict[str, float]) -> pd.DataFrame:
    """
    Build v1 psychometric component from profiles_psych + PAPI (legacy).

    - Uses z-scored Pauli plus selected PAPI scales ('Papi_P','Papi_S','Papi_G').
    - Missing columns are created and filled with 0.0 to keep pipeline robust.

    Returns:
        DataFrame ['employee_id','psy_score'] based on a weighted sum of z-scores.
    """
    # ambil pauli dari profiles_psych, ambil Papi_P, Papi_S, Papi_G dari PAPI wide
    psy_keep = ["pauli"]
    papi_keep = ["Papi_P", "Papi_S", "Papi_G"]

    psy_df  = _safe_get_cols(df_psych, psy_keep)
    papi_df = _safe_get_cols(df_papi_wide, papi_keep)

    # Merge on employee_id and fill missing to keep deterministic scoring.
    df = psy_df.merge(papi_df, on="employee_id", how="outer").fillna(0.0)
    cols = [c for c in df.columns if c != "employee_id"]
    zed  = df[cols].apply(_z)
    # Align psychology/PAPI weights to available columns.
    w = pd.Series({c: weights_psych.get(c, 0.0) for c in cols})
    psy_score = (zed * w).sum(axis=1)
    return pd.DataFrame({"employee_id": df["employee_id"], "psy_score": psy_score})

def build_strengths_component(df_strengths: pd.DataFrame,
                              top_themes_weights: dict[str, float]) -> pd.DataFrame:
    """
    Build v1 strengths component from top-5 CliftonStrengths themes (legacy).

    Approach:
        - One-hot encode themes per employee, select only weighted themes.
        - Z-score selected theme indicators, then compute a weighted sum.

    Returns:
        DataFrame ['employee_id','str_score'].

    Note:
        This is a legacy method (v1). The v2 module uses a cleaner rule-based approach.
    """
    if df_strengths is None or df_strengths.empty:
        return pd.DataFrame({"employee_id": [], "str_score": []})

    # one-hot untuk seluruh theme, lalu pilih yang di-bobotkan saja
    m = (
        df_strengths.assign(val=1)
        .pivot_table(index="employee_id", columns="theme", values="val", fill_value=0)
        .reset_index()
    )
    keep = [t for t in top_themes_weights.keys() if t in m.columns]
    if not keep:
        # kalau tidak ada theme yang cocok di data, skor 0
        return pd.DataFrame({"employee_id": m["employee_id"], "str_score": 0.0})

    # Standardize selected theme indicators before applying weights.
    zed = m[keep].apply(_z)
    w = pd.Series({t: top_themes_weights.get(t, 0.0) for t in keep})
    str_score = (zed * w).sum(axis=1)
    return pd.DataFrame({"employee_id": m["employee_id"], "str_score": str_score})

def build_context_adjuster(df_emp_org: pd.DataFrame,
                           yos_threshold_years: float = 10.0,
                           uplift: float = 0.05) -> pd.DataFrame:
    """
    Lightweight non-penalizing context adjuster (legacy v1).

    Adds +`uplift` if Years of Service (YoS) > `yos_threshold_years`.
    If contextual field is missing, returns 0.0 adjustments.

    Returns:
        DataFrame ['employee_id','ctx_adj'] used as a small context term in v1.
    """
    df = df_emp_org.copy()
    if "years_of_service_months" not in df.columns:
        # jika tidak tersedia, adjuster = 0
        return pd.DataFrame({"employee_id": df["employee_id"], "ctx_adj": 0.0})
    yos_years = (df["years_of_service_months"].fillna(0) / 12.0)
    adj = np.where(yos_years > yos_threshold_years, uplift, 0.0)
    return pd.DataFrame({"employee_id": df["employee_id"], "ctx_adj": adj})

# ---------------------- Legacy v1 weighted aggregation ---------------------- #
def combine_score(components: pd.DataFrame, w_main: dict[str, float]) -> pd.DataFrame:
    """
    Combine legacy v1 components into a single Success Score.

    The final score is a linear combination of component columns using `w_main`.
    Missing component columns are created with 0.0 to keep the pipeline stable.

    Returns:
        DataFrame with columns:
            ['employee_id','success_score','comp_score','str_score','psy_score','ctx_adj']
    """
    df = components.copy()
    # isi kolom yang mungkin belum ada
    for col in ["comp_score", "str_score", "psy_score", "ctx_adj"]:
        if col not in df.columns:
            df[col] = 0.0
    df["success_score"] = (
        w_main.get("competency", 0.0)   * df["comp_score"] +
        w_main.get("strengths", 0.0)    * df["str_score"] +
        w_main.get("psychometric", 0.0) * df["psy_score"] +
        w_main.get("context", 0.0)      * df["ctx_adj"]
    )
    keep = ["employee_id","success_score","comp_score","str_score","psy_score","ctx_adj"]
    return df[keep]


# DEPRECATED: Prefer `success_formula_v2.success_score_v2`. Kept for backward compatibility.
def success_score_v1(
    df_comp_wide: pd.DataFrame,
    df_strengths: pd.DataFrame,
    df_psych: pd.DataFrame,
    df_papi_wide: pd.DataFrame,
    df_emp_org: pd.DataFrame,
    weights_comp: dict[str, float] | None = None,
    weights_psych: dict[str, float] | None = None,
    weights_strengths: dict[str, float] | None = None,
    w_main: dict[str, float] | None = None,
    minmax: bool = True,
):
    """
    Legacy v1 API: returns (success_score_series, parts_df).

    Behavior:
        - Builds each component with z-score-based weighting (v1 style).
        - Applies `w_main` to combine components.
        - Optionally min-max scales the final series to [0, 1].

    Returns:
        Tuple[pd.Series, pd.DataFrame]
    """
    # default weights (sesuai v1)
    if weights_comp is None:
        weights_comp = {
            "SEA":0.22, "CEX":0.17, "VCU":0.12, "STO":0.12, "CSI":0.11,
            "QDD":0.08, "GDR":0.07, "LIE":0.05, "IDS":0.03, "FTC":0.03,
        }
    if weights_psych is None:
        weights_psych = {"pauli":0.6, "Papi_P":0.3, "Papi_S":-0.05, "Papi_G":-0.05}
    if weights_strengths is None:
        weights_strengths = {"Futuristic":0.40, "Intellection":0.35, "Context":0.25}
    if w_main is None:
        w_main = {"competency":0.50, "strengths":0.25, "psychometric":0.15, "context":0.10}

    # build parts (aman untuk missing kolom)
    comp_part = build_competency_component(df_comp_wide, weights_comp)
    psy_part  = build_psych_component(df_psych, df_papi_wide, weights_psych)
    str_part  = build_strengths_component(df_strengths, weights_strengths)
    ctx_part  = build_context_adjuster(df_emp_org, yos_threshold_years=10.0, uplift=0.05)

    parts = (
        comp_part.merge(psy_part, on="employee_id", how="outer")
                 .merge(str_part, on="employee_id", how="outer")
                 .merge(ctx_part, on="employee_id", how="outer")
                 .fillna(0.0)
    )

    scored = combine_score(parts, w_main)
    score_series = scored.set_index("employee_id")["success_score"]
    # Optional normalization for comparability across runs/populations.
    if minmax:
        score_series = _minmax01(score_series).rename("success_score")

    # kembalikan series + parts (tanpa duplikasi kolom success_score)
    return score_series, parts


# ---------------------------------------------------------------------------
# Wrappers (v1) — fetch data via core.io for quick end-to-end scoring
# ---------------------------------------------------------------------------
def compute_success_v1_from_fetchers(io_module,
                                     weights_comp_default: dict[str, float] | None = None,
                                     weights_psych_default: dict[str, float] | None = None,
                                     weights_strengths_default: dict[str, float] | None = None,
                                     w_main: dict[str, float] | None = None,
                                     minmax: bool = True):
    """
    Wrapper that fetches all required inputs from `core.io` and computes v1 scores.

    Note:
        Use the v2 wrapper/functions for new work. This exists to run older notebooks.
    Returns:
        (score_series, parts_df, perf_latest_df)
    """
    comp_wide = io_module.fetch_competency_wide_latest()
    papi_wide = io_module.fetch_papi_wide()
    psych     = io_module.fetch_psych()
    try:
        emp_org = io_module.fetch_employees_org()
    except Exception:
        emp_org = io_module.fetch_employees_org_min()
    try:
        strengths = io_module.read_sql("SELECT employee_id, rank, theme FROM core.strengths;")
    except Exception:
        strengths = pd.DataFrame(columns=["employee_id","rank","theme"])

    score_series, parts = success_score_v1(
        comp_wide, strengths, psych, papi_wide, emp_org,
        weights_comp=weights_comp_default,
        weights_psych=weights_psych_default,
        weights_strengths=weights_strengths_default,
        w_main=w_main,
        minmax=minmax,
    )
    perf = io_module.fetch_perf_latest()
    return score_series, parts, perf

def compute_success_score_from_fetchers(
    io_module,
    weights_comp_default: dict[str, float] | None = None,
    weights_psych_default: dict[str, float] | None = None,
    weights_strengths_default: dict[str, float] | None = None,
    w_main: dict[str, float] | None = None,
):
    """
    Convenience wrapper to compute Success Score v1 end-to-end using `core.io`.

    Migration:
        Prefer `success_formula_v2.success_score_v2` for production and new analyses.

    Args:
        io_module: The `core.io` module with `fetch_*` functions.

    Returns:
        (scores_df, perf_latest_df) — ready to merge for evaluation.
    """

    if weights_comp_default is None:
        # SEA paling kuat, lalu CEX, VCU/STO/CSI menengah, sisanya kecil.
        weights_comp_default = {
            "SEA":0.22, "CEX":0.17, "VCU":0.12, "STO":0.12, "CSI":0.11,
            "QDD":0.08, "GDR":0.07, "LIE":0.05, "IDS":0.03, "FTC":0.03
        }
    if weights_psych_default is None:
        # Pauli (+), Papi_P (+), Papi_S/G (- kecil)
        weights_psych_default = {"pauli":0.6, "Papi_P":0.3, "Papi_S":-0.05, "Papi_G":-0.05}
    if weights_strengths_default is None:
        # Strengths positif dari Step 1C
        weights_strengths_default = {"Futuristic":0.40, "Intellection":0.35, "Context":0.25}
    if w_main is None:
        w_main = {"competency":0.50, "strengths":0.25, "psychometric":0.15, "context":0.10}

    # ---- fetch data ----
    comp_wide = io_module.fetch_competency_wide_latest()
    papi_wide = io_module.fetch_papi_wide()
    psych     = io_module.fetch_psych()
    perf      = io_module.fetch_perf_latest()

    try:
        emp_org = io_module.fetch_employees_org()
    except Exception:
        emp_org = io_module.fetch_employees_org_min()

    try:
        strengths = io_module.read_sql("SELECT employee_id, rank, theme FROM core.strengths;")
    except Exception:
        strengths = pd.DataFrame(columns=["employee_id","rank","theme"])

    # ---- build setiap komponen ----
    comp_part = build_competency_component(comp_wide, weights_comp_default)
    psy_part  = build_psych_component(psych, papi_wide, weights_psych_default)
    str_part  = build_strengths_component(strengths, weights_strengths_default)
    ctx_part  = build_context_adjuster(emp_org, yos_threshold_years=10.0, uplift=0.05)

    # gabung komponen ke satu tabel
    parts = comp_part.merge(psy_part, on="employee_id", how="outer") \
                     .merge(str_part, on="employee_id", how="outer") \
                     .merge(ctx_part, on="employee_id", how="outer") \
                     .fillna(0.0)

    scores = combine_score(parts, w_main)
    return scores, perf