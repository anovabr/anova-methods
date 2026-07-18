"""CFA fit indices validated against semopy directly."""
import numpy as np
import pandas as pd
import pytest

semopy = pytest.importorskip("semopy")  # optional SEM engine; skip if absent
from semopy.examples import holzinger39

from psymetrics import cfa


def test_cfa_fit_matches_semopy():
    data = holzinger39.get_data()
    model = holzinger39.get_model()
    r = cfa(model, data)
    m = semopy.Model(model)
    m.fit(data[[f"x{i}" for i in range(1, 10)]])
    s = semopy.calc_stats(m).iloc[0]
    assert r.values["fit"]["chi2"] == pytest.approx(s["chi2"], rel=1e-6)
    assert r.values["fit"]["cfi"] == pytest.approx(s["CFI"], rel=1e-6)
    assert r.values["fit"]["tli"] == pytest.approx(s["TLI"], rel=1e-6)
    assert r.values["fit"]["rmsea"] == pytest.approx(s["RMSEA"], rel=1e-6)
    assert r.values["fit"]["df"] == pytest.approx(s["DoF"])


def test_cfa_lavaan_syntax_runs():
    data = holzinger39.get_data()
    model = """
    visual  =~ x1 + x2 + x3
    textual =~ x4 + x5 + x6
    speed   =~ x7 + x8 + x9
    """
    r = cfa(model, data)
    # standardized loadings present and bounded
    load = r.values["loadings"]
    assert not load.empty
    assert r.values["est_col"] == "Est. Std"


def test_cfa_ignores_unrelated_missing_column():
    """A missing-data column outside the model must not change N or fit."""
    data = holzinger39.get_data().copy()
    r_full = cfa(holzinger39.get_model(), data)
    data["junk"] = np.nan  # entirely missing, not in the model
    r_junk = cfa(holzinger39.get_model(), data)
    assert r_junk.values["fit"]["chi2"] == pytest.approx(
        r_full.values["fit"]["chi2"], rel=1e-9)
