"""freq() and corr_matrix() checks."""
import numpy as np
import pandas as pd
import pytest
from scipy import stats

from psystats import freq, corr_matrix


def test_freq_counts_and_percent():
    df = pd.DataFrame({"g": ["a", "a", "b", "c", "c", "c"]})
    r = freq(df, "g")
    t = r.table
    assert t.loc["c", "count"] == 3
    assert t.loc["c", "percent"] == pytest.approx(50.0)
    assert t["percent"].sum() == pytest.approx(100.0)


def test_corr_matrix_matches_scipy():
    rng = np.random.default_rng(4)
    df = pd.DataFrame({"x": rng.normal(size=100)})
    df["y"] = df["x"] * 0.6 + rng.normal(size=100)
    df["z"] = rng.normal(size=100)
    r = corr_matrix(df, ["x", "y", "z"])
    rv, pv = stats.pearsonr(df["x"], df["y"])
    assert r.values["r"].loc["x", "y"] == pytest.approx(rv)
    assert r.values["p"].loc["x", "y"] == pytest.approx(pv)
    assert r.values["r"].loc["x", "x"] == pytest.approx(1.0)
