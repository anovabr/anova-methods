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

---

## Contents

- [Installation](#installation)
- [The example dataset](#dataset)
- [**psystats** — statistics and biostatistics](#psystats)
  - [Goal](#psystats-goal) · [Functions](#psystats-functions) · [Examples](#psystats-examples)
- [**psymetrics** — reliability and latent variables](#psymetrics)
  - [Goal](#psymetrics-goal) · [Functions](#psymetrics-functions) · [Examples](#psymetrics-examples)
- [**psyreport** — APA-7 reporting](#psyreport)
  - [Goal](#psyreport-goal) · [Functions](#psyreport-functions) · [Examples](#psyreport-examples)
- [Documentation](#documentation)
- [Citing](#citing)
- [Validation](#validation)
- [Contributing](#contributing)
- [Development](#development)

---

<a id="installation"></a>

## Installation

```bash
pip install psystats psymetrics psyreport
```

Confirmatory factor analysis (`psymetrics.cfa`) uses `semopy`, kept as an
optional extra so the core installs cleanly everywhere:

```bash
pip install "psymetrics[sem]"
```

Requires Python 3.10 or newer.

<a id="dataset"></a>

## The example dataset

A real teaching dataset ships inside `psystats`, so every example on this page
runs as written with no download. It holds responses from 1,957 undergraduates
in Spain, Portugal, and Brazil (Afonso Junior et al., 2020): the Beck Depression
Inventory (`bdi_1`–`bdi_21`, `bdi_sum`, `bdi_class`), the Beck Anxiety Inventory
(`bai_*`), cyber-victimization, cyber-aggression, and emotion-regulation scales,
plus demographics (`country`, `sex`, `age`).

```python
from psystats import load_mapfre

df = load_mapfre()
df.shape          # (1957, 94)
```

Every function in all three packages returns a result object that prints an
R-style summary, exposes its raw numbers on `.values` and its table on
`.table`, and can be handed to `psyreport.report()` for APA-7 text.

---

<a id="psystats"></a>

## psystats — statistics and biostatistics

<a id="psystats-goal"></a>

### Goal

Cover the analyses that appear in most quantitative psychology papers, from a
data frame to a reportable table in one call. It handles descriptive and group
comparison tables, the common inferential tests with their effect sizes,
linear and logistic regression, and the epidemiological risk measures used in
risk-factor work. R analogues: `arsenal`, `tableone`, `epitools`, `apaTables`.

<a id="psystats-functions"></a>

### Functions

Each function links to a runnable example with real output.

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

<a id="psystats-examples"></a>

### Examples

**A Table 1, with the test chosen automatically per variable.** Continuous and
normal gets a Welch t test or ANOVA, continuous and skewed gets Mann-Whitney or
Kruskal-Wallis, categorical gets chi-square or Fisher's exact.

```python
from psystats import load_mapfre, table1

df = load_mapfre()
print(table1(df, group="country", columns=["age", "sex", "bdi_sum", "bai_sum"]))
```

```text
Table 1 by country (n groups = 3)
variable level                SPAIN             PORTUGAL               BRAZIL           test     p
     age       21.00 [20.00, 23.00] 20.00 [19.00, 22.00] 21.00 [20.00, 23.00] Kruskal-Wallis <.001
     sex     F          825 (68.2%)          223 (52.3%)          166 (52.7%)     Chi-square <.001
             M          384 (31.8%)          203 (47.7%)          149 (47.3%)
 bdi_sum         7.00 [3.00, 12.00]   7.00 [4.00, 12.00]   9.50 [5.00, 15.00] Kruskal-Wallis <.001
 bai_sum         6.00 [3.00, 12.00]   5.00 [2.00, 11.00]   6.00 [3.00, 12.00] Kruskal-Wallis 0.056
```

> **Tip:** always pass `columns=`. Without it every remaining column is
> compared, which on this dataset means all 93 of them.

**Linear regression**, with standardized betas alongside the raw coefficients.

```python
from psystats import linreg

print(linreg(df, outcome="bdi_sum", predictors=["bai_sum", "age"]))
```

```text
Linear regression: bdi_sum ~ bai_sum + age
  R^2 = 0.364, adj R^2 = 0.363, F(2, 1918) = 549.056, p = 2.896e-189, N = 1921

             b     se  ci_low  ci_high   beta       t      p
const    4.008  0.820   2.399    5.617  0.000   4.885  0.000
bai_sum  0.579  0.017   0.544    0.613  0.604  33.123  0.000
age      0.015  0.037  -0.057    0.087  0.008   0.418  0.676
```

**Risk factors.** Is high anxiety associated with a raised risk of depression?

```python
from psystats import riskratio

df["depressed"] = (df["bdi_sum"] >= 14).astype(int)
df["high_anxiety"] = (df["bai_sum"] >= 16).astype(int)

print(riskratio(df, exposure="high_anxiety", outcome="depressed",
                exposed=1, positive=1))
```

```text
Risk ratio (1 vs 0, outcome=1)
  RR = 4.232, 95% CI [3.651, 4.904], p = 0.0000
```

All 13 functions are documented with examples in
[**psystats by example**](packages/psystats/EXAMPLES.md).

---

<a id="psymetrics"></a>

## psymetrics — reliability and latent variables

<a id="psymetrics-goal"></a>

### Goal

Cover scale construction and validation: how reliable a set of items is,
whether the data are suitable for factoring, what factor structure they show,
and whether a hypothesised structure fits. R analogues: `psych`, `lavaan`.

<a id="psymetrics-functions"></a>

### Functions

| Function | What it gives you | R analogue |
|---|---|---|
| `alpha(data, keys=None)` | Cronbach's alpha, Feldt CI, mean inter-item r, corrected item-total r, alpha if dropped | `psych::alpha` |
| `kmo(data)` | Kaiser-Meyer-Olkin sampling adequacy, overall and per item | `psych::KMO` |
| `bartlett(data)` | Bartlett's test of sphericity | `psych::cortest.bartlett` |
| `efa(data, n_factors, method, rotation)` | exploratory factor analysis, selectable estimator and rotation | `psych::fa` |
| `cfa(model, data, standardized=True)` | confirmatory factor analysis and SEM from lavaan syntax, with fit indices | `lavaan::cfa` |

<a id="psymetrics-examples"></a>

### Examples

**Reliability** of the 21 BDI items, with `keys` available to reverse-score.

```python
from psystats import load_mapfre
from psymetrics import alpha

df = load_mapfre()
bdi = df[[f"bdi_{i}" for i in range(1, 22)]]

a = alpha(bdi)
a.values["raw_alpha"]        # 0.895
a.table.head()               # r_item_total, alpha_if_dropped, mean, sd per item
```

**Is the correlation matrix factorable?** Run both checks before an EFA.

```python
from psymetrics import kmo, bartlett

print(f"overall KMO = {kmo(bdi).values['overall']:.3f}")
print(bartlett(bdi))
```

```text
overall KMO = 0.942
Bartlett's test of sphericity
  chi2 = 11585.607, p = 0
```

**Exploratory factor analysis**, here two factors on the first eight items.

```python
from psymetrics import efa

print(efa(bdi[[f"bdi_{i}" for i in range(1, 9)]], n_factors=2))
```

```text
Exploratory factor analysis (minres, rotation=promax), 2 factors

Loadings:
          F1     F2
bdi_1 -0.076  1.045
bdi_2  0.480  0.069
bdi_3  0.697 -0.044
bdi_4  0.433  0.159
bdi_5  0.645 -0.083
bdi_6  0.402  0.089
bdi_7  0.646  0.065
bdi_8  0.596 -0.067

Variance explained:
    ss_loadings  prop_var  cum_var
F1        2.260     0.283    0.283
F2        1.147     0.143    0.426
```

**Confirmatory factor analysis** takes lavaan model syntax unchanged, so a
specification moves over from R as is. Requires the `sem` extra
(`pip install "psymetrics[sem]"`).

```python
from psymetrics import cfa

model = """
visual  =~ x1 + x2 + x3
textual =~ x4 + x5 + x6
speed   =~ x7 + x8 + x9
"""
fit = cfa(model, data)
fit.values["fit"]        # chi2, df, cfi, tli, rmsea
fit.values["loadings"]   # standardized loadings
```

---

<a id="psyreport"></a>

## psyreport — APA-7 reporting

<a id="psyreport-goal"></a>

### Goal

Turn a result from either sibling package into something you can paste into a
manuscript: an APA-7 sentence, a LaTeX table, or a Word document. Reporting is
kept separate from computation, so the same result feeds all three without
being recomputed. R analogues: `apaTables`, `report`.

<a id="psyreport-functions"></a>

### Functions

| Function | What it gives you |
|---|---|
| `report(result)` | APA-7 sentence for a result |
| `to_latex(result, caption=None, label=None)` | LaTeX table, `booktabs` style |
| `to_docx(result, path, caption=None)` | APA-style Word document; returns the path |

`report()` dispatches on the result's `kind` tag, so it renders results without
importing the package that produced them. It covers 15 result kinds: everything
`psystats` emits, and all of `psymetrics` except the `kmo` and `bartlett`
factorability checks.

<a id="psyreport-examples"></a>

### Examples

**An APA-7 sentence** from any supported result.

```python
from psystats import load_mapfre, ttest
from psyreport import report

df = load_mapfre()
print(report(ttest(df, dv="bdi_sum", group="sex")))
```

```text
t(1540.0) = -2.52, p = .012, d = -.12.
```

**A LaTeX table** ready to drop into a manuscript.

```python
from psystats import corr_matrix
from psyreport import to_latex

cm = corr_matrix(df, columns=["age", "bdi_sum", "bai_sum"])
print(to_latex(cm, caption="Correlations among study variables"))
```

```text
\begin{table}[htbp]
\centering
\caption{Correlations among study variables}
\begin{tabular}{llll}
\toprule
 & age & bdi\_sum & bai\_sum \\
\midrule
age & 1 & -0.02 & -0.04 \\
bdi\_sum & -0.02 & 1 & 0.60*** \\
bai\_sum & -0.04 & 0.60*** & 1 \\
\bottomrule
\end{tabular}
\end{table}
```

**A Word document**, for journals that want `.docx`.

```python
from psyreport import to_docx

to_docx(cm, "table1.docx", caption="Correlations among study variables")
```

---

<a id="documentation"></a>

## Documentation

- [**Documentation site**](https://anovabr.github.io/anova-methods/) — the
  landing page, with all 21 functions as collapsible entries whose descriptions
  are generated from the packages themselves. Rebuilt on every push, and stamped
  with the date it was last built.
- [**psystats by example**](packages/psystats/EXAMPLES.md) — every public
  function with a runnable example. The file is generated by executing each
  block and capturing its output, so the results shown in it are produced by
  the code rather than transcribed.
- [**The paper**](paper/paper.md) ([PDF](paper/paper.pdf)) — the manuscript
  describing all three packages, prepared for the Journal of Open Source
  Software.
- [`CHANGELOG.md`](CHANGELOG.md) — what changed in each version.

<a id="citing"></a>

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

<a id="validation"></a>

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

<a id="contributing"></a>

## Contributing

Bug reports, questions, and pull requests are welcome — see
[`CONTRIBUTING.md`](CONTRIBUTING.md). Reports that a statistic disagrees with an
established reference are especially useful; include the value you expected and
where it comes from.

<a id="development"></a>

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
