"""Reliability analysis with an R-like API (psych::alpha style)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from .result import Result


def alpha(data, keys=None, conf=0.95):
    """Cronbach's alpha and item statistics, like psych::alpha.

    Parameters
    ----------
    data : DataFrame (rows = respondents, cols = items) or 2D array.
    keys : optional sequence of +1/-1 to reverse-score items before analysis.
    conf : confidence level for the Feldt (1965) interval on raw alpha.

    Returns a Result with raw_alpha, std_alpha, the Feldt CI, mean inter-item
    correlation, and a per-item table (corrected item-total r and alpha-if-dropped).
    """
    X = pd.DataFrame(data).apply(pd.to_numeric, errors="coerce")
    X = X.dropna(axis=0, how="any")
    if keys is not None:
        keys = np.asarray(keys, dtype=float)
        if keys.shape[0] != X.shape[1]:
            raise ValueError("keys length must match number of items")
        # reverse-score: max+min - x for flagged items
        for j, k in enumerate(keys):
            if k < 0:
                col = X.iloc[:, j]
                X.iloc[:, j] = col.max() + col.min() - col
    n, k = X.shape
    if k < 2:
        raise ValueError("need at least 2 items")

    raw = _cronbach(X)
    corr = X.corr()
    r_bar = corr.values[np.triu_indices(k, 1)].mean()
    std = (k * r_bar) / (1 + (k - 1) * r_bar)
    lo, hi = _feldt_ci(raw, n, k, conf)

    total = X.sum(axis=1)
    rows = {}
    for col in X.columns:
        rest = total - X[col]
        r_drop = np.corrcoef(X[col], rest)[0, 1]  # corrected item-total
        a_drop = _cronbach(X.drop(columns=[col])) if k > 2 else np.nan
        rows[col] = {"r_item_total": r_drop, "alpha_if_dropped": a_drop,
                     "mean": X[col].mean(), "sd": X[col].std(ddof=1)}
    table = pd.DataFrame(rows).T

    values = {"raw_alpha": raw, "std_alpha": std, "ci_low": lo, "ci_high": hi,
              "conf": conf, "mean_r": r_bar, "n": n, "k": k, "items": table}
    summary = (f"Reliability analysis (Cronbach's alpha), {k} items, n = {n}\n"
               f"  raw_alpha = {raw:.3f}   std_alpha = {std:.3f}   "
               f"mean_r = {r_bar:.3f}\n"
               f"  {int(conf*100)}% CI (Feldt) [{lo:.3f}, {hi:.3f}]\n\n"
               + table.round(3).to_string())
    return Result("alpha", values, summary, table=table)


def _cronbach(X):
    k = X.shape[1]
    item_var = X.var(axis=0, ddof=1).sum()
    total_var = X.sum(axis=1).var(ddof=1)
    return (k / (k - 1)) * (1 - item_var / total_var)


def _feldt_ci(a, n, k, conf):
    """Feldt (1965) confidence interval for coefficient alpha."""
    df1, df2 = n - 1, (n - 1) * (k - 1)
    lower_alpha = (1 - conf) / 2
    f_hi = stats.f.ppf(1 - lower_alpha, df1, df2)
    f_lo = stats.f.ppf(lower_alpha, df1, df2)
    lo = 1 - (1 - a) * f_hi
    hi = 1 - (1 - a) * f_lo
    return lo, hi
