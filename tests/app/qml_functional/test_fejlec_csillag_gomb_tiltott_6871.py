"""A mappa-fejléc csillag gombja csillagozott kép nélkül tiltott - #6871.

Az eredeti Picasában a fejléc `select_star` ("Select starred photos") gombja
csillagozott kép nélküli mappában TILTOTT: kattintásra nincs hatás. Egy kép
csillagozása után a gomb azonnal aktív, és a csillagozott képet jelöli ki;
a csillag levétele után újra tiltott.

Referencia-képernyőképek (a tulajdonos gépéről, csak nézni valók):
`2026-11-12-fejlec-csillag-tiltott-job646.png` és
`2026-11-12-fejlec-csillag-aktiv-csillagozva-job-647.png`.

A próba VALÓDI egérkattintással (`QTest.mouseClick`) dolgozik a teljes
alkalmazásablakon, és a felhasználó felől néz: a gomb engedélyezett-e, és a
kattintás után mi lett a kijelölés.

Amit ez a próba NEM mér: a gomb halvány megjelenését (a tiltott állapot
negyedelt átlátszatlansága a `PicasaButton` saját dolga, #893), csak az
`enabled` állapotot és a kattintás hatását.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from conftest import _build_qml_app
from support.jpeg_factory import make_jpeg
from support.qt_wait import wait_for_photo_op
from support.varakozas import hibaturo_feltetel, var_feltetelre

_MAPPA = "cel"
_KEPEK = ("a_elso.jpg", "b_masodik.jpg", "c_harmadik.jpg")
_GOMB = "headerSelectStarredButton"


def _keszits_konyvtarat(lib: Path) -> None:
    """Három kép, EGY SEM csillagozott: a kiinduló állapot a tiltott gomb."""
    cel = lib / _MAPPA
    cel.mkdir()
    for nev in _KEPEK:
        make_jpeg(cel / nev, size=(120, 90))


@pytest.fixture
def mappa_app(qt_app, tmp_path, request):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_konyvtarat,
        keep_modul=request.module,
    )


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def _vizualis_bejaras(item):
    """A VIZUÁLIS fa bejárása: a delegátumoknak nincs QObject-szülőjük."""
    for gyerek in item.childItems():
        yield gyerek
        yield from _vizualis_bejaras(gyerek)


def _gomb(window):
    for item in _vizualis_bejaras(window.contentItem()):
        if item.objectName() == _GOMB:
            return item
    raise AssertionError(f"{_GOMB} vizuális elem nem található")


def _kattints(window, qt_app, elem) -> None:
    assert elem.isVisible() and elem.width() > 0 and elem.height() > 0, (
        f"{elem.objectName()}: nem látszik / nulla méretű, nem kattintható"
    )
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def _kijeloles(window) -> list:
    ertek = window.property("selectedIndexes")
    return list(ertek.toVariant() if hasattr(ertek, "toVariant") else ertek)


def _elokeszit(window, qt_app, controller) -> None:
    """Megnyitja a mappát, és megvárja a három képet a rácson."""
    window.show()
    window.requestActivate()
    qt_app.processEvents()
    cel = str(Path(str(controller.watchedFolders[0])) / _MAPPA)
    controller.selectFolder(cel)
    qt_app.processEvents()
    assert _varj(qt_app, lambda: len(controller.photos.photos) == len(_KEPEK))
    assert _varj(qt_app, lambda: _gomb(window).isVisible())


def _kijelol(window, qt_app, sorok: list[int]) -> None:
    window.setProperty("selectedIndexes", sorok)
    window.setProperty("selectedIndex", sorok[0] if sorok else -1)
    qt_app.processEvents()
    assert _kijeloles(window) == sorok


def _csillagoz(controller, qt_app, sor: int) -> None:
    wait_for_photo_op(controller, lambda: controller.toggleStar(sor), qt_app=qt_app)


class TestFejlecCsillagGomb:
    def test_csillagozott_kep_nelkul_a_gomb_tiltott_es_a_kattintas_hatastalan(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        _elokeszit(window, qt_app, controller)
        assert not any(foto.star for foto in controller.photos.photos), (
            "a kiinduló mappában nem lehet csillagozott kép"
        )
        _kijelol(window, qt_app, [1])

        gomb = _gomb(window)
        assert gomb.property("enabled") is False, (
            "csillagozott kép nélkül a fejléc csillag gombja engedélyezett"
        )
        _kattints(window, qt_app, gomb)

        assert _kijeloles(window) == [1], (
            "a tiltott csillag gomb kattintása megváltoztatta a kijelölést: "
            f"{_kijeloles(window)}"
        )

    def test_csillagozas_utan_azonnal_aktiv_es_a_csillagozott_kepet_jeloli_ki(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        _elokeszit(window, qt_app, controller)
        gomb = _gomb(window)
        assert gomb.property("enabled") is False

        _csillagoz(controller, qt_app, 2)

        assert _varj(qt_app, lambda: gomb.property("enabled") is True), (
            "egy kép csillagozása után a gomb nem lett azonnal aktív"
        )
        _kijelol(window, qt_app, [0])
        _kattints(window, qt_app, gomb)

        assert _varj(qt_app, lambda: _kijeloles(window) == [2]), (
            "az aktív csillag gomb nem a csillagozott képet jelölte ki: "
            f"{_kijeloles(window)}"
        )

    def test_a_csillag_levetele_utan_ujra_tiltott(self, mappa_app, qt_app):
        window, controller, _motor = mappa_app
        _elokeszit(window, qt_app, controller)
        gomb = _gomb(window)

        _csillagoz(controller, qt_app, 1)
        assert _varj(qt_app, lambda: gomb.property("enabled") is True)

        _csillagoz(controller, qt_app, 1)
        assert _varj(qt_app, lambda: gomb.property("enabled") is False), (
            "a csillag levétele után a gomb aktív maradt"
        )
        _kijelol(window, qt_app, [0])
        _kattints(window, qt_app, gomb)

        assert _kijeloles(window) == [0], (
            "az ismét tiltott csillag gomb kattintása megváltoztatta a "
            f"kijelölést: {_kijeloles(window)}"
        )

    def test_a_gomb_nem_a_kijelolestol_fugg(self, mappa_app, qt_app):
        """Üres kijelölésnél is aktív, ha van csillagozott kép a mappában.

        A gomb a MAPPA csillagozott képeitől függ, nem a kijelöltektől (a
        Mentés gombbal ellentétben): épp ez a gomb dolga, hogy kijelölést
        csináljon az üres kijelölésből."""
        window, controller, _motor = mappa_app
        _elokeszit(window, qt_app, controller)
        _csillagoz(controller, qt_app, 0)
        gomb = _gomb(window)
        assert _varj(qt_app, lambda: gomb.property("enabled") is True)

        _kijelol(window, qt_app, [])
        assert gomb.property("enabled") is True

        _kattints(window, qt_app, gomb)
        assert _varj(qt_app, lambda: _kijeloles(window) == [0])

