"""
eda_strengths.py
----------------
Step 1C – Strengths (Behavioral Themes, CliftonStrengths).

Responsibilities:
- Analyze the distribution of CliftonStrengths themes between high vs. non-high performers.
- Compute relative frequencies and percentage gaps to identify standout themes for top performers.
- Produce a tidy summary for downstream visualization and Red Threads discovery.

Output:
Returns a DataFrame with one row per theme including % share among high vs. non-high,
and the delta percentage (high minus non-high), sorted by the largest positive gaps.
"""

import pandas as pd

# ---------------------------------------------------------------------------
# Step 1C - Strengths Theme Distribution
# ---------------------------------------------------------------------------
def summarize_strengths(d: dict) -> pd.DataFrame:
    """
    Summarize CliftonStrengths themes for high vs. non-high performers.

    Args:
        d (dict): Dictionary containing:
            - 'perf_latest': DataFrame of latest performance ratings.
            - 'strengths': DataFrame of CliftonStrengths themes with ranks per employee.

    Returns:
        pd.DataFrame: Wide-format summary with columns:
            - theme: CliftonStrengths theme name.
            - pct_nonhigh: Percentage share among non-high performers.
            - pct_high: Percentage share among high performers.
            - delta_pct: pct_high minus pct_nonhigh, highlighting standout themes.
        Sorted by delta_pct in descending order.
    """
    perf = d["perf_latest"]
    strg = d["strengths"]

    # Merge latest performance labels with strengths themes at the employee level.
    abt = perf.merge(strg, on="employee_id", how="inner")

    # Create binary indicator: 1 = high performer (rating = 5), 0 = otherwise.
    abt["is_high"] = (abt["rating"] == 5).astype(int)

    # Count theme occurrences within each group (high vs. non-high).
    freq = abt.groupby(["theme", "is_high"]).size().reset_index(name="n")

    # Compute total theme records per group to derive percentages.
    total = abt.groupby("is_high")["theme"].count().rename("total").reset_index()

    # Convert counts to percentages within each group.
    freq["pct"] = freq["n"] / freq["total"] * 100

    # Pivot to a single row per theme with separate % columns for each group.
    wide = freq.pivot(index="theme", columns="is_high", values="pct").fillna(0).reset_index()

    # Rename columns for readability (note: column '0' = non-high, '1' = high).
    wide.columns = ["theme", "pct_nonhigh", "pct_high"]  # 0 = non, 1 = high

    # Highlight themes more prevalent among high performers (positive deltas).
    wide["delta_pct"] = wide["pct_high"] - wide["pct_nonhigh"]

    # Sort by the largest positive gaps first to surface standout themes.
    return wide.sort_values("delta_pct", ascending=False).reset_index(drop=True)