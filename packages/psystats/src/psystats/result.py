"""Shared lightweight result object.

Every psy result carries a ``kind`` tag and a ``values`` dict of raw numbers.
psyreport dispatches on ``kind`` for APA-7 rendering, so packages never need to
import psyreport (no circular dependency). Results also print an R-style
summary via ``__repr__``.
"""
from __future__ import annotations


class Result:
    def __init__(self, kind: str, values: dict, summary: str, table=None):
        self.kind = kind
        self.values = values
        self._summary = summary
        self.table = table  # optional pandas DataFrame

    def __repr__(self) -> str:
        return self._summary
