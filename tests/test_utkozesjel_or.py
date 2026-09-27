"""A repó szöveges fájljaiban nem maradhat összefésülési ütközésjel.

2026-09-27-én egy integráció a CHANGELOG-ban bent hagyta a
`<<<<<<< HEAD` … `>>>>>>>` blokkot, és egy bejegyzés a rossz kiadás alá
került; a CHANGELOG-kapu csak azt nézi, van-e új sor, a jeleket nem.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

GYOKER = Path(__file__).resolve().parents[1]
_JEL = re.compile(r"^(<<<<<<< |>>>>>>> |=======$)", re.M)
_KITERJESZTESEK = (".md", ".py", ".qml", ".ts", ".json", ".toml", ".yml", ".tsv")


def _kovetett_fajlok() -> list[Path]:
    kimenet = subprocess.run(
        ["git", "ls-files"], cwd=GYOKER, capture_output=True, text=True, check=True
    ).stdout
    return [
        GYOKER / sor
        for sor in kimenet.splitlines()
        if sor.endswith(_KITERJESZTESEK) and not sor.startswith("research/")
    ]


def test_nincs_utkozesjel_a_kovetett_fajlokban() -> None:
    hibas = []
    for fajl in _kovetett_fajlok():
        if fajl.name == Path(__file__).name or not fajl.is_file():
            continue
        szoveg = fajl.read_text(encoding="utf-8", errors="replace")
        if _JEL.search(szoveg):
            hibas.append(str(fajl.relative_to(GYOKER)))
    assert hibas == [], f"összefésülési ütközésjel maradt: {hibas}"
