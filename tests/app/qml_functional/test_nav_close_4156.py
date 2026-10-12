"""A szerkesztői nagyítás-navigátor a Picasa felületének része (#4568)."""

from __future__ import annotations

import csv
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_CSV = _ROOT / "docs/specs/ui-lefedettseg-elemek.csv"
_PANELEK_CSV = _ROOT / "docs/specs/ui-lefedettseg-megfeleltetes.csv"


def test_a_nagyitas_navigatora_megfeleltetett_photo_viewer_elem():
    rows = list(csv.reader(_CSV.open(encoding="utf-8")))
    panels = list(csv.reader(_PANELEK_CSV.open(encoding="utf-8")))
    panel = next(row for row in panels[1:] if row[0] == "nav")
    close = next(row for row in rows if row[0] == "nav/close")

    assert panel[1] == "parositva"
    assert "PhotoViewer.qml" in panel[2]
    assert close[1] == "megvan"
    assert "ZoomNavigator.qml" in close[2]
    assert "nagyítás" in close[3].lower()
