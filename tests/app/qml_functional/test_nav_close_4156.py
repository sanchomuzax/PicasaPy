"""A bal navigációs hasáb bezárható a főablakból (#4156)."""

from __future__ import annotations

import csv
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_CSV = _ROOT / "docs/specs/ui-lefedettseg-elemek.csv"


def test_a_nagyitas_navigatora_a_megfeleltetesi_csv_ben_indokolt_nem_cel():
    rows = list(csv.reader(_CSV.open(encoding="utf-8")))
    row = next(row for row in rows[1:] if row[0] == "nav/close")
    assert row[1] == "nem-cel"
    assert "nav.tre" in row[2]
    assert "navigátor" in row[3].lower()
