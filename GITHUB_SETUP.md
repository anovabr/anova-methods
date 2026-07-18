# GitHub + release setup

This repo is ready to push to `github.com/anovabr/anova-methods`. It ships two
workflows, a JOSS paper draft, and citation metadata.

## 1. Create the repo and push

```bash
git init
git add .
git commit -m "ANOVA Methods 0.1.0: psystats, psymetrics, psyreport"
git branch -M main
git remote add origin https://github.com/anovabr/anova-methods.git
git push -u origin main
```

`.github/workflows/ci.yml` then runs the full test suite on Python 3.10–3.12 for
every push and pull request.

## 2. Trusted publishing (no token needed for future releases)

Because you linked PyPI to GitHub, configure a Trusted Publisher on each of the
three PyPI projects so `.github/workflows/publish.yml` can upload via OIDC.

For each of `psystats`, `psymetrics`, `psyreport`: PyPI → the project → Manage →
Publishing → "Add a new publisher" with:

- Owner: `anovabr`
- Repository: `anova-methods`
- Workflow name: `publish.yml`
- Environment: `pypi`

## 3. Cut a release

Version numbers on PyPI cannot be reused, so bump each package's `version` in
its `pyproject.toml` (e.g. `0.1.1`) before releasing. Then on GitHub, draft a
release with a tag like `v0.1.1` and publish it. The publish workflow builds all
three packages and uploads them automatically — no token, no local `twine`.

## 4. DOI for citations (Zenodo)

Enable the Zenodo–GitHub integration for this repo, then publish a GitHub
release. Zenodo mints a DOI and archives the release, giving you a citable
software DOI. Add that DOI to `CITATION.cff` and the README badge.

## 5. JOSS submission

`packages/psystats/paper/paper.md` is a JOSS draft. Before submitting, note that
JOSS expects software of substantial scholarly effort; consider growing the API
surface and, if reviewers prefer, submitting one paper covering the whole ANOVA
Methods ecosystem rather than one per package. Submit at https://joss.theoj.org
with the repository URL once a release and DOI exist.
