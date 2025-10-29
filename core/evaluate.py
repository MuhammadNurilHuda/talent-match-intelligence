"""
evaluate.py
-----------
Evaluation metrics for the Success Score model.

Responsibilities:
- Provide core evaluation metrics for ranking and classification quality.
- Includes ROC-AUC, PR-AUC (Average Precision), Kolmogorov–Smirnov (KS) statistic,
  Precision@K, and Capture@K for top-percentile performance analysis.
- Used in Step 2 and Step 3 to validate scoring model performance and dashboard insights.

Output:
Dictionary or scalar metrics summarizing predictive discrimination and lift.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score

# ---------------------------------------------------------------------------
# Core Ranking Metrics
# ---------------------------------------------------------------------------

def precision_at_k(y_true, y_score, k=0.1):
    """
    Compute Precision@K — proportion of true positives among the top K fraction
    of ranked candidates based on predicted scores.

    Args:
        y_true (pd.Series): Ground-truth binary labels (1 = positive, 0 = negative).
        y_score (pd.Series): Model-predicted scores or probabilities.
        k (float): Fraction of total samples to consider (e.g., 0.1 = top 10%).

    Returns:
        float: Mean precision within the top-K ranked candidates.
    """
    # Determine number of samples and select top K fraction.
    n = len(y_true)
    top = int(np.ceil(k * n))
    idx = np.argsort(-y_score)[:top]
    return y_true.iloc[idx].mean()

def capture_at_k(y_true, y_score, k=0.1):
    """
    Compute Capture@K — proportion of all positives captured within the top K
    fraction of ranked candidates.

    Args:
        y_true (pd.Series): Ground-truth binary labels.
        y_score (pd.Series): Model-predicted scores or probabilities.
        k (float): Fraction of total samples to consider.

    Returns:
        float: Fraction of total positives captured (recall-like measure at top-K).
    """
    # Compute total number of positive labels for normalization.
    n_pos = y_true.sum()
    top = int(np.ceil(k * len(y_true)))
    idx = np.argsort(-y_score)[:top]
    return y_true.iloc[idx].sum() / n_pos if n_pos > 0 else np.nan

def ks_stat(y_true, y_score):
    """
    Compute the Kolmogorov–Smirnov (KS) statistic — the maximum separation
    between the cumulative distributions of scores for positive and negative classes.

    Args:
        y_true (pd.Series): Ground-truth binary labels.
        y_score (pd.Series): Model-predicted scores or probabilities.

    Returns:
        float: KS statistic value (0–1), where higher indicates better separation.
    """
    # Separate and sort scores for positive and negative classes.
    s1 = np.sort(y_score[y_true==1])
    s0 = np.sort(y_score[y_true==0])
    # Compute empirical CDFs for both distributions.
    from statsmodels.distributions.empirical_distribution import ECDF
    F1, F0 = ECDF(s1), ECDF(s0)
    xs = np.unique(np.concatenate([s1, s0]))
    return np.max(np.abs(F1(xs) - F0(xs)))

def evaluate_all(y_true: pd.Series, y_score: pd.Series, ks=True):
    """
    Compute a consolidated set of evaluation metrics for Success Score modeling.

    Args:
        y_true (pd.Series): Ground-truth binary labels.
        y_score (pd.Series): Model-predicted scores or probabilities.
        ks (bool): Whether to include Kolmogorov–Smirnov statistic.

    Returns:
        dict: Metrics including ROC-AUC, PR-AUC, Precision@10/20, Capture@10/20,
              and optionally KS statistic.
    """
    # Aggregate metrics into a single dictionary for reporting.
    out = {
        "roc_auc": float(roc_auc_score(y_true, y_score)),
        "pr_auc":  float(average_precision_score(y_true, y_score)),
        "prec@10": float(precision_at_k(y_true, y_score, 0.10)),
        "capt@10": float(capture_at_k(y_true, y_score, 0.10)),
        "prec@20": float(precision_at_k(y_true, y_score, 0.20)),
        "capt@20": float(capture_at_k(y_true, y_score, 0.20)),
    }
    if ks:
        out["ks"] = float(ks_stat(y_true, y_score))
    return out