"""
evaluate.py
-----------
Metrik evaluasi Success Score: AUC, AP, KS, precision@k, capture@k, lift chart.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, average_precision_score

def precision_at_k(y_true, y_score, k=0.1):
    n = len(y_true)
    top = int(np.ceil(k * n))
    idx = np.argsort(-y_score)[:top]
    return y_true.iloc[idx].mean()

def capture_at_k(y_true, y_score, k=0.1):
    n_pos = y_true.sum()
    top = int(np.ceil(k * len(y_true)))
    idx = np.argsort(-y_score)[:top]
    return y_true.iloc[idx].sum() / n_pos if n_pos > 0 else np.nan

def ks_stat(y_true, y_score):
    # Kolmogorov–Smirnov: max gap CDF antara dua kelas
    s1 = np.sort(y_score[y_true==1])
    s0 = np.sort(y_score[y_true==0])
    from statsmodels.distributions.empirical_distribution import ECDF
    F1, F0 = ECDF(s1), ECDF(s0)
    xs = np.unique(np.concatenate([s1, s0]))
    return np.max(np.abs(F1(xs) - F0(xs)))

def evaluate_all(y_true: pd.Series, y_score: pd.Series, ks=True):
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