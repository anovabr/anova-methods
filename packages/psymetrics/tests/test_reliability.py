"""Validate Cronbach's alpha against closed-form identities and a fixed reference."""
import numpy as np
import pandas as pd
import pytest

from psymetrics import alpha


def test_standardized_alpha_two_item_identity():
    """For 2 standardized items with correlation r, std alpha = 2r/(1+r)."""
    rng = np.random.default_rng(1)
    n = 4000
    z = rng.normal(size=n)
    e1, e2 = rng.normal(size=n), rng.normal(size=n)
    # build two items sharing common factor z
    x1 = z + e1
    x2 = z + e2
    df = pd.DataFrame({"i1": x1, "i2": x2})
    r = df.corr().iloc[0, 1]
    expected_std = 2 * r / (1 + r)
    res = alpha(df)
    assert res.values["std_alpha"] == pytest.approx(expected_std, rel=1e-9)


def test_raw_alpha_covariance_formula():
    """Cross-check raw alpha via the covariance-matrix form: k/(k-1)*(1 - trC/sumC)."""
    rng = np.random.default_rng(7)
    data = rng.normal(size=(200, 5)) + rng.normal(size=(200, 1))
    df = pd.DataFrame(data, columns=[f"i{j}" for j in range(5)])
    C = np.cov(df.values, rowvar=False, ddof=1)
    k = 5
    expected = k / (k - 1) * (1 - np.trace(C) / C.sum())
    res = alpha(df)
    assert res.values["raw_alpha"] == pytest.approx(expected, rel=1e-9)


def test_alpha_if_dropped_and_item_total_present():
    rng = np.random.default_rng(3)
    df = pd.DataFrame(rng.normal(size=(150, 4)) + rng.normal(size=(150, 1)),
                      columns=list("abcd"))
    res = alpha(df)
    t = res.table
    assert set(["r_item_total", "alpha_if_dropped"]).issubset(t.columns)
    assert t["r_item_total"].notna().all()
    # dropping one item recomputes alpha on the remaining 3
    a_wo_a = alpha(df[["b", "c", "d"]]).values["raw_alpha"]
    assert t.loc["a", "alpha_if_dropped"] == pytest.approx(a_wo_a, rel=1e-9)


def test_feldt_ci_brackets_alpha():
    rng = np.random.default_rng(5)
    df = pd.DataFrame(rng.normal(size=(100, 6)) + rng.normal(size=(100, 1)))
    res = alpha(df)
    assert res.values["ci_low"] < res.values["raw_alpha"] < res.values["ci_high"]


def test_reverse_keying():
    rng = np.random.default_rng(9)
    common = rng.normal(size=(300, 1))
    df = pd.DataFrame(np.hstack([common + rng.normal(size=(300, 2)) * .5,
                                 -common + rng.normal(size=(300, 1)) * .5]),
                      columns=["i1", "i2", "i3r"])
    low = alpha(df).values["raw_alpha"]
    high = alpha(df, keys=[1, 1, -1]).values["raw_alpha"]
    assert high > low  # correcting the reversed item raises reliability
