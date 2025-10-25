"""
EDA Psychometric Profiles (PAPI + Cognitive)
"""
import pandas as pd
from .stats import cohen_d, mwu_p

# ----- PAPI -----
def summarize_papi(d: dict) -> pd.DataFrame:
    """
    Bandingkan skor 20 skala PAPI antara high vs non-high performers.
    Output: DataFrame berisi mean_high, mean_non, delta, cohens_d, p_mwu.
    """
    perf = d["perf_latest"]
    papi = d["papi_wide"]
    abt = perf.merge(papi, on="employee_id", how="inner")
    abt["is_high"] = (abt["rating"] == 5).astype(int)

    non_cols = {"employee_id","rating","year","is_high"}
    scales = [c for c in abt.columns if c not in non_cols]

    rows = []
    hi = abt["is_high"] == 1
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

# ----- Cognitive -----
def summarize_cognitive(d: dict) -> pd.DataFrame:
    perf = d["perf_latest"]
    psych = d["psych"]
    abt = perf.merge(psych, on="employee_id", how="inner")
    abt["is_high"] = (abt["rating"] == 5).astype(int)

    numeric_cols = [c for c in abt.columns if c not in {"employee_id","rating","year","is_high","disc","mbti"}]
    hi = abt["is_high"] == 1
    rows = []
    for c in numeric_cols:
        x, y = abt.loc[hi, c], abt.loc[~hi, c]
        rows.append({
            "metric": c,
            "mean_high": x.mean(),
            "mean_non": y.mean(),
            "delta": x.mean() - y.mean(),
            "cohens_d": cohen_d(x, y),
            "p_mwu": mwu_p(x, y),
        })
    return pd.DataFrame(rows).sort_values("cohens_d", ascending=False).reset_index(drop=True)
