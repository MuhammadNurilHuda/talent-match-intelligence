"""
viz.py
------
Util visualisasi sederhana untuk Step 1.
Catatan: gunakan matplotlib (tanpa seaborn) agar dependensi minimal.
"""
import matplotlib.pyplot as plt

def plot_competency_effects(comp_tbl):
    """
    Bar chart Cohen's d per pilar (urut menurun).
    Expects columns: pillar_code, cohens_d
    """
    df = comp_tbl[["pillar_code","cohens_d"]].dropna().sort_values("cohens_d", ascending=False)
    plt.figure(figsize=(8, 4.5))
    plt.bar(df["pillar_code"], df["cohens_d"])
    plt.title("Effect Size (Cohen's d) per Competency Pillar")
    plt.xlabel("Pillar")
    plt.ylabel("Cohen's d")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.show()

def plot_competency_delta_bar(comp_tbl):
    """
    Bar chart delta (mean_high - mean_non) per pilar, urut menurun.
    """
    df = comp_tbl[["pillar_code","delta"]].dropna().sort_values("delta", ascending=False)
    plt.figure(figsize=(8, 4.5))
    plt.bar(df["pillar_code"], df["delta"])
    plt.title("Delta Mean (High - Non-High) per Competency Pillar")
    plt.xlabel("Pillar")
    plt.ylabel("Delta Mean")
    plt.xticks(rotation=0)
    plt.tight_layout()
    plt.show()