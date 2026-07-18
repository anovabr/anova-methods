"""Inferential tests validated against scipy and closed-form effect sizes."""
import numpy as np
import pandas as pd
import pytest
from scipy import stats

from psystats import ttest, anova, chisq


@pytest.fixture
def two_group():
    rng = np.random.default_rng(11)
    a = rng.normal(10, 2, 60)
    b = rng.normal(12, 2, 60)
    return pd.DataFrame({"score": np.concatenate([a, b]),
                         "grp": ["A"] * 60 + ["B"] * 60})


def test_ttest_matches_scipy_welch(two_group):
    r = ttest(two_group, "score", "grp")
    a = two_group[two_group.grp == "A"]["score"]
    b = two_group[two_group.grp == "B"]["score"]
    t, p = stats.ttest_ind(a, b, equal_var=False)
    assert r.values["t"] == pytest.approx(t)
    assert r.values["p"] == pytest.approx(p)


def test_ttest_cohens_d_pooled(two_group):
    r = ttest(two_group, "score", "grp")
    a = two_group[two_group.grp == "A"]["score"].values
    b = two_group[two_group.grp == "B"]["score"].values
    sp = np.sqrt(((len(a)-1)*a.var(ddof=1) + (len(b)-1)*b.var(ddof=1))
                 / (len(a)+len(b)-2))
    d = (a.mean() - b.mean()) / sp
    assert r.values["cohens_d"] == pytest.approx(d)


def test_anova_matches_scipy_and_eta(two_group):
    # add a third group for a genuine one-way ANOVA
    rng = np.random.default_rng(2)
    df = pd.concat([two_group,
                    pd.DataFrame({"score": rng.normal(11, 2, 60),
                                  "grp": ["C"] * 60})], ignore_index=True)
    r = anova(df, "score", "grp")
    groups = [df[df.grp == g]["score"].values for g in ["A", "B", "C"]]
    f, p = stats.f_oneway(*groups)
    assert r.values["F"] == pytest.approx(f)
    assert r.values["p"] == pytest.approx(p)
    # eta^2 = SS_between / SS_total
    grand = np.concatenate(groups)
    ssb = sum(len(g) * (g.mean() - grand.mean())**2 for g in groups)
    sst = ((grand - grand.mean())**2).sum()
    assert r.values["eta_squared"] == pytest.approx(ssb / sst)


def test_chisq_matches_scipy_and_cramers_v():
    rng = np.random.default_rng(3)
    df = pd.DataFrame({"x": rng.choice(list("ab"), 200),
                       "y": rng.choice(list("pqr"), 200)})
    r = chisq(df, "x", "y")
    ct = pd.crosstab(df.x, df.y)
    chi2, p, dof, _ = stats.chi2_contingency(ct.values, correction=False)
    assert r.values["chi2"] == pytest.approx(chi2)
    assert r.values["df"] == dof
    n = ct.values.sum()
    v = np.sqrt(chi2 / (n * (min(ct.shape) - 1)))
    assert r.values["cramers_v"] == pytest.approx(v)
