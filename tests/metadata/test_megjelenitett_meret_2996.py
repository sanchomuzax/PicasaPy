"""#2996: a MEGJELENÍTETT méret — az EXIF-orientációval korrigálva.

## A mérés (a #1620 készletével)

| orientáció | az index (tárolt) | a dekódolt kép |
|---|---|---|
| 1 | 60 × 40 | 60 × 40 |
| 6 | 60 × 40 | **40 × 60** |
| 8 | 60 × 40 | **40 × 60** |

Az index a fájlban TÁROLT méretet őrzi, a dekódolás viszont alkalmazza az
orientációt (OpenCV, a teljes ÉS a redukált ágon is — mérve). Aki a
`width`/`height` párból arányt számol, forgatott képnél rossz arányt kap:
a kollázs-elrendezés, a néző 1:1 nagyítása és a felbontás-felirat.

## A döntés

**A kanonikus adat marad a tárolt méret + az orientáció** — az index a
fájl igazságát tükrözi, nem a megjelenítését. A fogyasztók viszont a
MEGJELENÍTETT méretet kérik, egyetlen közös segéden át.

⚠️ A `.picasa.ini` `rotate=` forgatása NEM tartozik ide: azt a felület
alkalmazza külön (a dekódolt kép már EXIF-helyes, az ini-forgatás arra
jön rá). A két forgatás tehát halmozódik, és ez szándékos.
"""

from __future__ import annotations

import pytest

from picasapy.metadata import megjelenitett_meret


class TestAzAllo:
    @pytest.mark.parametrize("orientacio", [5, 6, 7, 8])
    def test_az_ALLO_allasok_cserelik_az_oldalakat(self, orientacio):
        assert megjelenitett_meret(60, 40, orientacio) == (40, 60)

    @pytest.mark.parametrize("orientacio", [1, 2, 3, 4])
    def test_a_FEKVO_allasok_valtozatlanul_hagyjak(self, orientacio):
        assert megjelenitett_meret(60, 40, orientacio) == (60, 40)


class TestAHatarok:
    def test_a_HIANYZO_orientacio_nem_cserel(self):
        assert megjelenitett_meret(60, 40, None) == (60, 40)

    def test_az_ERVENYTELEN_orientacio_nem_cserel(self):
        """A `0` és a `9` nem létező állás — ne találgassunk."""
        assert megjelenitett_meret(60, 40, 0) == (60, 40)
        assert megjelenitett_meret(60, 40, 9) == (60, 40)

    def test_a_HIANYZO_meret_atmegy(self):
        assert megjelenitett_meret(None, None, 6) == (None, None)
        assert megjelenitett_meret(0, 0, 6) == (0, 0)

    def test_a_meret_ERTELMEZES_NELKUL_megy_at(self):
        """A segéd CSAK az orientációt értelmezi; a méreteket ahogy kapta,
        úgy adja tovább (cserélve vagy sem) — nem a dolga eldönteni, mi
        számít érvényes méretnek."""
        assert megjelenitett_meret("nem szám", 40, 6) == (40, "nem szám")
        assert megjelenitett_meret("nem szám", 40, 1) == ("nem szám", 40)
