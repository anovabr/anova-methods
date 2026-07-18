"""Bundled example datasets."""
from __future__ import annotations

from importlib.resources import files

import pandas as pd


def load_mapfre():
    """Load the MAPFRE depression and anxiety dataset (returns a DataFrame).

    A representative sample of 1,957 undergraduate students in Spain, Portugal,
    and Brazil, with the Beck Depression Inventory (``bdi_1``–``bdi_21``,
    ``bdi_sum``, ``bdi_class``), the Beck Anxiety Inventory (``bai_1``–``bai_21``,
    ``bai_sum``, ``bai_class``), cyber-victimization/aggression and emotion-
    regulation scales, and demographics (``country``, ``sex``, ``age``, ``grado``).

    Source
    ------
    Afonso Junior, A., Portugal, A. C. d. A., Landeira-Fernandez, J., Bullón,
    F. F., dos Santos, E. J. R., de Vilhena, J., & Anunciação, L. (2020).
    Sintomas de Depressão e Ansiedade em uma Amostra Representativa de
    Universitários Espanhóis, Portugueses e Brasileiros [Depression and anxiety
    symptoms in a representative sample of undergraduate students in Spain,
    Portugal, and Brazil]. Psicologia: Teoria e Pesquisa, 36, Article e36412.
    https://doi.org/10.1590/0102.3772e36412
    """
    path = files("psystats.data").joinpath("mapfre.csv")
    with path.open("r", encoding="utf-8") as fh:
        return pd.read_csv(fh)
