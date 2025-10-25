"""
eda_competency.py
-----------------
Pipeline analisis Step 1A: Competency Pillars.

Fungsi:
- `build_abt_competency(d)` : gabungkan data performa dan kompetensi → ABT.
- `summarize_competency(abt, dim_labels)` :
      hitung rata-rata per grup, delta, Cohen's d, p-value.
Output:
      DataFrame 10 pilar sebagai dasar Red Threads & Success Formula.
"""

import pandas as pd
from .stats import cohen_d, mwu_p

def build_abt_competency(d: dict) -> pd.DataFrame:
    perf = d["perf_latest"]
    comp = d["competency_latest_wide"]
    abt = perf.merge(comp, on="employee_id", how="inner")
    abt["is_high"] = (abt["rating"] == 5).astype(int)
    return abt

def summarize_competency(abt: pd.DataFrame, dim_labels: pd.DataFrame|None=None) -> pd.DataFrame:
    # deteksi kolom pilar (semua selain id/label umum)
    non_cols = {"employee_id","year","rating","is_high"}
    pillar_cols = [c for c in abt.columns if c not in non_cols]
    hi = abt["is_high"] == 1
    rows = []
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
    df = pd.DataFrame(rows).sort_values(["cohens_d","delta"], ascending=[False, False])
    if dim_labels is not None and not dim_labels.empty:
        df = df.merge(dim_labels, on="pillar_code", how="left")
    # rapikan urutan kolom
    cols = ["pillar_code","pillar_label","mean_high","mean_non","delta","cohens_d","p_mwu","n_high","n_non"]
    return df[[c for c in cols if c in df.columns]].reset_index(drop=True)