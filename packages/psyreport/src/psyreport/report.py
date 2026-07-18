"""Render psy result objects to APA-7 style text.

Dispatch is by the result's ``kind`` tag, so psyreport has no import dependency
on psystats or psymetrics — it renders anything following the Result convention.
"""
from __future__ import annotations


def report(result, style="text"):
    """Return an APA-7 formatted string describing a psy result."""
    kind = getattr(result, "kind", None)
    v = getattr(result, "values", None)
    if kind is None or not isinstance(v, dict):
        raise TypeError("report() expects a psy Result object")
    fn = _RENDERERS.get(kind)
    if fn is None:
        raise ValueError(f"no APA renderer for result kind {kind!r}")
    return fn(v, result)


# ---- formatting helpers -----------------------------------------------------

def _nz(x, dec=2):
    """Format a value bounded by |1| without a leading zero (APA)."""
    s = f"{x:.{dec}f}"
    return s.replace("0.", ".", 1) if s.startswith(("0.", "-0.")) else s


def _apa_p(p):
    return "p < .001" if p < 0.001 else f"p = {_nz(p, 3)}"


def _df(x):
    xi = int(round(x))
    return str(xi) if abs(x - xi) < 1e-6 else f"{x:.1f}"


# ---- renderers --------------------------------------------------------------

def _alpha(v, r):
    conf = int(v["conf"] * 100)
    return (f"Cronbach's α = {_nz(v['raw_alpha'])}, {conf}% CI "
            f"[{_nz(v['ci_low'])}, {_nz(v['ci_high'])}], based on {v['k']} "
            f"items (N = {v['n']}).")


def _riskratio(v, r):
    conf = int(v["conf"] * 100)
    return (f"RR = {v['rr']:.2f}, {conf}% CI "
            f"[{v['ci_low']:.2f}, {v['ci_high']:.2f}], {_apa_p(v['p'])}.")


def _oddsratio(v, r):
    conf = int(v["conf"] * 100)
    return (f"OR = {v['or']:.2f}, {conf}% CI "
            f"[{v['ci_low']:.2f}, {v['ci_high']:.2f}], {_apa_p(v['p'])}.")


def _attributable_risk(v, r):
    conf = int(v["conf"] * 100)
    return (f"The attributable risk (risk difference) was {_nz(v['ar'])}, "
            f"{conf}% CI [{_nz(v['ci_low'])}, {_nz(v['ci_high'])}]. The "
            f"attributable risk percent among the exposed was "
            f"{v['arp']*100:.1f}%, the population attributable risk was "
            f"{_nz(v['par'])} ({v['parp']*100:.1f}%), and the number needed to "
            f"treat was {v['nnt']:.1f}.")


def _ttest(v, r):
    d = v["cohens_d"]
    return (f"t({_df(v['df'])}) = {v['t']:.2f}, {_apa_p(v['p'])}, "
            f"d = {_nz(d)}.")


def _anova(v, r):
    return (f"F({v['df_between']}, {v['df_within']}) = {v['F']:.2f}, "
            f"{_apa_p(v['p'])}, η² = {_nz(v['eta_squared'])}.")


def _chisq(v, r):
    return (f"χ²({v['df']}, N = {v['n']}) = {v['chi2']:.2f}, {_apa_p(v['p'])}, "
            f"Cramér's V = {_nz(v['cramers_v'])}.")


def _corr_matrix(v, r):
    return ("Table\nCorrelations.\n\n"
            f"{v['display'].to_string()}\n\n"
            "Note. * p < .05. ** p < .01. *** p < .001.")


def _freq(v, r):
    return ("Table\nFrequency distribution.\n\n"
            f"{v['freq'].round(1).to_string()}\n\n"
            "Note. Percentages are of valid responses.")


def _linreg(v, r):
    c = v["coefs"]
    lines = [f"Linear regression predicting {v['outcome']}.",
             f"R² = {_nz(v['r2'])}, adjusted R² = {_nz(v['adj_r2'])}, "
             f"F({v['df_model']}, {v['df_resid']}) = {v['f']:.2f}, "
             f"{_apa_p(v['f_p'])}, N = {v['n']}.", ""]
    for name in c.index:
        if name == "const":
            continue
        lines.append(f"{name}: b = {c.loc[name, 'b']:.3f}, β = "
                     f"{_nz(c.loc[name, 'beta'])}, {_apa_p(c.loc[name, 'p'])}.")
    return "\n".join(lines)


def _logreg(v, r):
    c = v["coefs"]
    lines = [f"Logistic regression predicting {v['outcome']}.",
             f"McFadden pseudo-R² = {_nz(v['pseudo_r2'])}, N = {v['n']}.", ""]
    for name in c.index:
        if name == "const":
            continue
        lines.append(f"{name}: OR = {c.loc[name, 'or']:.2f}, 95% CI "
                     f"[{c.loc[name, 'or_ci_low']:.2f}, "
                     f"{c.loc[name, 'or_ci_high']:.2f}], "
                     f"{_apa_p(c.loc[name, 'p'])}.")
    return "\n".join(lines)


def _efa(v, r):
    load = v["loadings"].round(2).copy()
    load["h²"] = v["communalities"].round(2).values
    var = v["variance"]
    prop = ", ".join(f"{f} = {100*p:.1f}%"
                     for f, p in zip(var.index, var["prop_var"]))
    return (f"Table\nExploratory factor analysis: factor loadings.\n\n"
            f"{load.to_string()}\n\n"
            f"Note. Extraction: {v['method']}; rotation: {v['rotation']}. "
            f"h² = communality. Variance explained per factor: {prop}. "
            f"Total = {100*var['cum_var'].iloc[-1]:.1f}%.")


def _cfa(v, r):
    fit = v["fit"]
    est = v["est_col"]
    load = v["loadings"][["lval", "rval", est, "p-value"]].copy()
    load.columns = ["indicator", "factor", "std_loading", "p"]
    return (f"Confirmatory factor analysis.\n"
            f"The model fit the data with χ²({fit['df']:.0f}) = "
            f"{fit['chi2']:.2f}, {_apa_p(fit['chi2_p'])}, CFI = "
            f"{_nz(fit['cfi'])}, TLI = {_nz(fit['tli'])}, RMSEA = "
            f"{_nz(fit['rmsea'])}.\n\nStandardized loadings:\n"
            f"{load.round(3).to_string(index=False)}")


def _describe(v, r):
    return ("Table\nDescriptive statistics.\n\n"
            f"{r.table.round(2).to_string()}\n\n"
            "Note. SD = standard deviation.")


def _table1(v, r):
    return (f"Table 1\nSample characteristics by {v['group']}.\n\n"
            f"{r.table.to_string(index=False)}\n\n"
            "Note. Continuous variables are shown as M (SD) or Mdn [IQR]; "
            "categorical variables as n (%). Tests were selected automatically "
            "by variable type and distribution.")


_RENDERERS = {
    "alpha": _alpha,
    "riskratio": _riskratio,
    "oddsratio": _oddsratio,
    "attributable_risk": _attributable_risk,
    "ttest": _ttest,
    "anova": _anova,
    "chisq": _chisq,
    "corr_matrix": _corr_matrix,
    "freq": _freq,
    "linreg": _linreg,
    "logreg": _logreg,
    "efa": _efa,
    "cfa": _cfa,
    "describe": _describe,
    "table1": _table1,
}
