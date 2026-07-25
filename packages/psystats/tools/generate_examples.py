"""Generate psystats/EXAMPLES.md by actually running every example.

Every code block in the output document is exec'd in a shared namespace and its
stdout captured verbatim, so the printed results in the docs are real. Run it
from anywhere:

    python packages/psystats/tools/generate_examples.py
"""
from __future__ import annotations

import io
import contextlib
import pathlib
import textwrap
import warnings

warnings.filterwarnings("ignore")

OUT_PATH = pathlib.Path(__file__).resolve().parent.parent / "EXAMPLES.md"

NS: dict = {}

PRELUDE = '''\
import pandas as pd
from psystats import load_mapfre

df = load_mapfre()

# Two derived binary variables used in the risk-factor and logistic examples.
# BDI-II >= 14 is the conventional cut-off for at least mild depression;
# BAI >= 16 for at least moderate anxiety.
df["depressed"] = (df["bdi_sum"] >= 14).astype("Int64")
df["high_anxiety"] = (df["bai_sum"] >= 16).astype("Int64")

# Scale means for the two emotion-regulation subscales (10 items each, 1-4).
ceri_items = [f"ceri_{i}" for i in range(1, 11)]
cerm_items = [f"cerm_{i}" for i in range(1, 11)]
df["ceri_mean"] = df[ceri_items].mean(axis=1)
df["cerm_mean"] = df[cerm_items].mean(axis=1)
'''


# Re-applied silently after every block: some examples legitimately rebind `df`
# (e.g. the `load_mapfre()` demo), which would drop the derived columns the
# later examples rely on.
REPAIR = '''\
if "depressed" not in df.columns:
    df["depressed"] = (df["bdi_sum"] >= 14).astype("Int64")
    df["high_anxiety"] = (df["bai_sum"] >= 16).astype("Int64")
    df["ceri_mean"] = df[[f"ceri_{i}" for i in range(1, 11)]].mean(axis=1)
    df["cerm_mean"] = df[[f"cerm_{i}" for i in range(1, 11)]].mean(axis=1)
'''


def run(code: str) -> str:
    """Exec code in the shared namespace, return captured stdout."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(textwrap.dedent(code), NS)
    return buf.getvalue().rstrip("\n")


def block(code: str) -> str:
    """Render a code block plus its real captured output."""
    code = textwrap.dedent(code).strip("\n")
    out = run(code)
    if "df" in NS:
        exec(REPAIR, NS)
    md = f"```python\n{code}\n```\n"
    if out:
        md += f"\n```text\n{out}\n```\n"
    return md


# ---------------------------------------------------------------- sections ---
SECTIONS: list[tuple[str, str, str, str, list[str]]] = []


def section(anchor, title, signature, prose, *code_blocks, notes=None):
    SECTIONS.append((anchor, title, signature, prose, list(code_blocks), notes))


section(
    "load_mapfre", "`load_mapfre()`",
    "load_mapfre() -> pd.DataFrame",
    "Loads the bundled teaching dataset: 1,957 undergraduates from Spain, "
    "Portugal, and Brazil, with the BDI-II, the BAI, cyber-victimization / "
    "cyber-aggression and emotion-regulation scales, and demographics "
    "(Afonso Junior et al., 2020). No arguments, no download — it ships inside "
    "the package.",
    """
    from psystats import load_mapfre

    df = load_mapfre()
    print(df.shape)
    print(df[["country", "sex", "age", "bdi_sum", "bai_sum", "bdi_class"]].head())
    """,
    """
    # What is in the file: 94 columns, grouped by instrument
    groups = {
        "demographics": ["country", "sex", "age", "grado", "curso_ou_ano"],
        "BDI-II items": [f"bdi_{i}" for i in range(1, 22)],
        "BAI items": [f"bai_{i}" for i in range(1, 22)],
        "emotion regulation": [f"ceri_{i}" for i in range(1, 11)]
                              + [f"cerm_{i}" for i in range(1, 11)],
        "cyber victimization": [f"cybvic_{i}" for i in range(1, 11)],
        "cyber aggression": [f"cybagress_{i}" for i in range(1, 11)],
        "totals / classes": ["bdi_sum", "bdi_class", "bai_sum", "bai_class"],
    }
    for name, cols in groups.items():
        print(f"{name:22s} {len(cols):3d} columns")
    """,
    notes=["`bdi_class` and `bai_class` are the clinical severity bands "
           "(`minima`, `leve`, `moderada`, `grave`).",
           "`country` has three levels, so it drives the ANOVA and chi-square "
           "examples; `sex` has two, so it drives the t-test."],
)

section(
    "describe", "`describe()`",
    "describe(df, columns=None) -> Result",
    "Per-column numeric descriptives: n, mean, sd, median, min, max, skew, and "
    "kurtosis. Non-numeric columns are ignored, so you can pass a whole frame. "
    "Pass `columns` to restrict the output.",
    """
    from psystats import describe

    print(describe(df, columns=["age", "bdi_sum", "bai_sum"]))
    """,
    """
    # The numbers are also available as a DataFrame for further work
    d = describe(df, columns=["bdi_sum", "bai_sum"])
    print(type(d.table))
    print(d.table[["mean", "sd", "skew"]].round(3))
    """,
    notes=["Skew and kurtosis are the bias-corrected versions "
           "(`scipy.stats.skew(..., bias=False)`); kurtosis is **excess** "
           "kurtosis, so 0 is normal.",
           "`n` is computed per column after dropping that column's missing "
           "values, so columns with different missingness report different `n`."],
)

section(
    "freq", "`freq()`",
    "freq(df, column, sort=True) -> Result",
    "Frequency table for a single variable: count, percent, and cumulative "
    "percent. Missing values are dropped, so percentages are of the valid n.",
    """
    from psystats import freq

    print(freq(df, "country"))
    """,
    """
    # sort=False keeps the natural order of the categories instead of
    # ordering by frequency -- useful for ordered severity bands.
    print(freq(df, "bdi_class", sort=False))
    """,
    notes=["`sort=True` (the default) orders rows by descending count; "
           "`sort=False` keeps the order pandas finds in the data.",
           "The `count` / `percent` / `cum_percent` DataFrame is on "
           "`.table`."],
)

section(
    "corr_matrix", "`corr_matrix()`",
    "corr_matrix(df, columns=None, method='pearson') -> Result",
    "Correlation matrix with significance stars, in the style of "
    "`apaTables`. Correlations are computed pairwise (each pair uses the rows "
    "complete for that pair). The printed matrix shows `r` with "
    "`*` p<.05, `**` p<.01, `***` p<.001.",
    """
    from psystats import corr_matrix

    print(corr_matrix(df, columns=["age", "bdi_sum", "bai_sum",
                                   "ceri_mean", "cerm_mean"]))
    """,
    """
    # Spearman for skewed / ordinal variables
    print(corr_matrix(df, columns=["bdi_sum", "bai_sum"], method="spearman"))
    """,
    """
    # The raw r and p matrices are separate DataFrames
    cm = corr_matrix(df, columns=["bdi_sum", "bai_sum", "age"])
    print("r matrix:")
    print(cm.values["r"].round(3))
    print("\\np matrix:")
    print(cm.values["p"].round(5))
    """,
    notes=["`method` accepts `'pearson'` (default) or `'spearman'`.",
           "Only numeric columns are used; anything else is silently dropped.",
           "`.values['r']`, `.values['p']`, and `.values['display']` give you "
           "the coefficients, the p-values, and the starred display matrix."],
)

section(
    "table1", "`table1()`",
    "table1(df, group, columns=None, conf=0.95) -> Result",
    "The classic **Table 1**: every variable compared across groups, with the "
    "test chosen automatically per variable.\n\n"
    "| variable type | 2 groups | >2 groups |\n"
    "|---|---|---|\n"
    "| continuous, normal | Welch t-test | one-way ANOVA |\n"
    "| continuous, non-normal | Mann-Whitney | Kruskal-Wallis |\n"
    "| categorical | Fisher exact (2x2) | chi-square |\n\n"
    "Normality is screened per group with Shapiro-Wilk. Normal variables are "
    "reported as `M (SD)`, non-normal ones as `median [Q1, Q3]`, and "
    "categorical ones as `n (%)` within each group.",
    """
    from psystats import table1

    print(table1(df, group="country",
                 columns=["age", "bdi_sum", "bai_sum", "sex", "bdi_class"]))
    """,
    """
    # Two groups -> the tests switch to their two-sample counterparts
    print(table1(df, group="sex",
                 columns=["age", "bdi_sum", "bai_sum", "bdi_class"]))
    """,
    notes=["If `columns` is omitted every column except `group` is used — on "
           "this dataset that means all 93 remaining columns, so pass "
           "`columns` explicitly.",
           "A numeric column with 2 or fewer distinct values is treated as "
           "categorical, which is what you want for 0/1 indicators.",
           "`.table` is a tidy DataFrame — hand it to "
           "`psyreport.to_docx()` / `to_latex()` for a publication table."],
)

section(
    "ttest", "`ttest()`",
    "ttest(df, dv, group=None, paired=False, equal_var=False, conf=0.95) -> Result",
    "Two-group t-test with Cohen's d. The data are in long form: `dv` is the "
    "numeric outcome and `group` is a column with exactly two levels. "
    "Welch's correction is the **default** (`equal_var=False`), matching R's "
    "`t.test()`.",
    """
    from psystats import ttest

    # Welch's t-test (default): depression scores by sex
    print(ttest(df, dv="bdi_sum", group="sex"))
    """,
    """
    # Student's t-test, assuming equal variances
    print(ttest(df, dv="bdi_sum", group="sex", equal_var=True))
    """,
    """
    # Every number is available individually
    t = ttest(df, dv="bai_sum", group="sex")
    print({k: round(v, 4) if isinstance(v, float) else v
           for k, v in t.values.items()})
    """,
    notes=["Cohen's d uses the pooled SD for independent samples and the SD of "
           "the differences for paired samples.",
           "`group` must have exactly two levels; with three or more use "
           "`anova()`.",
           "`paired=True` matches observations by **row order** within each "
           "level, so it is only appropriate when the two levels are already "
           "aligned row-for-row (see below)."],
)

section(
    "anova", "`anova()`",
    "anova(df, dv, group) -> Result",
    "One-way ANOVA with two effect sizes: eta squared (the proportion of "
    "variance explained in this sample) and omega squared (its less biased "
    "population estimate).",
    """
    from psystats import anova

    print(anova(df, dv="bdi_sum", group="country"))
    """,
    """
    # Anxiety across the same three countries
    a = anova(df, dv="bai_sum", group="country")
    print(a)
    print()
    print("F =", round(a.values["F"], 3),
          "| eta^2 =", round(a.values["eta_squared"], 4),
          "| omega^2 =", round(a.values["omega_squared"], 4),
          "| k =", a.values["k"])
    """,
    notes=["Group means are compared with `scipy.stats.f_oneway`, which assumes "
           "equal variances; check that assumption before reporting.",
           "This is a one-way (single factor) ANOVA — there is no interaction "
           "term. For factorial designs use `linreg()` with the factors as "
           "predictors."],
)

section(
    "chisq", "`chisq()`",
    "chisq(df, row, col, correction=False) -> Result",
    "Chi-square test of independence for two categorical variables, with "
    "Cramér's V as the effect size. The contingency table itself is returned "
    "on `.table`.",
    """
    from psystats import chisq

    print(chisq(df, row="bdi_class", col="country"))
    """,
    """
    # The crosstab used for the test
    c = chisq(df, row="sex", col="bdi_class")
    print(c)
    print()
    print(c.table)
    """,
    notes=["`correction=True` applies Yates' continuity correction (only "
           "meaningful for 2x2 tables); the default is `False`, matching R's "
           "`chisq.test(..., correction = FALSE)`.",
           "Cramér's V is `sqrt(chi2 / (N * (min(rows, cols) - 1)))`."],
)

section(
    "linreg", "`linreg()`",
    "linreg(df, outcome, predictors, conf=0.95) -> Result",
    "Ordinary least squares regression on top of `statsmodels`. Reports "
    "unstandardized coefficients with confidence intervals, **standardized "
    "betas**, t and p per predictor, R², adjusted R², and the overall F test. "
    "Categorical predictors are dummy-coded automatically with the first level "
    "as reference.",
    """
    from psystats import linreg

    print(linreg(df, outcome="bdi_sum", predictors=["bai_sum", "age", "sex"]))
    """,
    """
    # Model-level statistics
    m = linreg(df, outcome="bdi_sum", predictors=["bai_sum", "ceri_mean", "cerm_mean"])
    print(m)
    print()
    print("R^2 =", round(m.values["r2"], 4),
          "| adj R^2 =", round(m.values["adj_r2"], 4),
          "| N =", m.values["n"])
    """,
    notes=["Rows with a missing value on the outcome or any predictor are "
           "dropped (complete-case analysis), so `N` can be smaller than the "
           "full sample.",
           "`sex_M` in the output means *male relative to female* — the "
           "dropped first level is the reference.",
           "The standardized beta for the intercept is fixed at 0 by "
           "convention."],
)

section(
    "logreg", "`logreg()`",
    "logreg(df, outcome, predictors, conf=0.95) -> Result",
    "Logistic regression for a binary outcome. Reports log-odds coefficients, "
    "**odds ratios with confidence intervals**, Wald z and p, and McFadden's "
    "pseudo-R². The outcome must have exactly two levels; the higher one is "
    "modelled as the event.",
    """
    from psystats import logreg

    # P(depressed) as a function of anxiety, age, and sex
    print(logreg(df, outcome="depressed", predictors=["bai_sum", "age", "sex"]))
    """,
    """
    # Just the odds ratios with their CIs, ready to report
    m = logreg(df, outcome="depressed", predictors=["bai_sum", "country"])
    print(m.table[["or", "or_ci_low", "or_ci_high", "p"]].round(3))
    """,
    notes=["The outcome can be 0/1, `True`/`False`, or any two-level column — "
           "the higher level (sorted) is the modelled event.",
           "An odds ratio of 1.15 for `bai_sum` means each additional BAI point "
           "multiplies the odds of depression by 1.15.",
           "McFadden's pseudo-R² is not a proportion of variance; values of "
           ".2–.4 already indicate excellent fit."],
)

section(
    "riskratio", "`riskratio()`",
    "riskratio(df, exposure, outcome, exposed=None, positive=None, conf=0.95) -> Result",
    "Risk (incidence) ratio for a 2×2 table, in the style of "
    "`epitools::riskratio`. `RR = [a/(a+b)] / [c/(c+d)]`, with the Katz "
    "log-method confidence interval and a chi-square p-value.",
    """
    from psystats import riskratio

    # Is high anxiety associated with a higher risk of depression?
    print(riskratio(df, exposure="high_anxiety", outcome="depressed",
                    exposed=1, positive=1))
    """,
    """
    r = riskratio(df, exposure="high_anxiety", outcome="depressed",
                  exposed=1, positive=1)
    print("risk if exposed   =", round(r.values["risk_exposed"], 4))
    print("risk if unexposed =", round(r.values["risk_unexposed"], 4))
    print("2x2 cells a,b,c,d =", [r.values[k] for k in "abcd"])
    """,
    notes=["`exposed` and `positive` name the level that counts as *exposed* "
           "and as the *event*. Set them explicitly — otherwise levels are "
           "sorted descending, which puts `1` / `True` / `\"yes\"` first.",
           "Both variables must have exactly two levels after dropping missing "
           "values.",
           "A risk ratio is only interpretable when the design gives you real "
           "risks (cohort / cross-sectional). For case-control data use "
           "`oddsratio()`."],
)

section(
    "oddsratio", "`oddsratio()`",
    "oddsratio(df, exposure, outcome, exposed=None, positive=None, conf=0.95) -> Result",
    "Odds ratio for a 2×2 table (`epitools::oddsratio`, Wald method). "
    "`OR = ad / bc`, with the Woolf log-method confidence interval.",
    """
    from psystats import oddsratio

    print(oddsratio(df, exposure="high_anxiety", outcome="depressed",
                    exposed=1, positive=1))
    """,
    """
    # Same machinery on a demographic exposure
    print(oddsratio(df, exposure="sex", outcome="depressed",
                    exposed="F", positive=1))
    """,
    notes=["The odds ratio always sits further from 1 than the corresponding "
           "risk ratio, and the gap grows as the outcome gets more common.",
           "The p-value is from an uncorrected chi-square on the same 2×2 "
           "table, so it matches what `chisq()` would give."],
)

section(
    "attributable_risk", "`attributable_risk()`",
    "attributable_risk(df, exposure, outcome, exposed=None, positive=None, conf=0.95) -> Result",
    "The whole attributable-risk family from one 2×2 table:\n\n"
    "| quantity | meaning |\n"
    "|---|---|\n"
    "| `ar` | risk difference, `Re − Ru`, with a Wald CI |\n"
    "| `arp` | attributable risk percent **among the exposed**, `(Re−Ru)/Re` |\n"
    "| `par` | population attributable risk, `Rt − Ru` |\n"
    "| `parp` | population attributable risk percent, `(Rt−Ru)/Rt` |\n"
    "| `nnt` | number needed to treat/harm, `1/|AR|` |",
    """
    from psystats import attributable_risk

    print(attributable_risk(df, exposure="high_anxiety", outcome="depressed",
                            exposed=1, positive=1))
    """,
    """
    ar = attributable_risk(df, exposure="high_anxiety", outcome="depressed",
                           exposed=1, positive=1)
    for k in ["ar", "ci_low", "ci_high", "arp", "par", "parp", "nnt"]:
        print(f"{k:8s} = {ar.values[k]:.4f}")
    """,
    notes=["`arp` answers *what fraction of the risk in exposed people is "
           "attributable to the exposure*; `parp` answers the same question "
           "for the whole sample, so it depends on how common the exposure is.",
           "These are **associational** quantities. Reading them causally "
           "requires the design to support it.",
           "`nnt` is reported as a positive number; its direction follows the "
           "sign of `ar`."],
)


def main() -> None:
    run(PRELUDE)

    out: list[str] = []
    out.append("# `psystats` by example\n")
    out.append(
        "Every public function in `psystats`, with a runnable example on the "
        "dataset that ships with the package.\n\n"
        "**All output in this document is real** — the file is generated by "
        "executing each block against `load_mapfre()`, so what you see here is "
        "what you get.\n"
    )

    out.append("## Contents\n")
    out.append("| Function | What it does |")
    out.append("|---|---|")
    blurbs = {
        "load_mapfre": "load the bundled 1,957-student dataset",
        "describe": "n, mean, sd, median, min, max, skew, kurtosis",
        "freq": "frequency table with percent and cumulative percent",
        "corr_matrix": "correlation matrix with APA significance stars",
        "table1": "group comparison table with automatic test selection",
        "ttest": "two-group / paired t-test with Cohen's d",
        "anova": "one-way ANOVA with eta² and omega²",
        "chisq": "chi-square test of independence with Cramér's V",
        "linreg": "OLS regression with standardized betas",
        "logreg": "logistic regression with odds ratios",
        "riskratio": "risk ratio for a 2×2 table",
        "oddsratio": "odds ratio for a 2×2 table",
        "attributable_risk": "risk difference, ARP, PAR, PAR%, NNT",
    }
    for anchor, title, *_ in SECTIONS:
        out.append(f"| [`{anchor}()`](#{anchor}) | {blurbs[anchor]} |")
    out.append("")

    out.append("## Setup\n")
    out.append("```bash\npip install psystats\n```\n")
    out.append(
        "Every example below assumes this preamble. The two derived binary "
        "variables and the two scale means are used by the risk-factor, "
        "logistic-regression, and correlation examples.\n"
    )
    out.append(f"```python\n{PRELUDE.strip()}\n```\n")

    for anchor, title, signature, prose, code_blocks, notes in SECTIONS:
        out.append(f"---\n")
        out.append(f"<a id=\"{anchor}\"></a>\n")
        out.append(f"## {title}\n")
        out.append(f"```text\n{signature}\n```\n")
        out.append(prose + "\n")
        for cb in code_blocks:
            out.append(block(cb))
        if notes:
            out.append("**Notes**\n")
            for n in notes:
                out.append(f"- {n}")
            out.append("")

    # ---- paired t-test appendix (needs its own long-format frame) ----
    out.append("---\n")
    out.append('<a id="paired"></a>\n')
    out.append("## Appendix: paired `ttest()`\n")
    out.append(
        "`paired=True` pairs observations by **row order within each level**, "
        "so the data must be stacked with the two measurements aligned "
        "row-for-row. Here we compare each student's two emotion-regulation "
        "subscale means (`ceri` and `cerm`, both 10 items on a 1–4 scale) "
        "within person.\n"
    )
    out.append(block("""
        from psystats import ttest

        # Build a long frame where every student contributes two aligned rows
        paired_df = df[["ceri_mean", "cerm_mean"]].dropna()
        long = pd.concat([
            pd.DataFrame({"subscale": "ceri", "score": paired_df["ceri_mean"].values}),
            pd.DataFrame({"subscale": "cerm", "score": paired_df["cerm_mean"].values}),
        ], ignore_index=True)

        print(long.groupby("subscale")["score"].agg(["count", "mean", "std"]).round(3))
        print()
        print(ttest(long, dv="score", group="subscale", paired=True))
    """))
    out.append(
        "> **Careful:** because pairing is positional, this only works when "
        "both levels are sorted identically and have the same length — as "
        "guaranteed above by building both blocks from the same rows. If they "
        "differ in length the longer one is truncated, silently. When in "
        "doubt, compute the difference yourself and check it.\n"
    )

    # ---- Result object ----
    out.append("---\n")
    out.append('<a id="result"></a>\n')
    out.append("## The `Result` object\n")
    out.append(
        "Every function returns the same lightweight `Result`. Printing it "
        "gives the R-style summary; the pieces are addressable for programmatic "
        "use.\n\n"
        "| attribute | contents |\n|---|---|\n"
        "| `.kind` | a tag identifying the analysis (`\"ttest\"`, `\"linreg\"`, …) |\n"
        "| `.values` | dict of the raw numbers |\n"
        "| `.table` | the main result as a `DataFrame` (when there is one) |\n"
    )
    out.append(block("""
        from psystats import ttest, linreg, table1

        for res in [ttest(df, dv="bdi_sum", group="sex"),
                    linreg(df, outcome="bdi_sum", predictors=["bai_sum"]),
                    table1(df, group="sex", columns=["age", "bdi_sum"])]:
            has_table = "DataFrame" if res.table is not None else "None"
            print(f"kind={res.kind:8s} table={has_table:10s} "
                  f"values keys: {sorted(res.values)[:5]}")
    """))
    out.append(
        "`.kind` is what `psyreport` dispatches on, which is how a result "
        "becomes APA-7 text without `psystats` ever importing `psyreport`:\n"
    )
    out.append(block("""
        from psyreport import report
        from psystats import ttest, anova, chisq

        print(report(ttest(df, dv="bdi_sum", group="sex")))
        print(report(anova(df, dv="bdi_sum", group="country")))
        print(report(chisq(df, row="sex", col="bdi_class")))
    """))

    out.append("---\n")
    out.append("## Citing the dataset\n")
    out.append(
        "> Afonso Junior, A., Portugal, A. C. d. A., Landeira-Fernandez, J., "
        "Bullón, F. F., dos Santos, E. J. R., de Vilhena, J., & Anunciação, L. "
        "(2020). Sintomas de Depressão e Ansiedade em uma Amostra "
        "Representativa de Universitários Espanhóis, Portugueses e "
        "Brasileiros. *Psicologia: Teoria e Pesquisa, 36*, e36412. "
        "https://doi.org/10.1590/0102.3772e36412\n"
    )

    text = "\n".join(out).rstrip() + "\n"
    OUT_PATH.write_text(text, encoding="utf-8")
    print(f"wrote {OUT_PATH} ({len(text.splitlines())} lines)")


if __name__ == "__main__":
    main()
