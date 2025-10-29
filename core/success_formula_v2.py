"""
success_formula_v2.py
---------------------
Core implementation of Success Formula v2 for the Talent Match Intelligence project.

Responsibilities:
- Combine competency, strengths, and psychometric data into a unified success score.
- Apply rule-based weighting derived from Step 1 analyses.
- Include small DISC-style behavioral bonus adjustments.

Components:
- Competency (50%)
- Strengths (25%)
- Psychometric (20%)
- DISC Bonus (+2% conditional)

Output:
Returns both final normalized success scores and component-level breakdowns.
"""

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Constants for Success Formula v2
# ---------------------------------------------------------------------------

# Weighted importance of each competency pillar based on Step 1A effect sizes.
COMP_WEIGHTS = {
    "SEA": 0.30, "CEX": 0.20, "VCU": 0.15, "STO": 0.10, "CSI": 0.10,
    "QDD": 0.05, "GDR": 0.04, "LIE": 0.03, "IDS": 0.02, "FTC": 0.01
}
# CliftonStrengths themes positively associated with top performers.
SUCCESS_THEMES = {"Futuristic","Intellection","Context","Developer","Harmony","Analytical"}
# Small additive bonus for balanced DISC types (non-penalizing).
MILD_DISC_BONUS = {"SI","SD","IS"}  # soft bonus kecil, non-penalizing

def _minmax01(s: pd.Series) -> pd.Series:
    lo, hi = s.min(), s.max()
    if pd.isna(lo) or pd.isna(hi) or hi == lo:
        return pd.Series(0.0, index=s.index)
    return (s - lo) / (hi - lo)

def _z_clip(s: pd.Series) -> pd.Series:
    # Compute z-scores and clip them to [-2, 2] to limit outlier influence.
    st = s.std(ddof=0)
    if st == 0 or pd.isna(st):
        z = (s - s.mean())
    else:
        z = (s - s.mean()) / st
    return z.clip(-2, 2)

# ---------- Komponen skor ----------
def compute_comp_score(df_comp_wide: pd.DataFrame) -> pd.Series:
    """
    Compute weighted competency score for each employee.

    Args:
        df_comp_wide (pd.DataFrame): Output from fetch_competency_wide_latest(),
            containing columns [employee_id] + 10 competency pillars (scale 1–5).

    Returns:
        pd.Series: Weighted competency score (0–1 scale) indexed by employee_id.
    """
    df = df_comp_wide.set_index("employee_id")
    cols = [c for c in COMP_WEIGHTS if c in df.columns]
    if not cols:
        return pd.Series(0.0, index=df.index, name="comp_score")
    # Normalize 1–5 scale to 0–1.
    x = (df[cols] - 1.0) / 4.0  # skala 1..5 → 0..1
    w = pd.Series({c: COMP_WEIGHTS[c] for c in cols})
    return (x * w).sum(axis=1).rename("comp_score")

def compute_str_score(df_str_top5: pd.DataFrame) -> pd.Series:
    """
    Compute strengths alignment score based on presence of key success themes.

    Args:
        df_str_top5 (pd.DataFrame): Output from fetch_strengths(),
            containing columns [employee_id, rank, theme].

    Returns:
        pd.Series: Proportion of top 5 strengths that match SUCCESS_THEMES.
    """
    if not {"employee_id","theme"}.issubset(df_str_top5.columns):
        # fallback aman
        return pd.Series(0.0, index=pd.Index([], name="employee_id"), name="str_score")

    df = df_str_top5.copy()
    df["hit"] = df["theme"].isin(SUCCESS_THEMES)
    cnt = df.groupby("employee_id")["hit"].sum()  # 0..5
    return (cnt / 5.0).rename("str_score")

def compute_psy_score(df_psych: pd.DataFrame, df_papi_wide: pd.DataFrame) -> pd.Series:
    """
    Compute psychometric score using z-scored Pauli, Faxtor, and selected PAPI scales.

    Args:
        df_psych (pd.DataFrame): Output from fetch_profiles_psych_full().
        df_papi_wide (pd.DataFrame): Output from fetch_papi_wide().

    Returns:
        pd.Series: Normalized psychometric score (0–1 scale) per employee.
    """
    # pastikan index = employee_id
    psy = df_psych.set_index("employee_id")
    papi = df_papi_wide.set_index("employee_id")

    # siapkan kolom yang dibutuhkan (isi dengan NaN jika tidak ada)
    for c in ["pauli","faxtor"]:
        if c not in psy.columns:
            psy[c] = np.nan
    for c in ["Papi_P","Papi_W"]:
        if c not in papi.columns:
            papi[c] = np.nan

    # Standardize each psychometric variable (z-scored and clipped).
    z_pauli = _z_clip(psy["pauli"])
    z_faxt  = _z_clip(psy["faxtor"])
    z_pp    = _z_clip(papi["Papi_P"])
    z_pw    = _z_clip(papi["Papi_W"])

    # Weighted combination reflecting cognitive and behavioral components.
    psy_core = 0.50*z_pauli - 0.25*z_faxt + 0.15*z_pp + 0.10*z_pw
    # Rescale to [0, 1] and neutralize missing employees with 0.5 baseline.
    psy_score = ((psy_core + 2.0) / 4.0).clip(0, 1).rename("psy_score")  # rescale → [0,1]
    psy_score = psy_score.reindex(psy.index).fillna(0.5)  # netral bila missing
    return psy_score

def compute_disc_bonus(series_disc: pd.Series, comp_score: pd.Series) -> pd.Series:
    """
    Compute small DISC-based bonus for employees with balanced profiles.

    Args:
        series_disc (pd.Series): DISC 2-letter codes indexed by employee_id.
        comp_score (pd.Series): Competency score (used as minimum threshold).

    Returns:
        pd.Series: Bonus value (0 or 0.02) per employee.
    """
    sdisc = series_disc.astype(str).str.upper()
    # Activate +0.02 bonus for balanced DISC profiles when competency ≥ 0.6.
    cond = sdisc.isin(MILD_DISC_BONUS) & (comp_score >= 0.60)
    return cond.astype(float).rename("disc_bonus") * 0.02  # max +0.02

# ---------- Orkestrasi ----------
def success_score_v2(df_comp_wide: pd.DataFrame,
                     df_str_top5: pd.DataFrame,
                     df_psych: pd.DataFrame,
                     df_papi_wide: pd.DataFrame,
                     series_disc: pd.Series):
    """
    Aggregate all components into the final Success Formula v2 score.

    Args:
        df_comp_wide (pd.DataFrame): Competency pillar data.
        df_str_top5 (pd.DataFrame): Strengths data (top 5 themes).
        df_psych (pd.DataFrame): Psychometric data.
        df_papi_wide (pd.DataFrame): PAPI behavioral scales.
        series_disc (pd.Series): DISC 2-letter profiles.

    Returns:
        tuple:
            success_v2 (pd.Series): Final normalized success score [0–1].
            parts (pd.DataFrame): Component-level details for diagnostics.
    """
    # Compute each component and align indices.
    comp = compute_comp_score(df_comp_wide)                        # index employee_id
    strn = compute_str_score(df_str_top5).reindex(comp.index).fillna(0.0)
    psy  = compute_psy_score(df_psych, df_papi_wide).reindex(comp.index).fillna(0.5)
    disc_b = compute_disc_bonus(series_disc.reindex(comp.index), comp).fillna(0.0)

    # Weighted aggregation based on rule-defined formula.
    raw = 0.50*comp + 0.25*strn + 0.20*psy + disc_b
    # Normalize final scores across population to [0, 1].
    final = _minmax01(raw).rename("success_v2")

    # Combine component breakdowns for inspection or debugging.
    parts = pd.concat([comp.rename("comp_score"),
                       strn.rename("str_score"),
                       psy.rename("psy_score"),
                       disc_b.rename("disc_bonus")], axis=1)
    return final, parts