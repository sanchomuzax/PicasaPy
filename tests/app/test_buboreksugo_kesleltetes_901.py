"""#901: MINDEN buboréksúgó az egységes késleltetést kapja.

## Miért forrás-szintű őr

A `ToolTip` a QML-ben **csatolt tulajdonság**, nem komponens: a
`ToolTip.text` és a `ToolTip.delay` külön sorokban ül a hívó elemen. Egy
futásidejű próba ezt nehezen éri el (a csatolt tulajdonságot a teszt nem
tudja kiolvasni — `property("ToolTip.text")` → `null`, ld. a
`PicasaMenuItem.qml` megjegyzését), a hiány viszont a forrásban
kényelmesen mérhető.

## A mért állapot (2026-09-12)

A jegy törzse még **nyolc** `ToolTip`-használó fájlról írt. Azóta **21**
fájl használja, **77** valódi `ToolTip.text` kötéssel — és ezek közül
**hét** nem kapott késleltetést, tehát a Qt alapértelmezésével jelent meg,
nem a `Theme.tooltipDelay`-jel:

| fájl | hiányzó kötés |
|---|---:|
| `FolderPane.qml` | 1 |
| `MainToolbar.qml` | 1 |
| `PhotoViewer.qml` | 2 |
| `PicasaMenuItem.qml` | 1 |
| `UnnamedFacesView.qml` | 2 |

⚠️ Ez az őr **a késleltetés egységességét** méri, semmi mást. A jegy első
pontja (közös `PicasaToolTip` komponens) NEM ez: ahhoz stílus-szintű
`ToolTip` kell, mert a csatolt tulajdonságot komponensre cserélni minden
hívóhely átírását jelentené.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

QML_GYOKER = Path(__file__).resolve().parents[2] / "src/picasapy/app/qml"

_TEXT = re.compile(r"^[ \t]*ToolTip\.text:", re.M)
_DELAY = re.compile(r"^[ \t]*ToolTip\.delay:", re.M)
_EGYSEGES = re.compile(r"^[ \t]*ToolTip\.delay:[ \t]*Theme\.tooltipDelay[ \t]*$", re.M)

#: A 2026-09-12-i mérés. Ha a felület nő, a próba szándékosan megbukik, és a
#: következő kör tudja, hogy a jegy törzsében álló szám elavult.
MERT_SUGO_SZAM = 77

#: Az öt fájl, amelyikből a késleltetés hiányzott — ide ne csússzon vissza.
POTOLT = (
    "FolderPane.qml",
    "MainToolbar.qml",
    "PhotoViewer.qml",
    "PicasaMenuItem.qml",
    "UnnamedFacesView.qml",
)


def _qml_fajlok() -> list[Path]:
    fajlok = sorted(QML_GYOKER.rglob("*.qml"))
    assert fajlok, "nem találtam QML-fájlt — rossz a gyökér?"
    return fajlok


class TestMindenSugoKapKesleltetest:
    def test_minden_fajlban_annyi_delay_van_ahany_text(self):
        """A kettő száma fájlonként egyezzen — enélkül egy súgó a Qt
        alapértelmezésével jelenne meg, a többi meg a méréssel."""
        eltero: list[str] = []
        for ut in _qml_fajlok():
            szoveg = ut.read_text(encoding="utf-8")
            t, d = len(_TEXT.findall(szoveg)), len(_DELAY.findall(szoveg))
            if t != d:
                eltero.append(f"{ut.name}: text={t} delay={d}")
        assert not eltero, (
            "buboréksúgó egységes késleltetés nélkül (#901): " + " · ".join(eltero)
        )

    def test_a_kesleltetes_MINDENHOL_a_temabol_jon(self):
        """Beégetett millisekundum sehol — a #901 lényege, hogy egy helyen
        lehessen állítani."""
        beegetett: list[str] = []
        for ut in _qml_fajlok():
            szoveg = ut.read_text(encoding="utf-8")
            osszes = len(_DELAY.findall(szoveg))
            temabol = len(_EGYSEGES.findall(szoveg))
            if osszes != temabol:
                beegetett.append(f"{ut.name}: {osszes - temabol} nem a Theme-ből")
        assert not beegetett, (
            "a buboréksúgó késleltetése nem a `Theme.tooltipDelay`-ből jön: "
            + " · ".join(beegetett)
        )


class TestAMertDarabszam:
    def test_a_sugok_szama_nem_csokkent(self):
        ossz = sum(
            len(_TEXT.findall(ut.read_text(encoding="utf-8"))) for ut in _qml_fajlok()
        )
        assert ossz >= MERT_SUGO_SZAM, (
            f"{ossz} buboréksúgó — kevesebb a 2026-09-12-én mért "
            f"{MERT_SUGO_SZAM}-nél; ha ez szándékos, írd át a számot ÉS a jegyet"
        )

    @pytest.mark.parametrize("nev", POTOLT)
    def test_a_potolt_ot_fajl_mind_egyseges(self, nev: str):
        ut = next(p for p in _qml_fajlok() if p.name == nev)
        szoveg = ut.read_text(encoding="utf-8")
        assert len(_TEXT.findall(szoveg)) == len(_EGYSEGES.findall(szoveg))
