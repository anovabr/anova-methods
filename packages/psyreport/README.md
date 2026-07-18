# psyreport

APA-7 reporting of results from psystats and psymetrics. Part of the **ANOVA
Methods** family (psystats, psymetrics, psyreport).

Free and open (MIT). psyreport reads any psy result object and renders it as
APA-7 text, a LaTeX table, or a Word (.docx) table — without importing the other
packages (it dispatches on a shared result convention, so there is no circular
dependency).

## Install

```bash
pip install psyreport
```

## What's inside

`report(result)` — an APA-7 formatted string. Follows APA number style (no
leading zero on bounded statistics, `p < .001` thresholds, italic test
statistics spelled with their symbols).

`to_latex(result, caption=, label=)` — a LaTeX `table` environment for
table-bearing results; a commented APA sentence for inline-only results.

`to_docx(result, path)` — writes an APA-style Word document with the result's
table and note.

## Example

```python
from psymetrics import alpha
from psystats import table1, linreg
from psyreport import report, to_latex, to_docx

a = alpha(items)
print(report(a))
# -> "Cronbach's α = .87, 95% CI [.82, .91], based on 10 items (N = 240)."

print(report(linreg(df, "score", ["age", "condition"])))
# -> "age: b = 0.31, β = .28, p < .001." ...

to_docx(table1(df, group="condition"), "table1.docx")   # Word table
print(to_latex(alpha(items), caption="Reliability", label="tab:alpha"))
```

Supported result kinds: alpha, riskratio, oddsratio, attributable_risk, ttest,
anova, chisq, corr_matrix, freq, linreg, logreg, efa, cfa, describe, table1.
