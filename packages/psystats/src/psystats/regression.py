"""Regression models with an R-like API, wrapping statsmodels."""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from .result import Result


def _design(df, outcome, predictors, add_const=True):
    data = df[[outcome] + list(predictors)].dropna()
    y = data[outcome]
    X = pd.get_dummies(data[list(predictors)], drop_first=True).astype(float)
    if add_const:
        X = sm.add_constant(X)
    return y, X, data


def linreg(df, outcome, predictors, conf=0.95):
    """Ordinary least squares regression.

    Reports coefficients with CIs and p-values, standardized betas, R^2 and
    adjusted R^2, and the overall F test. Categorical predictors are
    dummy-coded (first level as reference).
    """
    y, X, data = _design(df, outcome, predictors)
    model = sm.OLS(y, X).fit()
    ci = model.conf_int(alpha=1 - conf)
    betas = _std_betas(model, X, y)
    coefs = pd.DataFrame({
        "b": model.params, "se": model.bse,
        "ci_low": ci[0], "ci_high": ci[1],
        "beta": betas, "t": model.tvalues, "p": model.pvalues,
    })
    values = {"model_type": "linear", "coefs": coefs, "r2": float(model.rsquared),
              "adj_r2": float(model.rsquared_adj), "f": float(model.fvalue),
              "f_p": float(model.f_pvalue), "df_model": int(model.df_model),
              "df_resid": int(model.df_resid), "n": int(model.nobs),
              "outcome": outcome}
    summary = (f"Linear regression: {outcome} ~ {' + '.join(predictors)}\n"
               f"  R^2 = {model.rsquared:.3f}, adj R^2 = {model.rsquared_adj:.3f}, "
               f"F({int(model.df_model)}, {int(model.df_resid)}) = "
               f"{model.fvalue:.3f}, p = {model.f_pvalue:.4g}, N = {int(model.nobs)}\n\n"
               + coefs.round(3).to_string())
    return Result("linreg", values, summary, table=coefs)


def _std_betas(model, X, y):
    """Standardized coefficients (beta): b * sd(x)/sd(y); const set to 0."""
    sy = y.std(ddof=1)
    out = {}
    for name in model.params.index:
        if name == "const":
            out[name] = 0.0
        else:
            out[name] = model.params[name] * X[name].std(ddof=1) / sy
    return pd.Series(out)


def logreg(df, outcome, predictors, conf=0.95):
    """Logistic regression.

    Reports log-odds coefficients, odds ratios with CIs, Wald p-values, and
    McFadden's pseudo-R^2. The outcome must be binary (0/1 or two levels; the
    higher level is modeled as the event).
    """
    y, X, data = _design(df, outcome, predictors)
    y = _binarize(y)
    model = sm.Logit(y, X).fit(disp=False)
    ci = model.conf_int(alpha=1 - conf)
    coefs = pd.DataFrame({
        "b": model.params, "se": model.bse,
        "or": np.exp(model.params),
        "or_ci_low": np.exp(ci[0]), "or_ci_high": np.exp(ci[1]),
        "z": model.tvalues, "p": model.pvalues,
    })
    values = {"model_type": "logistic", "coefs": coefs,
              "pseudo_r2": float(model.prsquared), "llf": float(model.llf),
              "n": int(model.nobs), "outcome": outcome}
    summary = (f"Logistic regression: {outcome} ~ {' + '.join(predictors)}\n"
               f"  McFadden pseudo-R^2 = {model.prsquared:.3f}, "
               f"N = {int(model.nobs)}\n\n" + coefs.round(3).to_string())
    return Result("logreg", values, summary, table=coefs)


def _binarize(y):
    levels = sorted(pd.unique(y))
    if len(levels) != 2:
        raise ValueError("logreg outcome must be binary")
    return (y == levels[-1]).astype(int)
