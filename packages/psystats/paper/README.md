# The `psystats` paper

| File | Purpose |
|---|---|
| `paper.md` | the manuscript (JOSS-style YAML front matter + body) |
| `paper.bib` | BibTeX bibliography |
| `apa.csl` | APA 7th citation style, vendored so builds work offline |
| `build_paper.py` | renders `paper.md` → `paper.pdf` |
| `paper.pdf` | the built article |

## Building the PDF

The build needs no LaTeX — pandoc renders the Markdown (resolving citations
with `--citeproc`), and WeasyPrint prints the styled HTML to PDF.

```bash
pip install pypandoc_binary weasyprint pyyaml
python packages/psystats/paper/build_paper.py
```

WeasyPrint cannot render MathML, so inline math is mapped to Unicode
equivalents by the `MATH` table in `build_paper.py`. The script warns on stderr
if it meets math it does not know how to convert — extend that table rather
than leaving `$...$` in the output.

## Note on the official JOSS build

If this is submitted to the Journal of Open Source Software, JOSS builds the
PDF itself from `paper.md` and `paper.bib` using its own
[`openjournals/inara`](https://github.com/openjournals/inara) container, and
the result carries JOSS branding. The local build here is for previewing and
for circulating the manuscript as a standalone article; it is not a
reproduction of the JOSS template.
