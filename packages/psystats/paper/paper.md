---
title: 'psystats: Basic statistics and biostatistics for psychologists in Python'
tags:
  - Python
  - statistics
  - psychology
  - biostatistics
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
date: 18 July 2026
bibliography: paper.bib
---

# Summary

`psystats` is a Python package that provides the routine statistical procedures
used in psychological research through a small, R-like functional interface. It
covers descriptive statistics and grouped "Table 1" summaries with automatic
selection of the appropriate significance test, common inferential tests
reported with their effect sizes (Cohen's *d*, $\eta^2$, Cramér's *V*), linear
and logistic regression, and epidemiological risk measures (relative risk, odds
ratio, and the attributable-risk family). Every procedure returns a lightweight
result object that both prints an R-style summary and can be rendered into
APA-7 text or tables by the companion package `psyreport`. `psystats` is the
foundational component of the **ANOVA Methods** ecosystem, which also includes
`psymetrics` (reliability, exploratory and confirmatory factor analysis) and
`psyreport` (APA reporting).

# Statement of need

Psychologists conducting quantitative work rely heavily on a handful of R
packages that pair a concise interface with output shaped for reporting:
`arsenal` and `tableone` for group-comparison tables [@arsenal; @tableone],
`epitools` for risk measures [@epitools], and `apaTables` for APA-formatted
output [@apaTables]. The Python scientific stack provides the underlying estimation
machinery — `pandas` [@mckinney2010], `scipy` [@virtanen2020], and `statsmodels`
[@seabold2010] — but exposes it through general-purpose interfaces that require
substantial boilerplate to reach a publication-ready table, and offers no direct
equivalent to the "describe a data frame, get an APA table" workflow that makes
the R tools attractive to applied researchers.

`psystats` closes that gap. It wraps the established estimators behind verbs
that mirror their R analogues (for example `table1(df, group="condition")`,
`riskratio(df, exposure=..., outcome=...)`, `alpha(items)`), so that a researcher
already familiar with R incurs little translation cost, while a Python-first
user obtains correct effect sizes, confidence intervals, and automatic test
selection without assembling them by hand. Because results are decoupled from
their presentation, the same computation feeds an interactive summary, a LaTeX
table, or a Word document without recomputation. The package is aimed at
researchers, students, and instructors in psychology and allied fields who work
in Python and need trustworthy, reportable output for everyday analyses.

# Functionality

`psystats` groups its functions into four areas. Descriptives and tables:
`describe`, `freq`, `corr_matrix` (a correlation matrix with significance stars),
and `table1`, which chooses a Welch *t*-test, one-way ANOVA, Mann–Whitney,
Kruskal–Wallis, $\chi^2$, or Fisher's exact test per variable according to its
type and distribution. Inferential tests with effect sizes: `ttest`, `anova`,
and `chisq`. Regression: `linreg`, reporting standardized coefficients and model
fit, and `logreg`, reporting odds ratios with confidence intervals. Risk
factors: `riskratio`, `oddsratio`, and `attributable_risk`, which returns the
risk difference with its confidence interval, the attributable risk percent, the
population attributable risk and its percent, and the number needed to treat.

# Quality control

All estimates are validated in an automated test suite against independent
references — `scipy` and `statsmodels` for test statistics, confidence
intervals, and regression coefficients, and closed-form identities for the
effect sizes — so that reported values match established implementations rather
than the package's own internals.

# Acknowledgements

We thank the maintainers of `pandas`, `scipy`, and `statsmodels`, on which
`psystats` builds.

# References
