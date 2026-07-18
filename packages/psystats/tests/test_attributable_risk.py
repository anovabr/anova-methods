"""Attributable-risk family checked against hand computation."""
import pandas as pd
import pytest

from psystats import attributable_risk


def _make_df(a, b, c, d):
    rows = ([(1, 1)] * a + [(1, 0)] * b + [(0, 1)] * c + [(0, 0)] * d)
    return pd.DataFrame(rows, columns=["exp", "out"])


def test_attributable_risk_hand_values():
    a, b, c, d = 30, 70, 10, 90
    df = _make_df(a, b, c, d)
    r = attributable_risk(df, "exp", "out", exposed=1, positive=1)
    re, ru = a / (a + b), c / (c + d)          # 0.30, 0.10
    rt = (a + c) / (a + b + c + d)             # 40/200 = 0.20
    assert r.values["risk_exposed"] == pytest.approx(re)
    assert r.values["risk_unexposed"] == pytest.approx(ru)
    assert r.values["ar"] == pytest.approx(re - ru)          # 0.20
    assert r.values["arp"] == pytest.approx((re - ru) / re)  # 0.6667
    assert r.values["par"] == pytest.approx(rt - ru)         # 0.10
    assert r.values["parp"] == pytest.approx((rt - ru) / rt) # 0.50
    assert r.values["nnt"] == pytest.approx(1 / (re - ru))   # 5.0


def test_attributable_risk_ci_brackets_point():
    df = _make_df(40, 60, 20, 80)
    r = attributable_risk(df, "exp", "out", exposed=1, positive=1)
    assert r.values["ci_low"] < r.values["ar"] < r.values["ci_high"]
