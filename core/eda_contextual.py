"""
eda_contextual.py
-----------------
Step 1D – Contextual Factors.

Responsibilities:
- Analyze relationships between organizational factors (grade, years of service, education, major)
  and the proportion of high performers.
- Compute performance distributions across categorical and numeric contextual variables.
- Prepare summary tables for visualization and interpretation in Step 1 (Red Threads Discovery).

Output:
Returns a DataFrame showing the percentage of high performers across each contextual factor category.
"""

import pandas as pd

# ---------------------------------------------------------------------------
# Step 1D - Contextual Factor Analysis
# ---------------------------------------------------------------------------
def summarize_contextual(d: dict) -> pd.DataFrame:
    """
    Summarize contextual (organizational) factors and their relationship with high performance.

    Args:
        d (dict): Dictionary containing:
            - 'perf_latest': Latest performance rating data.
            - 'employees_org': Employee demographic and organizational attributes.

    Returns:
        pd.DataFrame: Summary with columns:
            - factor: Name of the contextual factor (e.g., grade, education, major, years_of_service).
            - category: Category or range label of that factor.
            - pct_high: Percentage of high performers in that category.
    """
    # Merge performance data with employee organizational attributes.
    perf = d["perf_latest"]
    emp = d["employees_org"]

    abt = perf.merge(emp, on="employee_id", how="inner")
    # Create a binary indicator for high performers (rating = 5).
    abt["is_high"] = (abt["rating"] == 5).astype(int)

    # Define categorical factors to evaluate.
    factors = ["grade", "education", "major"]
    summary = []
    # Compute mean percentage of high performers per categorical factor.
    for col in factors:
        tab = (
            abt.groupby(col)["is_high"]
            .mean()
            .reset_index()
            .rename(columns={"is_high": "pct_high"})
        )
        tab["factor"] = col
        tab = tab.rename(columns={col: "category"})
        summary.append(tab)

    # Handle numeric contextual factor: years of service (tenure).
    yrs = abt[["years_of_service_months", "is_high"]].copy()

    # pakai nama lokal agar tidak tabrakan kalau pernah ada kolom serupa
    yos_years = yrs["years_of_service_months"] / 12

    # Define bins for grouping years of service (in years).
    bins = [0, 2, 5, 10, 20, 40]
    yos_bin = pd.cut(
        yos_years,
        bins=bins,
        right=True,
        include_lowest=True,
    ).rename("yos_bin")

    # Aggregate high performer percentage per tenure bin.
    yrs_summary = (
        pd.DataFrame({"yos_bin": yos_bin, "is_high": yrs["is_high"]})
        .groupby("yos_bin", observed=True)["is_high"]
        .mean()
        .reset_index()
        .rename(columns={"yos_bin": "category", "is_high": "pct_high"})
    )

    yrs_summary["factor"] = "years_of_service"

    # Combine all categorical and numeric contextual summaries.
    df = pd.concat(summary + [yrs_summary], ignore_index=True)
    # Convert proportions to percentages for easier interpretation.
    df["pct_high"] *= 100
    # Sort results for consistent presentation and readability.
    return df.sort_values(["factor", "pct_high"], ascending=[True, False]).reset_index(drop=True)