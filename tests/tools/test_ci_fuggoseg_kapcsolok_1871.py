"""#1871 — a CI csak LÉTEZŐ `print_dependencies.py`-kapcsolót hívhat.

## A hiba, ami ezt kikényszerítette

A #1863 új `docs-orok` jobja a `--pip` kapcsolót hívta. **Ilyen kapcsoló
nincs** (`--dev`, `--all`, `--apt` van). A hiba mégsem látszott, mert így
volt írva:

```
python3 scripts/print_dependencies.py --pip | xargs -r python3 -m pip install
```

Csővezetékben a kilépőkód az UTOLSÓ tagé, az `xargs -r` pedig üres
bemenetre SIKERREL tér vissza. A lépés tehát zölden ment tovább, **egyetlen
csomag telepítése nélkül**, és a job két lépéssel később halt meg
(`No module named pytest`) — a valódi okától távol.

⚠️ És mivel a #1863 a `docs-orok`-nak FOGAT adott (a kötelező ellenőrzés
megvárja), ez **minden csak-dokumentációs PR-t blokkolt**. A javítás előtti
állapotnál rosszabb: a hiba előbb néma volt, utána hangos, de mindent
megállított.

## Amit ez az őr rögzít

1. minden munkafolyamat-hívás LÉTEZŐ kapcsolót használ;
2. a csomagtelepítés nem csővezetéken megy, ahol a hiba elveszik.

Az 1. pontot a szkript SAJÁT értelmezőjétől kérdezzük, nem beégetett
listától — így új kapcsolónál magától bővül.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
MUNKAFOLYAMATOK = sorted((REPO / ".github" / "workflows").glob("*.yml"))
SZKRIPT = REPO / "scripts" / "print_dependencies.py"

#: `print_dependencies.py … --valami`
_HIVAS = re.compile(r"print_dependencies\.py((?:\s+--[a-z-]+)*)")


def _ervenyes_kapcsolok() -> set[str]:
    """A szkript saját súgójából — nem beégetve."""
    sugo = subprocess.run(
        [sys.executable, str(SZKRIPT), "--help"],
        capture_output=True, text=True, check=True,
    ).stdout
    return set(re.findall(r"--[a-z-]+", sugo)) | {"--help"}


def _hivasok() -> list[tuple[Path, str]]:
    talalt = []
    for f in MUNKAFOLYAMATOK:
        for m in _HIVAS.finditer(f.read_text(encoding="utf-8")):
            for kapcsolo in m.group(1).split():
                talalt.append((f, kapcsolo))
    return talalt


def test_van_mit_ellenoriznunk():
    """Üres méréssel a többi állítás semmit nem érne."""
    assert _hivasok(), "egyetlen print_dependencies-hívást sem találtam"


@pytest.mark.parametrize("fajl,kapcsolo", _hivasok(),
                         ids=lambda ertek: getattr(ertek, "name", str(ertek)))
def test_letezo_kapcsolo(fajl: Path, kapcsolo: str):
    ervenyes = _ervenyes_kapcsolok()
    assert kapcsolo in ervenyes, (
        f"{fajl.name}: a(z) {kapcsolo} kapcsoló nem létezik "
        f"(érvényes: {sorted(ervenyes)})"
    )


def test_a_telepites_nem_csovezeteken_megy():
    """Csőben a hiba elveszik — a #1871 pontosan ezen csúszott át."""
    rosszak = []
    for f in MUNKAFOLYAMATOK:
        for sor in f.read_text(encoding="utf-8").splitlines():
            if "print_dependencies.py" in sor and "|" in sor:
                rosszak.append(f"{f.name}: {sor.strip()}")
    assert not rosszak, (
        "a csomaglistát csővezetéken adjuk tovább; ott a hibás kilépőkód "
        f"elveszik — használj parancs-behelyettesítést: {rosszak}"
    )
