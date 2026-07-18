"""Common inferential tests with effect sizes, R-like API."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from .result import Result


def ttest(df, dv, group=None, paired=False, equal_var=False, conf=0.95):
    """Two-group or paired t-test with Cohen's d.

    Long form: ttest(df, dv="score", group="cond").
    Paired: pass group with exactly two levels and paired=True (matched by row
    order within each level after dropping NAs).
    Cohen's d uses the pooled SD (independent) or SD of differences (paired).
    """
    g = df[group]
    levels = list(pd.unique(g.dropna()))
    if len(levels) != 2:
        raise ValueError("group must have exactly 2 levels")
    x = df.loc[g == levels[0], dv].dropna()
    y = df.loc[g == levels[1], dv].dropna()
    if paired:
        n = min(len(x), len(y))
        x, y = x.iloc[:n].values, y.iloc[:n].values
        t, p = stats.ttest_rel(x, y)
        diff = x - y
        d = diff.mean() / diff.std(ddof=1)
        dfree = n - 1
        test = "Paired t-test"
    else:
        t, p = stats.ttest_ind(x, y, equal_var=equal_var)
        d = _cohen_d(x, y)
        dfree = _welch_df(x, y) if not equal_var else len(x) + len(y) - 2
        test = "Welch t-test" if not equal_var else "Student t-test"
    values = {"t": float(t), "df": float(dfree), "p": float(p), "cohens_d": float(d),
              "m1": float(np.mean(x)), "m2": float(np.mean(y)),
              "level1": levels[0], "level2": levels[1], "dv": dv}
    summary = (f"{test}: {dv} by {group}\n"
               f"  t({dfree:.1f}) = {t:.3f}, p = {p:.4f}, Cohen's d = {d:.3f}")
    return Result("ttest", values, summary)


def _cohen_d(x, y):
    nx, ny = len(x), len(y)
    sp = np.sqrt(((nx - 1) * np.var(x, ddof=1) + (ny - 1) * np.var(y, ddof=1))
                 / (nx + ny - 2))
    return (np.mean(x) - np.mean(y)) / sp


def _welch_df(x, y):
    vx, vy = np.var(x, ddof=1), np.var(y, ddof=1)
    nx, ny = len(x), len(y)
    num = (vx / nx + vy / ny) ** 2
    den = (vx / nx) ** 2 / (nx - 1) + (vy / ny) ** 2 / (ny - 1)
    return num / den


def anova(df, dv, group):
    """One-way ANOVA with eta squared and omega squared."""
    g = df[group]
    levels = list(pd.unique(g.dropna()))
    groups = [df.loc[g == lv, dv].dropna().values for lv in levels]
    f, p = stats.f_oneway(*groups)
    grand = np.concatenate(groups)
    ss_between = sum(len(gi) * (gi.mean() - grand.mean()) ** 2 for gi in groups)
    ss_total = ((grand - grand.mean()) ** 2).sum()
    ss_within = ss_total - ss_between
    k = len(groups)
    n = len(grand)
    df_b, df_w = k - 1, n - k
    ms_within = ss_within / df_w
    eta2 = ss_between / ss_total
    omega2 = (ss_between - df_b * ms_within) / (ss_total + ms_within)
    values = {"F": float(f), "df_between": df_b, "df_within": df_w, "p": float(p),
              "eta_squared": float(eta2), "omega_squared": float(omega2),
              "dv": dv, "group": group, "k": k}
    summary = (f"One-way ANOVA: {dv} by {group}\n"
               f"  F({df_b}, {df_w}) = {f:.3f}, p = {p:.4f}, "
               f"eta^2 = {eta2:.3f}, omega^2 = {omega2:.3f}")
    return Result("anova", values, summary)


def chisq(df, row, col, correction=False):
    """Chi-square test of independence with Cramer's V."""
    ct = pd.crosstab(df[row], df[col])
    chi2, p, dof, _ = stats.chi2_contingency(ct.values, correction=correction)
    n = ct.values.sum()
    r, c = ct.shape
    v = np.sqrt(chi2 / (n * (min(r, c) - 1)))
    values = {"chi2": float(chi2), "df": int(dof), "p": float(p),
              "cramers_v": float(v), "n": int(n), "row": row, "col": col}
    summary = (f"Chi-square test of independence: {row} x {col}\n"
               f"  chi2({dof}) = {chi2:.3f}, p = {p:.4f}, Cramer's V = {v:.3f}, "
               f"N = {n}")
    return Result("chisq", values, summary, table=ct)
