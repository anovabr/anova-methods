# Contributing to ANOVA Methods

Contributions are welcome, whether that is a bug report, a new statistic, a
better docstring, or a correction to a formula.

## Reporting a problem

Open an issue at
https://github.com/anovabr/anova-methods/issues and include:

- what you ran (a short, self contained snippet, ideally on `load_mapfre()`),
- what you expected,
- what you got, including the full traceback if there was one,
- your Python version and the package versions (`pip show psystats`).

If you believe a reported statistic is wrong, say what value you expected and
where it comes from (an R package and its version, a textbook formula, or a
published worked example). Numerical disagreements are the most valuable
reports this project receives, and a reference value makes them straightforward
to act on.

## Asking for help

Open an issue with the `question` label. Usage questions are welcome, and a
question that turns out to be hard to answer usually indicates a documentation
gap worth fixing.

## Contributing code

1. Fork the repository and create a branch off `main`.
2. Install the packages in editable mode along with the test tooling:

   ```bash
   pip install -e packages/psystats -e packages/psymetrics -e packages/psyreport
   pip install pytest
   ```

3. Make the change and add a test for it.
4. Run the suite:

   ```bash
   pytest packages/
   ```

5. Open a pull request describing what changed and why.

### What a good test looks like

Estimates are validated against an independent reference rather than against
this package's own output. When adding a statistic, check it against `scipy`,
`statsmodels`, a closed form identity, or a published worked example. A test
that only asserts the code returns what it currently returns will not catch the
errors that matter here.

### Style

Follow the surrounding code. Public functions take a `DataFrame` first, use
argument names that mirror the R analogue where one exists, and return a
`Result` carrying a `kind` tag, a `values` dictionary, and an optional table.
If a new result type should be reportable, add a renderer to `psyreport` keyed
on that `kind`.

### Documentation

`packages/psystats/EXAMPLES.md` is generated, not hand written. If you change
behaviour that appears in it, regenerate it rather than editing the Markdown:

```bash
python packages/psystats/tools/generate_examples.py
```

## Code of conduct

Participation in this project is governed by [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
