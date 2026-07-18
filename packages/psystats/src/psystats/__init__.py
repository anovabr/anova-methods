"""psystats: basic statistics and biostatistics for psychologists (ANOVA Methods)."""
from .descriptives import describe, freq, corr_matrix, table1
from .inference import ttest, anova, chisq
from .regression import linreg, logreg
from .biostats import riskratio, oddsratio, attributable_risk
from .datasets import load_mapfre

__all__ = [
    "describe", "freq", "corr_matrix", "table1",
    "ttest", "anova", "chisq",
    "linreg", "logreg",
    "riskratio", "oddsratio", "attributable_risk",
    "load_mapfre",
]
__version__ = "0.1.1"
