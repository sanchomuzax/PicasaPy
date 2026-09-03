"""#922 — a Létrehozás menü és a képtálca összekötése.

A felhasználó jelentése: a *Létrehozás ▸ Képkollázs…* nem indul el.

**A jegy eredeti diagnózisa (a néma `return`) TÉVES volt.** A valódi ok egy
FELTÉTEL-ELCSÚSZÁS a #455 óta:

| hol | feltétel |
|---|---|
| a menüpont engedélyezése (`Main.qml` → `photoActionsEnabled`) | `selectedIndexes.length > 0` |
| a párbeszéd nyitása (`CreateDialogs.qml`) | `trayHasPictures \|\| selectedIndexes.length > 0` |
| a vezérlő forrása (`create_controller._sources_for`) | **a TÁLCA, ha van benne kép** |

A #455 bekötötte a képtálcát a párbeszédbe és a vezérlőbe, de a **menü
feltételét nem vezette át**. Tálcán tartott képekkel, rácsbeli kijelölés
nélkül a menüpont ezért szürke — pedig a funkció hibátlanul működne.

A néma `return` külön, másodlagos hiba: ha a párbeszéd mégis megnyílna
forrás nélkül, a kattintás nyomtalanul elnyelődne. Az eredeti Picasában
ilyen nincs.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QEventLoop, QObject, QTimer

from tests.support.qml_halasztott import epitsd_fel


def _settle(qt_app, rounds=4):
    for _ in range(rounds):
        qt_app.processEvents()
        pause = QEventLoop()
        QTimer.singleShot(10, pause.quit)
        pause.exec()


def _hold_first_photos(controller, count=2):
    """Képek a TÁLCÁRA, rácsbeli kijelölés NÉLKÜL."""
    controller.holdRows(list(range(count)))
    return controller.heldCount



@pytest.fixture(autouse=True)
def _felepitett_parbeszedek(qml_app):
    """#2096: a Létrehozás-párbeszédek halasztva épülnek fel.

    Ez a fájl a VISELKEDÉSÜKET méri, nem a felépülés pillanatát (azt a
    #1720 őre), ezért minden eset előtt felépítjük őket — így az alábbi
    `findChild`-ok változatlanul maradhatnak."""
    epitsd_fel(qml_app[0], "createDialogs")

class TestMenuKovetiATalcat:
    def test_talcaval_de_kijeloles_NELKUL_a_menupont_EL(self, qml_app, qt_app):
        """Ez a #922 lényege: ma szürke, pedig a funkció menne."""
        window, controller, lib, engine = qml_app
        window.setProperty("selectedIndexes", [])
        assert _hold_first_photos(controller) > 0, "a tálcára nem került kép"
        _settle(qt_app, 2)
        for name in ("menuCreateCollage", "menuCreateMovie"):
            item = window.findChild(QObject, name)
            assert item is not None, name
            assert item.property("enabled") is True, (
                f"{name} szürke, pedig a tálcán van kép — a #455 feltétele nincs átvezetve"
            )

    def test_sem_talca_sem_kijeloles_eseten_szurke(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        window.setProperty("selectedIndexes", [])
        _settle(qt_app, 2)
        for name in ("menuCreateCollage", "menuCreateMovie"):
            assert window.findChild(QObject, name).property("enabled") is False

    def test_kijelolessel_talca_nelkul_is_el(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        _settle(qt_app, 2)
        for name in ("menuCreateCollage", "menuCreateMovie"):
            assert window.findChild(QObject, name).property("enabled") is True


class TestParbeszedNemNyelElKattintast:
    """A másodlagos hiba: forrás nélkül a nyitás némán visszatért."""

    def test_forras_nelkul_is_MEGNYILIK_es_megmondja_mi_hianyzik(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        window.setProperty("selectedIndexes", [])
        dialog = window.findChild(QObject, "collageDialog")
        dialog.metaObject().invokeMethod(dialog, "openForSelection")
        _settle(qt_app, 2)
        assert dialog.property("visible") is True, "a kattintás nyomtalanul elnyelődött"
        hint = window.findChild(QObject, "collageNoSourceHint")
        assert hint is not None and hint.property("visible") is True

    def test_forras_nelkul_az_OK_nem_nyomhato(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        window.setProperty("selectedIndexes", [])
        dialog = window.findChild(QObject, "collageDialog")
        dialog.metaObject().invokeMethod(dialog, "openForSelection")
        _settle(qt_app, 2)
        # a célfájl megadása ÖNMAGÁBAN nem elég, ha nincs mit betenni
        dialog.setProperty("targetFile", "/tmp/kollazs.jpg")
        _settle(qt_app, 2)
        assert dialog.property("sourceCount") == 0

    def test_forrassal_a_tipp_eltunik(self, qml_app, qt_app):
        window, controller, lib, engine = qml_app
        window.setProperty("selectedIndexes", [0, 1])
        dialog = window.findChild(QObject, "collageDialog")
        dialog.metaObject().invokeMethod(dialog, "openForSelection")
        _settle(qt_app, 2)
        assert dialog.property("sourceCount") == 2
        assert window.findChild(QObject, "collageNoSourceHint").property("visible") is False
