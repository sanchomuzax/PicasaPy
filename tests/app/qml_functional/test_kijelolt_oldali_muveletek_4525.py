"""#4525: a kettős nézet parancsai a „Kijelölve” jelvény oldalát célozzák."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QGuiApplication, QWheelEvent
from PySide6.QtTest import QTest

from picasapy.render.flip import FLIP_HORIZONTAL, FLIP_VERTICAL
from support.jpeg_factory import make_jpeg
from support.qml_halasztott import epitsd_fel_ha_fileops
from support.qt_wait import wait_for_photo_op
from tests.app.qml_functional.conftest import _build_qml_app


def _negy_kep(lib: Path) -> None:
    for nev in ("a", "b", "c", "d"):
        make_jpeg(lib / f"{nev}.jpg", size=(320, 180))


def _gyerek(gyoker, nev: str):
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _pump(qt_app, kor: int = 8) -> None:
    for _ in range(kor):
        qt_app.processEvents()


def _valodi_klikk(window, qt_app, elem) -> None:
    pont = elem.mapToScene(QPointF(elem.property("width") / 2,
                                   elem.property("height") / 2))
    assert 0 <= pont.x() < window.width() and 0 <= pont.y() < window.height(), (
        f"a kattintási pont ({pont.x():.0f}, {pont.y():.0f}) kívül esik "
        f"az ablakon ({window.width()}×{window.height()})"
    )
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    _pump(qt_app)


def _valodi_gorgo(window, qt_app, elem, irany: int) -> None:
    pont = elem.mapToScene(QPointF(elem.property("width") / 2,
                                   elem.property("height") / 2))
    esemeny = QWheelEvent(
        pont,
        pont,
        QPoint(0, 0),
        QPoint(0, irany * 120),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    QGuiApplication.sendEvent(window, esemeny)
    _pump(qt_app)


def _nezo_es_ab(window, qt_app):
    window.show()
    window.setProperty("viewerOpen", True)
    _pump(qt_app)
    nezo = _gyerek(window, "photoViewer")
    QMetaObject.invokeMethod(
        nezo, "show", Qt.ConnectionType.DirectConnection, Q_ARG("QVariant", 0)
    )
    _pump(qt_app)
    _valodi_klikk(window, qt_app, _gyerek(window, "viewerLayoutAb"))
    assert nezo.property("layoutMode") == "ab"
    return nezo


def _fokusz(window, qt_app, nezo, oldal: str) -> None:
    kep = "viewerImageElotte" if oldal == "bal" else "viewerImage"
    _valodi_klikk(window, qt_app, _gyerek(window, kep))
    assert nezo.property("aktivOldal") == oldal
    QMetaObject.invokeMethod(nezo, "forceActiveFocus", Qt.ConnectionType.DirectConnection)
    _pump(qt_app)


def _lapozas(window, qt_app, nezo, muvelet: str) -> None:
    if muvelet == "kovetkezo_gomb":
        _valodi_klikk(window, qt_app, _gyerek(window, "viewerNextButton"))
    elif muvelet == "elozo_gomb":
        _valodi_klikk(window, qt_app, _gyerek(window, "viewerPrevButton"))
    elif muvelet == "jobbra":
        QTest.keyClick(window, Qt.Key.Key_Right)
        _pump(qt_app)
    elif muvelet == "balra":
        QTest.keyClick(window, Qt.Key.Key_Left)
        _pump(qt_app)
    elif muvelet == "return":
        QTest.keyClick(window, Qt.Key.Key_Return)
        _pump(qt_app)
    elif muvelet == "gorgo_kovetkezo":
        _valodi_gorgo(window, qt_app, _gyerek(window, "viewerPhotoArea"), -1)
    elif muvelet == "gorgo_elozo":
        _valodi_gorgo(window, qt_app, _gyerek(window, "viewerPhotoArea"), 1)
    else:
        raise AssertionError(f"ismeretlen lapozás: {muvelet}")


def _caption(controller, sor: int) -> str:
    return controller.photos.captionAt(sor)


def _felirat_beir(controller, window, qt_app, mezo, szoveg: str) -> None:
    _valodi_klikk(window, qt_app, mezo)
    mezo.setProperty("text", szoveg)
    wait_for_photo_op(
        controller,
        lambda: QMetaObject.invokeMethod(
            mezo, "accepted", Qt.ConnectionType.DirectConnection
        ),
        qt_app=qt_app,
    )
    _pump(qt_app)


def test_lapozas_minden_belepesi_pontja_a_fokuszalt_oldalt_lepteti(
    qml_app, qt_app
):
    window, _controller, _engine = qml_app
    nezo = _nezo_es_ab(window, qt_app)
    hibak = []

    for magassag in (1019, 1024, 1029):
        window.resize(1280, magassag)
        _pump(qt_app)

        bal_muveletek = (
            ("kovetkezo_gomb", 0, 1),
            ("elozo_gomb", 1, 0),
            ("jobbra", 0, 1),
            ("balra", 1, 0),
            ("return", 0, 1),
            ("gorgo_kovetkezo", 1, 2),
            ("gorgo_elozo", 2, 1),
        )
        for muvelet, indulo, vart in bal_muveletek:
            nezo.setProperty("currentIndex", indulo)
            nezo.setProperty("masodikIndex", 3)
            _pump(qt_app)
            _fokusz(window, qt_app, nezo, "bal")
            _lapozas(window, qt_app, nezo, muvelet)
            mert = nezo.property("currentIndex")
            if mert != vart or nezo.property("aktivSor") != vart:
                hibak.append(
                    f"{magassag}px bal/{muvelet}: kijelölt sor "
                    f"{nezo.property('aktivSor')}, várt {vart}"
                )
            if nezo.property("abMasikSor") != 3:
                hibak.append(
                    f"{magassag}px bal/{muvelet}: a nem kijelölt jobb oldal "
                    f"{nezo.property('abMasikSor')}-ra változott"
                )

        jobb_muveletek = (
            ("kovetkezo_gomb", 1, 2),
            ("elozo_gomb", 2, 1),
            ("jobbra", 1, 2),
            ("balra", 2, 1),
            ("return", 1, 2),
            ("gorgo_kovetkezo", 2, 3),
            ("gorgo_elozo", 3, 2),
        )
        for muvelet, indulo, vart in jobb_muveletek:
            nezo.setProperty("currentIndex", 0)
            nezo.setProperty("masodikIndex", indulo)
            _pump(qt_app)
            _fokusz(window, qt_app, nezo, "jobb")
            _lapozas(window, qt_app, nezo, muvelet)
            mert = nezo.property("abMasikSor")
            if mert != vart or nezo.property("aktivSor") != vart:
                hibak.append(
                    f"{magassag}px jobb/{muvelet}: kijelölt sor "
                    f"{nezo.property('aktivSor')}, várt {vart}"
                )
            if nezo.property("currentIndex") != 0:
                hibak.append(
                    f"{magassag}px jobb/{muvelet}: a nem kijelölt bal oldal "
                    f"{nezo.property('currentIndex')}-ra változott"
                )

        # Rontáskontroll: az egyképes nézet továbbra is a currentIndex-et lépteti.
        _valodi_klikk(window, qt_app, _gyerek(window, "viewerLayoutOnly1up"))
        nezo.setProperty("currentIndex", 0)
        nezo.setProperty("masodikIndex", 3)
        _pump(qt_app)
        _lapozas(window, qt_app, nezo, "kovetkezo_gomb")
        if nezo.property("currentIndex") != 1 or nezo.property("aktivSor") != 1:
            hibak.append(
                f"{magassag}px 1-up/következő gomb: currentIndex="
                f"{nezo.property('currentIndex')}, aktivSor={nezo.property('aktivSor')}"
            )
        _lapozas(window, qt_app, nezo, "elozo_gomb")
        if nezo.property("currentIndex") != 0:
            hibak.append(
                f"{magassag}px 1-up/előző gomb: currentIndex="
                f"{nezo.property('currentIndex')}"
            )
        _valodi_klikk(window, qt_app, _gyerek(window, "viewerLayoutAb"))
        assert nezo.property("layoutMode") == "ab"

    assert not hibak, "\n".join(hibak)


def test_feliratiraskor_es_torleskor_a_kattintott_oldal_adataval_dolgozik(
    qml_app, qt_app
):
    window, controller, _engine = qml_app
    nezo = _nezo_es_ab(window, qt_app)
    mezo = _gyerek(window, "captionField")
    kuka = _gyerek(window, "captionTrashButton")
    hibak = []

    for magassag in (1019, 1024, 1029):
        window.resize(1280, magassag)
        wait_for_photo_op(
            controller,
            lambda szoveg=f"bal-{magassag}": controller.setCaption(0, szoveg),
            qt_app=qt_app,
        )
        wait_for_photo_op(
            controller,
            lambda szoveg=f"jobb-{magassag}": controller.setCaption(1, szoveg),
            qt_app=qt_app,
        )
        nezo.setProperty("currentIndex", 0)
        nezo.setProperty("masodikIndex", 1)
        _pump(qt_app)

        _fokusz(window, qt_app, nezo, "bal")
        if mezo.property("text") != f"bal-{magassag}":
            hibak.append(
                f"{magassag}px bal fókusz: a feliratmező "
                f"{mezo.property('text')!r}, várt {f'bal-{magassag}'!r}"
            )
        _felirat_beir(controller, window, qt_app, mezo, f"bal-uj-{magassag}")
        if _caption(controller, 0) != f"bal-uj-{magassag}":
            hibak.append(f"{magassag}px bal fókusz: nem a bal felirat módosult")
        if _caption(controller, 1) != f"jobb-{magassag}":
            hibak.append(f"{magassag}px bal fókusz: megváltozott a jobb felirat")

        _fokusz(window, qt_app, nezo, "jobb")
        if mezo.property("text") != f"jobb-{magassag}":
            hibak.append(
                f"{magassag}px jobb fókusz: a feliratmező "
                f"{mezo.property('text')!r}, várt {f'jobb-{magassag}'!r}"
            )
        _felirat_beir(controller, window, qt_app, mezo, f"jobb-uj-{magassag}")
        if _caption(controller, 1) != f"jobb-uj-{magassag}":
            hibak.append(f"{magassag}px jobb fókusz: nem a jobb felirat módosult")
        if _caption(controller, 0) != f"bal-uj-{magassag}":
            hibak.append(f"{magassag}px jobb fókusz: megváltozott a bal felirat")

        _fokusz(window, qt_app, nezo, "jobb")
        wait_for_photo_op(
            controller,
            lambda: _valodi_klikk(window, qt_app, kuka),
            qt_app=qt_app,
        )
        if _caption(controller, 1) != "":
            hibak.append(f"{magassag}px jobb fókusz: a jobb felirat nem törlődött")
        if _caption(controller, 0) != f"bal-uj-{magassag}":
            hibak.append(f"{magassag}px jobb fókusz: a bal felirat törlődött")

        _fokusz(window, qt_app, nezo, "bal")
        wait_for_photo_op(
            controller,
            lambda: _valodi_klikk(window, qt_app, kuka),
            qt_app=qt_app,
        )
        if _caption(controller, 0) != "":
            hibak.append(f"{magassag}px bal fókusz: a bal felirat nem törlődött")

    assert not hibak, "\n".join(hibak)


def test_ctrl_delete_es_tukrozes_a_kattintott_oldalra_hatas(
    qml_app, qt_app
):
    window, controller, _engine = qml_app
    nezo = _nezo_es_ab(window, qt_app)
    epitsd_fel_ha_fileops(window, "deleteConfirmDialog")
    torles = _gyerek(window, "deleteConfirmDialog")
    hibak = []

    for magassag in (1019, 1024, 1029):
        window.resize(1280, magassag)
        _pump(qt_app)
        nezo.setProperty("currentIndex", 0)
        nezo.setProperty("masodikIndex", 1)
        _pump(qt_app)

        for oldal, vart_sor in (("bal", 0), ("jobb", 1)):
            _fokusz(window, qt_app, nezo, oldal)
            QTest.keyClick(
                window,
                Qt.Key.Key_Delete,
                Qt.KeyboardModifier.ControlModifier,
            )
            _pump(qt_app)
            utak = torles.property("paths")
            if hasattr(utak, "toVariant"):
                utak = utak.toVariant()
            utak = [Path(p) for p in utak]
            vart_ut = Path(controller.photos.filePathAt(vart_sor))
            if utak != [vart_ut]:
                hibak.append(
                    f"{magassag}px {oldal} fókusz/Ctrl+Delete: {utak}, "
                    f"várt {[vart_ut]}"
                )
            torles.setProperty("visible", False)
            _pump(qt_app)

        _fokusz(window, qt_app, nezo, "bal")
        QTest.keyClick(
            window, Qt.Key.Key_H,
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
        )
        _pump(qt_app)
        if controller.photos.photos[0].flip_flags != FLIP_HORIZONTAL:
            hibak.append(f"{magassag}px bal fókusz/tükrözés: a bal kép nem tükröződött")
        if controller.photos.photos[1].flip_flags != 0:
            hibak.append(f"{magassag}px bal fókusz/tükrözés: a jobb kép is tükröződött")

        _fokusz(window, qt_app, nezo, "jobb")
        QTest.keyClick(
            window, Qt.Key.Key_V,
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
        )
        _pump(qt_app)
        if controller.photos.photos[1].flip_flags != FLIP_VERTICAL:
            hibak.append(f"{magassag}px jobb fókusz/tükrözés: a jobb kép nem tükröződött")
        if controller.photos.photos[0].flip_flags != FLIP_HORIZONTAL:
            hibak.append(f"{magassag}px jobb fókusz/tükrözés: megváltozott a bal kép")

        # A következő kör előtt a két jelzőt visszaállítjuk az indexen át.
        controller.flipHorizontalMany([0])
        controller.flipVerticalMany([1])
        _pump(qt_app)

    assert not hibak, "\n".join(hibak)


@pytest.fixture
def qml_app(qt_app, tmp_path):
    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_negy_kep)
