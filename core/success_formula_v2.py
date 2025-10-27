# core/success_v2.py
import numpy as np
import pandas as pd

# ====== Konstanta v2 ======
# Bobot pilar kompetensi (berdasar effect size Step 1A)
COMP_WEIGHTS = {
    "SEA": 0.30, "CEX": 0.20, "VCU": 0.15, "STO": 0.10, "CSI": 0.10,
    "QDD": 0.05, "GDR": 0.04, "LIE": 0.03, "IDS": 0.02, "FTC": 0.01
}
SUCCESS_THEMES = {"Futuristic","Intellection","Context","Developer","Harmony","Analytical"}
MILD_DISC_BONUS = {"SI","SD","IS"}  # soft bonus kecil, non-penalizing

def _minmax01(s: pd.Series) -> pd.Series:
    lo, hi = s.min(), s.max()
    if pd.isna(lo) or pd.isna(hi) or hi == lo:
        return pd.Series(0.0, index=s.index)
    return (s - lo) / (hi - lo)

def _z_clip(s: pd.Series) -> pd.Series:
    # z-score + clip untuk jaga outlier (pakai mean/std sample-pop)
    st = s.std(ddof=0)
    if st == 0 or pd.isna(st):
        z = (s - s.mean())
    else:
        z = (s - s.mean()) / st
    return z.clip(-2, 2)

# ---------- Komponen skor ----------
def compute_comp_score(df_comp_wide: pd.DataFrame) -> pd.Series:
    """
    df_comp_wide: hasil fetch_competency_wide_latest() → kolom: employee_id + 10 pilar (skala 1..5)
    """
    df = df_comp_wide.set_index("employee_id")
    cols = [c for c in COMP_WEIGHTS if c in df.columns]
    if not cols:
        return pd.Series(0.0, index=df.index, name="comp_score")
    x = (df[cols] - 1.0) / 4.0  # skala 1..5 → 0..1
    w = pd.Series({c: COMP_WEIGHTS[c] for c in cols})
    return (x * w).sum(axis=1).rename("comp_score")

def compute_str_score(df_str_top5: pd.DataFrame) -> pd.Series:
    """
    df_str_top5: hasil fetch_strengths() → long: [employee_id, rank (1..5), theme]
    """
    if not {"employee_id","theme"}.issubset(df_str_top5.columns):
        # fallback aman
        return pd.Series(0.0, index=pd.Index([], name="employee_id"), name="str_score")

    df = df_str_top5.copy()
    df["hit"] = df["theme"].isin(SUCCESS_THEMES)
    cnt = df.groupby("employee_id")["hit"].sum()  # 0..5
    return (cnt / 5.0).rename("str_score")

def compute_psy_score(df_psych: pd.DataFrame, df_papi_wide: pd.DataFrame) -> pd.Series:
    """
    df_psych: fetch_profiles_psych_full() → index employee_id + kolom [pauli, faxtor, ...]
    df_papi_wide: fetch_papi_wide() → index employee_id + kolom [Papi_P, Papi_W, ...]
    """
    # pastikan index = employee_id
    psy = df_psych.set_index("employee_id")
    papi = df_papi_wide.set_index("employee_id")

    # siapkan kolom yang dibutuhkan (isi dengan NaN jika tidak ada)
    for c in ["pauli","faxtor"]:
        if c not in psy.columns:
            psy[c] = np.nan
    for c in ["Papi_P","Papi_W"]:
        if c not in papi.columns:
            papi[c] = np.nan

    z_pauli = _z_clip(psy["pauli"])
    z_faxt  = _z_clip(psy["faxtor"])
    z_pp    = _z_clip(papi["Papi_P"])
    z_pw    = _z_clip(papi["Papi_W"])

    # formula v2 (evidence-based rule)
    psy_core = 0.50*z_pauli - 0.25*z_faxt + 0.15*z_pp + 0.10*z_pw
    psy_score = ((psy_core + 2.0) / 4.0).clip(0, 1).rename("psy_score")  # rescale → [0,1]
    psy_score = psy_score.reindex(psy.index).fillna(0.5)  # netral bila missing
    return psy_score

def compute_disc_bonus(series_disc: pd.Series, comp_score: pd.Series) -> pd.Series:
    """
    series_disc: pd.Series (index employee_id) berisi kode DISC 2 huruf (SI/SD/IS/...)
    comp_score: untuk syarat minimal kompetensi agar bonus aktif
    """
    sdisc = series_disc.astype(str).str.upper()
    cond = sdisc.isin(MILD_DISC_BONUS) & (comp_score >= 0.60)
    return cond.astype(float).rename("disc_bonus") * 0.02  # max +0.02

# ---------- Orkestrasi ----------
def success_score_v2(df_comp_wide: pd.DataFrame,
                     df_str_top5: pd.DataFrame,
                     df_psych: pd.DataFrame,
                     df_papi_wide: pd.DataFrame,
                     series_disc: pd.Series):
    """
    Kembalikan:
    - success_v2: pd.Series skor final [0..1] (index employee_id)
    - parts: pd.DataFrame detail komponen (comp_score, str_score, psy_score, disc_bonus)
    """
    comp = compute_comp_score(df_comp_wide)                        # index employee_id
    strn = compute_str_score(df_str_top5).reindex(comp.index).fillna(0.0)
    psy  = compute_psy_score(df_psych, df_papi_wide).reindex(comp.index).fillna(0.5)
    disc_b = compute_disc_bonus(series_disc.reindex(comp.index), comp).fillna(0.0)

    raw = 0.50*comp + 0.25*strn + 0.20*psy + disc_b
    final = _minmax01(raw).rename("success_v2")

    parts = pd.concat([comp.rename("comp_score"),
                       strn.rename("str_score"),
                       psy.rename("psy_score"),
                       disc_b.rename("disc_bonus")], axis=1)
    return final, parts