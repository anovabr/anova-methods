"""Build a typeset PDF article from paper.md.

Renders the Markdown through pandoc (with citeproc, APA style) into HTML, wraps
it in a journal-style template, and prints it to PDF with WeasyPrint. No LaTeX
required.

    pip install pypandoc_binary weasyprint pyyaml
    python packages/psystats/paper/build_paper.py

Output: paper.pdf next to this script.
"""
from __future__ import annotations

import html
import pathlib
import re
import sys

import pypandoc
import yaml
from weasyprint import HTML

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "paper.md"
BIB = HERE / "paper.bib"
CSL = HERE / "apa.csl"
OUT = HERE / "paper.pdf"

# WeasyPrint has no MathML support, so the handful of inline math spans in the
# paper are mapped to their Unicode equivalents instead.
MATH = {
    r"$\eta^2$": "η²",      # eta squared
    r"$\chi^2$": "χ²",      # chi squared
    r"$\omega^2$": "ω²",    # omega squared
    r"$R^2$": "R²",
}

CSS = """
@page {
    size: A4;
    margin: 22mm 20mm 20mm 20mm;
    @bottom-center {
        content: counter(page);
        font-family: "DejaVu Sans", sans-serif;
        font-size: 8.5pt;
        color: #666;
    }
}
html { font-size: 10.5pt; }
body {
    font-family: "Bitstream Charter", "Liberation Serif", serif;
    line-height: 1.45;
    color: #111;
    text-align: justify;
    hyphens: auto;
}
h1.title {
    font-family: "DejaVu Sans", sans-serif;
    font-size: 17pt;
    line-height: 1.25;
    margin: 0 0 0.7em 0;
    text-align: left;
    font-weight: bold;
    color: #0b0b0b;
}
.authors {
    font-family: "DejaVu Sans", sans-serif;
    font-size: 11pt;
    margin: 0 0 0.35em 0;
    text-align: left;
}
.affiliations, .meta {
    font-family: "DejaVu Sans", sans-serif;
    font-size: 8.5pt;
    color: #444;
    line-height: 1.4;
    text-align: left;
    margin: 0;
}
.affiliations { margin-bottom: 0.5em; }
.rule {
    border: 0;
    border-top: 1.5pt solid #222;
    margin: 0.9em 0 1.1em 0;
}
h1 {
    font-family: "DejaVu Sans", sans-serif;
    font-size: 11.5pt;
    margin: 1.4em 0 0.45em 0;
    text-align: left;
    color: #0b0b0b;
}
h2 {
    font-family: "DejaVu Sans", sans-serif;
    font-size: 10pt;
    margin: 1.1em 0 0.35em 0;
    text-align: left;
}
p { margin: 0 0 0.55em 0; }
code {
    font-family: "DejaVu Sans Mono", monospace;
    font-size: 0.86em;
    background: #f4f4f6;
    padding: 0.5pt 2pt;
    border-radius: 2pt;
}
pre {
    font-family: "DejaVu Sans Mono", monospace;
    font-size: 8.5pt;
    background: #f4f4f6;
    padding: 6pt 8pt;
    border-radius: 3pt;
    white-space: pre-wrap;
    text-align: left;
}
pre code { background: none; padding: 0; }
a { color: #14507d; text-decoration: none; }

/* Reference list: hanging indent, APA style */
#refs { font-size: 9.2pt; text-align: left; }
#refs div.csl-entry {
    margin-bottom: 0.4em;
    padding-left: 5mm;
    text-indent: -5mm;
}
.footnote-block {
    margin-top: 1.6em;
    padding-top: 0.5em;
    border-top: 0.5pt solid #bbb;
    font-family: "DejaVu Sans", sans-serif;
    font-size: 8pt;
    color: #555;
    text-align: left;
    line-height: 1.45;
}
"""


def split_front_matter(text: str) -> tuple[dict, str]:
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        raise SystemExit("paper.md must start with a YAML front-matter block")
    return yaml.safe_load(m.group(1)), m.group(2)


def render_authors(meta: dict) -> tuple[str, str]:
    """Return (authors_html, affiliations_html)."""
    parts = []
    for a in meta.get("authors", []):
        name = html.escape(str(a.get("name", "")))
        aff = str(a.get("affiliation", "")).replace(" ", "")
        sup = f"<sup>{html.escape(aff)}</sup>" if aff else ""
        orcid = a.get("orcid")
        link = (f' <a href="https://orcid.org/{orcid}">ORCID {html.escape(str(orcid))}</a>'
                if orcid else "")
        parts.append(f"{name}{sup}{link}")
    authors = "<div class='authors'>" + "; ".join(parts) + "</div>"

    lines = []
    for aff in meta.get("affiliations", []):
        idx = html.escape(str(aff.get("index", "")))
        nm = html.escape(str(aff.get("name", "")))
        lines.append(f"<sup>{idx}</sup>&nbsp;{nm}")
    affiliations = "<div class='affiliations'>" + "<br/>".join(lines) + "</div>"
    return authors, affiliations


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"missing {SRC}")
    meta, body = split_front_matter(SRC.read_text(encoding="utf-8"))

    for tex, uni in MATH.items():
        body = body.replace(tex, uni)
    leftover = re.findall(r"\$[^$\n]+\$", body)
    if leftover:
        print(f"warning: unconverted math (WeasyPrint cannot render it): "
              f"{sorted(set(leftover))}", file=sys.stderr)

    extra_args = ["--citeproc", f"--bibliography={BIB}", "--wrap=none"]
    if CSL.exists():
        extra_args.append(f"--csl={CSL}")
    else:
        print("warning: apa.csl not found, falling back to pandoc's default "
              "citation style", file=sys.stderr)

    content = pypandoc.convert_text(body, to="html5", format="markdown",
                                    extra_args=extra_args)

    authors_html, affil_html = render_authors(meta)
    title = html.escape(str(meta.get("title", "")))
    date = html.escape(str(meta.get("date", "")))
    kw = ", ".join(html.escape(str(t)) for t in meta.get("tags", []))

    meta_bits = []
    if date:
        meta_bits.append(f"<b>Date:</b> {date}")
    if kw:
        meta_bits.append(f"<b>Keywords:</b> {kw}")
    meta_line = ("<div class='meta'>" + " &nbsp;·&nbsp; ".join(meta_bits)
                 + "</div>") if meta_bits else ""

    doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>{title}</title>
<style>{CSS}</style></head><body>
<h1 class="title">{title}</h1>
{authors_html}
{affil_html}
{meta_line}
<hr class="rule"/>
{content}
<div class="footnote-block">
Software repository: <a href="https://github.com/anovabr/anova-methods">https://github.com/anovabr/anova-methods</a>
&nbsp;·&nbsp; License: MIT
&nbsp;·&nbsp; Archived releases and the citable DOI are listed in <code>CITATION.cff</code>.
</div>
</body></html>"""

    HTML(string=doc, base_url=str(HERE)).write_pdf(OUT)
    print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
