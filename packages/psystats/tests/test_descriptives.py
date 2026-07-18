"""Table 1 automatic test-selection and descriptives sanity checks."""
import numpy as np
import pandas as pd
import pytest
from scipy import stats

from psystats import describe, table1


@pytest.fixture
def df():
    rng = np.random.default_rng(42)
    n = 120
    grp = np.repeat(["A", "B"], n // 2)
    age = np.where(grp == "A", rng.normal(30, 5, n), rng.normal(35, 5, n))
    sex = rng.choice(["F", "M"], n)
    return pd.DataFrame({"group": grp, "age": age, "sex": sex})


def test_describe_matches_pandas(df):
    r = describe(df, ["age"])
    assert r.table.loc["age", "mean"] == pytest.approx(df["age"].mean())
    assert r.table.loc["age", "sd"] == pytest.approx(df["age"].std(ddof=1))


def test_table1_picks_ttest_for_normal_continuous(df):
    r = table1(df, group="group")
    age_row = r.table[r.table["variable"] == "age"].iloc[0]
    assert age_row["test"] == "Welch t-test"
    # p should match a direct Welch t-test
    a = df[df.group == "A"]["age"]
    b = df[df.group == "B"]["age"]
    _, p = stats.ttest_ind(a, b, equal_var=False)
    expected = "<.001" if p < 0.001 else f"{p:.3f}"
    assert age_row["p"] == expected


def test_table1_picks_chi2_or_fisher_for_categorical(df):
    r = table1(df, group="group")
    sex_first = r.table[r.table["variable"] == "sex"].iloc[0]
    assert sex_first["test"] in {"Chi-square", "Fisher exact"}
