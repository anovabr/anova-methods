# psystats

Basic statistics and biostatistics for psychologists, with an R-like functional
API. Part of the **ANOVA Methods** family (psystats, psymetrics, psyreport).

Free and open (MIT). Every function returns a result object that prints an
R-style summary and can be handed to `psyreport.report()` for APA-7 output.

## Install

```bash
pip install psystats
```

## What's inside

Descriptives and tables — `describe`, `freq`, `corr_matrix` (correlation matrix
with significance stars), and `table1` (group comparison with automatic test
selection by variable type and distribution).

Inferential tests with effect sizes — `ttest` (Cohen's d), `anova` (η² and ω²),
`chisq` (Cramér's V).

Regression — `linreg` (OLS with standardized betas, R²/adjusted R², F test) and
`logreg` (odds ratios with confidence intervals, McFadden pseudo-R²).

Risk factors — `riskratio`, `oddsratio`, and `attributable_risk` (risk
difference with CI, attributable risk percent, population attributable risk and
PAR%, number needed to treat).

## Example

The package ships a real teaching dataset — depression and anxiety symptoms in
1,957 undergraduate students from Spain, Portugal, and Brazil (Afonso Junior et
al., 2020, https://doi.org/10.1590/0102.3772e36412) — so every example runs as-is:

```python
from psystats import load_mapfre, table1, anova, corr_matrix, linreg

df = load_mapfre()

print(table1(df, group="country",                # auto test per variable
             columns=["age", "sex", "bdi_sum", "bai_sum"]))
print(anova(df, "bdi_sum", "country"))           # depression across countries
print(corr_matrix(df, ["age", "bdi_sum", "bai_sum"]))
print(linreg(df, "bdi_sum", ["age", "bai_sum"])) # predict depression score
```

All estimates are validated in the test suite against `scipy` and `statsmodels`.
