# ANOVA METHODS

[![PyPI](https://img.shields.io/pypi/v/psystats?label=psystats)](https://pypi.org/project/psystats/)
[![PyPI](https://img.shields.io/pypi/v/psymetrics?label=psymetrics)](https://pypi.org/project/psymetrics/)
[![PyPI](https://img.shields.io/pypi/v/psyreport?label=psyreport)](https://pypi.org/project/psyreport/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Free, open packages that help psychological professionals — researchers,
students, and practitioners — analyze and report data for the most common tasks
in psychology and applied statistics.**

Take a `DataFrame` to publication-ready, APA-style output without leaving
Python. The API is deliberately R-like and functional, so users coming from R
read it at a glance.

Maintainer: Luis Anunciação, PhD — Pontifical Catholic University of Rio de
Janeiro (PUC-Rio) & University of Oregon.
ORCID [0000-0001-5303-5782](https://orcid.org/0000-0001-5303-5782) ·
Lab [labmm.org](https://labmm.org/)

## Install

```bash
pip install psystats psymetrics psyreport
```

Confirmatory factor analysis (`psymetrics.cfa`) uses `semopy`, kept as an
optional extra so the core installs cleanly everywhere:

```bash
pip install "psymetrics[sem]"
```

## Sixty second tour

A real teaching dataset ships inside `psystats` — depression and anxiety in
1,957 students from Spain, Portugal, and Brazil (Afonso Junior et al., 2020) —
so every example below runs as written, with no download.

```python
from psystats import load_mapfre, table1, anova
from psymetrics import alpha
from psyreport import report

df = load_mapfre()

# 1. Reliability of the 21 BDI items, like psych::alpha
bdi = df[[f"bdi_{i}" for i in range(1, 22)]]
print(report(alpha(bdi)))

# 2. One-way ANOVA, reported in APA style
print(report(anova(df, dv="bdi_sum", group="country")))

# 3. A Table 1, with the test chosen automatically per variable
print(table1(df, group="country", columns=["age", "sex", "bdi_sum", "bai_sum"]))
```

```text
Cronbach's α = .89, 95% CI [.89, .90], based on 21 items (N = 1905).
F(2, 1946) = 8.85, p < .001, η² = .01.

Table 1 by country (n groups = 3)
variable level                SPAIN             PORTUGAL               BRAZIL           test     p
     age       21.00 [20.00, 23.00] 20.00 [19.00, 22.00] 21.00 [20.00, 23.00] Kruskal-Wallis <.001
     sex     F          825 (68.2%)          223 (52.3%)          166 (52.7%)     Chi-square <.001
             M          384 (31.8%)          203 (47.7%)          149 (47.3%)
 bdi_sum         7.00 [3.00, 12.00]   7.00 [4.00, 12.00]   9.50 [5.00, 15.00] Kruskal-Wallis <.001
 bai_sum         6.00 [3.00, 12.00]   5.00 [2.00, 11.00]   6.00 [3.00, 12.00] Kruskal-Wallis 0.056
```

Every function returns a result object that prints an R-style summary, exposes
its raw numbers on `.values` and its table on `.table`, and can be handed to
`psyreport.report()` for APA-7 text.

> **Tip:** pass `columns=` to `table1`. Without it, every remaining column is
> compared, which on this dataset means all 93 of them.

## Function reference

### `psystats` — statistics and biostatistics

Each function is linked to a runnable example with real output.

| Function | What it gives you | R analogue |
|---|---|---|
| [`load_mapfre()`](packages/psystats/EXAMPLES.md#load_mapfre) | the bundled 1,957 student dataset | `data()` |
| [`describe(df, columns=None)`](packages/psystats/EXAMPLES.md#describe) | n, mean, sd, median, min, max, skew, kurtosis | `psych::describe` |
| [`freq(df, column)`](packages/psystats/EXAMPLES.md#freq) | count, percent, cumulative percent | `table()` |
| [`corr_matrix(df, columns, method)`](packages/psystats/EXAMPLES.md#corr_matrix) | correlation matrix with APA significance stars | `apaTables` |
| [`table1(df, group, columns)`](packages/psystats/EXAMPLES.md#table1) | group comparison, test chosen per variable | `arsenal`, `tableone` |
| [`ttest(df, dv, group)`](packages/psystats/EXAMPLES.md#ttest) | Welch or Student t test, Cohen's d | `t.test` |
| [`anova(df, dv, group)`](packages/psystats/EXAMPLES.md#anova) | one-way ANOVA, η² and ω² | `aov` |
| [`chisq(df, row, col)`](packages/psystats/EXAMPLES.md#chisq) | chi-square test, Cramér's V | `chisq.test` |
| [`linreg(df, outcome, predictors)`](packages/psystats/EXAMPLES.md#linreg) | OLS with standardized betas, R², F test | `lm` |
| [`logreg(df, outcome, predictors)`](packages/psystats/EXAMPLES.md#logreg) | logistic regression, odds ratios with CIs | `glm` |
| [`riskratio(df, exposure, outcome)`](packages/psystats/EXAMPLES.md#riskratio) | risk ratio with CI | `epitools::riskratio` |
| [`oddsratio(df, exposure, outcome)`](packages/psystats/EXAMPLES.md#oddsratio) | odds ratio with CI | `epitools::oddsratio` |
| [`attributable_risk(df, exposure, outcome)`](packages/psystats/EXAMPLES.md#attributable_risk) | risk difference, ARP, PAR, PAR%, NNT | `epitools` |

### `psymetrics` — reliability and latent variables

| Function | What it gives you | R analogue |
|---|---|---|
| `alpha(data, keys=None)` | Cronbach's alpha, Feldt CI, corrected item total r, alpha if dropped | `psych::alpha` |
| `kmo(data)` | Kaiser-Meyer-Olkin sampling adequacy, overall and per item | `psych::KMO` |
| `bartlett(data)` | Bartlett's test of sphericity | `psych::cortest.bartlett` |
| `efa(data, n_factors, method, rotation)` | exploratory factor analysis, selectable estimator and rotation | `psych::fa` |
| `cfa(model, data, standardized=True)` | confirmatory factor analysis and SEM from lavaan syntax, with fit indices | `lavaan::cfa` |

`cfa` takes lavaan model syntax unchanged, so a specification moves over from R
as is:

```python
from psymetrics import cfa

model = """
visual  =~ x1 + x2 + x3
textual =~ x4 + x5 + x6
speed   =~ x7 + x8 + x9
"""
fit = cfa(model, data)
```

### `psyreport` — APA-7 reporting

| Function | What it gives you |
|---|---|
| `report(result)` | APA-7 sentence for a result |
| `to_latex(result, caption=None, label=None)` | LaTeX table |
| `to_docx(result, path, caption=None)` | APA-style Word document |

`report()` dispatches on the result's `kind` tag, so it renders results without
importing the package that produced them. It covers 15 result kinds: everything
`psystats` emits, and all of `psymetrics` except the `kmo` and `bartlett`
factorability checks.

## Documentation

- [**psystats by example**](packages/psystats/EXAMPLES.md) — every public
  function with a runnable example. The file is generated by executing each
  block and capturing its output, so the results shown in it are produced by
  the code rather than transcribed.
- [**The paper**](paper/paper.md) ([PDF](paper/paper.pdf)) — the manuscript
  describing all three packages, prepared for the Journal of Open Source
  Software.
- [`CHANGELOG.md`](CHANGELOG.md) — what changed in each version.

## Citing

If ANOVA Methods contributes to work you publish, please cite it. GitHub renders
a **"Cite this repository"** button in the sidebar from
[`CITATION.cff`](CITATION.cff), which gives you APA and BibTeX directly.

In APA style:

> Anunciação, L. (2026). *ANOVA Methods: psystats, psymetrics, and psyreport*
> (Version 0.1.2) [Computer software]. https://github.com/anovabr/anova-methods

As BibTeX:

```bibtex
@software{anunciacao_anova_methods,
  author  = {Anunciação, Luis},
  title   = {ANOVA Methods: psystats, psymetrics, and psyreport},
  year    = {2026},
  version = {0.1.2},
  url     = {https://github.com/anovabr/anova-methods}
}
```

Releases are archived on Zenodo, which mints a permanent DOI. Once the DOI is
available, add it to the entries above and to `CITATION.cff` so citations point
at an immutable archived version rather than a moving branch. See
[`GITHUB_SETUP.md`](GITHUB_SETUP.md) for the release procedure.

Please also cite the bundled dataset when you use it in a publication:

> Afonso Junior, A., Portugal, A. C. de A., Landeira-Fernandez, J., Bullón,
> F. F., dos Santos, E. J. R., de Vilhena, J., & Anunciação, L. (2020). Sintomas
> de depressão e ansiedade em uma amostra representativa de universitários
> espanhóis, portugueses e brasileiros. *Psicologia: Teoria e Pesquisa, 36*,
> e36412. https://doi.org/10.1590/0102.3772e36412

## Validation

Estimates are checked against independent references rather than against the
packages' own output. Test statistics, confidence intervals, and regression
coefficients are compared with `scipy` and `statsmodels`, effect sizes with
closed form identities, and the fit indices from `cfa` with `semopy` computed
directly on the Holzinger and Swineford data. The suite runs on every push and
pull request.

```bash
pytest packages/
```

## Contributing

Bug reports, questions, and pull requests are welcome — see
[`CONTRIBUTING.md`](CONTRIBUTING.md). Reports that a statistic disagrees with an
established reference are especially useful; include the value you expected and
where it comes from.

## Development

Each package under `packages/` is built and published to PyPI independently.

```bash
pip install -e packages/psystats -e packages/psymetrics -e packages/psyreport
pip install pytest
pytest packages/
```

See [`PUBLISHING.md`](PUBLISHING.md) for the PyPI release steps and
[`GITHUB_SETUP.md`](GITHUB_SETUP.md) for releases, Zenodo archiving, and the
JOSS submission checklist.

License: MIT
