"""Validate RR/OR point estimates and CIs against statsmodels Table2x2 (epitools-equivalent)."""
import numpy as np
import pandas as pd
import pytest
from statsmodels.stats.contingency_tables import Table2x2

from psystats import riskratio, oddsratio


def _make_df(a, b, c, d):
    # exposure: 1 = exposed, 0 = unexposed; outcome: 1 = positive, 0 = negative
    rows = ([(1, 1)] * a + [(1, 0)] * b + [(0, 1)] * c + [(0, 0)] * d)
    return pd.DataFrame(rows, columns=["exp", "out"])


@pytest.mark.parametrize("a,b,c,d", [(30, 70, 10, 90), (12, 5, 8, 20), (40, 60, 20, 80)])
def test_riskratio_matches_statsmodels(a, b, c, d):
    df = _make_df(a, b, c, d)
    r = riskratio(df, "exp", "out", exposed=1, positive=1)
    ref = Table2x2(np.array([[a, b], [c, d]]))
    assert r.values["rr"] == pytest.approx(ref.riskratio, rel=1e-9)
    lo, hi = ref.riskratio_confint()
    assert r.values["ci_low"] == pytest.approx(lo, rel=1e-6)
    assert r.values["ci_high"] == pytest.approx(hi, rel=1e-6)


@pytest.mark.parametrize("a,b,c,d", [(30, 70, 10, 90), (12, 5, 8, 20), (40, 60, 20, 80)])
def test_oddsratio_matches_statsmodels(a, b, c, d):
    df = _make_df(a, b, c, d)
    r = oddsratio(df, "exp", "out", exposed=1, positive=1)
    ref = Table2x2(np.array([[a, b], [c, d]]))
    assert r.values["or"] == pytest.approx(ref.oddsratio, rel=1e-9)
    lo, hi = ref.oddsratio_confint()
    assert r.values["ci_low"] == pytest.approx(lo, rel=1e-6)
    assert r.values["ci_high"] == pytest.approx(hi, rel=1e-6)


def test_oddsratio_hand_value():
    # OR = ad/bc = (30*90)/(70*10) = 3.857142857
    df = _make_df(30, 70, 10, 90)
    r = oddsratio(df, "exp", "out", exposed=1, positive=1)
    assert r.values["or"] == pytest.approx(3.857142857, rel=1e-9)
