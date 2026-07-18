"""Regression validated against statsmodels directly and against known betas."""
import numpy as np
import pandas as pd
import pytest
import statsmodels.api as sm

from psystats import linreg, logreg


@pytest.fixture
def reg_df():
    rng = np.random.default_rng(21)
    n = 300
    x1 = rng.normal(0, 1, n)
    x2 = rng.normal(0, 1, n)
    y = 1.5 + 2.0 * x1 - 1.0 * x2 + rng.normal(0, 1, n)
    return pd.DataFrame({"y": y, "x1": x1, "x2": x2})


def test_linreg_matches_statsmodels(reg_df):
    r = linreg(reg_df, "y", ["x1", "x2"])
    X = sm.add_constant(reg_df[["x1", "x2"]].astype(float))
    m = sm.OLS(reg_df["y"], X).fit()
    assert r.values["r2"] == pytest.approx(m.rsquared)
    for name in ["const", "x1", "x2"]:
        assert r.values["coefs"].loc[name, "b"] == pytest.approx(m.params[name])
        assert r.values["coefs"].loc[name, "p"] == pytest.approx(m.pvalues[name])


def test_linreg_standardized_beta(reg_df):
    r = linreg(reg_df, "y", ["x1", "x2"])
    b = r.values["coefs"].loc["x1", "b"]
    beta = b * reg_df["x1"].std(ddof=1) / reg_df["y"].std(ddof=1)
    assert r.values["coefs"].loc["x1", "beta"] == pytest.approx(beta)


def test_logreg_matches_statsmodels():
    rng = np.random.default_rng(22)
    n = 400
    x = rng.normal(0, 1, n)
    lin = -0.5 + 1.2 * x
    y = (rng.uniform(size=n) < 1 / (1 + np.exp(-lin))).astype(int)
    df = pd.DataFrame({"y": y, "x": x})
    r = logreg(df, "y", ["x"])
    X = sm.add_constant(df[["x"]].astype(float))
    m = sm.Logit(df["y"], X).fit(disp=False)
    assert r.values["coefs"].loc["x", "b"] == pytest.approx(m.params["x"])
    assert r.values["coefs"].loc["x", "or"] == pytest.approx(np.exp(m.params["x"]))
