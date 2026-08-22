"""A forrás fordítható SyntaxWarning nélkül (#1242).

## A tulajdonos jelentése (v0.8.42, Windows)

```
export_controller.py:105: SyntaxWarning: invalid escape sequence '\\ '
```

A #1166-ban írt docstringbe bekerült egy `\\ ` sorozat (a Windows tiltott
fájlnév-karaktereinek felsorolása). Python 3.12-ben az ismeretlen
escape-sorozat figyelmeztetés — minden induláskor kiírja.

## Miért jutott ki, és miért ez a teszt

A `ruff` alapbeállítása ezt nem jelzi, a tesztek pedig nem fordították le
a forrást figyelmeztetés-figyeléssel — a CI zölden átengedte. Ez az őr a
teljes `src/` fát lefordítja, és minden `SyntaxWarning`-ot hibának vesz:
így a jövőbeli előfordulás a KIADÁS ELŐTT kiderül.

A funkcióra nincs hatása, de zajos — és épp az ilyen üzenetek fedik el a
valódi hibákat a naplóban (#1185).
"""

from __future__ import annotations

import warnings
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"


def test_a_teljes_forras_figyelmeztetes_nelkul_fordul():
    talalatok: list[str] = []
    for fajl in sorted(_SRC.rglob("*.py")):
        with warnings.catch_warnings(record=True) as fogott:
            warnings.simplefilter("always")
            compile(fajl.read_text(encoding="utf-8"), str(fajl), "exec")
        for tetel in fogott:
            if issubclass(tetel.category, SyntaxWarning):
                talalatok.append(
                    f"{fajl.relative_to(_SRC)}: {tetel.category.__name__}: "
                    f"{tetel.message}"
                )
    assert not talalatok, (
        "SyntaxWarning a forrásban (a felhasználó minden induláskor látja):\n  "
        + "\n  ".join(talalatok)
    )
