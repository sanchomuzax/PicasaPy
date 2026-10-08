"""A windowsos tesztdarab kapjon elég időt, az ubuntu-mátrix maradjon érintetlen (#4667)."""

from __future__ import annotations

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_WORKFLOW = _ROOT / ".github" / "workflows" / "teszt-darabok.yml"


def test_a_windows_hatarido_60_perc_az_ubuntu_40_marad() -> None:
    """A Windows kapjon 20 perc többletet, a közös négydarabos mátrix maradjon."""
    forras = _WORKFLOW.read_text(encoding="utf-8")
    talalat = re.search(r"(?m)^\s*timeout-minutes:\s*(.+?)\s*$", forras)
    matrix = re.search(r"(?m)^\s*shard:\s*\[([^]]+)\]\s*$", forras)

    assert talalat is not None, "hiányzik a teszt-job időkorlátja"
    assert talalat.group(1) == "${{ inputs.os == 'windows-latest' && 60 || 40 }}"
    assert matrix is not None, "hiányzik a darabmátrix"
    assert [int(elem.strip()) for elem in matrix.group(1).split(",")] == [1, 2, 3, 4]
