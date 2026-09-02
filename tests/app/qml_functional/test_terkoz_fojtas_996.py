"""#996: a térköz-csúszka húzása NE fagyassza be a felületet.

## A mérés, ami ezt kikényszerítette

A térköz a PAKOLÁS bemenete (#1121), tehát minden `setCollageSpacing`
teljes újrarendezést indít. Egy újrarendezés ára tíz képre, ezen a gépen:

| téma | egy újrarendezés |
|---|---:|
| `picturegrid` (Mozaik) | **520,9 ms** |
| `framegrid` (Képkockamozaik) | **519,4 ms** |
| `regulargrid` (Sima rács) | 0,1 ms |
| `picturepile` (Képkupac) | 0,3 ms |

A `packing.PACK_TIME_LIMIT` 0,5 s — a két drága téma ezt ki is használja.
A QML `Slider` `onValueChanged`-je húzás közben **tickenként** tüzel, tehát
fojtás nélkül a csúszka mozgatása félmásodperces szakaszokra fagyasztja a
felületet. A #996 „Kész, ha" pontja szó szerint ezt kérte: *„a Mozaik nem
akad meg közben"*.

## Amit ez a fájl őriz

A fojtás **nem** késleltetheti a végleges értéket: elengedéskor azonnal
érvényesül. És a fojtás nem lehet olyan, hogy a csúszka „nem csinál
semmit" — az volt az eredeti #1121-es panasz.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject

from test_collage_settings_tab_946 import _child, _tab


@pytest.fixture
def lap(qt_app):
    return _tab(qt_app, spacing=0.0)


def _csuszka(tab):
    return _child(tab, "collageSpacingSlider")


def _fojto(tab):
    return tab.findChild(QObject, "collageSpacingThrottle")


class TestFojtasLetezik:
    def test_van_fojto_idozito(self, lap):
        """Fog: fojtás nélkül a `collageSpacingThrottle` nincs meg, és a
        csúszka minden tickje azonnal újrarendez."""
        assert _fojto(lap) is not None

    def test_a_fojtas_nem_tul_hosszu(self, lap):
        """Egy fél másodperces fojtás már érezhető késleltetés lenne."""
        assert 0 < _fojto(lap).property("interval") <= 250


class TestHuzasKozben:
    def test_a_tickek_NEM_hivjak_azonnal_a_vezerlot(self, qt_app, lap):
        """A húzás közbeni tickek a fojtón mennek át.

        Fog: a régi `onValueChanged` → `setCollageSpacing` közvetlen kötés
        mellett ez a hívás azonnal megtörténne, és a mérés szerint 520 ms-ot
        blokkolna — tickenként.
        """
        csuszka = _csuszka(lap)
        vezerlo = lap.property("_stub")
        elotte = vezerlo.property("collageSpacing")

        for ertek in (0.2, 0.4, 0.6, 0.8):
            csuszka.setProperty("value", ertek)
        qt_app.processEvents()

        assert vezerlo.property("collageSpacing") == pytest.approx(elotte), (
            "a húzás közbeni tick azonnal újrarendezett — nincs fojtás"
        )

    def test_a_fojto_UJRAINDUL_minden_ticknel(self, qt_app, lap):
        """Folyamatos húzásnál egyszer sem szabad lefutnia."""
        csuszka = _csuszka(lap)
        fojto = _fojto(lap)
        for ertek in (0.1, 0.2, 0.3):
            csuszka.setProperty("value", ertek)
            assert fojto.property("running") is True


class TestElengedes:
    def test_elengedeskor_AZONNAL_ervenyesul(self, qt_app, lap):
        """A felhasználó befejezte a mozdulatot — ne várjon az időzítőre.

        Fog: ha valaki csak a `Timer`-re bízza az alkalmazást, a végleges
        érték a fojtás idejével késne, és gyors elengedésnél a felület
        „lemaradna" a csúszkáról.
        """
        csuszka = _csuszka(lap)
        vezerlo = lap.property("_stub")

        csuszka.setProperty("value", 0.75)
        csuszka.setProperty("pressed", True)
        csuszka.setProperty("pressed", False)
        qt_app.processEvents()

        assert vezerlo.property("collageSpacing") == pytest.approx(0.75)

    def test_elengedeskor_a_fojto_LEALL(self, qt_app, lap):
        """Különben az elengedés után még egyszer lefutna — fölösleges
        újrarendezés, ami a kézi elrendezést vinné el."""
        csuszka = _csuszka(lap)
        csuszka.setProperty("value", 0.4)
        csuszka.setProperty("pressed", True)
        csuszka.setProperty("pressed", False)
        qt_app.processEvents()

        assert _fojto(lap).property("running") is False
