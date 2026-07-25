---
title: 'ANOVA Methods: statistics, psychometrics, and APA reporting for psychology in Python'
tags:
  - Python
  - statistics
  - psychometrics
  - psychology
  - factor analysis
  - APA reporting
authors:
  - name: Luis Anunciação
    orcid: 0000-0001-5303-5782
    affiliation: "1, 2"
affiliations:
  - name: Department of Psychology, Pontifical Catholic University of Rio de Janeiro (PUC-Rio), Brazil
    index: 1
  - name: Center on Human Development, College of Education, University of Oregon, USA
    index: 2
date: 25 July 2026
bibliography: paper.bib
---

# Summary

ANOVA Methods is a family of three Python packages covering the analyses that
appear in most quantitative psychology reports. `psystats` provides descriptive
statistics, group comparison tables, inferential tests with effect sizes,
regression, and epidemiological risk measures. `psymetrics` provides reliability
analysis, factorability checks, exploratory factor analysis, and confirmatory
factor analysis with structural equation models. `psyreport` renders the results
of the other two as APA 7 text, LaTeX tables, and Word documents.

The three packages share one convention. Every analysis returns a lightweight
result object carrying a `kind` tag, a dictionary of raw estimates, and an
optional table. Printing the object gives an R style console summary, and passing
it to `psyreport.report()` gives APA 7 prose. Dispatch happens on the `kind` tag,
so `psyreport` renders a result without importing the package that produced it.
One computation therefore feeds a console summary, a LaTeX table, and a Word
document without being recomputed.

# Statement of need

Psychologists working in R use a small set of packages that pair a concise
interface with output shaped for reporting. These include `arsenal` and
`tableone` for group comparison tables [@arsenal; @tableone], `epitools` for risk
measures [@epitools], `psych` for reliability and exploratory factor analysis
[@psych], `lavaan` for structural equation models [@rosseel2012], and `apaTables`
and `report` for formatted output [@apaTables; @report].

Python provides the estimation machinery for these analyses through `numpy`
[@harris2020], `pandas` [@mckinney2010], `scipy` [@virtanen2020], `statsmodels`
[@seabold2010], `factor_analyzer` [@factoranalyzer], and `semopy`
[@meshcheryakov2020]. Those libraries expose general purpose interfaces. Moving
from them to a reportable table takes considerable boilerplate, because the
analyst selects a test appropriate to each variable, computes the matching effect
size and confidence interval, and formats the result by hand. The workflow that
makes the R packages attractive, in which a data frame becomes an APA table in
one call, has no direct Python equivalent.

ANOVA Methods supplies that workflow. It wraps established estimators behind
verbs that mirror their R analogues, so a researcher who already knows the R
tools incurs little translation cost. `table1(df, group="country")` builds a
group comparison table and selects a test per variable,
`riskratio(df, exposure=..., outcome=...)` returns a risk ratio with its
confidence interval, and `alpha(items)` returns coefficient alpha with item level
statistics. A user coming from Python obtains effect sizes, confidence intervals,
and automatic test selection without assembling them by hand.

The intended users are researchers, students, and instructors in psychology and
allied fields who work in Python and need reportable output for routine analyses.
A documented teaching dataset ships inside `psystats`, so the examples in the
documentation run without any download. It contains responses from 1,957
undergraduate students in Spain, Portugal, and Brazil on the Beck Depression
Inventory and the Beck Anxiety Inventory, together with cyber victimization,
cyber aggression, and emotion regulation scales [@afonso2020].

# Software description

`psystats` covers four areas. Descriptives and tables are handled by `describe`,
`freq`, `corr_matrix`, which reports a correlation matrix with significance
stars, and `table1`. For each variable `table1` selects a Welch t test, a one way
analysis of variance, a Mann-Whitney test, a Kruskal-Wallis test, a χ² test, or
Fisher's exact test according to the variable type, the number of groups, and a
Shapiro-Wilk screen for normality. Inferential tests with effect sizes are
handled by `ttest`, which reports Cohen's d, `anova`, which reports η² and ω²,
and `chisq`, which reports Cramér's V. Regression is handled by `linreg`, which
reports standardized coefficients and model fit, and `logreg`, which reports odds
ratios with confidence intervals. Risk factors are handled by `riskratio`,
`oddsratio`, and `attributable_risk`, the last returning the risk difference with
its confidence interval, the attributable risk percent, the population
attributable risk and its percent, and the number needed to treat.

`psymetrics` covers reliability and latent variable models. `alpha` returns
coefficient alpha with the Feldt confidence interval, the mean inter item
correlation, and a per item table of corrected item total correlations and alpha
if dropped. `kmo` and `bartlett` provide the two standard factorability checks.
`efa` runs exploratory factor analysis with selectable estimators and rotations.
`cfa` fits confirmatory factor models and structural equation models from lavaan
style syntax, so a model specification transfers from R unchanged.

`psyreport` renders results as APA 7 text through `report`, and exports tables
through `to_latex` and `to_docx`. It currently renders 15 result types, which
covers everything `psystats` emits and all of `psymetrics` except the two
factorability checks.

# Example

```python
from psystats import load_mapfre, logreg, anova
from psymetrics import alpha
from psyreport import report

df = load_mapfre()
bdi = df[[f"bdi_{i}" for i in range(1, 22)]]
print(report(alpha(bdi)))

df["depressed"] = (df["bdi_sum"] >= 14).astype(int)
print(report(logreg(df, outcome="depressed", predictors=["bai_sum"])))
print(report(anova(df, dv="bdi_sum", group="country")))
```

```text
Cronbach's α = .89, 95% CI [.89, .90], based on 21 items (N = 1905).

Logistic regression predicting depressed.
McFadden pseudo-R² = .19, N = 1952.

bai_sum: OR = 1.15, 95% CI [1.13, 1.16], p < .001.

F(2, 1946) = 8.85, p < .001, η² = .01.
```

# Quality control

An automated test suite of 50 tests runs on every change. Estimates are checked
against independent references rather than against the packages' own internals.
Test statistics, confidence intervals, and regression coefficients are compared
with `scipy` and `statsmodels`, effect sizes are compared with closed form
identities, and the fit indices returned by `cfa` are compared with `semopy`
computed directly on the Holzinger and Swineford data. The documentation for
`psystats` is generated by executing every example against the bundled dataset,
so the output shown in it is produced by the code rather than transcribed.

# Availability

The three packages are published on PyPI and installable with
`pip install psystats psymetrics psyreport`. Confirmatory factor analysis
requires `semopy`, which is kept as an optional extra so that the core installs
without a compiler toolchain. The source is developed in one repository at
https://github.com/anovabr/anova-methods under the MIT license.

# Acknowledgements

We thank the maintainers of `numpy`, `pandas`, `scipy`, `statsmodels`,
`factor_analyzer`, and `semopy`, on which ANOVA Methods builds.

# References
