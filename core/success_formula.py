"""
success_formula.py
------------------
Success Score yang *explainable*, memanfaatkan hasil Step 1A–1D
dengan MINIMAL perubahan pada kode lain.

Ketergantungan (sudah ada di proyekmu):
- core.io: fetch_competency_wide_latest, fetch_papi_wide, fetch_psych,
           fetch_employees_org_min (atau fetch_employees_org), fetch_perf_latest, fetch_strengths
"""

from __future__ import annotations
import numpy as np
import pandas as pd

# ---------------------- util ---------------------- #
def _z(s: pd.Series) -> pd.Series:
    m = s.mean()
    sd = s.std(ddof=0)
    if pd.isna(sd) or sd == 0:
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (s - m) / sd

def _safe_get_cols(df: pd.DataFrame, keep: list[str]) -> pd.DataFrame:
    cols = ["employee_id"] + [c for c in keep if c in df.columns]
    out = df[cols].copy()
    for k in keep:
        if k not in out.columns:
            out[k] = 0.0
    return out

# --- minmax helper for v1/v2 API --- #
def _minmax01(s: pd.Series) -> pd.Series:
    lo, hi = s.min(), s.max()
    if pd.isna(lo) or pd.isna(hi) or hi == lo:
        return pd.Series(0.0, index=s.index)
    return (s - lo) / (hi - lo)

# ---------------------- builder komponen ---------------------- #
def build_competency_component(df_comp_wide: pd.DataFrame,
                               weights_comp: dict[str, float]) -> pd.DataFrame:
    comp_cols = [c for c in df_comp_wide.columns if c != "employee_id"]
    comp_z = df_comp_wide[comp_cols].apply(_z)
    # align bobot ke kolom yang ada
    w = pd.Series({c: weights_comp.get(c, 0.0) for c in comp_cols})
    comp_score = (comp_z * w).sum(axis=1)
    return pd.DataFrame({"employee_id": df_comp_wide["employee_id"], "comp_score": comp_score})

def build_psych_component(df_psych: pd.DataFrame,
                          df_papi_wide: pd.DataFrame,
                          weights_psych: dict[str, float]) -> pd.DataFrame:
    # ambil pauli dari profiles_psych, ambil Papi_P, Papi_S, Papi_G dari PAPI wide
    psy_keep = ["pauli"]
    papi_keep = ["Papi_P", "Papi_S", "Papi_G"]

    psy_df  = _safe_get_cols(df_psych, psy_keep)
    papi_df = _safe_get_cols(df_papi_wide, papi_keep)

    df = psy_df.merge(papi_df, on="employee_id", how="outer").fillna(0.0)
    cols = [c for c in df.columns if c != "employee_id"]
    zed  = df[cols].apply(_z)
    w = pd.Series({c: weights_psych.get(c, 0.0) for c in cols})
    psy_score = (zed * w).sum(axis=1)
    return pd.DataFrame({"employee_id": df["employee_id"], "psy_score": psy_score})

def build_strengths_component(df_strengths: pd.DataFrame,
                              top_themes_weights: dict[str, float]) -> pd.DataFrame:
    """
    Mengubah top-5 themes per karyawan menjadi fitur biner untuk theme yang kita pedulikan,
    lalu di-zscore dan dibobot.
    """
    if df_strengths is None or df_strengths.empty:
        return pd.DataFrame({"employee_id": [], "str_score": []})

    # one-hot untuk seluruh theme, lalu pilih yang di-bobotkan saja
    m = (
        df_strengths.assign(val=1)
        .pivot_table(index="employee_id", columns="theme", values="val", fill_value=0)
        .reset_index()
    )
    keep = [t for t in top_themes_weights.keys() if t in m.columns]
    if not keep:
        # kalau tidak ada theme yang cocok di data, skor 0
        return pd.DataFrame({"employee_id": m["employee_id"], "str_score": 0.0})

    zed = m[keep].apply(_z)
    w = pd.Series({t: top_themes_weights.get(t, 0.0) for t in keep})
    str_score = (zed * w).sum(axis=1)
    return pd.DataFrame({"employee_id": m["employee_id"], "str_score": str_score})

def build_context_adjuster(df_emp_org: pd.DataFrame,
                           yos_threshold_years: float = 10.0,
                           uplift: float = 0.05) -> pd.DataFrame:
    """
    Adjuster ringan & non-penalty: +uplift jika YoS > threshold (default 10 tahun).
    Gunakan employees_org_min (yang penting ada years_of_service_months).
    """
    df = df_emp_org.copy()
    if "years_of_service_months" not in df.columns:
        # jika tidak tersedia, adjuster = 0
        return pd.DataFrame({"employee_id": df["employee_id"], "ctx_adj": 0.0})
    yos_years = (df["years_of_service_months"].fillna(0) / 12.0)
    adj = np.where(yos_years > yos_threshold_years, uplift, 0.0)
    return pd.DataFrame({"employee_id": df["employee_id"], "ctx_adj": adj})

def combine_score(components: pd.DataFrame, w_main: dict[str, float]) -> pd.DataFrame:
    df = components.copy()
    # isi kolom yang mungkin belum ada
    for col in ["comp_score", "str_score", "psy_score", "ctx_adj"]:
        if col not in df.columns:
            df[col] = 0.0
    df["success_score"] = (
        w_main.get("competency", 0.0)   * df["comp_score"] +
        w_main.get("strengths", 0.0)    * df["str_score"] +
        w_main.get("psychometric", 0.0) * df["psy_score"] +
        w_main.get("context", 0.0)      * df["ctx_adj"]
    )
    keep = ["employee_id","success_score","comp_score","str_score","psy_score","ctx_adj"]
    return df[keep]


# --- v1 API compatible with v2: returns (score_series, parts_df) --- #
def success_score_v1(
    df_comp_wide: pd.DataFrame,
    df_strengths: pd.DataFrame,
    df_psych: pd.DataFrame,
    df_papi_wide: pd.DataFrame,
    df_emp_org: pd.DataFrame,
    weights_comp: dict[str, float] | None = None,
    weights_psych: dict[str, float] | None = None,
    weights_strengths: dict[str, float] | None = None,
    w_main: dict[str, float] | None = None,
    minmax: bool = True,
):
    """
    Versi API v1 yang kompatibel dengan v2: mengembalikan (success_score_series, parts_df).
    Menggunakan builder v1 yang sudah ada serta bobot default v1 agar backward compatible.
    """
    # default weights (sesuai v1)
    if weights_comp is None:
        weights_comp = {
            "SEA":0.22, "CEX":0.17, "VCU":0.12, "STO":0.12, "CSI":0.11,
            "QDD":0.08, "GDR":0.07, "LIE":0.05, "IDS":0.03, "FTC":0.03,
        }
    if weights_psych is None:
        weights_psych = {"pauli":0.6, "Papi_P":0.3, "Papi_S":-0.05, "Papi_G":-0.05}
    if weights_strengths is None:
        weights_strengths = {"Futuristic":0.40, "Intellection":0.35, "Context":0.25}
    if w_main is None:
        w_main = {"competency":0.50, "strengths":0.25, "psychometric":0.15, "context":0.10}

    # build parts (aman untuk missing kolom)
    comp_part = build_competency_component(df_comp_wide, weights_comp)
    psy_part  = build_psych_component(df_psych, df_papi_wide, weights_psych)
    str_part  = build_strengths_component(df_strengths, weights_strengths)
    ctx_part  = build_context_adjuster(df_emp_org, yos_threshold_years=10.0, uplift=0.05)

    parts = (
        comp_part.merge(psy_part, on="employee_id", how="outer")
                 .merge(str_part, on="employee_id", how="outer")
                 .merge(ctx_part, on="employee_id", how="outer")
                 .fillna(0.0)
    )

    scored = combine_score(parts, w_main)
    score_series = scored.set_index("employee_id")["success_score"]
    if minmax:
        score_series = _minmax01(score_series).rename("success_score")

    # kembalikan series + parts (tanpa duplikasi kolom success_score)
    return score_series, parts


# --- wrapper for direct call from core.io, v1 API with v2 signature --- #
def compute_success_v1_from_fetchers(io_module,
                                     weights_comp_default: dict[str, float] | None = None,
                                     weights_psych_default: dict[str, float] | None = None,
                                     weights_strengths_default: dict[str, float] | None = None,
                                     w_main: dict[str, float] | None = None,
                                     minmax: bool = True):
    """Wrapper aman: fetch semua input dari core.io dan kembalikan (score_series, parts_df, perf_df)."""
    comp_wide = io_module.fetch_competency_wide_latest()
    papi_wide = io_module.fetch_papi_wide()
    psych     = io_module.fetch_psych()
    try:
        emp_org = io_module.fetch_employees_org()
    except Exception:
        emp_org = io_module.fetch_employees_org_min()
    try:
        strengths = io_module.read_sql("SELECT employee_id, rank, theme FROM core.strengths;")
    except Exception:
        strengths = pd.DataFrame(columns=["employee_id","rank","theme"])

    score_series, parts = success_score_v1(
        comp_wide, strengths, psych, papi_wide, emp_org,
        weights_comp=weights_comp_default,
        weights_psych=weights_psych_default,
        weights_strengths=weights_strengths_default,
        w_main=w_main,
        minmax=minmax,
    )
    perf = io_module.fetch_perf_latest()
    return score_series, parts, perf

def compute_success_score_from_fetchers(
    io_module,
    weights_comp_default: dict[str, float] | None = None,
    weights_psych_default: dict[str, float] | None = None,
    weights_strengths_default: dict[str, float] | None = None,
    w_main: dict[str, float] | None = None,
):
    """
    Menghitung Success Score end-to-end dengan memanggil fetcher yang sudah ada di core.io.
    Hanya butuh modul `core.io` yang kamu pakai saat ini.

    Args:
      io_module: modul core.io (sudah kamu import di notebook)
    Returns:
      (scores_df, perf_latest_df) -> tinggal kamu merge untuk evaluasi.
    """

    if weights_comp_default is None:
        # SEA paling kuat, lalu CEX, VCU/STO/CSI menengah, sisanya kecil.
        weights_comp_default = {
            "SEA":0.22, "CEX":0.17, "VCU":0.12, "STO":0.12, "CSI":0.11,
            "QDD":0.08, "GDR":0.07, "LIE":0.05, "IDS":0.03, "FTC":0.03
        }
    if weights_psych_default is None:
        # Pauli (+), Papi_P (+), Papi_S/G (- kecil)
        weights_psych_default = {"pauli":0.6, "Papi_P":0.3, "Papi_S":-0.05, "Papi_G":-0.05}
    if weights_strengths_default is None:
        # Strengths positif dari Step 1C
        weights_strengths_default = {"Futuristic":0.40, "Intellection":0.35, "Context":0.25}
    if w_main is None:
        w_main = {"competency":0.50, "strengths":0.25, "psychometric":0.15, "context":0.10}

    # ---- fetch data ----
    comp_wide = io_module.fetch_competency_wide_latest()
    papi_wide = io_module.fetch_papi_wide()
    psych     = io_module.fetch_psych()
    perf      = io_module.fetch_perf_latest()

    try:
        emp_org = io_module.fetch_employees_org()
    except Exception:
        emp_org = io_module.fetch_employees_org_min()

    try:
        strengths = io_module.read_sql("SELECT employee_id, rank, theme FROM core.strengths;")
    except Exception:
        strengths = pd.DataFrame(columns=["employee_id","rank","theme"])

    # ---- build setiap komponen ----
    comp_part = build_competency_component(comp_wide, weights_comp_default)
    psy_part  = build_psych_component(psych, papi_wide, weights_psych_default)
    str_part  = build_strengths_component(strengths, weights_strengths_default)
    ctx_part  = build_context_adjuster(emp_org, yos_threshold_years=10.0, uplift=0.05)

    # gabung komponen ke satu tabel
    parts = comp_part.merge(psy_part, on="employee_id", how="outer") \
                     .merge(str_part, on="employee_id", how="outer") \
                     .merge(ctx_part, on="employee_id", how="outer") \
                     .fillna(0.0)

    scores = combine_score(parts, w_main)
    return scores, perf