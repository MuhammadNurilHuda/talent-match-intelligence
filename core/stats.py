"""
stats.py
--------
Lightweight statistical utilities used across EDA modules.

Functions:
- cohen_d(x, y): Compute the standardized effect size (Cohen’s d) between two groups.
- mwu_p(x, y):   Compute the p-value of the Mann–Whitney U test (non-parametric).

Notes:
- All functions gracefully handle missing values.
- Designed for quick exploratory comparisons between high vs. non-high performers.
"""

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

def cohen_d(x: pd.Series, y: pd.Series) -> float:
    """
    Compute Cohen’s d effect size between two numeric samples.

    Args:
        x (pd.Series): Numeric values for group 1.
        y (pd.Series): Numeric values for group 2.

    Returns:
        float: Standardized mean difference between groups.
               Positive = higher mean in x, Negative = higher mean in y.
    """
    # Remove missing values before computation.
    x, y = x.dropna(), y.dropna()
    nx, ny = len(x), len(y)
    if nx < 2 or ny < 2: return float("nan")
    # Pooled standard deviation calculation (sample-based, ddof=1).
    s = np.sqrt(((nx-1)*x.var(ddof=1) + (ny-1)*y.var(ddof=1)) / (nx+ny-2)) if (nx+ny-2)>0 else np.nan
    # Handle edge cases: zero variance or undefined standard deviation.
    if not s or np.isnan(s) or s == 0: return 0.0
    return (x.mean() - y.mean()) / s

def mwu_p(x: pd.Series, y: pd.Series):
    """
    Compute the Mann–Whitney U test p-value (two-sided) for two independent samples.

    Args:
        x (pd.Series): Sample 1.
        y (pd.Series): Sample 2.

    Returns:
        float: p-value indicating whether the two distributions differ significantly.
    """
    # Drop missing values to avoid errors in statistical test.
    x, y = x.dropna(), y.dropna()
    # Return NaN if one of the groups has no valid observations.
    if len(x)==0 or len(y)==0: return float("nan")
    # Perform Mann–Whitney U test (non-parametric, two-sided).
    return mannwhitneyu(x, y, alternative="two-sided").pvalue