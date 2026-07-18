"""EFA and factorability validated against factor_analyzer directly."""
import numpy as np
import pandas as pd
import pytest
from factor_analyzer import (FactorAnalyzer, calculate_kmo,
                             calculate_bartlett_sphericity)

from psymetrics import efa, kmo, bartlett


@pytest.fixture
def items():
    rng = np.random.default_rng(101)
    n = 300
    f1 = rng.normal(size=n)
    f2 = rng.normal(size=n)
    cols = {}
    for i in range(1, 4):
        cols[f"a{i}"] = f1 + rng.normal(scale=0.6, size=n)
    for i in range(1, 4):
        cols[f"b{i}"] = f2 + rng.normal(scale=0.6, size=n)
    return pd.DataFrame(cols)


def test_efa_loadings_match_factor_analyzer(items):
    r = efa(items, 2, method="minres", rotation="varimax")
    fa = FactorAnalyzer(n_factors=2, method="minres", rotation="varimax")
    fa.fit(items.values)
    np.testing.assert_allclose(r.values["loadings"].values, fa.loadings_,
                               rtol=1e-6, atol=1e-8)


def test_efa_communalities_and_variance(items):
    r = efa(items, 2, rotation="varimax")
    fa = FactorAnalyzer(n_factors=2, rotation="varimax")
    fa.fit(items.values)
    np.testing.assert_allclose(r.values["communalities"].values,
                               fa.get_communalities(), rtol=1e-6)
    # variance table columns present and cumulative is monotonic
    var = r.values["variance"]
    assert list(var.columns) == ["ss_loadings", "prop_var", "cum_var"]
    assert var["cum_var"].is_monotonic_increasing


def test_efa_oblique_returns_phi(items):
    r = efa(items, 2, rotation="promax")
    assert r.values["phi"] is not None
    assert r.values["phi"].shape == (2, 2)


def test_kmo_and_bartlett_match_reference(items):
    per, overall = calculate_kmo(items.values)
    chi2, p = calculate_bartlett_sphericity(items.values)
    assert kmo(items).values["overall"] == pytest.approx(overall)
    assert bartlett(items).values["chi2"] == pytest.approx(chi2)
    assert bartlett(items).values["p"] == pytest.approx(p)
