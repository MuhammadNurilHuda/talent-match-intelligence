"""
EDA Step 1D – Contextual Factors
--------------------------------
Menganalisis hubungan antara faktor organisasi (grade, masa kerja, pendidikan, jurusan)
dan proporsi high performers.
"""

import pandas as pd

def summarize_contextual(d: dict) -> pd.DataFrame:
    perf = d["perf_latest"]
    emp = d["employees_org"]

    abt = perf.merge(emp, on="employee_id", how="inner")
    abt["is_high"] = (abt["rating"] == 5).astype(int)

    # hitung proporsi high performer per kategori
    factors = ["grade", "education", "major"]
    summary = []
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

    # numeric: years_of_service
    yrs = abt[["years_of_service_months", "is_high"]].copy()

    # pakai nama lokal agar tidak tabrakan kalau pernah ada kolom serupa
    yos_years = yrs["years_of_service_months"] / 12

    # binning masa kerja (tahun)
    bins = [0, 2, 5, 10, 20, 40]
    yos_bin = pd.cut(
        yos_years,
        bins=bins,
        right=True,
        include_lowest=True,
    ).rename("yos_bin")

    # agregasi hanya ke target (is_high) -> hindari kolom lain ikut dihitung
    yrs_summary = (
        pd.DataFrame({"yos_bin": yos_bin, "is_high": yrs["is_high"]})
        .groupby("yos_bin", observed=True)["is_high"]
        .mean()
        .reset_index()
        .rename(columns={"yos_bin": "category", "is_high": "pct_high"})
    )

    yrs_summary["factor"] = "years_of_service"

    df = pd.concat(summary + [yrs_summary], ignore_index=True)
    df["pct_high"] *= 100
    return df.sort_values(["factor", "pct_high"], ascending=[True, False]).reset_index(drop=True)