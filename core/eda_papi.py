"""
eda_papi.py
-----------
Step 1B – PAPI (Workstyle / Behavioral Preferences).

Responsibilities:
- Analyze 20 PAPI scales comparing high vs. non-high performers.
- Compute group-level statistics including mean difference, Cohen’s d effect size, and Mann–Whitney U p-value.
- Identify which behavioral traits most differentiate top performers.

Output:
Returns a DataFrame summarizing each PAPI scale with effect size, delta, and statistical significance.
"""

import pandas as pd
from .stats import cohen_d, mwu_p

# ---------------------------------------------------------------------------
# Step 1B - PAPI Scale Analysis
# ---------------------------------------------------------------------------
def summarize_papi(d: dict) -> pd.DataFrame:
    """
    Compare 20 PAPI behavioral preference scales between high and non-high performers.

    Args:
        d (dict): Dictionary containing:
            - 'perf_latest': DataFrame with latest performance ratings.
            - 'papi_wide': DataFrame containing 20 PAPI scales per employee.

    Returns:
        pd.DataFrame: Summary table including:
            - scale: PAPI scale name.
            - mean_high / mean_non: Average scores for high and non-high performers.
            - delta: Difference in mean scores.
            - cohens_d: Standardized effect size.
            - p_mwu: Mann–Whitney U test p-value.
    """
    # Merge latest performance ratings with PAPI behavioral scales.
    perf = d["perf_latest"]
    papi = d["papi_wide"]
    abt = perf.merge(papi, on="employee_id", how="inner")

    # Create a binary indicator for high performers (rating = 5).
    abt["is_high"] = (abt["rating"] == 5).astype(int)

    # Identify non-scale columns to exclude from analysis.
    non_cols = {"employee_id","rating","year","is_high"}
    scales = [c for c in abt.columns if c not in non_cols]

    # Iterate through each PAPI scale to compute summary statistics.
    hi = abt["is_high"] == 1
    rows = []
    for sc in scales:
        x, y = abt.loc[hi, sc], abt.loc[~hi, sc]
        rows.append({
            "scale": sc,
            "mean_high": x.mean(),
            "mean_non": y.mean(),
            "delta": x.mean() - y.mean(),
            "cohens_d": cohen_d(x, y),
            "p_mwu": mwu_p(x, y),
        })

    # Sort results by effect size (Cohen's d) to highlight strongest differentiators.
    df = pd.DataFrame(rows).sort_values("cohens_d", ascending=False).reset_index(drop=True)
    return df