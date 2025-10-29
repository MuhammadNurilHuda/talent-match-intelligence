"""
eda_competency.py
-----------------
Step 1A Analysis Pipeline: Competency Pillars.

Responsibilities:
- Build the analysis base table (ABT) combining performance and competency data.
- Summarize group-level statistics across competency pillars.
- Compute mean differences, Cohen’s d effect sizes, and Mann–Whitney U p-values
  to identify statistically meaningful performance gaps between high and non-high performers.

Outputs:
A DataFrame summarizing 10 competency pillars, serving as the foundation
for the Red Threads and Success Formula discovery.
"""

import pandas as pd
from .stats import cohen_d, mwu_p

# ---------------------------------------------------------------------------
# Step 1A - Competency ABT Construction
# ---------------------------------------------------------------------------
def build_abt_competency(d: dict) -> pd.DataFrame:
    """
    Construct the Analysis Base Table (ABT) by merging the latest performance
    and competency data on `employee_id`.

    Args:
        d (dict): Dictionary containing:
            - 'perf_latest': DataFrame of latest performance ratings.
            - 'competency_latest_wide': DataFrame of latest competency pillar scores.

    Returns:
        pd.DataFrame: Combined dataset with a binary 'is_high' flag
        indicating high performers (rating = 5).
    """
    perf = d["perf_latest"]
    comp = d["competency_latest_wide"]
    abt = perf.merge(comp, on="employee_id", how="inner")
    abt["is_high"] = (abt["rating"] == 5).astype(int)
    return abt

# ---------------------------------------------------------------------------
# Step 1A - Competency Summary Statistics
# ---------------------------------------------------------------------------
def summarize_competency(abt: pd.DataFrame, dim_labels: pd.DataFrame|None=None) -> pd.DataFrame:
    """
    Summarize group-level competency statistics for high vs. non-high performers.

    Args:
        abt (pd.DataFrame): Analysis base table containing pillar scores and performance labels.
        dim_labels (pd.DataFrame | None): Optional lookup for pillar labels.

    Returns:
        pd.DataFrame: Summary statistics including mean values, deltas,
        Cohen’s d effect sizes, and Mann–Whitney U p-values, sorted by effect size and delta.
    """
    # Identify non-pillar columns to exclude from analysis.
    non_cols = {"employee_id","year","rating","is_high"}
    # Extract all competency pillar columns.
    pillar_cols = [c for c in abt.columns if c not in non_cols]
    hi = abt["is_high"] == 1
    rows = []
    # Iterate through each pillar to compute group-level metrics.
    for p in pillar_cols:
        x, y = abt.loc[hi, p], abt.loc[~hi, p]
        rows.append({
            "pillar_code": p,
            "mean_high": x.mean(),
            "mean_non": y.mean(),
            "delta": x.mean() - y.mean(),
            "cohens_d": cohen_d(x, y),
            "p_mwu": mwu_p(x, y),
            "n_high": x.notna().sum(),
            "n_non": y.notna().sum(),
        })
    # Sort by effect size (Cohen's d) and mean delta to highlight key differentiators.
    df = pd.DataFrame(rows).sort_values(["cohens_d","delta"], ascending=[False, False])
    # Optionally join with dimension labels for readability.
    if dim_labels is not None and not dim_labels.empty:
        df = df.merge(dim_labels, on="pillar_code", how="left")
    # Reorder and clean up the output columns for presentation.
    cols = ["pillar_code","pillar_label","mean_high","mean_non","delta","cohens_d","p_mwu","n_high","n_non"]
    return df[[c for c in cols if c in df.columns]].reset_index(drop=True)