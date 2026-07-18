"""Biostatistics / risk-factor routines with an R-like API (epitools style)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from .result import Result


def _two_by_two(df, exposure, outcome, exposed, positive):
    """Return counts a,b,c,d for a 2x2 table.

    Rows = exposure (exposed first), cols = outcome (positive first):
        a = exposed & positive, b = exposed & negative,
        c = unexposed & positive, d = unexposed & negative.
    """
    e = df[exposure]
    o = df[outcome]
    mask = e.notna() & o.notna()
    e, o = e[mask], o[mask]

    e_levels = _order_levels(e, exposed)
    o_levels = _order_levels(o, positive)
    if len(e_levels) != 2 or len(o_levels) != 2:
        raise ValueError("exposure and outcome must each have exactly 2 levels")

    exp_hi, exp_lo = e_levels
    out_pos, out_neg = o_levels
    a = int(((e == exp_hi) & (o == out_pos)).sum())
    b = int(((e == exp_hi) & (o == out_neg)).sum())
    c = int(((e == exp_lo) & (o == out_pos)).sum())
    d = int(((e == exp_lo) & (o == out_neg)).sum())
    return a, b, c, d, (exp_hi, exp_lo), (out_pos, out_neg)


def _order_levels(series, preferred):
    levels = list(pd.unique(series.dropna()))
    if preferred is not None:
        if preferred not in levels:
            raise ValueError(f"level {preferred!r} not found in data")
        rest = [x for x in levels if x != preferred]
        return [preferred] + rest
    try:
        return sorted(levels, reverse=True)  # 1/True/"yes" first by default
    except TypeError:
        return levels


def _z(conf):
    return stats.norm.ppf(1 - (1 - conf) / 2)


def _chi2_p(a, b, c, d):
    chi2, p, _, _ = stats.chi2_contingency(np.array([[a, b], [c, d]]),
                                           correction=False)
    return chi2, p


def riskratio(df, exposure, outcome, exposed=None, positive=None, conf=0.95):
    """Risk (incidence) ratio for a 2x2 table, epitools::riskratio style.

    RR = [a/(a+b)] / [c/(c+d)]. CI by the log method (Katz).
    """
    a, b, c, d, elv, olv = _two_by_two(df, exposure, outcome, exposed, positive)
    r1, r0 = a / (a + b), c / (c + d)
    rr = r1 / r0
    se = np.sqrt(b / (a * (a + b)) + d / (c * (c + d)))
    z = _z(conf)
    lo, hi = np.exp(np.log(rr) - z * se), np.exp(np.log(rr) + z * se)
    _, p = _chi2_p(a, b, c, d)
    values = {"rr": rr, "ci_low": lo, "ci_high": hi, "conf": conf, "p": p,
              "a": a, "b": b, "c": c, "d": d, "risk_exposed": r1,
              "risk_unexposed": r0}
    summary = (f"Risk ratio ({elv[0]} vs {elv[1]}, outcome={olv[0]})\n"
               f"  RR = {rr:.3f}, {int(conf*100)}% CI [{lo:.3f}, {hi:.3f}], "
               f"p = {p:.4f}")
    return Result("riskratio", values, summary)


def oddsratio(df, exposure, outcome, exposed=None, positive=None, conf=0.95):
    """Odds ratio for a 2x2 table, epitools::oddsratio (Wald) style.

    OR = ad / bc. CI by the log method (Woolf).
    """
    a, b, c, d, elv, olv = _two_by_two(df, exposure, outcome, exposed, positive)
    or_ = (a * d) / (b * c)
    se = np.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    z = _z(conf)
    lo, hi = np.exp(np.log(or_) - z * se), np.exp(np.log(or_) + z * se)
    _, p = _chi2_p(a, b, c, d)
    values = {"or": or_, "ci_low": lo, "ci_high": hi, "conf": conf, "p": p,
              "a": a, "b": b, "c": c, "d": d}
    summary = (f"Odds ratio ({elv[0]} vs {elv[1]}, outcome={olv[0]})\n"
               f"  OR = {or_:.3f}, {int(conf*100)}% CI [{lo:.3f}, {hi:.3f}], "
               f"p = {p:.4f}")
    return Result("oddsratio", values, summary)


def attributable_risk(df, exposure, outcome, exposed=None, positive=None,
                      conf=0.95):
    """Attributable-risk family for a 2x2 cohort table.

    Reports the risk difference (attributable risk, AR = Re - Ru) with a Wald
    CI, the attributable risk percent among the exposed (ARP = (Re-Ru)/Re),
    the population attributable risk (PAR = Rt - Ru) and its percent (PAR% =
    (Rt-Ru)/Rt), and the number needed to treat/harm (NNT = 1/|AR|).
    """
    a, b, c, d, elv, olv = _two_by_two(df, exposure, outcome, exposed, positive)
    n1, n0 = a + b, c + d
    re, ru = a / n1, c / n0
    rt = (a + c) / (n1 + n0)  # total risk in the whole sample
    ar = re - ru
    se = np.sqrt(re * (1 - re) / n1 + ru * (1 - ru) / n0)
    z = _z(conf)
    ar_lo, ar_hi = ar - z * se, ar + z * se
    arp = (re - ru) / re if re > 0 else np.nan          # among exposed
    par = rt - ru
    parp = (rt - ru) / rt if rt > 0 else np.nan         # in the population
    nnt = 1 / abs(ar) if ar != 0 else np.inf
    values = {"ar": ar, "ci_low": ar_lo, "ci_high": ar_hi, "conf": conf,
              "arp": arp, "par": par, "parp": parp, "nnt": nnt,
              "risk_exposed": re, "risk_unexposed": ru, "risk_total": rt,
              "a": a, "b": b, "c": c, "d": d}
    summary = (f"Attributable risk ({elv[0]} vs {elv[1]}, outcome={olv[0]})\n"
               f"  AR (risk difference) = {ar:.4f}, {int(conf*100)}% CI "
               f"[{ar_lo:.4f}, {ar_hi:.4f}]\n"
               f"  ARP (exposed) = {100*arp:.1f}%   "
               f"PAR = {par:.4f}   PAR% = {100*parp:.1f}%   "
               f"NNT = {nnt:.1f}")
    return Result("attributable_risk", values, summary)
