"""
EDA Step 1C – Strengths (Behavioral Themes)
-------------------------------------------
Menganalisis distribusi tema CliftonStrengths antara high vs non-high performers.
"""

import pandas as pd

def summarize_strengths(d: dict) -> pd.DataFrame:
    perf = d["perf_latest"]
    strg = d["strengths"]
    abt = perf.merge(strg, on="employee_id", how="inner")
    abt["is_high"] = (abt["rating"] == 5).astype(int)

    # Hitung frekuensi theme untuk dua grup
    freq = abt.groupby(["theme", "is_high"]).size().reset_index(name="n")
    total = abt.groupby("is_high")["theme"].count().rename("total").reset_index()
    freq = freq.merge(total, on="is_high")
    freq["pct"] = freq["n"] / freq["total"] * 100

    # Pivot agar 1 baris per theme
    wide = freq.pivot(index="theme", columns="is_high", values="pct").fillna(0).reset_index()
    wide.columns = ["theme", "pct_nonhigh", "pct_high"]  # 0 = non, 1 = high
    wide["delta_pct"] = wide["pct_high"] - wide["pct_nonhigh"]
    return wide.sort_values("delta_pct", ascending=False).reset_index(drop=True)