"""A Vágás panel elrendezése és üres kijelölésű gombállapota (#7394)."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QSignalSpy, QTest

from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.varakozas import var_feltetelre

_TURES = 3
_REFERENCIA_TABHOZ_KEPEST = {
    "cropGuideText": 77,
    "cropAspectComboRow": 132,
    "cropSuggestionRow": 163,
    "cropRotateButton": 242,
}
_GOMBALLAPOT = {
    "cropRotateButton": False,
    "cropPreviewButton": False,
    "cropResetButton": False,
    "cropApplyButton": False,
    "cropCancelButton": True,
}


def _var(qt_app, condition, timeout: float = 10.0) -> bool:
    return var_feltetelre(qt_app, condition, timeout)


def _szurke_atmenet(konyvtar) -> None:
    kep = QImage(1024, 256, QImage.Format.Format_RGB32)
    festo = QPainter(kep)
    atmenet = QLinearGradient(0, 0, 1024, 0)
    atmenet.setColorAt(0.0, QColor(0, 0, 0))
    atmenet.setColorAt(1.0, QColor(255, 255, 255))
    festo.fillRect(0, 0, 1024, 256, atmenet)
    festo.end()
    assert kep.save(str(konyvtar / "gray_ramp.jpg"), "JPG", 95)


@pytest.fixture
def crop_app(rogzitett_betu, qt_app, tmp_path, request):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_szurke_atmenet,
        belyegkep_meret=256,
        valodi_belyegkep=True,
        keep_modul=request.module,
    )


def _item(root: QObject, name: str) -> QQuickItem:
    found = root.findChild(QObject, name)
    assert isinstance(found, QQuickItem), f"a(z) {name} nem QQuickItem"
    return found


def _click(window: QQuickWindow, item: QQuickItem) -> None:
    assert item.isVisible() and item.width() > 0 and item.height() > 0
    center = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )


def _open_viewer_and_crop(window, qt_app, height_delta: int) -> QObject:
    window.setWidth(1280)
    window.setHeight(960 + height_delta)
    assert _var(
        qt_app,
        lambda: window.width() == 1280 and window.height() == 960 + height_delta,
    )
    window.setProperty("viewerOpen", True)
    viewer = window.findChild(QObject, "photoViewer")
    assert viewer is not None
    viewer.setProperty("currentIndex", 0)

    panel = window.findChild(QObject, "viewerEditorPanel")
    assert panel is not None
    tile = _item(window, "editToolCrop")
    _click(window, tile)
    assert _var(qt_app, lambda: panel.property("cropActive") is True), (
        "a Vágás csempére kattintás nem nyitotta meg a panelt"
    )
    return panel


def _render_frame(window: QQuickWindow, qt_app) -> QImage:
    frames = QSignalSpy(window.frameSwapped)
    window.update()
    assert _var(qt_app, lambda: frames.count() > 0), (
        "az eszközpanel renderelt képkockája nem készült el"
    )
    image = window.grabWindow()
    assert not image.isNull(), "az eszközpanel renderelt képe üres"
    return image


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_a_renderelt_panel_es_ures_kijelolesu_gombok_megegyeznek_a_referenciaval(
    crop_app, qt_app, height_delta, tmp_path
):
    window, _controller, _engine = crop_app
    assert isinstance(window, QQuickWindow)
    _open_viewer_and_crop(window, qt_app, height_delta)

    tab_bar = _item(window, "editTabBar")
    assert tab_bar.isVisible(), "a fülsáv nem látszik a Vágás panel fölött"
    tab_top = tab_bar.mapToScene(QPointF(0, 0)).y()
    elteresek = {}
    for name, expected in _REFERENCIA_TABHOZ_KEPEST.items():
        item = _item(window, name)
        assert item.isVisible(), f"a(z) {name} nem látszik"
        actual = item.mapToScene(QPointF(0, 0)).y() - tab_top
        elteresek[name] = actual - expected

    kepkockak = QSignalSpy(window.frameSwapped)
    window.update()
    assert _var(qt_app, lambda: kepkockak.count() > 0), (
        "a Vágás panel renderelt képkockája nem készült el"
    )
    kep = window.grabWindow()
    assert not kep.isNull(), "a renderelt Vágás panel képe üres"
    if height_delta == 0:
        assert kep.save(str(tmp_path / "vagas_panel_7394.png")), (
            "a renderelt Vágás panel képe nem menthető"
        )

    assert all(abs(delta) <= _TURES for delta in elteresek.values()), (
        "a job-911 __10 mért elemeihez képest a panel fülsávhoz viszonyított "
        f"eltérése nagyobb ±{_TURES} px-nél: {elteresek}"
    )
    assert abs(_item(window, "cropSuggestionRow").height() - 70) <= _TURES, (
        "a bélyegképcsempék magassága eltér az eredeti 70 px-es dobozától"
    )
    allapotok = {
        name: bool(_item(window, name).property("enabled"))
        for name in _GOMBALLAPOT
    }
    assert allapotok == _GOMBALLAPOT, (
        "kijelölés nélkül a gombállapotok nem egyeznek a job-911 __10-zel: "
        f"{allapotok}"
    )


def test_a_cancel_valodi_egerkattintasra_bezarja_a_vagast(crop_app, qt_app):
    window, _controller, _engine = crop_app
    panel = _open_viewer_and_crop(window, qt_app, 0)

    cancel = _item(window, "cropCancelButton")
    assert cancel.isEnabled(), "a Cancelnek kijelölés nélkül is aktívnak kell lennie"
    _click(window, cancel)
    assert _var(qt_app, lambda: panel.property("cropActive") is False), (
        "a Cancel valódi egérkattintása nem zárta be a Vágás panelt"
    )


def test_a_szomszedos_eszkopanelek_renderelt_kepe(crop_app, qt_app, tmp_path):
    """A Crop layoutváltozása mellett a három szomszéd panel tovább rajzol."""
    window, _controller, _engine = crop_app
    window.setWidth(1280)
    window.setHeight(960)
    window.setProperty("viewerOpen", True)
    viewer = window.findChild(QObject, "photoViewer")
    assert viewer is not None
    viewer.setProperty("currentIndex", 0)
    panel = window.findChild(QObject, "viewerEditorPanel")
    assert panel is not None

    eszkozok = (
        ("editToolRedeye", "redeyeActive", "redeyeCancelButton", "vorosszem"),
        ("editToolRetouch", "retouchActive", "retouchCancelButton", "retus"),
        ("editToolTilt", "tiltActive", "tiltCancelButton", "kiegyenesites"),
    )
    for tile_name, active_name, cancel_name, output_name in eszkozok:
        _click(window, _item(window, tile_name))
        assert _var(qt_app, lambda active_name=active_name: panel.property(active_name) is True), (
            f"a(z) {tile_name} csempe nem nyitotta meg az eszközt"
        )
        if active_name == "redeyeActive":
            assert _var(qt_app, lambda: panel.property("redeyeFoundCount") == 0), (
                "a szürke próbaképen a Vörösszem találatszáma nem állt be"
            )
        assert _item(window, "editTabBar").isVisible(), (
            f"a fülsáv nem látszik a(z) {active_name} eszköz fölött"
        )
        image = _render_frame(window, qt_app)
        assert image.save(str(tmp_path / f"{output_name}_7394.png")), (
            f"a(z) {active_name} regressziós képe nem menthető"
        )

        _click(window, _item(window, cancel_name))
        assert _var(qt_app, lambda active_name=active_name: panel.property(active_name) is False), (
            f"a(z) {cancel_name} nem zárta be a panelt"
        )
