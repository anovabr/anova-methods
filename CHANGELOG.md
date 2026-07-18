# Changelog

All three packages are versioned together during initial development.

## 0.1.1 — unreleased

### psystats
- Added `load_mapfre()`: a bundled teaching dataset of depression and anxiety
  symptoms in 1,957 undergraduates from Spain, Portugal, and Brazil (Afonso
  Junior et al., 2020, doi:10.1590/0102.3772e36412). All package examples now
  use it.

## 0.1.0

### psystats
- Descriptives: `describe`, `freq`, `corr_matrix` (with significance stars).
- `table1` group comparison with automatic test selection.
- Inferential tests with effect sizes: `ttest` (Cohen's d), `anova` (η², ω²),
  `chisq` (Cramér's V).
- Regression: `linreg` (standardized betas, R², F test), `logreg` (odds ratios,
  pseudo-R²).
- Risk factors: `riskratio`, `oddsratio`, `attributable_risk` (risk difference,
  ARP, PAR, PAR%, NNT).

### psymetrics
- `alpha`: Cronbach's alpha with Feldt CI, item-total stats, alpha-if-dropped,
  reverse keying.
- Factorability: `kmo`, `bartlett`.
- `efa`: exploratory factor analysis with selectable estimator and rotation.
- `cfa`: confirmatory factor analysis / SEM from lavaan-style syntax with fit
  indices.

### psyreport
- `report`: APA-7 text for every psy result kind.
- `to_latex`, `to_docx`: LaTeX and Word table export.

### Validation
- 50 tests validating estimates against scipy, statsmodels, factor_analyzer, and
  semopy, plus closed-form identities.
