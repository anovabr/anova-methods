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

This mints a real, citable DOI and needs no peer review. Do it before the JOSS
submission, because JOSS asks for an archived release.

1. Sign in at https://zenodo.org with the GitHub account that owns the repo.
2. Go to https://zenodo.org/account/settings/github/ and switch this repository
   **on**. Zenodo only archives releases created *after* the switch is flipped,
   so do this first.
3. Publish a GitHub release (step 3 above). Zenodo archives the tarball and
   mints the DOI within a few minutes.
4. Zenodo issues two DOIs. The **concept DOI** always resolves to the newest
   version and is the one to cite; each release also gets its own version DOI.
5. Paste the concept DOI into `CITATION.cff` (an `identifiers:` block is
   prepared there, commented out) and add the badge to `README.md`:

   ```markdown
   [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
   ```

`.zenodo.json` in the repository root supplies the record's title, description,
authors, ORCID, keywords, and licence, so the Zenodo entry is populated rather
than inheriting bare defaults. Check the draft record once before publishing;
Zenodo has changed its metadata schema over time, and the `license` field is the
one most likely to need adjusting in the web form.

## 5. JOSS submission

`paper/paper.md` is the JOSS manuscript. It covers all three packages as one
ecosystem, which is the stronger submission: JOSS expects software representing
substantial scholarly effort and uses roughly a thousand lines of code as a
rule of thumb, and no single package here clears that bar alone.

Before submitting, confirm the checklist JOSS reviewers work through:

- [x] OSI approved licence (MIT)
- [x] Public repository with version control
- [x] Automated tests (`pytest packages/`)
- [x] Community guidelines (`CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`)
- [x] Statement of need in the paper
- [x] Documented API with runnable examples
- [ ] An archived release with a DOI (step 4)

Submit at https://joss.theoj.org with the repository URL and the archive DOI.
JOSS builds its own branded PDF from `paper.md` and `paper.bib` using the
`openjournals/inara` container, so the locally built `paper/paper.pdf` is for
preview and circulation rather than for submission.

To rebuild the local preview:

```bash
pip install pypandoc_binary weasyprint pyyaml
python paper/build_paper.py
```
