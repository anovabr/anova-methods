"""Exploratory factor analysis and factorability checks (psych/factor_analyzer)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from factor_analyzer import (FactorAnalyzer, calculate_kmo,
                             calculate_bartlett_sphericity)

from .result import Result


def _numeric(data):
    X = pd.DataFrame(data).apply(pd.to_numeric, errors="coerce").dropna(axis=0,
                                                                        how="any")
    if X.shape[1] < 2:
        raise ValueError("need at least 2 items")
    return X


def kmo(data):
    """Kaiser-Meyer-Olkin sampling adequacy (overall and per item)."""
    X = _numeric(data)
    per_item, overall = calculate_kmo(X.values)
    table = pd.Series(per_item, index=X.columns, name="kmo")
    summary = (f"KMO measure of sampling adequacy\n  overall KMO = {overall:.3f}\n\n"
               + table.round(3).to_string())
    return Result("kmo", {"overall": float(overall), "per_item": table},
                  summary, table=table.to_frame())


def bartlett(data):
    """Bartlett's test of sphericity (H0: correlation matrix is identity)."""
    X = _numeric(data)
    chi2, p = calculate_bartlett_sphericity(X.values)
    summary = (f"Bartlett's test of sphericity\n"
               f"  chi2 = {chi2:.3f}, p = {p:.4g}")
    return Result("bartlett", {"chi2": float(chi2), "p": float(p)}, summary)


def efa(data, n_factors, method="minres", rotation="promax"):
    """Exploratory factor analysis with selectable estimator and rotation.

    method   : 'minres' (default), 'ml' (maximum likelihood), or 'principal'.
    rotation : None, 'varimax', 'promax' (default), 'oblimin', 'quartimax',
               'oblimax', 'quartimin', 'equamax' — oblique rotations also return
               the factor correlation matrix (phi).

    Returns loadings, communalities, uniquenesses, eigenvalues, and the variance
    explained per factor (SS loadings, proportion, cumulative).
    """
    X = _numeric(data)
    fa = FactorAnalyzer(n_factors=n_factors, method=method,
                        rotation=rotation)
    fa.fit(X.values)
    fnames = [f"F{i+1}" for i in range(n_factors)]
    loadings = pd.DataFrame(fa.loadings_, index=X.columns, columns=fnames)
    comm = pd.Series(fa.get_communalities(), index=X.columns, name="communality")
    uniq = pd.Series(fa.get_uniquenesses(), index=X.columns, name="uniqueness")
    orig_eig, _ = fa.get_eigenvalues()
    ss, prop, cum = fa.get_factor_variance()
    variance = pd.DataFrame({"ss_loadings": ss, "prop_var": prop,
                             "cum_var": cum}, index=fnames)
    phi = (pd.DataFrame(fa.phi_, index=fnames, columns=fnames)
           if getattr(fa, "phi_", None) is not None else None)

    values = {"loadings": loadings, "communalities": comm, "uniquenesses": uniq,
              "eigenvalues": pd.Series(orig_eig, name="eigenvalue"),
              "variance": variance, "phi": phi, "n_factors": n_factors,
              "method": method, "rotation": rotation}
    summary = (f"Exploratory factor analysis ({method}, "
               f"rotation={rotation}), {n_factors} factors\n\n"
               f"Loadings:\n{loadings.round(3).to_string()}\n\n"
               f"Variance explained:\n{variance.round(3).to_string()}")
    return Result("efa", values, summary, table=loadings)
