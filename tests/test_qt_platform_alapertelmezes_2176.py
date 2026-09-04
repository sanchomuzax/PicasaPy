"""#2176: Qt-alkalmazást létrehozó tesztmodul NE függjön valódi
megjelenítőtől.

A `QGuiApplication([])` valódi platform-plugint próbál betölteni. Ha nincs
használható megjelenítő (fejnélküli gép, törött X11-hitelesítés, konténer),
a Qt nem kivételt dob, hanem **abortál** — a pytest `Fatal Python error:
Aborted`-tal, 134-es kilépőkóddal áll meg, és a már lefutott próbák
eredménye is elvész.

Mérve a #2176-ban: platform-alapértelmezés nélkül 3/3 futás abortált,
`QT_QPA_PLATFORM=offscreen`-nel 3/3 zöld volt.

A projekt bevett védelme az `os.environ.setdefault("QT_QPA_PLATFORM",
"offscreen")` — a `tests/app/conftest.py` az egész `tests/app/` fát így
fedi. Ez az őr azt tartatja be, hogy **minden** Qt-alkalmazást példányosító
tesztmodul kapjon ilyen védelmet: vagy maga állítsa be, vagy a mappájában
(illetve valamelyik szülőmappájában) legyen conftest, ami beállítja.

`setdefault`, tehát aki valódi megjelenítőn akar futni, továbbra is
felülírhatja a környezetből.
"""

from __future__ import annotations

import re
from pathlib import Path

TESZTGYOKER = Path(__file__).resolve().parent

#: Qt-alkalmazás példányosítása — `QGuiApplication([])`, `QApplication([])`,
#: `QCoreApplication([])` és a szóközös/argumentumos változataik.
_PELDANYOSITAS = re.compile(r"\bQ(?:Gui|Core)?Application\s*\(\s*\[")

#: A védelem: a platform alapértelmezésének beállítása.
_VEDELEM = re.compile(
    r"""environ\s*\.\s*setdefault\s*\(\s*["']QT_QPA_PLATFORM["']"""
)


def _vedett(modul: Path) -> bool:
    """Igaz, ha a modul maga vagy valamelyik szülőmappájának conftestje
    beállítja a platform alapértelmezését."""
    if _VEDELEM.search(modul.read_text(encoding="utf-8")):
        return True
    mappa = modul.parent
    while True:
        conftest = mappa / "conftest.py"
        if conftest.exists() and _VEDELEM.search(
            conftest.read_text(encoding="utf-8")
        ):
            return True
        if mappa == TESZTGYOKER:
            return False
        mappa = mappa.parent


def _qt_alkalmazast_letrehozo_modulok() -> list[Path]:
    return sorted(
        p
        for p in TESZTGYOKER.rglob("*.py")
        if "__pycache__" not in p.parts
        and _PELDANYOSITAS.search(p.read_text(encoding="utf-8"))
    )


def test_az_or_talal_ilyen_modult() -> None:
    """A minta foga: ha a keresés semmit nem talál, az őr nem őriz semmit."""
    assert _qt_alkalmazast_letrehozo_modulok(), (
        "egyetlen Qt-alkalmazást létrehozó tesztmodult sem találtam — "
        "a minta elavult, az őr vak"
    )


def test_minden_qt_alkalmazast_letrehozo_modul_vedett() -> None:
    vedtelen = [
        str(p.relative_to(TESZTGYOKER))
        for p in _qt_alkalmazast_letrehozo_modulok()
        if not _vedett(p)
    ]
    assert not vedtelen, (
        "Qt-alkalmazást hoz létre, de nincs platform-alapértelmezése "
        "(valódi megjelenítő nélkül abortál, #2176): " + ", ".join(vedtelen)
    )
