"""Shared lightweight result object (mirrors psystats.result.Result).

Kept local so psymetrics has no cross-package runtime dependency. psyreport
dispatches on ``kind``.
"""
from __future__ import annotations


class Result:
    def __init__(self, kind: str, values: dict, summary: str, table=None):
        self.kind = kind
        self.values = values
        self._summary = summary
        self.table = table

    def __repr__(self) -> str:
        return self._summary
