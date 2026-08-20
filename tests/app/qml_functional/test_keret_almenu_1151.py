r"""A Keret-almenü csak a keretet TÁMOGATÓ témákon aktív (#1151).

## A tulajdonos jelentése

> „A Rács esetén sem működik a keret."

A #1122 lezárásakor a rajzolót és a panelt néztük meg — **mindkettő
helyes**: a téma képesség-maszkjának 9. bitje (a témák vtábláiból
igazolva) a Rácsnál nulla, a panel keretválasztója pedig rejtve van
(`CollageSettingsTab.qml:116`).

**A lezárás fele mégis hiányzott.** A jobbklikk-menü Keret-almenüje NEM
volt gátolva: kirakta mind a három tételt, az `applyBorder()` meghívta a
`setCollageBorder`-t, az érték eltárolódott — és a rajzoló (helyesen)
eldobta. **A felhasználó tehát egy menütételt kapott, ami némán nem csinál
semmit**, és jogosan hitte, hogy elromlott.

## A tanulság, ami ennél tágabb

Ha egy FELHASZNÁLÓ ÁLTAL jelentett jegyet „nem hiba" indoklással zárunk,
előbb meg kell válaszolni: **akkor mit látott?** A mag lehet helyes úgy is,
hogy a felület mást ígér — és a felület MINDEN belépési pontját végig kell
nézni, nem csak azt, amelyiket mi használnánk.

⚠️ **Tiltás és nem elrejtés:** a szürke tétel megmondja, hogy a funkció
létezik, csak nem ehhez a témához. Hogy az eredeti rejt vagy tilt,
**nincs kimérve** — ezt a kód is kimondja.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject
from PySide6.QtGui import QGuiApplication

from support.collage_canvas_harness import (
    _panel,
    keszits_kepeket,
    nyitott_vezerlo,
)

#: A keretet TÁMOGATÓ témák (a maszk 9. bitje 1) és a többi.
KERETES = ("picturepile", "contactsheet")
KERET_NELKULI = ("picturegrid", "framegrid", "regulargrid", "multiexp")


@pytest.fixture
def library(tmp_path):
    return keszits_kepeket(tmp_path)


@pytest.fixture
def controller(qt_app, tmp_path, library):
    yield from nyitott_vezerlo(tmp_path, library)


def _keret_almenu(panel):
    menu = panel.findChild(QObject, "collageMenuChangeBorder")
    assert menu is not None, "nincs Keret-almenü"
    return menu


class TestATiltas:
    @pytest.mark.parametrize("tema", KERET_NELKULI)
    def test_a_keretet_nem_tamogato_teman_TILTOTT(self, controller, tema):
        controller.setCollageTheme(tema)
        panel = _panel(controller)
        QGuiApplication.instance().processEvents()

        assert _keret_almenu(panel).property("enabled") is False, (
            f"a Keret-almenü aktív a(z) {tema} témán, pedig a maszk tiltja"
        )

    @pytest.mark.parametrize("tema", KERETES)
    def test_a_keretes_temakon_AKTIV(self, controller, tema):
        controller.setCollageTheme(tema)
        panel = _panel(controller)
        QGuiApplication.instance().processEvents()

        assert _keret_almenu(panel).property("enabled") is True
