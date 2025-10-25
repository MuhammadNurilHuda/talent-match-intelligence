"""
stats.py
--------
Fungsi statistik kecil yang digunakan di berbagai EDA.

Fungsi:
- `cohen_d(x, y)` : menghitung effect size antara dua grup.
- `mwu_p(x, y)`   : p-value uji Mann–Whitney U (nonparametrik).
"""

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

def cohen_d(x: pd.Series, y: pd.Series) -> float:
    x, y = x.dropna(), y.dropna()
    nx, ny = len(x), len(y)
    if nx < 2 or ny < 2: return float("nan")
    s = np.sqrt(((nx-1)*x.var(ddof=1) + (ny-1)*y.var(ddof=1)) / (nx+ny-2)) if (nx+ny-2)>0 else np.nan
    if not s or np.isnan(s) or s == 0: return 0.0
    return (x.mean() - y.mean()) / s

def mwu_p(x: pd.Series, y: pd.Series):
    x, y = x.dropna(), y.dropna()
    if len(x)==0 or len(y)==0: return float("nan")
    return mannwhitneyu(x, y, alternative="two-sided").pvalue