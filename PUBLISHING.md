# Publishing to PyPI

**No external approval is required.** PyPI is self-serve: you create an account,
generate an API token, and upload. Nobody at Anthropic, Python, or anywhere else
reviews or approves a package before it goes live. (You may be thinking of
conda-forge or some Linux distributions, which *do* have a review step — plain
`pip install` from PyPI does not.)

The one thing that can block you is a **name collision**: a name is first-come,
first-served. As of the last check, `psystats`, `psymetrics`, and `psyreport`
were all free — but claim them soon, since anyone can register them.

## One-time setup

1. Create an account at https://pypi.org (and, optionally,
   https://test.pypi.org for rehearsals).
2. Enable two-factor authentication.
3. Create an API token (Account settings → API tokens). Use it as the password
   with username `__token__`.

## Build the distributions

Each package is built independently. From the repo root:

```bash
python -m pip install --upgrade build twine
for pkg in psystats psymetrics psyreport; do
  python -m build packages/$pkg
done
python -m twine check packages/*/dist/*
```

This produces a source distribution (`.tar.gz`) and a wheel (`.whl`) under each
`packages/<name>/dist/`.

## Upload

Rehearse on TestPyPI first (recommended):

```bash
python -m twine upload --repository testpypi packages/psystats/dist/*
pip install --index-url https://test.pypi.org/simple/ --no-deps psystats
```

Then publish for real:

```bash
python -m twine upload packages/psystats/dist/*
python -m twine upload packages/psymetrics/dist/*
python -m twine upload packages/psyreport/dist/*
```

After a minute or two, anyone can `pip install psystats psymetrics psyreport`.

## Before the first upload

- Set a final version in each `pyproject.toml` (they are at `0.1.0`).
- A version number can never be reused on PyPI. To fix a mistake you must bump
  the version (e.g. `0.1.1`) and upload again.
- Consider reserving the three names now with an initial `0.1.0` even if you
  keep iterating locally, so nobody else takes them.

## Citation / DOI

For your h-index goal, mint a DOI by connecting the GitHub repo to Zenodo and
cutting a release; then submit a short software paper to JOSS (per package) and,
later, an ecosystem paper to Behavior Research Methods.
