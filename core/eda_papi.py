"""
EDA Step 1B – PAPI (Workstyle / Behavioral Preferences)
-------------------------------------------------------
Menganalisis 20 skala PAPI antara high vs non-high performers.
Output: DataFrame berisi effect size, delta, dan p-value tiap skala.
"""

import pandas as pd
from .stats import cohen_d, mwu_p

def summarize_papi(d: dict) -> pd.DataFrame:
    perf = d["perf_latest"]
    papi = d["papi_wide"]
    abt = perf.merge(papi, on="employee_id", how="inner")
    abt["is_high"] = (abt["rating"] == 5).astype(int)

    # deteksi kolom skala (semua selain kolom non-numerik)
    non_cols = {"employee_id","rating","year","is_high"}
    scales = [c for c in abt.columns if c not in non_cols]

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
    df = pd.DataFrame(rows).sort_values("cohens_d", ascending=False).reset_index(drop=True)
    return df