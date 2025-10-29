"""
viz.py
------
Simple visualization utilities for Step 1 (Exploratory Data Analysis).

Responsibilities:
- Generate minimal Matplotlib-based plots to visualize competency effects.
- Avoid seaborn dependency to keep the project lightweight.

Functions:
- plot_competency_effects(): Bar chart of Cohen’s d effect sizes per competency pillar.
- plot_competency_delta_bar(): Bar chart of mean score deltas between high vs. non-high performers.
"""
import matplotlib.pyplot as plt

def plot_competency_effects(comp_tbl):
    """
    Create a bar chart showing Cohen’s d (effect size) per competency pillar.

    Args:
        comp_tbl (pd.DataFrame): Table containing columns ['pillar_code', 'cohens_d'].

    Behavior:
        - Sorts pillars by descending effect size.
        - Displays a simple bar chart for quick visual inspection.
    """
    # Select relevant columns and sort pillars by descending effect size.
    df = comp_tbl[["pillar_code","cohens_d"]].dropna().sort_values("cohens_d", ascending=False)
    # Initialize Matplotlib figure and configure basic layout.
    plt.figure(figsize=(8, 4.5))
    plt.bar(df["pillar_code"], df["cohens_d"])
    plt.title("Effect Size (Cohen's d) per Competency Pillar")
    plt.xlabel("Pillar")
    plt.ylabel("Cohen's d")
    plt.xticks(rotation=0)
    plt.tight_layout()
    # Render the plot inline.
    plt.show()

def plot_competency_delta_bar(comp_tbl):
    """
    Create a bar chart showing mean score differences (High - Non-High) per competency pillar.

    Args:
        comp_tbl (pd.DataFrame): Table containing columns ['pillar_code', 'delta'].

    Behavior:
        - Sorts pillars by descending delta values.
        - Visualizes which pillars show the largest mean gaps between groups.
    """
    # Select relevant columns and sort by descending delta (mean difference).
    df = comp_tbl[["pillar_code","delta"]].dropna().sort_values("delta", ascending=False)
    # Initialize Matplotlib figure for delta visualization.
    plt.figure(figsize=(8, 4.5))
    plt.bar(df["pillar_code"], df["delta"])
    plt.title("Delta Mean (High - Non-High) per Competency Pillar")
    plt.xlabel("Pillar")
    plt.ylabel("Delta Mean")
    plt.xticks(rotation=0)
    plt.tight_layout()
    # Display the completed bar chart.
    plt.show()