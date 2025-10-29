"""
eda_psych.py
------------
Step 1B/1C – Psychometric Profiles (PAPI + Cognitive + DISC/MBTI).

Responsibilities:
- PAPI: compare 20 workstyle scales between high vs. non-high performers.
- Cognitive: compare numeric psychometric indices (Pauli, Faxtor, IQ, GTQ, TIKI).
- DISC/MBTI: clean categorical profiles and summarize % high performers.

Outputs:
DataFrames for each block used in Red Threads discovery and the Success Formula.
"""

import pandas as pd
from .stats import cohen_d, mwu_p

# ---------------------------------------------------------------------------
# Step 1B - PAPI (Workstyle / Behavioral Preferences)
# ---------------------------------------------------------------------------
# ----- PAPI -----
def summarize_papi(d: dict) -> pd.DataFrame:
    """
    Compare 20 PAPI behavioral preference scales between high and non-high performers.

    Args:
        d (dict): Dictionary containing:
            - 'perf_latest': DataFrame with latest performance ratings.
            - 'papi_wide': DataFrame containing 20 PAPI scales per employee.

    Returns:
        pd.DataFrame: Summary with columns:
            - scale: PAPI scale name.
            - mean_high / mean_non: Average scores for high vs. non-high performers.
            - delta: Difference in mean scores (high minus non-high).
            - cohens_d: Standardized effect size.
            - p_mwu: Mann–Whitney U test p-value.
    """
    # Merge latest performance ratings with PAPI behavioral scales.
    perf = d["perf_latest"]
    papi = d["papi_wide"]
    abt = perf.merge(papi, on="employee_id", how="inner")
    # Create a binary indicator for high performers (rating = 5).
    abt["is_high"] = (abt["rating"] == 5).astype(int)

    # Identify non-scale columns to exclude from analysis.
    non_cols = {"employee_id","rating","year","is_high"}
    scales = [c for c in abt.columns if c not in non_cols]

    # Iterate through each PAPI scale to compute summary statistics.
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
    # Sort by effect size (Cohen's d) to highlight strongest differentiators.
    df = pd.DataFrame(rows).sort_values("cohens_d", ascending=False).reset_index(drop=True)
    return df

# ---------------------------------------------------------------------------
# Step 1C - Cognitive (Numeric Psychometric Indices)
# ---------------------------------------------------------------------------
# ----- Cognitive -----
def summarize_cognitive(d: dict) -> pd.DataFrame:
    """
    Compare numeric psychometric indices between high and non-high performers.

    Args:
        d (dict): Dictionary containing:
            - 'perf_latest': DataFrame with latest performance ratings.
            - 'psych': DataFrame with psychometric metrics (e.g., pauli, faxtor, iq, gtq, tiki).

    Returns:
        pd.DataFrame: Summary with columns:
            - metric: Name of the psychometric variable.
            - mean_high / mean_non: Average scores for high vs. non-high performers.
            - delta: Difference in means.
            - cohens_d: Standardized effect size.
            - p_mwu: Mann–Whitney U test p-value.
    """
    # Merge latest performance ratings with available psychometric metrics.
    perf = d["perf_latest"]
    psych = d["psych"]
    abt = perf.merge(psych, on="employee_id", how="inner")
    # Label high performers.
    abt["is_high"] = (abt["rating"] == 5).astype(int)

    # Consider only known numeric psychometric fields if present in the dataset.
    numeric_candidates = ["pauli", "faxtor", "iq", "gtq", "tiki"]
    numeric_cols = [c for c in numeric_candidates if c in abt.columns]

    # Compute group statistics per psychometric metric.
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

# ---------------------------------------------------------------------------
# Psychometric Profile Cleaning & Categorical Summaries (DISC / MBTI)
# ---------------------------------------------------------------------------
# ----- Cleaning -----
def fix_disc_combination(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize and synchronize DISC two-letter codes (e.g., DS, SC) with long-form labels.

    Rules:
    - If 'disc' (code) is missing but 'disc_word' exists, infer code from the word label.
    - If 'disc_word' is missing but 'disc' exists, map code to a standardized long label.
    - Tolerant of capitalization, spaces, and dash variations (en/em dash vs. hyphen).

    Returns a copy of the input DataFrame with cleaned 'disc' and 'disc_word' columns.
    """
    df = df.copy()

    # Ensure required columns exist.
    if "disc" not in df.columns:
        df["disc"] = pd.NA
    if "disc_word" not in df.columns:
        df["disc_word"] = pd.NA

    # Normalize 'disc_word' into a compact token form like "dominant-conscientious".
    disc_word_norm = (
        df["disc_word"]
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace("–", "-", regex=False)   # en dash to hyphen
        .str.replace("—", "-", regex=False)   # em dash to hyphen
        .str.replace(" ", "", regex=False)    # remove spaces
    )

    # Map normalized long-form labels to two-letter DISC codes (common variants accommodated).
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
    }

    # Fill missing 'disc' codes using the mapped 'disc_word' tokens.
    mask_disc_empty = df["disc"].isna() | (df["disc"].astype(str).str.strip() == "")
    df.loc[mask_disc_empty, "disc"] = disc_word_norm.map(word2code)

    # Standardize 'disc' codes to uppercase and drop invalid placeholders.
    df["disc"] = df["disc"].astype(str).str.upper().str.strip()
    df.loc[df["disc"].isin(["", "NAN", "NONE"]), "disc"] = pd.NA

    # Map codes back to standardized, human-readable long labels.
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

    # Fill missing 'disc_word' using the code-to-word mapping.
    df["disc_word"] = df["disc_word"].astype("string")
    s = df["disc_word"].astype("string")
    mask_word_empty = s.isna() | (s.str.strip() == "")
    df.loc[mask_word_empty, "disc_word"] = df.loc[mask_word_empty, "disc"].map(code2word)

    return df

def summarize_disc(df: pd.DataFrame) -> pd.DataFrame:
    """
    Summarize the proportion of high performers by DISC profile, with association tests.

    Requirements:
    - Input must include either 'is_high' or 'rating' (to derive 'is_high') and 'disc'.

    Returns:
        pd.DataFrame sorted by 'pct_high' with columns:
        ['disc', 'pct_high', 'pct_non', 'n'].
    Prints:
        Chi-square statistic, p-value, and Cramér’s V for association strength.
    """
    import pandas as pd
    from scipy.stats import chi2_contingency
    import numpy as np

    df = df.copy()

    # Ensure label availability: derive 'is_high' from 'rating' if necessary.
    if "is_high" not in df.columns:
        if "rating" in df.columns:
            df["is_high"] = (df["rating"] == 5).astype(int)
        else:
            raise KeyError("summarize_disc() requires 'is_high' or 'rating' column in the input dataframe.")

    # Drop rows missing DISC or label information to avoid bias.
    df = df.dropna(subset=["disc", "is_high"])
    ctab = pd.crosstab(df["disc"], df["is_high"])

    # Compute proportions of high vs. non-high within each DISC code.
    summary = (
        ctab.div(ctab.sum(axis=1), axis=0)
        .rename(columns={1: "pct_high", 0: "pct_non"})
        .reset_index()
    )
    summary["n"] = ctab.sum(axis=1).values

    # Perform chi-square test of independence and compute Cramér’s V.
    chi2, p, _, _ = chi2_contingency(ctab)
    n = ctab.values.sum()
    k = min(ctab.shape) - 1
    cramers_v = np.sqrt(chi2 / (n * k))

    print(f"Chi² = {chi2:.2f}, p = {p:.4f}, Cramér’s V = {cramers_v:.3f}")

    return summary.sort_values("pct_high", ascending=False).reset_index(drop=True)

# ----- MBTI -----

def _normalize_mbti_series(s: pd.Series) -> pd.Series:
    """Clean MBTI strings: uppercase, ensure 4 letters, drop anomalies."""
    return (
        s.astype(str)
         .str.strip()
         .str.upper()
         .where(lambda x: x.str.len() == 4, other=pd.NA)
         .where(lambda x: x.str.fullmatch(r"[EI][SN][TF][JP]"), other=pd.NA)
    )

def _mbti_split_letters(s: pd.Series) -> pd.DataFrame:
    """Split MBTI types into the four dimensions (E/I, S/N, T/F, J/P)."""
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
    Summarize % high for each letter across the 4 MBTI dimensions (E/I, S/N, T/F, J/P).

    Returns:
        DataFrame with columns [dimension, letter, pct_high, pct_non, n].
    Side effect:
        Prints chi-square and Cramér's V for each dimension.
    """
    from scipy.stats import chi2_contingency
    import numpy as np

    if "is_high" not in df.columns:
        if "rating" in df.columns:
            df = df.copy()
            df["is_high"] = (df["rating"] == 5).astype(int)
        else:
            raise KeyError("summarize_mbti_dimensions() membutuhkan kolom 'is_high' atau 'rating'.")

    # Split MBTI into per-dimension letters.
    letters = _mbti_split_letters(df.get("mbti", pd.Series(dtype="string")))
    work = pd.concat([df[["is_high"]], letters], axis=1).dropna()

    out_frames = []
    for dim in ["EI", "SN", "TF", "JP"]:
        ctab = pd.crosstab(work[dim], work["is_high"])
        # Skip if the contingency table is degenerate (e.g., only one category).
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
        # Log association metrics per dimension.
        print(f"[MBTI-{dim}] Chi² = {chi2:.2f}, p = {p:.4f}, Cramér’s V = {cramers_v:.3f}, N = {n_tot}")

        out_frames.append(summary)

    if not out_frames:
        return pd.DataFrame(columns=["dimension", "letter", "pct_high", "pct_non", "n"])

    res = pd.concat(out_frames, ignore_index=True)
    order = {"EI": ["E","I"], "SN": ["S","N"], "TF": ["T","F"], "JP": ["J","P"]}
    res["letter_order"] = res.apply(lambda r: order.get(r["dimension"], []).index(r["letter"]) if r["letter"] in order.get(r["dimension"], []) else 99, axis=1)
    res = res.sort_values(["dimension", "letter_order"]).drop(columns=["letter_order"]).reset_index(drop=True)
    return res

def summarize_mbti_types(df: pd.DataFrame, min_n: int = 30) -> pd.DataFrame:
    """
    Summarize % high across the 16 MBTI types.

    Filters out types with count < min_n for stability.

    Returns:
        DataFrame columns: [mbti, pct_high, pct_non, n], sorted by pct_high then n.
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