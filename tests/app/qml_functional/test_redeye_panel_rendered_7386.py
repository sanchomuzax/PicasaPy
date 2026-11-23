"""#7386: a Vörösszem panel képi és egéreseményes paritása.

Az eredeti referencia a `.tmp/job-837/kepernyo__24.png` (kiegyenesítés utáni
panel) és `__10.png` (figyelmeztetés nélküli panel). A pixelteszt csak a
fülsáv ikonjainak nem szöveges rajzát nézi; minden méretet a QML-elemek
tényleges geometriájából mér, a gomboknál a
`docs/specs/szerkeszto-panel-meretek.md` értékeihez képest ±3 px tűréssel.
Betűképpont-méretet nem rögzít.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.varakozas import hibaturo_feltetel, var_feltetelre

_TURES = 3
_GOMB_X = {
    "redeyeAutoButton": 38,
    "redeyePreviewButton": 144,
    "redeyeResetButton": 91,
    "redeyeApplyButton": 38,
    "redeyeCancelButton": 144,
}
_GOMB_FELIRAT = {
    "redeyeAutoButton": "Auto",
    "redeyePreviewButton": "Preview",
    "redeyeResetButton": "Reset",
    "redeyeApplyButton": "Apply",
    "redeyeCancelButton": "Cancel",
}


def _szurke_atmenet(lib) -> None:
    """A job-837 szürke ramp képe, vörösszem-találat nélküli alapállapothoz."""
    kep = QImage(1024, 256, QImage.Format.Format_RGB32)
    festo = QPainter(kep)
    atmenet = QLinearGradient(0, 0, 1024, 0)
    atmenet.setColorAt(0.0, QColor(0, 0, 0))
    atmenet.setColorAt(1.0, QColor(255, 255, 255))
    festo.fillRect(0, 0, 1024, 256, atmenet)
    festo.end()
    assert kep.save(str(lib / "gray_ramp.jpg"), "JPG", 95)


@pytest.fixture
def redeye_app(rogzitett_betu, qt_app, tmp_path, request):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_szurke_atmenet,
        belyegkep_meret=256,
        valodi_belyegkep=True,
        keep_modul=request.module,
    )


def _var(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def _item(root, object_name: str) -> QQuickItem:
    found = root.findChild(QObject, object_name)
    assert isinstance(found, QQuickItem), f"a(z) {object_name} nem QQuickItem"
    return found


def _click(window, item: QQuickItem) -> None:
    assert item.isVisible() and item.width() > 0 and item.height() > 0
    center = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )


def _open_viewer(window, qt_app, height_delta: int = 0):
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
    image = _item(window, "viewerImage")
    assert _var(qt_app, lambda: image.isVisible() and image.property("paintedWidth") > 0)
    return viewer


def _open_tool(window, qt_app, tool_name: str, active_property: str):
    tile = _item(window, tool_name)
    _click(window, tile)
    panel = _item(window, "viewerEditorPanel")
    assert _var(qt_app, lambda: panel.property(active_property) is True)
    return panel


def _visual_items(root: QQuickItem):
    """A Repeater rajzolt gyerekeit is bejárja (#651)."""
    yield root
    for child in root.childItems():
        yield from _visual_items(child)


def _visual_named(root: QQuickItem, object_name: str):
    return next(
        (item for item in _visual_items(root) if item.objectName() == object_name),
        None,
    )


def _icon_ink_pixels(frame: QImage, icon: QQuickItem) -> int:
    """A fülikon nem szöveges, kirajzolt vonalait számolja a saját hátteréhez képest."""
    top_left = icon.mapToScene(QPointF(0, 0))
    left, top = round(top_left.x()), round(top_left.y())
    width, height = round(icon.width()), round(icon.height())
    background = frame.pixelColor(min(left + width - 1, left + 2), min(top + height - 1, top + 2))
    return sum(
        1
        for y in range(max(0, top), min(frame.height(), top + height))
        for x in range(max(0, left), min(frame.width(), left + width))
        if _color_distance(frame.pixelColor(x, y), background) > 30
    )


def _color_distance(first, second) -> int:
    return (
        abs(first.red() - second.red())
        + abs(first.green() - second.green())
        + abs(first.blue() - second.blue())
    )


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_redeye_renderelt_panel_egyezik_a_job_837_al(
    redeye_app, qt_app, height_delta
):
    window, _controller, engine = redeye_app
    _open_viewer(window, qt_app, height_delta)
    panel = _open_tool(window, qt_app, "editToolRedeyeIcon", "redeyeActive")
    edit = engine.rootContext().contextProperty("editController")
    assert _var(qt_app, lambda: edit.property("redeyeFoundCount") == 0)

    tab_bar = _item(window, "editTabBar")
    tab_icon = _item(window, "editTabFixesIcon")
    title = _item(window, "redeyeTitleText")
    title_icon = _item(window, "redeyeTitleIcon")
    guide = _item(window, "redeyeGuideText")
    instruction_block = _item(window, "redeyeInstructionBlock")
    note = window.findChild(QObject, "redeyeFrameHintLabel")
    cancel = _item(window, "redeyeCancelButton")
    preview = window.findChild(QObject, "redeyePreviewButton")

    hibak = []
    if not tab_bar.isVisible():
        hibak.append("a fülsáv rejtett")
    if not title.isVisible() or title.property("text") != "Redeye Repair":
        hibak.append("a Redeye Repair cím nem látszik")
    if not title_icon.isVisible():
        hibak.append("a vörösszem-eszköz ikonja nem látszik")
    if not guide.isVisible():
        hibak.append("az útmutató nem látszik")
    if note is None:
        hibak.append("a Note hiányzik")
    elif not note.property("visible"):
        hibak.append("a Note rejtett találat nélküli állapotban")
    if preview is None or preview.property("label") != "Preview":
        hibak.append("a Preview gomb hiányzik")
    if window.findChild(QObject, "redeyeRegionCountLabel") is not None:
        hibak.append("a Regions selected sor jelen van")
    if window.findChild(QObject, "redeyeHideOutlinesCheck") is not None:
        hibak.append("a Preview changes without square outlines jelölő jelen van")

    if note is not None and guide.isVisible():
        guide_bottom = guide.mapToScene(QPointF(0, guide.height())).y()
        note_top = note.mapToScene(QPointF(0, 0)).y()
        note_gap = note_top - guide_bottom
        if abs(note_gap) > _TURES:
            hibak.append(f"a Note és az útmutató közötti rés {note_gap:.1f} px")

    for name, expected_label in _GOMB_FELIRAT.items():
        button = window.findChild(QObject, name)
        if button is None:
            hibak.append(f"hiányzik: {name}")
        elif button.property("label") != expected_label:
            hibak.append(f"{name}: {button.property('label')!r}, nem {expected_label!r}")

    if preview is not None and all(
        window.findChild(QObject, name) is not None for name in _GOMB_FELIRAT
    ):
        for name, expected_x in _GOMB_X.items():
            button = _item(window, name)
            point = button.mapToItem(panel, QPointF(0, 0))
            if abs(point.x() - expected_x) > _TURES:
                hibak.append(f"{name} x={point.x():.1f} px, a referencia {expected_x} px")
        centers = {
            name: _item(window, name).mapToScene(
                QPointF(_item(window, name).width() / 2, _item(window, name).height() / 2)
            ).y()
            for name in _GOMB_FELIRAT
        }
        if not centers["redeyeAutoButton"] < centers["redeyeResetButton"] < centers["redeyeApplyButton"]:
            hibak.append("a gombsorok sorrendje nem Auto/Preview, Reset, Apply/Cancel")

        column_top = instruction_block.mapToScene(QPointF(0, 0)).y()
        block_bottom = column_top + instruction_block.height()
        auto_top = _item(window, "redeyeAutoButton").mapToScene(QPointF(0, 0)).y()
        reset_top = _item(window, "redeyeResetButton").mapToScene(QPointF(0, 0)).y()
        apply_top = _item(window, "redeyeApplyButton").mapToScene(QPointF(0, 0)).y()
        preview_top = _item(window, "redeyePreviewButton").mapToScene(QPointF(0, 0)).y()
        cancel_top = _item(window, "redeyeCancelButton").mapToScene(QPointF(0, 0)).y()
        elteresek = {
            "a Note-blokk és az Auto közötti rés": (auto_top - block_bottom, 36),
            "a Reset eltolása az Auto sorától": (reset_top - auto_top, 34),
            "az Apply eltolása az Auto sorától": (apply_top - auto_top, 68),
            "a Preview függőleges eltolása": (preview_top - auto_top, 0),
            "a Cancel függőleges eltolása": (cancel_top - apply_top, 0),
        }
        for nev, (mert, vart) in elteresek.items():
            if abs(mert - vart) > _TURES:
                hibak.append(f"{nev}: {mert:.1f} px, elvárt {vart} px")

    for name in ("redeyeAutoButton", "redeyeResetButton", "redeyeApplyButton"):
        button = window.findChild(QObject, name)
        if button is not None and button.property("enabled"):
            hibak.append(f"találat nélkül a(z) {name} aktív")
    if preview is not None and preview.property("enabled"):
        hibak.append("találat nélkül a Preview aktív")
    if not cancel.property("enabled"):
        hibak.append("a Cancel letiltott")

    frame = window.grabWindow()
    if frame.isNull():
        hibak.append("a QQuickWindow nem adott renderelt képkockát")
    else:
        if _icon_ink_pixels(frame, tab_icon) < 4:
            hibak.append("a fülsáv ikonja nem rajzolódik ki")
        if _icon_ink_pixels(frame, title_icon) < 4:
            hibak.append("a vörösszem-eszköz ikonja nem rajzolódik ki")

    assert not hibak, "job-837 panel-eltérések: " + "; ".join(hibak)


def test_preview_valodi_egerkattintasra_elrejti_es_visszaallitja_a_keretet(
    redeye_app, qt_app
):
    window, _controller, actual_engine = redeye_app
    _open_viewer(window, qt_app)
    panel = _open_tool(window, qt_app, "editToolRedeyeIcon", "redeyeActive")
    edit = actual_engine.rootContext().contextProperty("editController")
    assert _var(qt_app, lambda: edit.property("redeyeFoundCount") == 0)

    # A csíkos próbaképen nincs automatikus találat; egy normált kézi régió
    # teszi kattinthatóvá a Preview vezérlőt, ugyanúgy, ahogy az eredeti Auto
    # találata vagy egy felhasználói kijelölés tenné.
    edit.addRedeyeRegion(0.2, 0.2, 0.15, 0.15)
    button = window.findChild(QObject, "redeyePreviewButton")
    overlay = _item(window, "redeyeOverlay")
    assert button is not None, "a Preview gomb hiányzik"
    assert _var(qt_app, lambda: button.property("enabled"))
    assert _var(qt_app, lambda: _visual_named(overlay, "redeyeRegionFrame") is not None)

    _click(window, button)
    assert _var(qt_app, lambda: panel.property("redeyeHideOutlines") is True)
    assert _var(qt_app, lambda: _visual_named(overlay, "redeyeRegionFrame") is None)

    _click(window, button)
    assert _var(qt_app, lambda: panel.property("redeyeHideOutlines") is False)
    assert _var(qt_app, lambda: _visual_named(overlay, "redeyeRegionFrame") is not None)


def test_a_fulsav_minden_mod_eszköz_panel_folott_latszik(redeye_app, qt_app):
    window, _controller, _engine = redeye_app
    _open_viewer(window, qt_app)
    panel = _item(window, "viewerEditorPanel")
    tab_bar = _item(window, "editTabBar")
    tab_icon = _item(window, "editTabFixesIcon")
    mode_tools = _item(window, "editorModeToolScroll")
    mode_panels = {
        "redeye": _item(window, "redeyeColumn"),
        "retouch": _item(window, "retouchColumn"),
        "text": _item(window, "textColumn"),
        "crop": _item(window, "cropColumn"),
    }
    eredmeny = {}

    tools = (
        ("redeye", "editToolRedeyeIcon", "redeyeActive", "redeyeCancelButton"),
        ("retouch", "editToolRetouch", "retouchActive", "retouchCancelButton"),
        ("text", "editToolText", "textActive", "textCancelButton"),
        ("crop", "editToolCrop", "cropActive", "cropCancelButton"),
    )
    for nev, tile_name, active, cancel_name in tools:
        _open_tool(window, qt_app, tile_name, active)
        eredmeny[nev] = tab_bar.isVisible()
        if tab_bar.isVisible():
            tab_bottom = tab_bar.mapToScene(QPointF(0, tab_bar.height())).y()
            tool_top = mode_tools.mapToScene(QPointF(0, 0)).y()
            eredmeny[f"{nev}_res"] = tool_top - tab_bottom
            panel_top = mode_panels[nev].mapToScene(QPointF(0, 0)).y()
            eredmeny[f"{nev}_panelen_beluli_felso_margó"] = panel_top - tool_top
            frame = window.grabWindow()
            eredmeny[f"{nev}_fülikon_rajzolt"] = (
                not frame.isNull() and _icon_ink_pixels(frame, tab_icon) >= 4
            )
        _click(window, _item(window, cancel_name))
        assert _var(
            qt_app,
            lambda active_name=active: panel.property(active_name) is False,
        )

    rejtett = [name for name in ("redeye", "retouch", "text", "crop") if not eredmeny[name]]
    assert not rejtett, f"eszköz módban rejtett a fülsáv: {rejtett}; mérés: {eredmeny}"
    for nev, *_ in tools:
        assert abs(eredmeny[f"{nev}_res"]) <= _TURES, (
            f"a {nev} tartalma ráfed a fülsávra: {eredmeny}"
        )
        assert abs(eredmeny[f"{nev}_panelen_beluli_felso_margó"] - 10) <= _TURES, (
            f"a {nev} panel fülsáv alatti eltolása eltér: {eredmeny}"
        )
        assert eredmeny[f"{nev}_fülikon_rajzolt"], (
            f"a fülsáv ikonja a {nev} panel fölött nem rajzolódik ki"
        )
