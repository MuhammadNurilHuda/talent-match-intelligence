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

    # only consider known numeric psych columns that exist
    numeric_candidates = ["pauli", "faxtor", "iq", "gtq", "tiki"]
    numeric_cols = [c for c in numeric_candidates if c in abt.columns]

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

# ----- Cleaning -----
def fix_disc_combination(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sinkronisasi DISC dua-huruf (e.g., DS, SC) dan label panjang.
    - Jika 'disc' kosong tetapi 'disc_word' ada, isi 'disc' dari 'disc_word'.
    - Jika 'disc_word' kosong tetapi 'disc' ada, isi 'disc_word' dari 'disc'.
    - Toleran terhadap variasi kapitalisasi, spasi, dan tanda hubung (– vs -).
    """
    df = df.copy()

    # pastikan kolom eksis
    if "disc" not in df.columns:
        df["disc"] = pd.NA
    if "disc_word" not in df.columns:
        df["disc_word"] = pd.NA

    # normalisasi disc_word -> token bentuk "dominant-conscientious"
    disc_word_norm = (
        df["disc_word"]
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace("–", "-", regex=False)   # en dash to hyphen
        .str.replace("—", "-", regex=False)   # em dash to hyphen
        .str.replace(" ", "", regex=False)    # remove spaces
    )

    # mapping word -> code (akomodir beberapa variasi umum)
    word2code = {
        "dominant-conscientious": "DC",
        "dominantsteadiness": "DS",
        "dominant-steadiness": "DS",
        "steadiness-conscientious": "SC",
        "steadinessinfluencer": "SI",
        "steadiness-influencer": "SI",
        "influencer-steadiness": "IS",
        "influencersteadiness": "IS",
        "influencer-dominant": "ID",
        "influencerdominant": "ID",
        "dominant-influencer": "DI",
        "dominantinfluencer": "DI",
        "conscientious-dominant": "CD",
        "conscientiousdominant": "CD",
        "steadiness-dominant": "SD",
        "steadinessdominant": "SD",
        "conscientious-steadiness": "CS",
        "conscientioussteadiness": "CS",
        # tambahkan varian lain jika ditemukan di data
    }

    # isi 'disc' bila kosong dari disc_word
    mask_disc_empty = df["disc"].isna() | (df["disc"].astype(str).str.strip() == "")
    df.loc[mask_disc_empty, "disc"] = disc_word_norm.map(word2code)

    # standardisasi disc: uppercase & valid 2-letter combos only
    df["disc"] = df["disc"].astype(str).str.upper().str.strip()
    df.loc[df["disc"].isin(["", "NAN", "NONE"]), "disc"] = pd.NA

    # mapping code -> word (untuk label rapih)
    code2word = {
        "DC": "Dominant–Conscientious",
        "DS": "Dominant–Steadiness",
        "SC": "Steadiness–Conscientious",
        "SI": "Steadiness–Influencer",
        "IS": "Influencer–Steadiness",
        "ID": "Influencer–Dominant",
        "DI": "Dominant–Influencer",
        "CD": "Conscientious–Dominant",
        "SD": "Steadiness–Dominant",
        "CS": "Conscientious–Steadiness",
    }

    # isi 'disc_word' dari 'disc' bila kosong
    df["disc_word"] = df["disc_word"].astype("string")
    s = df["disc_word"].astype("string")
    mask_word_empty = s.isna() | (s.str.strip() == "")
    df.loc[mask_word_empty, "disc_word"] = df.loc[mask_word_empty, "disc"].map(code2word)

    return df

def summarize_disc(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ringkasan proporsi high performers per profil DISC.
    """
    import pandas as pd
    from scipy.stats import chi2_contingency
    import numpy as np

    df = df.copy()

    # pastikan label tersedia: buat is_high dari rating bila belum ada
    if "is_high" not in df.columns:
        if "rating" in df.columns:
            df["is_high"] = (df["rating"] == 5).astype(int)
        else:
            raise KeyError("summarize_disc() requires 'is_high' or 'rating' column in the input dataframe.")

    # buang baris yang tidak punya DISC atau label
    df = df.dropna(subset=["disc", "is_high"])
    ctab = pd.crosstab(df["disc"], df["is_high"])

    # hitung proporsi high
    summary = (
        ctab.div(ctab.sum(axis=1), axis=0)
        .rename(columns={1: "pct_high", 0: "pct_non"})
        .reset_index()
    )
    summary["n"] = ctab.sum(axis=1).values

    # uji chi-square
    chi2, p, _, _ = chi2_contingency(ctab)
    n = ctab.values.sum()
    k = min(ctab.shape) - 1
    cramers_v = np.sqrt(chi2 / (n * k))

    print(f"Chi² = {chi2:.2f}, p = {p:.4f}, Cramér’s V = {cramers_v:.3f}")

    return summary.sort_values("pct_high", ascending=False).reset_index(drop=True)

    # ----- MBTI -----

def _normalize_mbti_series(s: pd.Series) -> pd.Series:
    """Bersihkan MBTI: uppercase, 4 huruf, drop anomali."""
    return (
        s.astype(str)
         .str.strip()
         .str.upper()
         .where(lambda x: x.str.len() == 4, other=pd.NA)
         .where(lambda x: x.str.fullmatch(r"[EI][SN][TF][JP]"), other=pd.NA)
    )

def _mbti_split_letters(s: pd.Series) -> pd.DataFrame:
    """Pecah MBTI menjadi 4 dimensi (E/I, S/N, T/F, J/P)."""
    s = _normalize_mbti_series(s)
    df = pd.DataFrame({
        "EI": s.str[0],  # E / I
        "SN": s.str[1],  # S / N
        "TF": s.str[2],  # T / F
        "JP": s.str[3],  # J / P
    })
    return df

def summarize_mbti_dimensions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ringkas % high per huruf untuk 4 dimensi MBTI (E/I, S/N, T/F, J/P).
    Return: DataFrame kolom [dimension, letter, pct_high, pct_non, n]
    Cetak juga chi-square & Cramér's V per dimensi.
    """
    from scipy.stats import chi2_contingency
    import numpy as np

    if "is_high" not in df.columns:
        if "rating" in df.columns:
            df = df.copy()
            df["is_high"] = (df["rating"] == 5).astype(int)
        else:
            raise KeyError("summarize_mbti_dimensions() membutuhkan kolom 'is_high' atau 'rating'.")

    # pecah huruf per dimensi
    letters = _mbti_split_letters(df.get("mbti", pd.Series(dtype="string")))
    work = pd.concat([df[["is_high"]], letters], axis=1).dropna()

    out_frames = []
    for dim in ["EI", "SN", "TF", "JP"]:
        ctab = pd.crosstab(work[dim], work["is_high"])
        # skip bila kategorinya tidak lengkap
        if ctab.shape[0] < 2 or ctab.shape[1] < 2:
            continue

        summary = (
            ctab.div(ctab.sum(axis=1), axis=0)
                .rename(columns={1: "pct_high", 0: "pct_non"})
                .reset_index()
                .rename(columns={dim: "letter"})
        )
        summary["dimension"] = dim
        summary["n"] = ctab.sum(axis=1).values

        chi2, p, _, _ = chi2_contingency(ctab)
        n_tot = ctab.values.sum()
        k = min(ctab.shape) - 1
        cramers_v = np.sqrt(chi2 / (n_tot * k))
        # tampilkan metrik per dimensi
        print(f"[MBTI-{dim}] Chi² = {chi2:.2f}, p = {p:.4f}, Cramér’s V = {cramers_v:.3f}, N = {n_tot}")

        out_frames.append(summary)

    if not out_frames:
        return pd.DataFrame(columns=["dimension", "letter", "pct_high", "pct_non", "n"])

    res = pd.concat(out_frames, ignore_index=True)
    # urutkan agar konsisten (E>I, S>N, T>F, J>P) tapi tetap berdasarkan dimensi dulu
    order = {"EI": ["E","I"], "SN": ["S","N"], "TF": ["T","F"], "JP": ["J","P"]}
    res["letter_order"] = res.apply(lambda r: order.get(r["dimension"], []).index(r["letter"]) if r["letter"] in order.get(r["dimension"], []) else 99, axis=1)
    res = res.sort_values(["dimension", "letter_order"]).drop(columns=["letter_order"]).reset_index(drop=True)
    return res

def summarize_mbti_types(df: pd.DataFrame, min_n: int = 30) -> pd.DataFrame:
    """
    Ringkas % high per 16 tipe MBTI.
    Filter tipe dengan n < min_n agar hasil stabil.
    Return: [mbti, pct_high, pct_non, n]
    """
    if "is_high" not in df.columns:
        if "rating" in df.columns:
            df = df.copy()
            df["is_high"] = (df["rating"] == 5).astype(int)
        else:
            raise KeyError("summarize_mbti_types() membutuhkan kolom 'is_high' atau 'rating'.")

    s = _normalize_mbti_series(df.get("mbti", pd.Series(dtype="string")))
    work = pd.concat([df[["is_high"]], s.rename("mbti")], axis=1).dropna()
    if work.empty:
        return pd.DataFrame(columns=["mbti","pct_high","pct_non","n"])

    ctab = pd.crosstab(work["mbti"], work["is_high"])
    summary = (
        ctab.div(ctab.sum(axis=1), axis=0)
            .rename(columns={1: "pct_high", 0: "pct_non"})
            .reset_index()
    )
    summary["n"] = ctab.sum(axis=1).values
    summary = summary[summary["n"] >= min_n]
    return summary.sort_values(["pct_high","n"], ascending=[False, False]).reset_index(drop=True)