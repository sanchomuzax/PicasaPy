"""Az Options OK/Cancel működése valódi felületi eseményekkel (#5906)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QPointF, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QTest
from PySide6.QtQml import QQmlExpression, qmlContext

from conftest import _build_qml_app
from support.jpeg_factory import make_minta_jpeg
from support.varakozas import var_feltetelre
from tests.app.qml_functional._felsomenupontok_helpers_4329 import (
    _objektum,
)
from tests.app.qml_functional._fomenu_4420_menu import _megnyit
from tests.app.qml_functional.test_menu_talca_egyeb_valodi_5135 import (
    _menupont_kattintasa,
)

_KEPEK = ("elso.jpg", "masodik.jpg")
_MAGASSAG_ELTOLASOK = (-5, 0, 5)


def _keszits_kepeket(lib: Path) -> None:
    make_minta_jpeg(lib / _KEPEK[0], size=(320, 240), seed=59)
    make_minta_jpeg(lib / _KEPEK[1], size=(240, 320), seed=60)


@pytest.fixture
def options_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_kepeket,
        belyegkep_meret=256,
        valodi_belyegkep=True,
    )


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, feltetel, masodperc)


def _gyerek(ablak, nev: str):
    elem = _objektum(ablak, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _thumb_kepek(ablak):
    def bejar(item):
        for gyerek in item.childItems():
            yield gyerek
            yield from bejar(gyerek)

    return [
        kep for kep in bejar(ablak.contentItem())
        if kep.objectName() == "thumbImage"
    ]


def _fotok_betoltve(ablak, qt_app) -> bool:
    racs = _objektum(ablak, "photoGrid")
    if racs is None or racs.width() <= 0 or racs.height() <= 0:
        return False
    betoltott = 0
    for kep in _thumb_kepek(ablak):
        forras = kep.property("source")
        forras_szoveg = forras.toString() if hasattr(forras, "toString") else str(forras)
        if (
            kep.objectName() != "thumbImage"
            or not forras_szoveg.startswith("image://thumbs/")
            or not kep.isVisible()
        ):
            continue
        # A PySide nem tudja közvetlenül átalakítani a QQuickImage Status
        # enumot; a QML-ből kiolvasott 1 az Image.Ready értéke.
        kifejezes = QQmlExpression(qmlContext(kep), kep, "status")
        ertek, hiba = kifejezes.evaluate()
        hely = kep.mapToItem(racs, QPointF(0, 0))
        if (
            not hiba
            and ertek == 1
            and hely.x() + kep.width() > 0
            and hely.y() + kep.height() > 0
            and hely.x() < racs.width()
            and hely.y() < racs.height()
        ):
            betoltott += 1
    return betoltott >= len(_KEPEK)


def _beallitasok_megnyit(ablak, qt_app):
    menu_bar = ablak.property("menuBar")
    _megnyit(menu_bar, qt_app, "&Tools")
    _menupont_kattintasa(ablak, qt_app, "menuToolsOptions")
    assert _varj(qt_app, lambda: _objektum(ablak, "optionsDialog") is not None)
    beallitasok = _gyerek(ablak, "optionsDialog")
    assert _varj(qt_app, lambda: beallitasok.property("visible") is True)
    beallitasok.requestActivate()
    assert _varj(qt_app, lambda: beallitasok.property("active") is True)
    return beallitasok


def _kattints_ablakban(qt_app, ablak, elem) -> None:
    assert elem.width() > 0 and elem.height() > 0, (
        f"{elem.objectName()}: nincs kattintható mérete"
    )
    center = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        center.toPoint(),
    )
    qt_app.processEvents()


@pytest.mark.parametrize("height_offset", _MAGASSAG_ELTOLASOK)
def test_options_cancel_discards_ok_and_enter_commit_escape_cancels(
    options_app, qt_app, height_offset: int
):
    ablak, controller, _engine = options_app
    ablak.show()
    ablak.requestActivate()
    assert _varj(qt_app, lambda: len(controller.photos.photos) == len(_KEPEK))
    racs = _gyerek(ablak, "photoGrid")
    racs.setProperty("contentY", 0)
    ablak.setProperty("selectedIndexes", [0, 1])
    ablak.setProperty("selectedIndex", 0)
    QMetaObject.invokeMethod(racs, "forceLayout")
    assert _varj(qt_app, lambda: _fotok_betoltve(ablak, qt_app)), (
        "a valódi bélyegképek nem töltődtek be a főablakba; "
        f"fotók={len(controller.photos.photos)}, "
        f"képelemek={[(kep.property('source').toString(), kep.isVisible()) for kep in _thumb_kepek(ablak)]}"
    )

    beallitasok = _beallitasok_megnyit(ablak, qt_app)
    celmagassag = beallitasok.height() + height_offset
    beallitasok.setHeight(celmagassag)
    assert _varj(qt_app, lambda: beallitasok.height() == celmagassag)
    ok_gomb = _gyerek(beallitasok, "optionsOkButton")
    cancel_gomb = _gyerek(beallitasok, "optionsCancelButton")
    assert ok_gomb.isEnabled() and cancel_gomb.isEnabled()
    ok_kozep = ok_gomb.mapToScene(
        QPointF(ok_gomb.width() / 2, ok_gomb.height() / 2)
    )
    cancel_kozep = cancel_gomb.mapToScene(
        QPointF(cancel_gomb.width() / 2, cancel_gomb.height() / 2)
    )
    assert ok_kozep.x() < cancel_kozep.x(), (
        "az eredeti sorrendben az OK a Cancel előtt áll"
    )
    ok_teteje = ok_gomb.mapToScene(QPointF(0, 0)).y()
    ok_alja = ok_gomb.mapToScene(QPointF(0, ok_gomb.height())).y()
    cancel_teteje = cancel_gomb.mapToScene(QPointF(0, 0)).y()
    cancel_alja = cancel_gomb.mapToScene(
        QPointF(0, cancel_gomb.height())
    ).y()
    assert -3 <= ok_teteje and ok_alja <= beallitasok.height() + 3
    assert -3 <= cancel_teteje and cancel_alja <= beallitasok.height() + 3
    assert _gyerek(beallitasok, "optionsOkDefaultBorder").property("visible") is True

    kep_ut = os.environ.get("PICASAPY_5906_KIADASKEP")
    if height_offset == 0 and kep_ut:
        # Kiadáskép: a képernyő összetett képén a megnyitott Options ablak
        # és a mögötte kirajzolt, szolgáltatón át betöltött fotók látszanak.
        kep = QGuiApplication.primaryScreen().grabWindow(0)
        cel = Path(kep_ut)
        cel.parent.mkdir(parents=True, exist_ok=True)
        assert not kep.isNull() and kep.save(str(cel)), (
            "az Options kiadásképe nem menthető"
        )

    stack = _gyerek(beallitasok, "optionsTabStack")
    _kattints_ablakban(
        qt_app, beallitasok, _gyerek(beallitasok, "optionsTabSlideshow")
    )
    assert _varj(qt_app, lambda: stack.property("currentIndex") == 3)
    loop = _gyerek(beallitasok, "optionsSlideshowLoopCheck")
    alap = bool(controller.slideshowLoop)

    # Tényleges kattintás, majd Cancel: az érték csak a piszkozatban változik.
    _kattints_ablakban(qt_app, beallitasok, loop)
    assert bool(loop.property("checked")) is not alap
    assert bool(controller.slideshowLoop) is alap
    _kattints_ablakban(qt_app, beallitasok, cancel_gomb)
    assert _varj(qt_app, lambda: beallitasok.property("visible") is False)
    assert bool(controller.slideshowLoop) is alap

    # OK kattintása menti a megváltoztatott jelölőt.
    beallitasok = _beallitasok_megnyit(ablak, qt_app)
    _kattints_ablakban(
        qt_app, beallitasok, _gyerek(beallitasok, "optionsTabSlideshow")
    )
    loop = _gyerek(beallitasok, "optionsSlideshowLoopCheck")
    _kattints_ablakban(qt_app, beallitasok, loop)
    _kattints_ablakban(qt_app, beallitasok, _gyerek(beallitasok, "optionsOkButton"))
    assert _varj(qt_app, lambda: beallitasok.property("visible") is False)
    assert bool(controller.slideshowLoop) is not alap

    # Enter az OK-t aktiválja; Escape a változtatás megtartása nélkül zár.
    beallitasok = _beallitasok_megnyit(ablak, qt_app)
    _kattints_ablakban(
        qt_app, beallitasok, _gyerek(beallitasok, "optionsTabSlideshow")
    )
    loop = _gyerek(beallitasok, "optionsSlideshowLoopCheck")
    _kattints_ablakban(qt_app, beallitasok, loop)
    QTest.keyClick(beallitasok, Qt.Key.Key_Return)
    assert _varj(qt_app, lambda: beallitasok.property("visible") is False)
    assert bool(controller.slideshowLoop) is alap

    # A numerikus Enter (Qt.Key_Enter) ugyanúgy az alapértelmezett OK.
    beallitasok = _beallitasok_megnyit(ablak, qt_app)
    _kattints_ablakban(
        qt_app, beallitasok, _gyerek(beallitasok, "optionsTabSlideshow")
    )
    loop = _gyerek(beallitasok, "optionsSlideshowLoopCheck")
    _kattints_ablakban(qt_app, beallitasok, loop)
    QTest.keyClick(beallitasok, Qt.Key.Key_Enter)
    assert _varj(qt_app, lambda: beallitasok.property("visible") is False)
    assert bool(controller.slideshowLoop) is not alap

    beallitasok = _beallitasok_megnyit(ablak, qt_app)
    _kattints_ablakban(
        qt_app, beallitasok, _gyerek(beallitasok, "optionsTabSlideshow")
    )
    loop = _gyerek(beallitasok, "optionsSlideshowLoopCheck")
    _kattints_ablakban(qt_app, beallitasok, loop)
    QTest.keyClick(beallitasok, Qt.Key.Key_Escape)
    assert _varj(qt_app, lambda: beallitasok.property("visible") is False)
    assert bool(controller.slideshowLoop) is not alap
