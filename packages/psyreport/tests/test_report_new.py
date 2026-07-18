"""APA rendering of the new psystats result types."""
import numpy as np
import pandas as pd
import pytest

from psystats import (ttest, anova, chisq, corr_matrix, freq, linreg, logreg,
                      attributable_risk, describe)
from psyreport import report


@pytest.fixture
def df():
    rng = np.random.default_rng(30)
    n = 150
    return pd.DataFrame({
        "score": np.concatenate([rng.normal(10, 2, 75), rng.normal(12, 2, 75)]),
        "grp": ["A"] * 75 + ["B"] * 75,
        "x": rng.normal(size=n),
    })


def test_ttest_apa(df):
    s = report(ttest(df, "score", "grp"))
    assert s.startswith("t(") and "d = " in s and s.endswith(".")


def test_anova_apa(df):
    df2 = pd.concat([df, pd.DataFrame({"score": [9, 10, 11], "grp": ["C"]*3,
                                       "x": [0, 0, 0]})], ignore_index=True)
    s = report(anova(df2, "score", "grp"))
    assert s.startswith("F(") and "η²" in s


def test_chisq_apa(df):
    df["cat"] = np.where(df["x"] > 0, "hi", "lo")
    s = report(chisq(df, "grp", "cat"))
    assert s.startswith("χ²(") and "Cramér's V" in s


def test_attributable_risk_apa():
    rows = ([(1, 1)] * 30 + [(1, 0)] * 70 + [(0, 1)] * 10 + [(0, 0)] * 90)
    d = pd.DataFrame(rows, columns=["e", "o"])
    s = report(attributable_risk(d, "e", "o", exposed=1, positive=1))
    assert "attributable risk" in s and "number needed to treat" in s


def test_linreg_apa(df):
    df["y"] = 2 * df["x"] + np.random.default_rng(1).normal(size=len(df))
    s = report(linreg(df, "y", ["x"]))
    assert "R² =" in s and "β =" in s


def test_logreg_apa(df):
    rng = np.random.default_rng(5)
    df["bin"] = (rng.uniform(size=len(df)) < 0.5).astype(int)
    s = report(logreg(df, "bin", ["x"]))
    assert "OR =" in s and "pseudo-R²" in s


def test_corr_and_freq_and_describe_apa(df):
    assert "Correlations" in report(corr_matrix(df, ["score", "x"]))
    assert "Frequency" in report(freq(df, "grp"))
    assert "Descriptive" in report(describe(df, ["score", "x"]))
