"""#4928/#4949: Ctrl+Alt a kijelölt képet nyitja meg, a specifikációs határral."""
# rontás-kontroll: PopDisplay megvalósítás nélkül → 1 failed

from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.varakozas import var_feltetelre


def _elonezetesi_probak_kepei(lib):
    Image.new("RGB", (1600, 900), (255, 0, 0)).save(lib / "a-nagy.jpg")
    Image.new("RGB", (320, 160), (0, 0, 255)).save(lib / "b-kicsi.jpg")


@pytest.fixture
def qml_app_ctrl_alt(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_elonezetesi_probak_kepei,
    )


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, feltetel, masodperc)


def _sor_fajlnev_alapjan(controller, fajlnev: str) -> int:
    return next(
        sor
        for sor in range(controller.photos.rowCount())
        if Path(controller.photos.filePathAt(sor)).name == fajlnev
    )


def _racs_szelessege(window, grid, qt_app, cel: int) -> None:
    ablakcel = round(window.width() + cel - grid.width())
    window.setWidth(ablakcel)
    assert _varj(qt_app, lambda: round(grid.width()) == cel), (
        f"a tartalomnézet kliensszélessége nem állt be {cel} px-re "
        f"(ablak={window.width()}, nézet={grid.width()})"
    )


def _vizualis_leszarmazottak(elem):
    for gyermek in elem.childItems():
        yield gyermek
        yield from _vizualis_leszarmazottak(gyermek)


def _lathato_belyegkepek(window):
    teruletek = [
        (area, area.parentItem().property("resolution"))
        for area in _vizualis_leszarmazottak(window.contentItem())
        if area.objectName() == "thumbMouseArea"
        if area.isVisible() and area.width() > 0 and area.height() > 0
    ]
    meretek = [
        (area, int(resolution.split("x", 1)[0]))
        for area, resolution in teruletek
        if resolution and "x" in resolution
    ]
    kis = next((area for area, width in meretek if width <= 1024), None)
    nagy = next((area for area, width in meretek if width > 1024), None)
    assert kis is not None and nagy is not None, (
        "a könyvtár-rácsban nem látszik egy kis és egy 1024 px-nél szélesebb kép"
    )

    def kozep(area):
        return area.mapToScene(
            QPointF(area.width() / 2, area.height() / 2)
        ).toPoint()

    return (kis, kozep(kis)), (nagy, kozep(nagy))


def test_ctrl_alt_a_kijelolt_kepet_mutatja_es_elengedesre_elrejti(
    qml_app_ctrl_alt, qt_app, tmp_path
):
    window, controller, _engine = qml_app_ctrl_alt
    alapmagassag = window.height()
    window.show()
    window.requestActivate()
    assert _varj(qt_app, lambda: window.property("active")), (
        "a könyvtárablak nem került előtérbe"
    )

    popup = window.findChild(QObject, "ctrlAltHoverPreviewWindow")
    grid = window.findChild(QObject, "photoGrid")
    assert popup is not None, "a Ctrl+Alt előnézeti felugró ablak hiányzik"
    assert grid is not None, "a könyvtár-rács nem található"
    _racs_szelessege(window, grid, qt_app, 1200)
    kis_sor = _sor_fajlnev_alapjan(controller, "b-kicsi.jpg")
    nagy_sor = _sor_fajlnev_alapjan(controller, "a-nagy.jpg")
    for magassag_eltolas in (-5, 0, 5):
        window.setHeight(alapmagassag + magassag_eltolas)
        assert _varj(
            qt_app,
            lambda delta=magassag_eltolas: window.height()
            == alapmagassag + delta,
        ), f"az ablakmagasság nem állt be ({magassag_eltolas:+} px)"
        (kis_area, kis_pont), (nagy_area, nagy_pont) = _lathato_belyegkepek(
            window
        )
        # A kurzor a nagy piros képen áll, a kijelölés a kis kék kép.
        window.setProperty("selectedIndexes", [kis_sor])
        window.setProperty("selectedIndex", kis_sor)
        QTest.mouseMove(window, nagy_pont, delay=10)
        assert _varj(
            qt_app, lambda area=nagy_area: area.property("containsMouse")
        ), "a nagy képcella lebegtetése nem jutott el a könyvtár-rácsig"
        QTest.keyPress(window, Qt.Key.Key_Control)
        QTest.keyPress(
            window, Qt.Key.Key_Alt, Qt.KeyboardModifier.ControlModifier
        )
        assert _varj(qt_app, lambda: popup.isVisible()), (
            "1024 px-nél szélesebb tartalomnézetben nem jelent meg a kis kép"
        )
        image = window.findChild(QObject, "ctrlAltHoverPreviewImage")
        assert _varj(qt_app, lambda: popup.property("previewImageStatus") == 1)
        rendered = popup.grabWindow()
        image_center = image.mapToScene(
            QPointF(image.width() / 2, image.height() / 2)
        ).toPoint()
        center_pixel = rendered.pixelColor(image_center)
        assert center_pixel.blue() > center_pixel.red() * 2, (
            "a kurzor alatti nagy piros kép jelent meg a kijelölt kis kék helyett"
        )
        QTest.keyRelease(
            window, Qt.Key.Key_Alt, Qt.KeyboardModifier.ControlModifier
        )
        assert _varj(qt_app, lambda: not popup.isVisible())
        QTest.keyRelease(window, Qt.Key.Key_Control)

        # Most a kijelölés a nagy piros kép, a kurzor a kis kék képen áll.
        window.setProperty("selectedIndexes", [nagy_sor])
        window.setProperty("selectedIndex", nagy_sor)
        QTest.mouseMove(window, kis_pont, delay=10)
        assert _varj(
            qt_app, lambda area=kis_area: area.property("containsMouse")
        ), "a valódi egérmozgás nem jutott el a kis képcelláig"
        assert _varj(
            qt_app,
            lambda: popup.width() == popup.property("previewWidth") + 24,
        ), "a popup szélessége nem követte a kijelölt kép geometriáját"
        QTest.keyPress(window, Qt.Key.Key_Control)
        QTest.keyPress(
            window, Qt.Key.Key_Alt, Qt.KeyboardModifier.ControlModifier
        )
        assert controller.property("ctrlAltHeld"), (
            "a valódi Ctrl+Alt billentyűesemény nem frissítette az állapotot"
        )
        image = window.findChild(QObject, "ctrlAltHoverPreviewImage")
        assert _varj(qt_app, lambda: popup.isVisible()), (
            "Ctrl+Alt mellett nem jelent meg a kijelölt nagy kép: "
            f"active={window.property('active')}, "
            f"held={controller.property('ctrlAltHeld')}, "
            f"selected={window.property('selectedIndex')} (várt: {nagy_sor}), "
            f"previewRow={grid.property('currentPreviewRow')}, "
            f"previewPhoto={grid.property('currentPreviewPhoto')}, "
            f"requested={popup.property('requested')}, "
            f"clientWidth={popup.property('clientWidth')}, "
            f"previewWidth={popup.property('previewWidth')}, "
            f"imageStatus={popup.property('previewImageStatus')}, "
            f"imageVisible={image.property('visible')}"
        )

        assert image is not None
        assert _varj(qt_app, lambda: popup.property("previewImageStatus") == 1), (
            "a felugró előnézet képe nem töltődött be"
        )
        rendered = popup.grabWindow()
        assert not rendered.isNull(), "a felugró előnézet ablaka nem renderelődött"
        if magassag_eltolas == 0:
            assert rendered.save(str(tmp_path / "ctrl-alt-preview.png")), (
                "a renderelt előnézet képe nem menthető"
            )
        assert popup.property("clientWidth") > 1024, (
            "a PopDisplay kliensszélessége nem nagyobb 1024 px-nél"
        )
        image_center = image.mapToScene(
            QPointF(image.width() / 2, image.height() / 2)
        ).toPoint()
        center_pixel = rendered.pixelColor(image_center)
        assert center_pixel.red() > center_pixel.blue() * 2, (
            "a renderelt felugró ablak közepén nem a kijelölt piros kép látszik"
        )

        QTest.keyRelease(
            window, Qt.Key.Key_Alt, Qt.KeyboardModifier.ControlModifier
        )
        assert _varj(qt_app, lambda: not popup.isVisible()), (
            "az Alt elengedése után látható maradt az előnézet"
        )
        QTest.keyRelease(window, Qt.Key.Key_Control)

    controller.setShowTooltipsEnabled(False)
    QTest.mouseMove(window, QPoint(1, 1))
    QTest.mouseMove(window, nagy_pont, delay=10)
    assert _varj(
        qt_app,
        lambda area=nagy_area: area.property("containsMouse"),
    ), "a nagy képcella lebegtetése nem jutott el a könyvtár-rácsig"
    QTest.keyPress(window, Qt.Key.Key_Control)
    QTest.keyPress(window, Qt.Key.Key_Alt, Qt.KeyboardModifier.ControlModifier)
    assert _varj(qt_app, lambda: popup.isVisible()), (
        "a buboréksúgó kikapcsolása elrejtette az előnézetet (#4949)"
    )
    QTest.keyRelease(window, Qt.Key.Key_Alt, Qt.KeyboardModifier.ControlModifier)
    QTest.keyRelease(window, Qt.Key.Key_Control)
    assert _varj(qt_app, lambda: not popup.isVisible())

    controller.setEnableHover(False)
    QTest.keyPress(window, Qt.Key.Key_Control)
    QTest.keyPress(window, Qt.Key.Key_Alt, Qt.KeyboardModifier.ControlModifier)
    assert not popup.isVisible(), (
        "a kikapcsolt EnableHover mellett megjelent az előnézet"
    )
    QTest.keyRelease(window, Qt.Key.Key_Alt, Qt.KeyboardModifier.ControlModifier)
    QTest.keyRelease(window, Qt.Key.Key_Control)

    controller.setEnableHover(True)
    controller.setShowTooltipsEnabled(True)

    # A tartalomnézet kliensszélességének határa szigorú: 1024 px-en zárva,
    # 1025 px-en nyitva. A popup és az egérkurzor helye ettől független.
    window.setProperty("selectedIndexes", [nagy_sor])
    window.setProperty("selectedIndex", nagy_sor)
    _racs_szelessege(window, grid, qt_app, 1024)
    QTest.keyPress(window, Qt.Key.Key_Control)
    QTest.keyPress(window, Qt.Key.Key_Alt, Qt.KeyboardModifier.ControlModifier)
    assert _varj(qt_app, lambda: popup.property("clientWidth") == 1024), (
        "a tartalomnézet szélessége nem állt be pontosan 1024 px-re"
    )
    assert not popup.isVisible(), "1024 px-es tartalomnézetnél megjelent a popup"
    _racs_szelessege(window, grid, qt_app, 1025)
    assert _varj(qt_app, lambda: popup.property("clientWidth") == 1025), (
        "a tartalomnézet szélessége nem állt be pontosan 1025 px-re"
    )
    assert _varj(qt_app, lambda: popup.isVisible()), (
        "1025 px-es tartalomnézetnél nem jelent meg a popup"
    )
    QTest.keyRelease(window, Qt.Key.Key_Alt, Qt.KeyboardModifier.ControlModifier)
    QTest.keyRelease(window, Qt.Key.Key_Control)
    assert _varj(qt_app, lambda: not popup.isVisible())
