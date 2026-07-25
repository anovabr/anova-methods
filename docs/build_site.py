"""Generate docs/index.html, the GitHub Pages landing page.

The function reference is built by introspecting the installed packages, so
signatures and descriptions cannot drift from the code. The worked examples are
executed at build time and their real output captured, following the same rule
as packages/psystats/EXAMPLES.md.

    pip install -e packages/psystats -e packages/psymetrics -e packages/psyreport
    python docs/build_site.py
"""
from __future__ import annotations

import contextlib
import datetime as dt
import html
import inspect
import io
import pathlib
import re
import textwrap
import warnings

warnings.filterwarnings("ignore")

import psymetrics
import psyreport
import psystats

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "index.html"
README = HERE.parent / "README.md"
SITE_URL = "https://anovabr.github.io/anova-methods/"

# Zenodo mints a version DOI for each release and one concept DOI for the
# record as a whole. Only the concept DOI is used here: it always resolves to
# the newest release, so nothing needs updating when a version is published.
DOI = "10.5281/zenodo.21566785"
DOI_URL = f"https://doi.org/{DOI}"

BUILT = dt.datetime.now(dt.timezone.utc)
BUILT_HUMAN = BUILT.strftime("%d %B %Y")
BUILT_ISO = BUILT.strftime("%Y-%m-%dT%H:%M:%SZ")

NS: dict = {}

# R analogue per function. Kept here rather than in the packages because it is
# documentation, not behaviour.
R_ANALOGUE = {
    "load_mapfre": "data()",
    "describe": "psych::describe",
    "freq": "table()",
    "corr_matrix": "apaTables",
    "table1": "arsenal, tableone",
    "ttest": "t.test",
    "anova": "aov",
    "chisq": "chisq.test",
    "linreg": "lm",
    "logreg": "glm",
    "riskratio": "epitools::riskratio",
    "oddsratio": "epitools::oddsratio",
    "attributable_risk": "epitools",
    "alpha": "psych::alpha",
    "kmo": "psych::KMO",
    "bartlett": "psych::cortest.bartlett",
    "efa": "psych::fa",
    "cfa": "lavaan::cfa",
    "report": "report",
    "to_latex": "apaTables",
    "to_docx": "apaTables",
}

PACKAGES = [
    {
        "module": psystats,
        "name": "psystats",
        "role": "statistics and biostatistics",
        "goal": (
            "To cover the analyses that appear in most quantitative psychology "
            "papers: descriptive statistics and group comparison tables, the "
            "common inferential tests reported with their effect sizes, linear "
            "and logistic regression, and the epidemiological risk measures used "
            "in risk-factor work."
        ),
        "analogues": "arsenal, tableone, epitools, apaTables",
        # Order the reference the way the package is used, not alphabetically.
        "order": ["load_mapfre", "describe", "freq", "corr_matrix", "table1",
                  "ttest", "anova", "chisq", "linreg", "logreg",
                  "riskratio", "oddsratio", "attributable_risk"],
    },
    {
        "module": psymetrics,
        "name": "psymetrics",
        "role": "reliability and latent variables",
        "goal": (
            "To cover scale construction and validation: how reliable a set of "
            "items is, whether the correlation matrix is suitable for factoring, "
            "what factor structure the items show, and whether a hypothesised "
            "structure fits the data."
        ),
        "analogues": "psych, lavaan",
        "order": ["alpha", "kmo", "bartlett", "efa", "cfa"],
    },
    {
        "module": psyreport,
        "name": "psyreport",
        "role": "APA-7 reporting",
        "goal": (
            "To render a result produced by either of the other two packages as "
            "APA-7 text, a LaTeX table, or a Word document. Reporting is kept "
            "separate from computation, so one result can feed all three outputs "
            "without being recomputed. Dispatch is by the result's <code>kind</code> "
            "tag, which is why psyreport renders a result without importing the "
            "package that produced it. It covers 15 result kinds: everything "
            "psystats emits, and all of psymetrics except the <code>kmo</code> and "
            "<code>bartlett</code> factorability checks."
        ),
        "analogues": "apaTables, report",
        "order": ["report", "to_latex", "to_docx"],
    },
]

PRELUDE = """
import pandas as pd
from psystats import load_mapfre
df = load_mapfre()
df["depressed"] = (df["bdi_sum"] >= 14).astype(int)
df["high_anxiety"] = (df["bai_sum"] >= 16).astype(int)
bdi = df[[f"bdi_{i}" for i in range(1, 22)]]
"""


# One example per exported function, executed at build time. Where a function
# needs a variable the dataset does not already carry, the example derives it
# in full rather than assuming it, because that derivation is usually the part
# a reader gets stuck on.
FUNCTION_EXAMPLES = {
    "load_mapfre": '''
        from psystats import load_mapfre

        df = load_mapfre()
        print(df.shape)
        print(df[["country", "sex", "age", "bdi_sum", "bai_sum"]].head())
    ''',
    "describe": '''
        from psystats import describe

        print(describe(df, columns=["age", "bdi_sum", "bai_sum"]))
    ''',
    "freq": '''
        from psystats import freq

        print(freq(df, "bdi_class", sort=False))
    ''',
    "corr_matrix": '''
        from psystats import corr_matrix

        print(corr_matrix(df, columns=["age", "bdi_sum", "bai_sum"]))
    ''',
    "table1": '''
        from psystats import table1

        print(table1(df, group="country", columns=["age", "sex", "bdi_sum"]))
    ''',
    "ttest": '''
        from psystats import ttest

        print(ttest(df, dv="bdi_sum", group="sex"))
    ''',
    "anova": '''
        from psystats import anova

        print(anova(df, dv="bdi_sum", group="country"))
    ''',
    "chisq": '''
        from psystats import chisq

        print(chisq(df, row="sex", col="bdi_class"))
    ''',
    "linreg": '''
        from psystats import linreg

        print(linreg(df, outcome="bdi_sum", predictors=["bai_sum", "age"]))
    ''',
    "logreg": '''
        from psystats import logreg

        # The outcome has to be binary, so derive it first. Here a BDI total
        # above 10 marks a student at risk.
        df["risk"] = (df["bdi_sum"] > 10).astype(int)

        print(logreg(df, outcome="risk", predictors=["bai_sum", "sex"]))
    ''',
    "riskratio": '''
        from psystats import riskratio

        # Both variables have to be binary, so derive them first.
        df["risk"] = (df["bdi_sum"] > 10).astype(int)
        df["high_anxiety"] = (df["bai_sum"] > 15).astype(int)

        print(riskratio(df, exposure="high_anxiety", outcome="risk",
                        exposed=1, positive=1))
    ''',
    "oddsratio": '''
        from psystats import oddsratio

        df["risk"] = (df["bdi_sum"] > 10).astype(int)
        df["high_anxiety"] = (df["bai_sum"] > 15).astype(int)

        print(oddsratio(df, exposure="high_anxiety", outcome="risk",
                        exposed=1, positive=1))
    ''',
    "attributable_risk": '''
        from psystats import attributable_risk

        df["risk"] = (df["bdi_sum"] > 10).astype(int)
        df["high_anxiety"] = (df["bai_sum"] > 15).astype(int)

        print(attributable_risk(df, exposure="high_anxiety", outcome="risk",
                                exposed=1, positive=1))
    ''',
    "alpha": '''
        from psymetrics import alpha

        # Reliability is computed over the items, not the total score.
        bdi_items = df[[f"bdi_{i}" for i in range(1, 22)]]

        a = alpha(bdi_items)
        print(a)
    ''',
    "kmo": '''
        from psymetrics import kmo

        bdi_items = df[[f"bdi_{i}" for i in range(1, 22)]]

        r = kmo(bdi_items)
        print(f"overall KMO = {r.values['overall']:.3f}")
        print(r.table.head())
    ''',
    "bartlett": '''
        from psymetrics import bartlett

        bdi_items = df[[f"bdi_{i}" for i in range(1, 22)]]

        print(bartlett(bdi_items))
    ''',
    "efa": '''
        from psymetrics import efa

        # The first eight BDI items, asking for two factors.
        items = df[[f"bdi_{i}" for i in range(1, 9)]]

        print(efa(items, n_factors=2, rotation="promax"))
    ''',
    "cfa": '''
        from psymetrics import cfa

        # lavaan model syntax, so a specification moves over from R unchanged.
        model = """
        visual  =~ x1 + x2 + x3
        textual =~ x4 + x5 + x6
        speed   =~ x7 + x8 + x9
        """
        fit = cfa(model, data)
        fit.values["fit"]        # chi2, df, cfi, tli, rmsea
        fit.values["loadings"]   # standardized loadings
    ''',
    "report": '''
        from psystats import ttest, anova
        from psyreport import report

        print(report(ttest(df, dv="bdi_sum", group="sex")))
        print(report(anova(df, dv="bdi_sum", group="country")))
    ''',
    "to_latex": '''
        from psystats import corr_matrix
        from psyreport import to_latex

        cm = corr_matrix(df, columns=["age", "bdi_sum", "bai_sum"])
        print(to_latex(cm, caption="Correlations among study variables"))
    ''',
    "to_docx": '''
        from psystats import corr_matrix
        from psyreport import to_docx

        cm = corr_matrix(df, columns=["age", "bdi_sum", "bai_sum"])
        to_docx(cm, "correlations.docx", caption="Correlations among study variables")
        # returns the path it wrote
    ''',
}

# cfa needs the optional semopy extra and to_docx writes a file, so neither is
# executed. They are shown as code, never with invented output.
NO_RUN = {"cfa", "to_docx"}

# Filled by resolve_function_examples(); name -> {"code": str, "out": str|None}
FN_EX: dict = {}


def run(code: str) -> str:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exec(textwrap.dedent(code), NS)
    return buf.getvalue().rstrip("\n")


# Re-applied after every example. Some of them legitimately rebind `df` (the
# load_mapfre example does), which would drop the columns the prelude derived
# and break every example that runs afterwards.
REPAIR = '''
if "depressed" not in df.columns:
    df["depressed"] = (df["bdi_sum"] >= 14).astype(int)
    df["high_anxiety"] = (df["bai_sum"] >= 16).astype(int)
    bdi = df[[f"bdi_{i}" for i in range(1, 22)]]
'''


def resolve_function_examples() -> None:
    """Execute each function's example once, keeping code and real output."""
    for name, code in FUNCTION_EXAMPLES.items():
        code = textwrap.dedent(code).strip("\n")
        out = None if name in NO_RUN else run(code)
        exec(textwrap.dedent(REPAIR), NS)
        FN_EX[name] = {"code": code, "out": out}


def esc(s: str) -> str:
    return html.escape(s, quote=False)


def code_block(code: str, label: str = "Python", copy: bool = True) -> str:
    """Static code block, no execution."""
    code = textwrap.dedent(code).strip("\n")
    btn = '<button class="copy" type="button">Copy</button>' if copy else ""
    return (f'<div class="code"><div class="code-label"><span>{esc(label)}</span>'
            f'{btn}</div><pre>{esc(code)}</pre></div>')


def example(code: str, label: str = "Python") -> str:
    """Code block plus the output produced by actually running it."""
    code = textwrap.dedent(code).strip("\n")
    out = run(code)
    parts = [code_block(code, label)]
    if out:
        parts.append('<div class="code out"><div class="code-label">'
                     f'<span>Output</span></div><pre>{esc(out)}</pre></div>')
    return "\n".join(parts)


def _inline(s: str) -> str:
    """Escape, then turn ``x`` into a code span and bare URLs into links."""
    s = re.sub(r"``([^`]+)``", r"<code>\1</code>", esc(s))
    return re.sub(r"(https?://[^\s<)]+)", r'<a href="\1">\1</a>', s)


def _section_body(lines: list[str]) -> str:
    """Render the body of a numpydoc section.

    Lines shaped ``name : description`` become a definition list; anything else
    (a citation under Source, for instance) becomes a paragraph.
    """
    entries: list[tuple[str, list[str]]] = []
    loose: list[str] = []
    for line in lines:
        # numpydoc puts a space before the colon, which is what keeps a bare
        # URL ("https://…") from being read as a parameter named "https".
        m = re.match(r"^(\w[\w, ]*?) +: +(.*)$", line)
        if m:
            entries.append((m.group(1), [m.group(2)]))
        elif entries and line.strip():
            entries[-1][1].append(line.strip())
        elif line.strip():
            loose.append(line.strip())
    out = []
    if entries:
        items = "".join(
            f"<dt><code>{esc(nm)}</code></dt><dd>{_inline(' '.join(desc).strip())}</dd>"
            for nm, desc in entries
        )
        out.append(f"<dl class='params'>{items}</dl>")
    if loose:
        out.append(f"<p>{_inline(' '.join(loose))}</p>")
    return "".join(out)


def docstring_html(fn, skip_summary: bool = True) -> str:
    """Render a docstring as HTML.

    The first paragraph is skipped by default because it is already shown on the
    collapsed row, so expanding a card adds information rather than repeating it.
    """
    doc = inspect.getdoc(fn) or ""
    blocks = [b for b in doc.split("\n\n") if b.strip()]
    if skip_summary and blocks:
        blocks = blocks[1:]
    out = []
    for b in blocks:
        lines = b.split("\n")
        # A numpydoc section: a title underlined by dashes.
        if len(lines) >= 2 and lines[1].strip() and set(lines[1].strip()) == {"-"}:
            out.append(f"<h5>{esc(lines[0].strip())}</h5>")
            out.append(_section_body(lines[2:]))
        elif any(line.startswith("    ") for line in lines):
            # Indented content (model syntax, a worked snippet) keeps its shape.
            out.append(f"<pre class='doc-pre'>{_inline(textwrap.dedent(b))}</pre>")
        else:
            out.append("<p>" + _inline(" ".join(l.strip() for l in lines)) + "</p>")
    return "\n".join(out) or "<p>No further description.</p>"


def function_card(mod, name: str) -> str:
    fn = getattr(mod, name)
    sig = str(inspect.signature(fn))
    summary = (inspect.getdoc(fn) or "").split("\n\n")[0].replace("\n", " ").strip()
    analogue = R_ANALOGUE.get(name, "")
    r_html = (f'<span class="fn-r" title="R analogue">{esc(analogue)}</span>'
              if analogue else "")
    ex = FN_EX.get(name)
    ex_html = ""
    if ex:
        ex_html = "<h5>Example</h5>" + code_block(ex["code"])
        if ex["out"]:
            ex_html += ('<div class="code out"><div class="code-label">'
                        f'<span>Output</span></div><pre>{esc(ex["out"])}</pre></div>')
    return f"""<details class="fn">
<summary>
  <span class="fn-name"><code>{esc(name)}{esc(sig)}</code></span>
  <span class="fn-sum">{esc(summary)}</span>
  {r_html}
</summary>
<div class="fn-body">
{docstring_html(fn)}
{ex_html}
</div>
</details>"""


# The two palettes are written once and emitted into three places: the default
# :root, the prefers-color-scheme media query, and the explicit data-theme
# overrides the toggle sets. Keeping one source stops the themes drifting.
LIGHT_TOKENS = {
    "--paper": "#F4F6F3", "--surface": "#FFFFFF", "--surface-2": "#ECEFEA",
    "--ink": "#0F1417", "--ink-soft": "#3A443F", "--muted": "#63706A",
    "--rule": "#D6DCD6", "--accent": "#17594A", "--accent-ink": "#FFFFFF",
    "--accent-dim": "#DCE9E3", "--signal": "#B5462F", "--code-bg": "#EDF0EC",
    "--shadow": "0 2px 10px rgba(15,20,23,0.10)",
}
DARK_TOKENS = {
    "--paper": "#0D1114", "--surface": "#141A1D", "--surface-2": "#1B2226",
    "--ink": "#E8EDE9", "--ink-soft": "#BFC9C3", "--muted": "#8A9791",
    "--rule": "#2A3431", "--accent": "#2E9C7E", "--accent-ink": "#06120E",
    "--accent-dim": "#16332B", "--signal": "#E0785C", "--code-bg": "#101619",
    "--shadow": "0 2px 10px rgba(0,0,0,0.45)",
}


def _tokens(d: dict) -> str:
    return "\n".join(f"  {k}: {v};" for k, v in d.items())


CSS = f"""
:root {{
{_tokens(LIGHT_TOKENS)}
  --display:"Iowan Old Style","Palatino Linotype",Palatino,"Book Antiqua",Georgia,serif;
  --body:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",sans-serif;
  --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
  --step--1:0.815rem; --step-0:1rem; --step-1:1.2rem;
  --step-2:1.5rem; --step-3:1.95rem; --step-5:3.4rem;
}}
@media (prefers-color-scheme: dark) {{
  :root {{
{_tokens(DARK_TOKENS)}
  }}
}}
/* An explicit choice from the toggle wins over the system preference. */
:root[data-theme="dark"] {{
{_tokens(DARK_TOKENS)}
}}
:root[data-theme="light"] {{
{_tokens(LIGHT_TOKENS)}
}}
""" + """
* { box-sizing:border-box; }
body {
  margin:0; background:var(--paper); color:var(--ink);
  font-family:var(--body); font-size:var(--step-0); line-height:1.65;
  -webkit-font-smoothing:antialiased;
}
.shell {
  max-width:1180px; margin:0 auto; padding:0 1.25rem 5rem;
  display:grid; grid-template-columns:1fr; gap:2.5rem;
}
@media (min-width:1000px) {
  .shell { grid-template-columns:230px minmax(0,1fr); gap:3.5rem; padding-top:1rem; }
}
.hero { grid-column:1/-1; padding:3.25rem 0 2.25rem; border-bottom:2px solid var(--ink); }
.eyebrow {
  font-family:var(--mono); font-size:var(--step--1); letter-spacing:0.12em;
  text-transform:uppercase; color:var(--accent); margin:0 0 1rem;
}
.hero h1 {
  font-family:var(--display); font-weight:600;
  font-size:clamp(2.3rem,5.5vw,var(--step-5)); line-height:1.05;
  letter-spacing:-0.02em; margin:0 0 1.1rem; text-wrap:balance;
}
.hero .lede { font-size:var(--step-1); color:var(--ink-soft); max-width:62ch; margin:0 0 1.5rem; text-wrap:pretty; }
.hero .meta { font-size:0.9rem; color:var(--muted); max-width:62ch; margin:0 0 1.5rem; }
.badges { display:flex; flex-wrap:wrap; gap:0.5rem; align-items:center; }
.badge {
  font-family:var(--mono); font-size:0.74rem; border:1px solid var(--rule);
  background:var(--surface); border-radius:2px; padding:0.2rem 0.55rem;
  color:var(--ink-soft); display:inline-flex; gap:0.4rem; align-items:center;
}
.badge b { color:var(--accent); font-weight:700; }
.badge.stamp { border-style:dashed; }
.toc { align-self:start; }
@media (min-width:1000px) {
  .toc { position:sticky; top:1.5rem; max-height:calc(100vh - 3rem); overflow-y:auto; }
}
.toc h2 {
  font-family:var(--mono); font-size:var(--step--1); text-transform:uppercase;
  letter-spacing:0.1em; color:var(--muted); margin:0 0 0.85rem; font-weight:600;
}
.toc ol { list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:0.12rem; }
.toc a {
  display:block; padding:0.3rem 0 0.3rem 0.75rem; border-left:2px solid var(--rule);
  color:var(--ink-soft); text-decoration:none; font-size:0.9rem;
}
.toc a:hover { color:var(--accent); border-left-color:var(--accent); }
.toc a:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
.toc .sub a { padding-left:1.6rem; font-size:0.83rem; color:var(--muted); }
.toc .pkg a { font-weight:600; color:var(--ink); }
main { min-width:0; display:flex; flex-direction:column; gap:3.25rem; }
section { scroll-margin-top:1.5rem; }
h2.sec {
  font-family:var(--display); font-size:var(--step-3); line-height:1.15;
  margin:0 0 0.5rem; letter-spacing:-0.01em; text-wrap:balance;
}
h3 {
  font-family:var(--body); font-size:0.83rem; text-transform:uppercase;
  letter-spacing:0.1em; color:var(--muted); margin:2rem 0 0.75rem; font-weight:700;
}
p { margin:0 0 1rem; max-width:68ch; text-wrap:pretty; }
a { color:var(--accent); }
.marker { display:flex; gap:3px; margin-bottom:0.9rem; }
.marker i { width:13px; height:13px; border:1.5px solid var(--accent); border-radius:1px; display:block; }
.marker i.on { background:var(--accent); }
.pkg-head { display:flex; align-items:baseline; gap:0.75rem; flex-wrap:wrap; }
.pkg-head code {
  font-family:var(--mono); font-size:var(--step-2); color:var(--accent);
  background:none; padding:0; font-weight:600;
}
.pkg-head .role { color:var(--muted); font-size:var(--step-0); }
.analogue { color:var(--muted); font-size:0.9rem; }
.analogue code { background:none; padding:0; color:var(--muted); }
.callout {
  background:var(--accent-dim); border-left:3px solid var(--accent);
  padding:1.1rem 1.35rem; border-radius:0 3px 3px 0;
}
.callout p { margin:0; max-width:62ch; }
.callout p + p { margin-top:0.6rem; }
.callout strong { color:var(--accent); }
.parts { display:grid; gap:1.25rem; grid-template-columns:1fr; margin-bottom:1.5rem; }
@media (min-width:720px) { .parts { grid-template-columns:repeat(3,1fr); } }
.part { background:var(--surface); border:1px solid var(--rule); border-radius:3px; padding:1.15rem 1.25rem; }
.part .n {
  font-family:var(--mono); font-size:0.74rem; color:var(--accent);
  letter-spacing:0.08em; display:block; margin-bottom:0.4rem; font-weight:700;
}
.part h4 { margin:0 0 0.4rem; font-size:var(--step-0); font-weight:650; }
.part p { margin:0; font-size:0.9rem; color:var(--ink-soft); }
.code {
  background:var(--code-bg); border:1px solid var(--rule); border-radius:3px;
  margin:0 0 1rem; overflow:hidden;
}
.code pre {
  margin:0; padding:1rem 1.1rem; overflow-x:auto; font-family:var(--mono);
  font-size:0.845rem; line-height:1.6; tab-size:2;
}
.code.out pre { color:var(--ink-soft); }
.code-label {
  font-family:var(--mono); font-size:0.7rem; text-transform:uppercase;
  letter-spacing:0.1em; color:var(--muted); padding:0.45rem 1.1rem;
  border-bottom:1px solid var(--rule); display:flex; justify-content:space-between;
  align-items:center; gap:1rem;
}
.copy {
  font-family:var(--body); font-size:0.72rem; letter-spacing:0.04em;
  background:transparent; border:1px solid var(--rule); color:var(--muted);
  border-radius:2px; padding:0.15rem 0.5rem; cursor:pointer;
}
.copy:hover { color:var(--accent); border-color:var(--accent); }
.copy:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
code { font-family:var(--mono); font-size:0.88em; background:var(--surface-2); padding:0.1em 0.34em; border-radius:2px; }

/* ---- folding function cards ---------------------------------------- */
.fn-controls { display:flex; gap:0.5rem; margin-bottom:0.85rem; }
.fn-controls button {
  font-family:var(--body); font-size:0.74rem; letter-spacing:0.04em;
  background:transparent; border:1px solid var(--rule); color:var(--muted);
  border-radius:2px; padding:0.25rem 0.7rem; cursor:pointer;
}
.fn-controls button:hover { color:var(--accent); border-color:var(--accent); }
.fn-controls button:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
.fn-list { display:flex; flex-direction:column; gap:0.4rem; }
details.fn {
  background:var(--surface); border:1px solid var(--rule); border-radius:3px;
  overflow:hidden;
}
details.fn summary {
  cursor:pointer; padding:0.7rem 0.95rem; list-style:none;
  display:grid; grid-template-columns:auto 1fr; gap:0.15rem 0.75rem;
  align-items:baseline;
}
details.fn summary::-webkit-details-marker { display:none; }
details.fn summary::before {
  content:"+"; font-family:var(--mono); color:var(--accent); font-weight:700;
  grid-row:1; grid-column:1; width:1ch; display:inline-block;
}
details.fn[open] summary::before { content:"\\2212"; }
details.fn summary:hover { background:var(--surface-2); }
details.fn summary:focus-visible { outline:2px solid var(--accent); outline-offset:-2px; }
.fn-name { grid-row:1; grid-column:2; }
.fn-name code {
  background:none; padding:0; color:var(--accent); font-weight:600; font-size:0.9rem;
}
.fn-sum { grid-row:2; grid-column:2; font-size:0.85rem; color:var(--muted); }
.fn-r {
  grid-row:1; grid-column:3; font-family:var(--mono); font-size:0.72rem;
  color:var(--muted); white-space:nowrap; justify-self:end;
}
@media (max-width:640px) { .fn-r { display:none; } }
.fn-body {
  padding:0.2rem 0.95rem 1rem 2.1rem; border-top:1px solid var(--rule);
  background:var(--paper);
}
.fn-body p { margin:0.75rem 0 0; font-size:0.92rem; max-width:66ch; }
.fn-body h5 {
  margin:1rem 0 0; font-family:var(--body); font-size:0.72rem;
  text-transform:uppercase; letter-spacing:0.1em; color:var(--muted); font-weight:700;
}
.fn-body dl.params { margin:0.4rem 0 0; display:grid; grid-template-columns:auto 1fr; gap:0.3rem 0.9rem; }
.fn-body dl.params dt { font-family:var(--mono); font-size:0.82rem; }
.fn-body dl.params dt code { background:none; padding:0; color:var(--accent); font-weight:600; }
.fn-body dl.params dd { margin:0; font-size:0.9rem; color:var(--ink-soft); max-width:60ch; }
@media (max-width:560px) {
  .fn-body dl.params { grid-template-columns:1fr; gap:0.1rem; }
  .fn-body dl.params dd { margin-bottom:0.5rem; }
}
.fn-body pre.doc-pre {
  margin:0.75rem 0 0; font-family:var(--mono); font-size:0.8rem;
  line-height:1.55; overflow-x:auto; color:var(--ink-soft);
  background:var(--code-bg); border:1px solid var(--rule);
  border-radius:3px; padding:0.7rem 0.85rem;
}
footer {
  grid-column:1/-1; border-top:1px solid var(--rule); margin-top:1rem;
  padding-top:1.5rem; color:var(--muted); font-size:0.85rem;
}
footer p { max-width:70ch; }

/* ---- theme toggle --------------------------------------------------- */
.theme-toggle {
  font-family:var(--body); font-size:0.74rem; letter-spacing:0.04em;
  background:var(--surface); border:1px solid var(--rule); color:var(--ink-soft);
  border-radius:2px; padding:0.2rem 0.6rem; cursor:pointer;
  display:inline-flex; align-items:center; gap:0.4rem;
}
.theme-toggle:hover { color:var(--accent); border-color:var(--accent); }
.theme-toggle:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
.theme-toggle .icon { font-size:0.9rem; line-height:1; }

/* ---- back to top ---------------------------------------------------- */
#to-top {
  position:fixed; right:1.25rem; bottom:1.25rem; z-index:50;
  display:inline-flex; align-items:center; gap:0.4rem;
  font-family:var(--body); font-size:0.78rem; letter-spacing:0.03em;
  background:var(--surface); color:var(--ink-soft);
  border:1px solid var(--rule); border-radius:3px;
  padding:0.5rem 0.8rem; cursor:pointer; box-shadow:var(--shadow);
  opacity:0; visibility:hidden; transform:translateY(6px);
  transition:opacity 0.18s ease, transform 0.18s ease, visibility 0.18s;
}
#to-top.show { opacity:1; visibility:visible; transform:translateY(0); }
#to-top:hover { color:var(--accent); border-color:var(--accent); }
#to-top:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
#to-top .arrow { font-size:0.95rem; line-height:1; }
@media (max-width:560px) { #to-top .label { display:none; } }

html { scroll-behavior:smooth; }
@media (prefers-reduced-motion:reduce) {
  html { scroll-behavior:auto; }
  #to-top { transition:none; }
}
"""

JS = """
document.querySelectorAll(".copy").forEach(function (btn) {
  btn.addEventListener("click", function () {
    var block = btn.closest(".code");
    var pre = block ? block.querySelector("pre") : null;
    if (!pre) return;
    navigator.clipboard.writeText(pre.innerText).then(function () {
      var prev = btn.textContent;
      btn.textContent = "Copied";
      setTimeout(function () { btn.textContent = prev; }, 1400);
    }).catch(function () { btn.textContent = "Press Ctrl+C"; });
  });
});
document.querySelectorAll("[data-expand]").forEach(function (btn) {
  btn.addEventListener("click", function () {
    var open = btn.getAttribute("data-expand") === "all";
    var scope = document.querySelector(btn.getAttribute("data-scope"));
    if (!scope) return;
    scope.querySelectorAll("details.fn").forEach(function (d) { d.open = open; });
  });
});

// ---- theme toggle ----------------------------------------------------
(function () {
  var btn = document.getElementById("theme-toggle");
  if (!btn) return;
  var icon = btn.querySelector(".icon");
  var label = btn.querySelector(".label");

  function current() {
    var set = document.documentElement.getAttribute("data-theme");
    if (set) return set;
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark" : "light";
  }
  function paint(mode) {
    // The button offers the theme you would switch to, not the one you are in.
    var next = mode === "dark" ? "light" : "dark";
    icon.textContent = next === "dark" ? "\\u25D1" : "\\u25D0";
    label.textContent = next === "dark" ? "Dark" : "Light";
    btn.setAttribute("aria-label", "Switch to the " + next + " theme");
  }
  paint(current());
  btn.addEventListener("click", function () {
    var next = current() === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    try { localStorage.setItem("anova-theme", next); } catch (e) {}
    paint(next);
  });
})();

// ---- back to top -----------------------------------------------------
(function () {
  var btn = document.getElementById("to-top");
  if (!btn) return;
  var ticking = false;
  function update() {
    btn.classList.toggle("show", window.scrollY > 600);
    ticking = false;
  }
  window.addEventListener("scroll", function () {
    if (!ticking) { window.requestAnimationFrame(update); ticking = true; }
  }, { passive: true });
  update();
  btn.addEventListener("click", function () {
    var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top: 0, behavior: reduce ? "auto" : "smooth" });
    document.querySelector("h1").focus({ preventScroll: true });
  });
})();
"""


def docstring_md(fn) -> str:
    """The same docstring rendering as the site, in Markdown."""
    doc = inspect.getdoc(fn) or ""
    blocks = [b for b in doc.split("\n\n") if b.strip()][1:]  # summary is in the row
    out = []
    for b in blocks:
        lines = b.split("\n")
        if len(lines) >= 2 and lines[1].strip() and set(lines[1].strip()) == {"-"}:
            out.append(f"**{lines[0].strip()}**\n")
            entries, loose = [], []
            for line in lines[2:]:
                m = re.match(r"^(\w[\w, ]*?) +: +(.*)$", line)
                if m:
                    entries.append((m.group(1), [m.group(2)]))
                elif entries and line.strip():
                    entries[-1][1].append(line.strip())
                elif line.strip():
                    loose.append(line.strip())
            for nm, desc in entries:
                out.append(f"- `{nm}` — {' '.join(desc).strip()}")
            if entries:
                out.append("")
            if loose:
                out.append(" ".join(loose) + "\n")
        elif any(line.startswith("    ") for line in lines):
            out.append("```\n" + textwrap.dedent(b) + "\n```\n")
        else:
            out.append(" ".join(l.strip() for l in lines) + "\n")
    return "\n".join(out).strip() or "_No further description._"


def function_card_md(mod, name: str) -> str:
    fn = getattr(mod, name)
    sig = str(inspect.signature(fn))
    summary = (inspect.getdoc(fn) or "").split("\n\n")[0].replace("\n", " ").strip()
    analogue = R_ANALOGUE.get(name, "")
    r_note = f"\nR analogue: `{analogue}`\n" if analogue else ""
    ex = FN_EX.get(name)
    ex_md = ""
    if ex:
        ex_md = f"\n**Example**\n\n```python\n{ex['code']}\n```\n"
        if ex["out"]:
            ex_md += f"\n```text\n{ex['out']}\n```\n"
    return (f"<details>\n<summary><code>{name}{sig}</code> — {summary}</summary>\n\n"
            f"{docstring_md(fn)}\n{ex_md}{r_note}\n</details>")


def package_section_md(pkg: dict, index: int, ex_md: str) -> str:
    mod = pkg["module"]
    name = pkg["name"]
    order = list(pkg["order"]) + [f for f in mod.__all__ if f not in pkg["order"]]
    cards = "\n\n".join(function_card_md(mod, f) for f in order)
    goal = re.sub(r"</?code>", "`", pkg["goal"])
    return f"""<a id="{name}"></a>

## {index + 1}. `{name}` — {pkg['role']}

### Goal

{goal}

R analogues: `{pkg['analogues']}`

### Functions ({len(order)})

Each entry is collapsed. Select one to read its full description, taken
directly from the function's documentation.

{cards}

### Examples

{ex_md}"""


def package_section(pkg: dict, index: int, examples_html: str) -> str:
    mod = pkg["module"]
    name = pkg["name"]
    marker = "".join(
        f'<i class="on"></i>' if i <= index else "<i></i>" for i in range(4)
    )
    cards = "\n".join(function_card(mod, fn) for fn in pkg["order"])
    listed = set(pkg["order"])
    missing = [f for f in mod.__all__ if f not in listed]
    if missing:  # a new export would otherwise be silently left out
        cards += "\n" + "\n".join(function_card(mod, fn) for fn in missing)
    n = len(pkg["order"]) + len(missing)
    return f"""
<section id="{name}">
  <div class="marker" aria-hidden="true">{marker}</div>
  <div class="pkg-head">
    <h2 class="sec"><code>{name}</code></h2>
    <span class="role">{esc(pkg['role'])}</span>
  </div>

  <h3 id="{name}-goal">Goal</h3>
  <p>{pkg['goal']}</p>
  <p class="analogue">R analogues: <code>{esc(pkg['analogues'])}</code></p>

  <h3 id="{name}-fn">Functions ({n})</h3>
  <p>Each entry is collapsed. Select one to read its full description, taken
     directly from the function's documentation.</p>
  <div class="fn-controls">
    <button type="button" data-expand="all" data-scope="#{name}-fnlist">Expand all</button>
    <button type="button" data-expand="none" data-scope="#{name}-fnlist">Collapse all</button>
  </div>
  <div class="fn-list" id="{name}-fnlist">
{cards}
  </div>

  <h3 id="{name}-ex">Examples</h3>
{examples_html}
</section>"""


# Examples are written once, as prose in Markdown plus code. They are executed
# once and rendered into both the HTML page and the README, so the two cannot
# disagree about what the packages produce.
EXAMPLE_SPECS = {
    "psystats": [
        ("Linear regression. Standardized coefficients appear in the `beta` "
         "column beside the unstandardized `b`.",
         '''
         from psystats import linreg

         print(linreg(df, outcome="bdi_sum", predictors=["bai_sum", "age"]))
         ''', True),
        ("Risk measures for a 2 × 2 table. `exposed` and `positive` name the "
         "level counted as exposed and as the event.",
         '''
         from psystats import riskratio

         print(riskratio(df, exposure="high_anxiety", outcome="depressed",
                         exposed=1, positive=1))
         ''', True),
    ],
    "psymetrics": [
        ("Reliability and the two standard factorability checks, run on the "
         "21 BDI items.",
         '''
         from psymetrics import alpha, kmo, bartlett

         bdi = df[[f"bdi_{i}" for i in range(1, 22)]]

         print(f"raw alpha   = {alpha(bdi).values['raw_alpha']:.3f}")
         print(f"overall KMO = {kmo(bdi).values['overall']:.3f}")
         print(bartlett(bdi))
         ''', True),
        ("Confirmatory factor analysis. The model is written in lavaan syntax, "
         "so a specification transfers from R unchanged. This function requires "
         "the `sem` extra, and so is shown here without output.",
         '''
         from psymetrics import cfa

         model = """
         visual  =~ x1 + x2 + x3
         textual =~ x4 + x5 + x6
         speed   =~ x7 + x8 + x9
         """
         fit = cfa(model, data)
         fit.values["fit"]        # chi2, df, cfi, tli, rmsea
         fit.values["loadings"]   # standardized loadings
         ''', False),
    ],
    "psyreport": [
        ("APA-7 text for a t test and a one-way ANOVA.",
         '''
         from psystats import ttest, anova
         from psyreport import report

         print(report(ttest(df, dv="bdi_sum", group="sex")))
         print(report(anova(df, dv="bdi_sum", group="country")))
         ''', True),
        ("The same machinery exports a correlation matrix as a LaTeX table.",
         '''
         from psystats import corr_matrix
         from psyreport import to_latex

         cm = corr_matrix(df, columns=["age", "bdi_sum", "bai_sum"])
         print(to_latex(cm, caption="Correlations among study variables"))
         ''', True),
    ],
}


def _md_inline(s: str) -> str:
    """Render the small Markdown subset used in example prose as HTML."""
    s = esc(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)


WORKED_CODE = '''
from psystats import load_mapfre, table1

df = load_mapfre()
print(table1(df, group="country", columns=["age", "sex", "bdi_sum"]))
'''


def resolve_examples() -> dict:
    """Execute each example once, keeping the code and its captured output."""
    resolved = {}
    for pkg, specs in EXAMPLE_SPECS.items():
        items = []
        for prose, code, execute in specs:
            code = textwrap.dedent(code).strip("\n")
            items.append({
                "prose": prose,
                "code": code,
                "out": run(code) if execute else None,
            })
        resolved[pkg] = items
    worked = textwrap.dedent(WORKED_CODE).strip("\n")
    resolved["_worked"] = [{"prose": "", "code": worked, "out": run(worked)}]
    return resolved


def examples_html(items: list) -> str:
    out = []
    for it in items:
        out.append(f"<p>{_md_inline(it['prose'])}</p>")
        out.append(code_block(it["code"]))
        if it["out"]:
            out.append('<div class="code out"><div class="code-label">'
                       f'<span>Output</span></div><pre>{esc(it["out"])}</pre></div>')
    return "\n".join(out)


def examples_md(items: list) -> str:
    out = []
    for it in items:
        out.append(it["prose"] + "\n")
        out.append(f"```python\n{it['code']}\n```\n")
        if it["out"]:
            out.append(f"```text\n{it['out']}\n```\n")
    return "\n".join(out)


def build_readme(resolved: dict) -> str:
    """The repository landing page, mirroring the documentation site."""
    toc = "\n".join(
        f"- [{i+1}. **{p['name']}** — {p['role']}](#{p['name']})"
        for i, p in enumerate(PACKAGES)
    )
    sections = "\n\n---\n\n".join(
        package_section_md(p, i, examples_md(resolved[p["name"]]))
        for i, p in enumerate(PACKAGES)
    )
    worked = resolved["_worked"][0]

    return f"""# ANOVA METHODS

[![Tests](https://github.com/anovabr/anova-methods/actions/workflows/ci.yml/badge.svg)](https://github.com/anovabr/anova-methods/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/psystats?label=psystats)](https://pypi.org/project/psystats/)
[![PyPI](https://img.shields.io/pypi/v/psymetrics?label=psymetrics)](https://pypi.org/project/psymetrics/)
[![PyPI](https://img.shields.io/pypi/v/psyreport?label=psyreport)](https://pypi.org/project/psyreport/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/{DOI}.svg)]({DOI_URL})

Three packages covering the statistical analyses commonly reported in
psychology: descriptive and group comparison tables, inferential tests with
effect sizes, regression, risk measures, reliability and factor analysis, and
APA-7 formatted output. The interface is functional and modelled on the
equivalent R packages.

Maintained by Luis Anunciação, PhD — Pontifical Catholic University of Rio de
Janeiro (PUC-Rio) and University of Oregon.
ORCID [0000-0001-5303-5782](https://orcid.org/0000-0001-5303-5782).
Free and open under the MIT licence.

📖 **[Documentation site]({SITE_URL})** — the same content as this page, with a
sticky contents rail and a light or dark theme.

## Contents

- [Installation](#installation)
- [The example dataset](#the-example-dataset)
- [A worked example](#a-worked-example)
- [Equivalents in R](#equivalents-in-r)
{toc}
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
{worked['code']}
```

```text
{worked['out']}
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

{sections}

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

- [**Documentation site**]({SITE_URL}) — this page with a sticky contents rail
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
> reporting for psychology in Python* [Computer software]. Zenodo. {DOI_URL}

```bibtex
@software{{anunciacao_anova_methods,
  author    = {{Anunciação, Luis}},
  title     = {{ANOVA Methods: statistics, psychometrics, and APA reporting
               for psychology in Python}},
  year      = {{2026}},
  publisher = {{Zenodo}},
  doi       = {{{DOI}}},
  url       = {{{DOI_URL}}}
}}
```

The DOI above is the **concept DOI**: it always resolves to the most recent
release, so a citation does not go stale when a new version is archived. To
cite one specific version instead, use that release's own version DOI, shown
on its record on [Zenodo]({DOI_URL}).

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
     rebuilds both. Last built {BUILT_HUMAN}. -->
"""


def main() -> None:
    run(PRELUDE)
    resolve_function_examples()

    resolved = resolve_examples()
    examples = [examples_html(resolved[p["name"]]) for p in PACKAGES]

    w = resolved["_worked"][0]
    worked = (code_block(w["code"])
              + '<div class="code out"><div class="code-label"><span>Output</span>'
                f'</div><pre>{esc(w["out"])}</pre></div>')

    dataset_block = code_block('''
        from psystats import load_mapfre

        df = load_mapfre()
        df.shape          # (1957, 94)
    ''')

    sections = "\n".join(
        package_section(pkg, i, examples[i]) for i, pkg in enumerate(PACKAGES)
    )

    toc_pkgs = "\n".join(
        f'      <li class="pkg"><a href="#{p["name"]}">{i+1} · {p["name"]}</a></li>\n'
        f'      <li class="sub"><a href="#{p["name"]}-goal">Goal</a></li>\n'
        f'      <li class="sub"><a href="#{p["name"]}-fn">Functions</a></li>\n'
        f'      <li class="sub"><a href="#{p["name"]}-ex">Examples</a></li>'
        for i, p in enumerate(PACKAGES)
    )

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ANOVA Methods — Python packages for psychological research</title>
<meta name="description" content="Three Python packages covering the statistical analyses commonly reported in psychology: group comparison tables, inferential tests with effect sizes, regression, risk measures, reliability, factor analysis, and APA-7 output.">
<script>
// Applied before the first paint so a stored theme does not flash the other one.
(function () {{
  try {{
    var t = localStorage.getItem("anova-theme");
    if (t) document.documentElement.setAttribute("data-theme", t);
  }} catch (e) {{}}
}})();
</script>
<style>{CSS}</style>
</head>
<body>
<div class="shell">

  <header class="hero">
    <p class="eyebrow">Python packages for psychological research</p>
    <h1>ANOVA Methods</h1>
    <p class="lede">
      Three packages covering the statistical analyses commonly reported in
      psychology: descriptive and group comparison tables, inferential tests with
      effect sizes, regression, risk measures, reliability and factor analysis, and
      APA-7 formatted output. The interface is functional and modelled on the
      equivalent R packages.
    </p>
    <p class="meta">
      Maintained by Luis Anunciação, PhD — Pontifical Catholic University of Rio de
      Janeiro (PUC-Rio) and University of Oregon.
      ORCID <a href="https://orcid.org/0000-0001-5303-5782">0000-0001-5303-5782</a>.
      Free and open under the MIT licence.
      <a href="https://github.com/anovabr/anova-methods">Source on GitHub</a>.
    </p>
    <div class="badges">
      <span class="badge">psystats <b>{psystats.__version__}</b></span>
      <span class="badge">psymetrics <b>{psymetrics.__version__}</b></span>
      <span class="badge">psyreport <b>{psyreport.__version__}</b></span>
      <span class="badge">Python <b>3.10+</b></span>
      <span class="badge">MIT</span>
      <span class="badge stamp">Last updated
        <b><time datetime="{BUILT_ISO}">{BUILT_HUMAN}</time></b></span>
      <button id="theme-toggle" class="theme-toggle" type="button"
              aria-label="Switch theme">
        <span class="icon" aria-hidden="true">◑</span><span class="label">Dark</span>
      </button>
    </div>
  </header>

  <nav class="toc" aria-label="Contents">
    <h2>Contents</h2>
    <ol>
      <li><a href="#install">Installation</a></li>
      <li><a href="#dataset">The example dataset</a></li>
      <li><a href="#example">A worked example</a></li>
      <li><a href="#requiv">Equivalents in R</a></li>
{toc_pkgs}
      <li><a href="#validation">Validation</a></li>
      <li><a href="#citing">Citing</a></li>
    </ol>
  </nav>

  <main>

    <section id="install">
      <h2 class="sec">Installation</h2>
      <p>The three packages are published on PyPI and can be installed together.</p>
      {code_block("pip install psystats psymetrics psyreport", "Terminal")}
      <div class="callout">
        <p><strong>Notes for a first installation.</strong> Python 3.10 or newer is
        required. If the <code>pip</code> command is not recognised, use
        <code>python -m pip install …</code> instead.</p>
        <p>Confirmatory factor analysis (<code>psymetrics.cfa</code>) depends on
        <code>semopy</code>, which is kept as an optional extra so that the core
        packages install without a compiler toolchain:
        <code>pip install "psymetrics[sem]"</code>.</p>
      </div>
    </section>

    <section id="dataset">
      <h2 class="sec">The example dataset</h2>
      <p>
        A teaching dataset is bundled inside <code>psystats</code>, so the examples on
        this page run without any download. It contains responses from 1,957
        undergraduate students in Spain, Portugal, and Brazil on the Beck Depression
        Inventory (<code>bdi_1</code> to <code>bdi_21</code>, <code>bdi_sum</code>,
        <code>bdi_class</code>) and the Beck Anxiety Inventory (<code>bai_*</code>),
        together with cyber-victimization, cyber-aggression, and emotion-regulation
        scales, and the demographics <code>country</code>, <code>sex</code>, and
        <code>age</code>.
      </p>
      {dataset_block}
      <p>
        The data are described in Afonso Junior et al. (2020),
        <em>Psicologia: Teoria e Pesquisa, 36</em>, e36412.
      </p>
    </section>

    <section id="example">
      <h2 class="sec">A worked example</h2>
      <p>
        Every function returns a result object. Printing it gives a summary in the
        style R would produce, <code>.values</code> holds the raw numbers,
        <code>.table</code> holds the result table, and passing it to
        <code>psyreport.report()</code> gives APA-7 text.
      </p>
      <div class="parts">
        <div class="part">
          <span class="n">Line 1</span>
          <h4>Load the data</h4>
          <p><code>load_mapfre()</code> returns a pandas DataFrame with 1,957 rows and 94 columns.</p>
        </div>
        <div class="part">
          <span class="n">Line 2</span>
          <h4>Run the analysis</h4>
          <p><code>table1()</code> compares each listed variable across the levels of <code>country</code>.</p>
        </div>
        <div class="part">
          <span class="n">Line 3</span>
          <h4>Print the result</h4>
          <p>The result object prints the table, the test used per variable, and its p value.</p>
        </div>
      </div>
      {worked}
      <p>
        <code>table1()</code> selects the test per variable. Each group is screened for
        normality with Shapiro-Wilk. Continuous variables are compared with a Welch t
        test or a one-way ANOVA when normal, and with Mann-Whitney or Kruskal-Wallis
        when not; categorical variables are compared with Fisher's exact test for a
        2 × 2 table and chi-square otherwise. Normal variables are summarised as
        <em>M (SD)</em>, non-normal ones as median [Q1, Q3], and categorical ones as
        <em>n</em> (%) within each group.
      </p>
      <div class="callout">
        <p><strong>Pass <code>columns</code> explicitly.</strong> When it is omitted,
        every remaining column is compared, which on this dataset means all 93 of them.</p>
      </div>
    </section>

    <section id="requiv">
      <h2 class="sec">Equivalents in R</h2>
      <p>
        Function and argument names follow the R packages that perform the same
        analyses, so a specification written in R generally transfers with little
        change. The R analogue for each function is shown on the right of its entry
        in the reference below.
      </p>
      {code_block('''# R                              # Python
library(psych)                   from psymetrics import alpha
alpha(bdi)                       alpha(bdi)

library(arsenal)                 from psystats import table1
tableby(country ~ ., df)         table1(df, group="country")

library(epitools)                from psystats import riskratio
riskratio(x)                     riskratio(df, exposure=..., outcome=...)''', "R and Python")}
    </section>
{sections}

    <section id="validation">
      <h2 class="sec">Validation</h2>
      <p>
        Estimates are checked against independent references rather than against the
        packages' own output. Test statistics, confidence intervals, and regression
        coefficients are compared with <code>scipy</code> and <code>statsmodels</code>,
        effect sizes with closed form identities, and the fit indices returned by
        <code>cfa</code> with <code>semopy</code> computed directly on the Holzinger
        and Swineford data. The suite of 50 tests runs on every push and pull request.
      </p>
      {code_block("pytest packages/", "Terminal")}
    </section>

    <section id="citing">
      <h2 class="sec">Citing</h2>
      <p>
        Citation metadata is held in <code>CITATION.cff</code>, which GitHub renders as
        a <em>Cite this repository</em> button in the repository sidebar, giving APA and
        BibTeX entries directly. Releases are archived on
        <a href="{DOI_URL}">Zenodo</a>, which mints a permanent DOI, so a citation
        points at an immutable archive rather than a moving branch. The DOI below
        is the concept DOI: it always resolves to the most recent release.
      </p>
      {code_block(f'''Anunciação, L. (2026). ANOVA Methods: statistics, psychometrics,
and APA reporting for psychology in Python [Computer software].
Zenodo. {DOI_URL}''', "APA", copy=False)}
      <p>
        The bundled dataset has its own citation, which applies when it is used in a
        publication.
      </p>
      {code_block('''Afonso Junior, A., Portugal, A. C. de A., Landeira-Fernandez, J.,
Bullón, F. F., dos Santos, E. J. R., de Vilhena, J., &
Anunciação, L. (2020). Sintomas de depressão e ansiedade em uma
amostra representativa de universitários espanhóis, portugueses e
brasileiros. Psicologia: Teoria e Pesquisa, 36, e36412.
https://doi.org/10.1590/0102.3772e36412''', "APA — dataset", copy=False)}
    </section>

  </main>

  <footer>
    <p>
      ANOVA Methods is developed in a single repository at
      <a href="https://github.com/anovabr/anova-methods">github.com/anovabr/anova-methods</a>
      under the MIT licence. Each package is built and published to PyPI
      independently. Contribution guidelines are in <code>CONTRIBUTING.md</code>;
      reports that an estimate disagrees with an established reference are
      particularly useful.
    </p>
    <p style="margin-top:0.75rem;">
      This page is generated from the installed packages, and the output shown in
      the examples is produced by running them.
      Last updated <time datetime="{BUILT_ISO}">{BUILT_HUMAN}</time>.
    </p>
  </footer>

</div>

<button id="to-top" type="button" aria-label="Back to top">
  <span class="arrow" aria-hidden="true">↑</span><span class="label">Top</span>
</button>

<script>{JS}</script>
</body>
</html>
"""
    OUT.write_text(doc, encoding="utf-8")
    total = sum(len(p["module"].__all__) for p in PACKAGES)
    print(f"wrote {OUT} ({len(doc.splitlines())} lines, {total} functions documented)")

    readme = build_readme(resolved)
    README.write_text(readme, encoding="utf-8")
    print(f"wrote {README} ({len(readme.splitlines())} lines)")
    print(f"last updated stamp: {BUILT_ISO}")


if __name__ == "__main__":
    main()
