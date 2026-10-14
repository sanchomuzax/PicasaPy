"""#4928: a Ctrl+Alt felugró előnézet valódi eseményre jelenik meg."""
# rontás-kontroll: PopDisplay megvalósítás nélkül → 1 failed

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.jpeg_factory import make_jpeg
from tests.support.varakozas import var_feltetelre


def _elonezetesi_probak_kepei(lib):
    make_jpeg(lib / "a-nagy.jpg", size=(1600, 900))
    make_jpeg(lib / "b-kicsi.jpg", size=(320, 160))


@pytest.fixture
def qml_app_ctrl_alt(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_elonezetesi_probak_kepei,
    )


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, feltetel, masodperc)


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


def test_ctrl_alt_a_mutato_alatti_kepet_mutatja_es_elengedesre_elrejti(
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

        QTest.mouseMove(window, QPoint(1, 1))
        QTest.keyPress(window, Qt.Key.Key_Control)
        QTest.keyPress(
            window, Qt.Key.Key_Alt, Qt.KeyboardModifier.ControlModifier
        )
        assert not popup.isVisible(), (
            "üres pontról kép nélkül is megjelent az előnézet"
        )
        QTest.keyRelease(
            window, Qt.Key.Key_Alt, Qt.KeyboardModifier.ControlModifier
        )
        QTest.keyRelease(window, Qt.Key.Key_Control)

        QTest.mouseMove(window, kis_pont, delay=10)
        assert _varj(
            qt_app, lambda area=kis_area: area.property("containsMouse")
        ), (
            "a valódi egérmozgás nem jutott el a kis képcelláig: "
            f"pont=({kis_pont.x()}, {kis_pont.y()}), "
            f"ablak=({window.width()}, {window.height()}), "
            f"cella=({kis_area.x()}, {kis_area.y()}, "
            f"{kis_area.width()}, {kis_area.height()})"
        )
        assert _varj(
            qt_app,
            lambda area=kis_area: grid.property("hoverPreviewRow")
            == area.parentItem().property("index"),
        ), "a kis képcella lebegtetése nem jutott el a könyvtár-rácsig"
        QTest.keyPress(window, Qt.Key.Key_Control)
        QTest.keyPress(
            window, Qt.Key.Key_Alt, Qt.KeyboardModifier.ControlModifier
        )
        assert not popup.isVisible(), (
            "1024 px-nél keskenyebb előnézeti ablak is megjelent"
        )
        QTest.keyRelease(
            window, Qt.Key.Key_Alt, Qt.KeyboardModifier.ControlModifier
        )
        QTest.keyRelease(window, Qt.Key.Key_Control)

        QTest.mouseMove(window, nagy_pont, delay=10)
        assert _varj(
            qt_app, lambda area=nagy_area: area.property("containsMouse")
        ), (
            "a valódi egérmozgás nem jutott el a nagy képcelláig"
        )
        assert _varj(
            qt_app,
            lambda area=nagy_area: grid.property("hoverPreviewRow")
            == area.parentItem().property("index"),
        ), "a nagy képcella lebegtetése nem jutott el a könyvtár-rácsig"
        QTest.keyPress(window, Qt.Key.Key_Control)
        QTest.keyPress(
            window, Qt.Key.Key_Alt, Qt.KeyboardModifier.ControlModifier
        )
        assert controller.property("ctrlAltHeld"), (
            "a valódi Ctrl+Alt billentyűesemény nem frissítette az állapotot"
        )
        image = window.findChild(QObject, "ctrlAltHoverPreviewImage")
        assert _varj(qt_app, lambda: popup.isVisible()), (
            "Ctrl+Alt és képre mutatás mellett nem jelent meg az előnézet: "
            f"active={window.property('active')}, "
            f"held={controller.property('ctrlAltHeld')}, "
            f"row={grid.property('hoverPreviewRow')}, "
            f"requested={popup.property('requested')}, "
            f"windowSize=({popup.width()}, {popup.height()}), "
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
        assert popup.width() > 1024, (
            "a specifikáció szerinti gyermekablak-szélesség nem nagyobb 1024 px-nél"
        )
        image_center = image.mapToScene(
            QPointF(image.width() / 2, image.height() / 2)
        ).toPoint()
        center_pixel = rendered.pixelColor(image_center)
        assert center_pixel.red() > center_pixel.green() * 2, (
            "a renderelt felugró ablak közepén nem a próbakép látszik"
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
        lambda: grid.property("hoverPreviewRow")
        == nagy_area.parentItem().property("index"),
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
