# psymetrics

Reliability, factor analysis and SEM for psychologists, with an R-like
functional API. Part of the **ANOVA Methods** family (psystats, psymetrics,
psyreport).

Free and open (MIT). Results print R-style summaries and render to APA-7 through
`psyreport.report()`.

## Install

```bash
pip install psymetrics
```

## What's inside

Reliability — `alpha` (Cronbach's alpha with the Feldt confidence interval,
corrected item-total correlations, alpha-if-dropped, reverse keying), like
`psych::alpha`.

Factorability — `kmo` (Kaiser-Meyer-Olkin, overall and per item) and `bartlett`
(test of sphericity).

Exploratory factor analysis — `efa` with selectable estimator (`minres`, `ml`,
`principal`) and rotation (`varimax`, `promax`, `oblimin`, `quartimax`, ...);
returns loadings, communalities, eigenvalues, variance explained, and the factor
correlation matrix for oblique rotations.

Confirmatory factor analysis and SEM — `cfa` using **lavaan-style syntax**;
returns standardized loadings and the usual fit indices (χ², df, p, CFI, TLI,
RMSEA).

## Example

Using the MAPFRE teaching dataset bundled with `psystats` (Beck Depression
Inventory, 21 items):

```python
from psystats import load_mapfre
from psymetrics import alpha, kmo, efa, cfa

df = load_mapfre().dropna(subset=[f"bdi_{i}" for i in range(1, 22)])
bdi = df[[f"bdi_{i}" for i in range(1, 22)]]

print(alpha(bdi))                   # like psych::alpha  (raw_alpha ≈ .90)
print(kmo(bdi))                     # sampling adequacy
print(efa(bdi, 3, method="minres", rotation="promax"))

model = "depression =~ " + " + ".join(f"bdi_{i}" for i in range(1, 8))
print(cfa(model, df))               # lavaan-style CFA
```

EFA is validated against `factor_analyzer` and CFA fit indices against `semopy`.

> Note: `factor_analyzer` (0.5.x) requires `scikit-learn < 1.6`; this pin is
> declared as a dependency so `efa` works out of the box.
