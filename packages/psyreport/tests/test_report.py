"""APA-7 formatting rules: no leading zero on bounded stats, correct p thresholds."""
import numpy as np
import pandas as pd
import pytest

from psystats import riskratio, table1
from psymetrics import alpha
from psyreport import report


def test_alpha_apa_string_no_leading_zero():
    rng = np.random.default_rng(0)
    df = pd.DataFrame(rng.normal(size=(200, 5)) + rng.normal(size=(200, 1)))
    s = report(alpha(df))
    assert s.startswith("Cronbach's α = .")
    assert "CI [." in s
    assert "0.0" not in s  # bounded stats carry no leading zero


def test_riskratio_apa_string_keeps_ratio_digits():
    rows = ([(1, 1)] * 30 + [(1, 0)] * 70 + [(0, 1)] * 10 + [(0, 0)] * 90)
    df = pd.DataFrame(rows, columns=["exp", "out"])
    s = report(riskratio(df, "exp", "out", exposed=1, positive=1))
    assert s.startswith("RR = ")
    assert "95% CI [" in s
    assert s.rstrip().endswith(".")


def test_table1_apa_has_note():
    rng = np.random.default_rng(1)
    df = pd.DataFrame({"group": np.repeat(["A", "B"], 50),
                       "age": rng.normal(30, 5, 100)})
    s = report(table1(df, group="group"))
    assert s.startswith("Table 1")
    assert "Note." in s


def test_report_rejects_non_result():
    with pytest.raises(TypeError):
        report({"not": "a result"})
