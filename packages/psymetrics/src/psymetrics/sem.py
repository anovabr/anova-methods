"""Confirmatory factor analysis and structural equation modeling (semopy).

Uses lavaan-style model syntax so users coming from R read it unchanged, e.g.::

    model = '''
    visual  =~ x1 + x2 + x3
    textual =~ x4 + x5 + x6
    speed   =~ x7 + x8 + x9
    '''
    fit = cfa(model, df)
"""
from __future__ import annotations

import pandas as pd

from .result import Result


def _import_semopy():
    try:
        import semopy
        return semopy
    except ImportError as e:  # pragma: no cover - exercised via install extras
        raise ImportError(
            "cfa() requires semopy, which is an optional dependency.\n"
            "Install it with:  pip install psymetrics[sem]\n"
            "(or:  pip install semopy). If the build fails on newer setuptools, "
            "use:  SETUPTOOLS_USE_DISTUTILS=stdlib pip install semopy"
        ) from e


# fit-index label -> list of possible column names semopy may emit
_FIT_KEYS = {
    "chi2": ["chi2", "chi-square", "chisq"],
    "df": ["DoF", "dof", "df"],
    "chi2_p": ["chi2 p-value", "p-value", "pvalue"],
    "cfi": ["CFI"],
    "tli": ["TLI"],
    "rmsea": ["RMSEA"],
    "srmr": ["SRMR"],
    "gfi": ["GFI"],
    "agfi": ["AGFI"],
    "nfi": ["NFI"],
    "aic": ["AIC"],
    "bic": ["BIC"],
}


def _pick(stats_row, names):
    for n in names:
        for col in stats_row.index:
            if str(col).strip().lower() == n.lower():
                return float(stats_row[col])
    return float("nan")


def cfa(model, data, standardized=True):
    """Fit a confirmatory factor / structural model from lavaan-style syntax.

    Returns the parameter table (unstandardized and standardized estimates,
    SE, z, p) and the common fit indices: chi2, df, p, CFI, TLI, RMSEA, SRMR,
    plus AIC/BIC.
    """
    semopy = _import_semopy()
    full = pd.DataFrame(data)
    m = semopy.Model(model)
    # drop incomplete rows using only the model's observed variables, so an
    # unrelated column with missing data does not change the analysis N
    obs = [v for v in m.vars["observed"] if v in full.columns]
    df = full[obs].apply(pd.to_numeric, errors="coerce").dropna(axis=0, how="any")
    m.fit(df)
    params = m.inspect(std_est=standardized)
    stats_df = semopy.calc_stats(m)
    row = stats_df.iloc[0]
    fit = {k: _pick(row, names) for k, names in _FIT_KEYS.items()}

    # standardized loadings only (measurement paths)
    est_col = "Est. Std" if "Est. Std" in params.columns else "Estimate"
    load_mask = params["op"].isin(["~", "=~"])
    loadings = params[load_mask].copy()

    values = {"params": params, "fit": fit, "loadings": loadings,
              "est_col": est_col, "model": model}

    def f(x, dec=3):
        return "—" if x != x else f"{x:.{dec}f}"  # NaN-safe

    fit_line = (f"chi2({fit['df']:.0f}) = {f(fit['chi2'])}, "
                f"p = {f(fit['chi2_p'], 4)}; CFI = {f(fit['cfi'])}, "
                f"TLI = {f(fit['tli'])}, RMSEA = {f(fit['rmsea'])}, "
                f"SRMR = {f(fit['srmr'])}")
    summary = ("Confirmatory factor analysis / SEM (semopy)\n"
               f"  {fit_line}\n\n"
               + params.round(3).to_string(index=False))
    return Result("cfa", values, summary, table=params)
