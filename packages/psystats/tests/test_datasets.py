"""The bundled MAPFRE example dataset loads and has the expected structure."""
from psystats import load_mapfre


def test_load_mapfre_shape_and_columns():
    df = load_mapfre()
    assert df.shape == (1957, 94)
    for col in ["country", "sex", "age", "bdi_sum", "bai_sum", "bdi_class"]:
        assert col in df.columns
    for i in range(1, 22):
        assert f"bdi_{i}" in df.columns
        assert f"bai_{i}" in df.columns


def test_load_mapfre_countries():
    df = load_mapfre()
    assert set(df["country"].dropna().unique()) == {"SPAIN", "PORTUGAL", "BRAZIL"}
