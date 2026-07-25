# ANOVA METHODS

[![Tests](https://github.com/anovabr/anova-methods/actions/workflows/ci.yml/badge.svg)](https://github.com/anovabr/anova-methods/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/psystats?label=psystats)](https://pypi.org/project/psystats/)
[![PyPI](https://img.shields.io/pypi/v/psymetrics?label=psymetrics)](https://pypi.org/project/psymetrics/)
[![PyPI](https://img.shields.io/pypi/v/psyreport?label=psyreport)](https://pypi.org/project/psyreport/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21566785.svg)](https://doi.org/10.5281/zenodo.21566785)

Three packages covering the statistical analyses commonly reported in
psychology: descriptive and group comparison tables, inferential tests with
effect sizes, regression, risk measures, reliability and factor analysis, and
APA-7 formatted output. The interface is functional and modelled on the
equivalent R packages.

Maintained by Luis Anunciação, PhD — Pontifical Catholic University of Rio de
Janeiro (PUC-Rio) and University of Oregon.
ORCID [0000-0001-5303-5782](https://orcid.org/0000-0001-5303-5782).
Free and open under the MIT licence.

📖 **[Documentation site](https://anovabr.github.io/anova-methods/)** — the same content as this page, with a
sticky contents rail and a light or dark theme.

## Contents

- [Installation](#installation)
- [The example dataset](#the-example-dataset)
- [A worked example](#a-worked-example)
- [Equivalents in R](#equivalents-in-r)
- [1. **psystats** — statistics and biostatistics](#psystats)
- [2. **psymetrics** — reliability and latent variables](#psymetrics)
- [3. **psyreport** — APA-7 reporting](#psyreport)
- [Validation](#validation)
- [Citing](#citing)
- [Contributing](#contributing)
- [Development](#development)

---

## Installation

The three packages are published on PyPI and can be installed together.

```bash
pip install psystats psymetrics psyreport
```

Python 3.10 or newer is required. If the `pip` command is not recognised, use
`python -m pip install …` instead.

Confirmatory factor analysis (`psymetrics.cfa`) depends on `semopy`, which is
kept as an optional extra so that the core packages install without a compiler
toolchain:

```bash
pip install "psymetrics[sem]"
```

## The example dataset

A teaching dataset is bundled inside `psystats`, so every example below runs
without any download. It contains responses from 1,957 undergraduate students
in Spain, Portugal, and Brazil on the Beck Depression Inventory (`bdi_1` to
`bdi_21`, `bdi_sum`, `bdi_class`) and the Beck Anxiety Inventory (`bai_*`),
together with cyber-victimization, cyber-aggression, and emotion-regulation
scales, and the demographics `country`, `sex`, and `age`.

```python
from psystats import load_mapfre

df = load_mapfre()
df.shape          # (1957, 94)
```

The data are described in Afonso Junior et al. (2020), *Psicologia: Teoria e
Pesquisa, 36*, e36412.

## A worked example

Every function returns a result object. Printing it gives a summary in the style
R would produce, `.values` holds the raw numbers, `.table` holds the result
table, and passing it to `psyreport.report()` gives APA-7 text.

```python
from psystats import load_mapfre, table1

df = load_mapfre()
print(table1(df, group="country", columns=["age", "sex", "bdi_sum"]))
```

```text
Table 1 by country (n groups = 3)
variable level                SPAIN             PORTUGAL               BRAZIL           test     p
     age       21.00 [20.00, 23.00] 20.00 [19.00, 22.00] 21.00 [20.00, 23.00] Kruskal-Wallis <.001
     sex     F          825 (68.2%)          223 (52.3%)          166 (52.7%)     Chi-square <.001
             M          384 (31.8%)          203 (47.7%)          149 (47.3%)                     
 bdi_sum         7.00 [3.00, 12.00]   7.00 [4.00, 12.00]   9.50 [5.00, 15.00] Kruskal-Wallis <.001
```

`table1()` selects the test per variable. Each group is screened for normality
with Shapiro-Wilk. Continuous variables are compared with a Welch t test or a
one-way ANOVA when normal, and with Mann-Whitney or Kruskal-Wallis when not;
categorical variables are compared with Fisher's exact test for a 2 × 2 table
and chi-square otherwise. Normal variables are summarised as *M (SD)*,
non-normal ones as median [Q1, Q3], and categorical ones as *n* (%) within each
group.

> [!TIP]
> Pass `columns` explicitly. When it is omitted, every remaining column is
> compared, which on this dataset means all 93 of them.

## Equivalents in R

Function and argument names follow the R packages that perform the same
analyses, so a specification written in R generally transfers with little
change.

| R | Python |
|---|---|
| `psych::alpha(bdi)` | `psymetrics.alpha(bdi)` |
| `arsenal::tableby(country ~ ., df)` | `psystats.table1(df, group="country")` |
| `epitools::riskratio(x)` | `psystats.riskratio(df, exposure=..., outcome=...)` |
| `psych::fa(items, nfactors=2)` | `psymetrics.efa(items, n_factors=2)` |
| `lavaan::cfa(model, data)` | `psymetrics.cfa(model, data)` |

---

<a id="psystats"></a>

## 1. `psystats` — statistics and biostatistics

### Goal

To cover the analyses that appear in most quantitative psychology papers: descriptive statistics and group comparison tables, the common inferential tests reported with their effect sizes, linear and logistic regression, and the epidemiological risk measures used in risk-factor work.

R analogues: `arsenal, tableone, epitools, apaTables`

### Functions (13)

Each entry is collapsed. Select one to read its full description, taken
directly from the function's documentation.

<details>
<summary><code>load_mapfre()</code> — Load the MAPFRE depression and anxiety dataset (returns a DataFrame).</summary>

A representative sample of 1,957 undergraduate students in Spain, Portugal, and Brazil, with the Beck Depression Inventory (``bdi_1``–``bdi_21``, ``bdi_sum``, ``bdi_class``), the Beck Anxiety Inventory (``bai_1``–``bai_21``, ``bai_sum``, ``bai_class``), cyber-victimization/aggression and emotion- regulation scales, and demographics (``country``, ``sex``, ``age``, ``grado``).

**Source**

Afonso Junior, A., Portugal, A. C. d. A., Landeira-Fernandez, J., Bullón, F. F., dos Santos, E. J. R., de Vilhena, J., & Anunciação, L. (2020). Sintomas de Depressão e Ansiedade em uma Amostra Representativa de Universitários Espanhóis, Portugueses e Brasileiros [Depression and anxiety symptoms in a representative sample of undergraduate students in Spain, Portugal, and Brazil]. Psicologia: Teoria e Pesquisa, 36, Article e36412. https://doi.org/10.1590/0102.3772e36412

R analogue: `data()`

</details>

<details>
<summary><code>describe(df, columns=None)</code> — Numeric descriptives per column: n, mean, sd, median, min, max, skew, kurtosis.</summary>

_No further description._

R analogue: `psych::describe`

</details>

<details>
<summary><code>freq(df, column, sort=True)</code> — Frequency table for one variable: count, percent, cumulative percent.</summary>

_No further description._

R analogue: `table()`

</details>

<details>
<summary><code>corr_matrix(df, columns=None, method='pearson')</code> — Correlation matrix with p-values and APA significance stars (apaTables style).</summary>

method: 'pearson' or 'spearman'. Returns r, p, and n matrices plus a display table with stars (* p<.05, ** p<.01, *** p<.001).

R analogue: `apaTables`

</details>

<details>
<summary><code>table1(df, group, columns=None, conf=0.95)</code> — Group-comparison 'Table 1' with automatic per-variable test selection.</summary>

Continuous, normal, 2 groups -> Welch t-test; >2 groups -> one-way ANOVA. Continuous, non-normal -> Mann-Whitney (2) / Kruskal-Wallis (>2). Categorical -> chi-square (or Fisher exact for 2x2).

R analogue: `arsenal, tableone`

</details>

<details>
<summary><code>ttest(df, dv, group=None, paired=False, equal_var=False, conf=0.95)</code> — Two-group or paired t-test with Cohen's d.</summary>

Long form: ttest(df, dv="score", group="cond"). Paired: pass group with exactly two levels and paired=True (matched by row order within each level after dropping NAs). Cohen's d uses the pooled SD (independent) or SD of differences (paired).

R analogue: `t.test`

</details>

<details>
<summary><code>anova(df, dv, group)</code> — One-way ANOVA with eta squared and omega squared.</summary>

_No further description._

R analogue: `aov`

</details>

<details>
<summary><code>chisq(df, row, col, correction=False)</code> — Chi-square test of independence with Cramer's V.</summary>

_No further description._

R analogue: `chisq.test`

</details>

<details>
<summary><code>linreg(df, outcome, predictors, conf=0.95)</code> — Ordinary least squares regression.</summary>

Reports coefficients with CIs and p-values, standardized betas, R^2 and adjusted R^2, and the overall F test. Categorical predictors are dummy-coded (first level as reference).

R analogue: `lm`

</details>

<details>
<summary><code>logreg(df, outcome, predictors, conf=0.95)</code> — Logistic regression.</summary>

Reports log-odds coefficients, odds ratios with CIs, Wald p-values, and McFadden's pseudo-R^2. The outcome must be binary (0/1 or two levels; the higher level is modeled as the event).

R analogue: `glm`

</details>

<details>
<summary><code>riskratio(df, exposure, outcome, exposed=None, positive=None, conf=0.95)</code> — Risk (incidence) ratio for a 2x2 table, epitools::riskratio style.</summary>

RR = [a/(a+b)] / [c/(c+d)]. CI by the log method (Katz).

R analogue: `epitools::riskratio`

</details>

<details>
<summary><code>oddsratio(df, exposure, outcome, exposed=None, positive=None, conf=0.95)</code> — Odds ratio for a 2x2 table, epitools::oddsratio (Wald) style.</summary>

OR = ad / bc. CI by the log method (Woolf).

R analogue: `epitools::oddsratio`

</details>

<details>
<summary><code>attributable_risk(df, exposure, outcome, exposed=None, positive=None, conf=0.95)</code> — Attributable-risk family for a 2x2 cohort table.</summary>

Reports the risk difference (attributable risk, AR = Re - Ru) with a Wald CI, the attributable risk percent among the exposed (ARP = (Re-Ru)/Re), the population attributable risk (PAR = Rt - Ru) and its percent (PAR% = (Rt-Ru)/Rt), and the number needed to treat/harm (NNT = 1/|AR|).

R analogue: `epitools`

</details>

### Examples

Linear regression. Standardized coefficients appear in the `beta` column beside the unstandardized `b`.

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

Risk measures for a 2 × 2 table. `exposed` and `positive` name the level counted as exposed and as the event.

```python
from psystats import riskratio

print(riskratio(df, exposure="high_anxiety", outcome="depressed",
                exposed=1, positive=1))
```

```text
Risk ratio (1 vs 0, outcome=1)
  RR = 4.232, 95% CI [3.651, 4.904], p = 0.0000
```


---

<a id="psymetrics"></a>

## 2. `psymetrics` — reliability and latent variables

### Goal

To cover scale construction and validation: how reliable a set of items is, whether the correlation matrix is suitable for factoring, what factor structure the items show, and whether a hypothesised structure fits the data.

R analogues: `psych, lavaan`

### Functions (5)

Each entry is collapsed. Select one to read its full description, taken
directly from the function's documentation.

<details>
<summary><code>alpha(data, keys=None, conf=0.95)</code> — Cronbach's alpha and item statistics, like psych::alpha.</summary>

**Parameters**

- `data` — DataFrame (rows = respondents, cols = items) or 2D array.
- `keys` — optional sequence of +1/-1 to reverse-score items before analysis.
- `conf` — confidence level for the Feldt (1965) interval on raw alpha.

Returns a Result with raw_alpha, std_alpha, the Feldt CI, mean inter-item correlation, and a per-item table (corrected item-total r and alpha-if-dropped).

R analogue: `psych::alpha`

</details>

<details>
<summary><code>kmo(data)</code> — Kaiser-Meyer-Olkin sampling adequacy (overall and per item).</summary>

_No further description._

R analogue: `psych::KMO`

</details>

<details>
<summary><code>bartlett(data)</code> — Bartlett's test of sphericity (H0: correlation matrix is identity).</summary>

_No further description._

R analogue: `psych::cortest.bartlett`

</details>

<details>
<summary><code>efa(data, n_factors, method='minres', rotation='promax')</code> — Exploratory factor analysis with selectable estimator and rotation.</summary>

```
method   : 'minres' (default), 'ml' (maximum likelihood), or 'principal'.
rotation : None, 'varimax', 'promax' (default), 'oblimin', 'quartimax',
           'oblimax', 'quartimin', 'equamax' — oblique rotations also return
           the factor correlation matrix (phi).
```

Returns loadings, communalities, uniquenesses, eigenvalues, and the variance explained per factor (SS loadings, proportion, cumulative).

R analogue: `psych::fa`

</details>

<details>
<summary><code>cfa(model, data, standardized=True)</code> — Fit a confirmatory factor / structural model from lavaan-style syntax.</summary>

Returns the parameter table (unstandardized and standardized estimates, SE, z, p) and the common fit indices: chi2, df, p, CFI, TLI, RMSEA, SRMR, plus AIC/BIC.

R analogue: `lavaan::cfa`

</details>

### Examples

Reliability and the two standard factorability checks, run on the 21 BDI items.

```python
from psymetrics import alpha, kmo, bartlett

bdi = df[[f"bdi_{i}" for i in range(1, 22)]]

print(f"raw alpha   = {alpha(bdi).values['raw_alpha']:.3f}")
print(f"overall KMO = {kmo(bdi).values['overall']:.3f}")
print(bartlett(bdi))
```

```text
raw alpha   = 0.895
overall KMO = 0.942
Bartlett's test of sphericity
  chi2 = 11585.607, p = 0
```

Confirmatory factor analysis. The model is written in lavaan syntax, so a specification transfers from R unchanged. This function requires the `sem` extra, and so is shown here without output.

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

## 3. `psyreport` — APA-7 reporting

### Goal

To render a result produced by either of the other two packages as APA-7 text, a LaTeX table, or a Word document. Reporting is kept separate from computation, so one result can feed all three outputs without being recomputed. Dispatch is by the result's `kind` tag, which is why psyreport renders a result without importing the package that produced it. It covers 15 result kinds: everything psystats emits, and all of psymetrics except the `kmo` and `bartlett` factorability checks.

R analogues: `apaTables, report`

### Functions (3)

Each entry is collapsed. Select one to read its full description, taken
directly from the function's documentation.

<details>
<summary><code>report(result, style='text')</code> — Return an APA-7 formatted string describing a psy result.</summary>

_No further description._

R analogue: `report`

</details>

<details>
<summary><code>to_latex(result, caption=None, label=None)</code> — Return a LaTeX table for a result that carries a table.</summary>

Falls back to a LaTeX comment with the APA sentence for inline-only results (t-test, correlations text, etc.).

R analogue: `apaTables`

</details>

<details>
<summary><code>to_docx(result, path, caption=None)</code> — Write an APA-style .docx with the result's table and note. Returns path.</summary>

Requires python-docx (imported lazily).

R analogue: `apaTables`

</details>

### Examples

APA-7 text for a t test and a one-way ANOVA.

```python
from psystats import ttest, anova
from psyreport import report

print(report(ttest(df, dv="bdi_sum", group="sex")))
print(report(anova(df, dv="bdi_sum", group="country")))
```

```text
t(1540.0) = -2.52, p = .012, d = -.12.
F(2, 1946) = 8.85, p < .001, η² = .01.
```

The same machinery exports a correlation matrix as a LaTeX table.

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


---

<a id="validation"></a>

## Validation

Estimates are checked against independent references rather than against the
packages' own output. Test statistics, confidence intervals, and regression
coefficients are compared with `scipy` and `statsmodels`, effect sizes with
closed form identities, and the fit indices returned by `cfa` with `semopy`
computed directly on the Holzinger and Swineford data. The suite of 50 tests
runs on every push and pull request.

```bash
pytest packages/
```

## Documentation

- [**Documentation site**](https://anovabr.github.io/anova-methods/) — this page with a sticky contents rail
  and a light or dark theme. Rebuilt on every push and stamped with the date it
  was last built.
- [**psystats by example**](packages/psystats/EXAMPLES.md) — every public
  function with a runnable example, generated by executing each block.
- [**The paper**](paper/paper.md) ([PDF](paper/paper.pdf)) — the manuscript
  describing all three packages.
- [`CHANGELOG.md`](CHANGELOG.md) — what changed in each version.

<a id="citing"></a>

## Citing

Citation metadata is held in [`CITATION.cff`](CITATION.cff), which GitHub
renders as a **Cite this repository** button in the sidebar, giving APA and
BibTeX entries directly. Releases are archived on Zenodo, which mints a
permanent DOI for each version, so a citation points at an immutable archive
rather than a moving branch.

> Anunciação, L. (2026). *ANOVA Methods: statistics, psychometrics, and APA
> reporting for psychology in Python* [Computer software]. Zenodo. https://doi.org/10.5281/zenodo.21566785

```bibtex
@software{anunciacao_anova_methods,
  author    = {Anunciação, Luis},
  title     = {ANOVA Methods: statistics, psychometrics, and APA reporting
               for psychology in Python},
  year      = {2026},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.21566785},
  url       = {https://doi.org/10.5281/zenodo.21566785}
}
```

The DOI above is the **concept DOI**: it always resolves to the most recent
release, so a citation does not go stale when a new version is archived. To
cite one specific version instead, use its own DOI, which for v0.1.2 is
[10.5281/zenodo.21566786](https://doi.org/10.5281/zenodo.21566786).

The bundled dataset has its own citation, which applies when it is used in a
publication.

> Afonso Junior, A., Portugal, A. C. de A., Landeira-Fernandez, J., Bullón,
> F. F., dos Santos, E. J. R., de Vilhena, J., & Anunciação, L. (2020). Sintomas
> de depressão e ansiedade em uma amostra representativa de universitários
> espanhóis, portugueses e brasileiros. *Psicologia: Teoria e Pesquisa, 36*,
> e36412. https://doi.org/10.1590/0102.3772e36412

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

<!-- This file is generated by docs/build_site.py, which also builds the
     documentation site. Edit that script rather than this file; a push
     rebuilds both. Last built 25 July 2026. -->
