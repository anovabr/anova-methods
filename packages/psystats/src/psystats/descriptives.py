"""Descriptives, frequencies, correlations, and Table 1 (arsenal/tableone/apaTables)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from .result import Result


def describe(df, columns=None):
    """Numeric descriptives per column: n, mean, sd, median, min, max, skew, kurtosis."""
    data = df if columns is None else df[columns]
    num = data.select_dtypes(include="number")
    rows = {}
    for col in num.columns:
        s = num[col].dropna()
        rows[col] = {
            "n": int(s.shape[0]), "mean": s.mean(), "sd": s.std(ddof=1),
            "median": s.median(), "min": s.min(), "max": s.max(),
            "skew": stats.skew(s, bias=False) if s.shape[0] > 2 else np.nan,
            "kurtosis": stats.kurtosis(s, bias=False) if s.shape[0] > 3 else np.nan,
        }
    table = pd.DataFrame(rows).T
    return Result("describe", {"describe": table}, table.round(3).to_string(),
                  table=table)


def freq(df, column, sort=True):
    """Frequency table for one variable: count, percent, cumulative percent."""
    s = df[column].dropna()
    counts = s.value_counts(sort=sort)
    pct = 100 * counts / counts.sum()
    table = pd.DataFrame({"count": counts, "percent": pct,
                          "cum_percent": pct.cumsum()})
    table.index.name = column
    summary = (f"Frequencies: {column} (n = {int(counts.sum())})\n"
               + table.round(2).to_string())
    return Result("freq", {"freq": table, "column": column}, summary, table=table)


def corr_matrix(df, columns=None, method="pearson"):
    """Correlation matrix with p-values and APA significance stars (apaTables style).

    method: 'pearson' or 'spearman'. Returns r, p, and n matrices plus a
    display table with stars (* p<.05, ** p<.01, *** p<.001).
    """
    data = (df if columns is None else df[columns]).select_dtypes(include="number")
    cols = list(data.columns)
    k = len(cols)
    r = pd.DataFrame(np.eye(k), index=cols, columns=cols)
    p = pd.DataFrame(np.zeros((k, k)), index=cols, columns=cols)
    func = stats.pearsonr if method == "pearson" else stats.spearmanr
    for i in range(k):
        for j in range(i + 1, k):
            pair = data[[cols[i], cols[j]]].dropna()
            rv, pv = func(pair.iloc[:, 0], pair.iloc[:, 1])
            r.iloc[i, j] = r.iloc[j, i] = rv
            p.iloc[i, j] = p.iloc[j, i] = pv
    disp = r.copy().astype(object)
    for i in range(k):
        for j in range(k):
            if i == j:
                disp.iloc[i, j] = "1"
            else:
                disp.iloc[i, j] = f"{r.iloc[i, j]:.2f}{_stars(p.iloc[i, j])}"
    summary = (f"Correlation matrix ({method})\n" + disp.to_string()
               + "\n* p<.05  ** p<.01  *** p<.001")
    return Result("corr_matrix",
                  {"r": r, "p": p, "method": method, "display": disp},
                  summary, table=disp)


def _stars(p):
    return "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""


def _normal(s):
    """Shapiro-Wilk normality check; True if p > .05 (within Shapiro's range)."""
    s = s.dropna()
    if s.shape[0] < 3 or s.shape[0] > 5000:
        return True
    try:
        return stats.shapiro(s).pvalue > 0.05
    except Exception:
        return True


def table1(df, group, columns=None, conf=0.95):
    """Group-comparison 'Table 1' with automatic per-variable test selection.

    Continuous, normal, 2 groups -> Welch t-test; >2 groups -> one-way ANOVA.
    Continuous, non-normal -> Mann-Whitney (2) / Kruskal-Wallis (>2).
    Categorical -> chi-square (or Fisher exact for 2x2).
    """
    if columns is None:
        columns = [c for c in df.columns if c != group]
    g = df[group]
    levels = list(pd.unique(g.dropna()))
    rows = []
    for col in columns:
        s = df[col]
        if pd.api.types.is_numeric_dtype(s) and s.dropna().nunique() > 2:
            rows.append(_row_continuous(s, g, levels))
        else:
            rows.extend(_rows_categorical(col, s, g, levels))
    table = pd.DataFrame(rows)
    summary = (f"Table 1 by {group} (n groups = {len(levels)})\n"
               + table.to_string(index=False))
    return Result("table1", {"table1": table, "group": group, "levels": levels},
                  summary, table=table)


def _fmt_p(p):
    if p != p:
        return "—"
    return "<.001" if p < 0.001 else f"{p:.3f}"


def _row_continuous(s, g, levels):
    groups = [s[g == lv].dropna() for lv in levels]
    normal = all(_normal(x) for x in groups)
    if normal:
        cells = {str(lv): f"{x.mean():.2f} ({x.std(ddof=1):.2f})"
                 for lv, x in zip(levels, groups)}
        if len(levels) == 2:
            stat, p = stats.ttest_ind(groups[0], groups[1], equal_var=False)
            test = "Welch t-test"
        else:
            stat, p = stats.f_oneway(*groups)
            test = "ANOVA"
    else:
        cells = {str(lv): f"{x.median():.2f} [{x.quantile(.25):.2f}, {x.quantile(.75):.2f}]"
                 for lv, x in zip(levels, groups)}
        if len(levels) == 2:
            stat, p = stats.mannwhitneyu(groups[0], groups[1])
            test = "Mann-Whitney"
        else:
            stat, p = stats.kruskal(*groups)
            test = "Kruskal-Wallis"
    row = {"variable": s.name, "level": ""}
    row.update(cells)
    row["test"] = test
    row["p"] = _fmt_p(p)
    return row


def _rows_categorical(col, s, g, levels):
    ct = pd.crosstab(s, g).reindex(columns=levels, fill_value=0)
    if ct.shape[0] == 2 and ct.shape[1] == 2:
        _, p = stats.fisher_exact(ct.values)
        test = "Fisher exact"
    else:
        _, p, _, _ = stats.chi2_contingency(ct.values)
        test = "Chi-square"
    colsum = ct.sum(axis=0)
    rows, first = [], True
    for cat in ct.index:
        cells = {str(lv): f"{ct.loc[cat, lv]} ({100*ct.loc[cat, lv]/colsum[lv]:.1f}%)"
                 for lv in levels}
        row = {"variable": col if first else "", "level": str(cat)}
        row.update(cells)
        row["test"] = test if first else ""
        row["p"] = _fmt_p(p) if first else ""
        rows.append(row)
        first = False
    return rows
