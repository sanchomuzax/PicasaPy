"""#4083: a nagyított néző az aktív képi eszköznek adja az egéreseményt.

Közös segédmodul (#4829): a 21 esetes fájl egyben a CI-n túllépte a
2400 MB-os memóriaplafont (a QML-példányok memóriája tesztről tesztre
halmozódik), ezért az esetek három tesztfájlba kerültek — a #4764 mintájára.
A próbák törzse itt él, a fájlok csak a paraméterezést adják."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest


def _item(window, name: str) -> QObject:
    item = window.findChild(QObject, name)
    assert item is not None, f"{name} nem található a főablakban"
    return item


def _pump(qt_app, count: int = 8) -> None:
    for _ in range(count):
        qt_app.processEvents()


def _point(item, x: float = 0.5, y: float = 0.5) -> QPoint:
    scene = item.mapToScene(QPointF(item.width() * x, item.height() * y))
    return QPoint(round(scene.x()), round(scene.y()))


def _open_viewer(
    qml_app_negyzet_kepek, qt_app, tmp_path, height_delta: int, paint=False
):
    window, controller, engine = qml_app_negyzet_kepek
    window.setProperty("width", 1280)
    window.setProperty("height", 1005 + height_delta)
    if paint:
        from picasapy.ini import update_document

        kep = Path(tmp_path / "kepek" / "a.jpg")
        update_document(
            kep.parent / ".picasa.ini",
            lambda document: document.with_value(
                kep.name,
                "filters",
                "ReanimatedEyeColor=1,6.000000,20.000000;",
            ),
            backup=False,
        )
        controller.rescan()
        _pump(qt_app)
    window.setProperty("viewerOpen", True)
    _pump(qt_app)
    viewer = _item(window, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    _pump(qt_app)
    return window, controller, engine, viewer, _item(window, "viewerEditorPanel")


def _zoom(window, viewer, qt_app, target: float = 2.0) -> float:
    """A valódi, látható zoomcsúszkán egérkattintással nagyít."""
    slider = _item(window, "zoomSlider")
    also, felso = 0.0, 1.0
    mert = float(viewer.property("zoomFactor"))
    for _ in range(12):
        arany = (also + felso) / 2
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            _point(slider, arany, 0.5),
        )
        _pump(qt_app)
        mert = float(viewer.property("zoomFactor"))
        if mert < target:
            also = arany
        else:
            felso = arany
    assert mert > 1.01, f"a valódi zoomcsúszka nem nagyított: {mert:.3f}"
    return mert


def _drag(
    window, target, pan_area, qt_app,
    start_ratio=(0.34, 0.34), finish=(0.62, 0.62),
):
    start = _point(target, *start_ratio)
    end = _point(target, *finish)
    QTest.mouseMove(window, start, 5)
    _pump(qt_app, 2)
    QTest.mousePress(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        start,
    )
    _pump(qt_app, 2)
    pan_pressed = bool(pan_area.property("pressed"))
    target_pressed = bool(target.property("pressed"))
    QTest.mouseMove(window, end, 10)
    _pump(qt_app, 3)
    QTest.mouseRelease(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        end,
    )
    _pump(qt_app)
    return pan_pressed, target_pressed


def _click(window, target, pan_area, qt_app, ratio=(0.45, 0.45)):
    point = _point(target, *ratio)
    QTest.mouseMove(window, point, 5)
    _pump(qt_app, 2)
    QTest.mousePress(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        point,
    )
    _pump(qt_app, 2)
    pan_pressed = bool(pan_area.property("pressed"))
    target_pressed = bool(target.property("pressed"))
    QTest.mouseRelease(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        point,
    )
    _pump(qt_app)
    return pan_pressed, target_pressed


def _outside_overlay_drag(window, pan_area, overlay, qt_app):
    """Valódi pan-area húzáspontot választ a kirajzolt átfedőn kívülről."""
    pairs = (
        ((0.02, 0.3), (0.02, 0.7)),
        ((0.98, 0.3), (0.98, 0.7)),
        ((0.3, 0.02), (0.7, 0.02)),
        ((0.3, 0.98), (0.7, 0.98)),
    )
    for start_ratio, finish_ratio in pairs:
        start = _point(pan_area, *start_ratio)
        finish = _point(pan_area, *finish_ratio)
        start_local = overlay.mapFromScene(start)
        finish_local = overlay.mapFromScene(finish)
        start_outside = (
            start_local.x() < 0 or start_local.y() < 0
            or start_local.x() >= overlay.width()
            or start_local.y() >= overlay.height()
        )
        finish_outside = (
            finish_local.x() < 0 or finish_local.y() < 0
            or finish_local.x() >= overlay.width()
            or finish_local.y() >= overlay.height()
        )
        if start_outside and finish_outside:
            return _drag(
                window, pan_area, pan_area, qt_app,
                start_ratio=start_ratio, finish=finish_ratio,
            )
    pytest.fail("nem találtam a tényleges átfedőn kívüli pásztázási sávot")


def eszkoz_proba(
    qml_app_negyzet_kepek, qt_app, tmp_path, height_delta, device
):
    window, _app_controller, engine, viewer, panel = _open_viewer(
        qml_app_negyzet_kepek,
        qt_app,
        tmp_path,
        height_delta,
        paint=device == "ecset",
    )
    edit = engine.rootContext().contextProperty("editController")
    if device == "ecset":
        for _ in range(100):
            _pump(qt_app, 2)
            if edit.paintMaskSupported:
                break
            QTest.qWait(20)
        assert edit.paintMaskSupported is True, "a próbakép ecset-effektje nem töltődött be"

    zoom = _zoom(window, viewer, qt_app)
    pan_area = _item(window, "viewerPanArea")
    assert zoom > 1.01 and pan_area.property("enabled") is True

    if device == "ecset":
        target = _item(window, "paintMaskArea")
        pan_pressed, target_pressed = _drag(
            window, target, pan_area, qt_app
        )
    elif device == "voros-szem":
        panel.setProperty("redeyeActive", True)
        target = _item(window, "redeyeDragArea")
        pan_pressed, target_pressed = _drag(
            window, target, pan_area, qt_app
        )
    elif device == "retus":
        panel.setProperty("retouchActive", True)
        target = _item(window, "retouchClickArea")
        pan_pressed, target_pressed = _click(
            window, target, pan_area, qt_app
        )
    elif device == "szoveg":
        panel.setProperty("textActive", True)
        _item(window, "textContentField").setProperty("text", "Próbaszöveg")
        _pump(qt_app)
        target = _item(window, "textClickArea")
        pan_pressed, target_pressed = _drag(
            window, target, pan_area, qt_app
        )
        elso_pozicio = edit._text_pending_pos
        _drag(
            window,
            target,
            pan_area,
            qt_app,
            start_ratio=(0.62, 0.62),
            finish=(0.78, 0.78),
        )
        masodik_pozicio = edit._text_pending_pos
    else:
        viewer.setProperty("facesEditMode", True)
        viewer.setProperty("facesVisible", True)
        target = _item(window, "facesCreateArea")
        pan_pressed, target_pressed = _drag(
            window, target, pan_area, qt_app
        )

    assert target_pressed is True, (
        f"#4083 {device}: zoom={zoom:.3f}; az aktív átfedő nem kapott egérlenyomást"
    )
    assert pan_pressed is False, (
        f"#4083 {device}: zoom={zoom:.3f}; az átfedő eseményét a pásztázó kapta meg"
    )

    if device == "ecset":
        assert edit._paint_strokes(), "az egérhúzás nem módosította az ecsetmaszkot"
    elif device == "voros-szem":
        assert len(edit.redeyeRegions) == 1, "a húzás nem hozott létre vörösszem-kört"
    elif device == "retus":
        assert panel.property("retouchPatchPending") is True, (
            "a kattintás nem jelölte ki a retusálás célpontját"
        )
    elif device == "szoveg":
        assert panel.property("textPlacementPending") is True, (
            "a kattintás nem helyezte el a szövegátfedőt"
        )
        assert masodik_pozicio != elso_pozicio, (
            "a következő kattintás nem mozdította el a szövegátfedőt"
        )
    else:
        overlay = _item(window, "facesOverlay")
        assert overlay.property("hasDraft") is True, (
            "a húzás nem hozott létre arcjelölő-négyzetet"
        )
    # Az aktív eszköz kirajzolt felületén kívüli szürke sávban továbbra is
    # a pásztázó nyer; a pontokat a valódi pan-terület és átfedő geometriája
    # alapján választjuk.
    before = (float(viewer.property("panX")), float(viewer.property("panY")))
    margin_zoom = _zoom(window, viewer, qt_app, target=1.05)
    assert margin_zoom > 1.01
    margin_pan_pressed, _ = _outside_overlay_drag(
        window, pan_area, target, qt_app
    )
    after = (float(viewer.property("panX")), float(viewer.property("panY")))
    assert margin_pan_pressed is True, (
        f"#4083 {device}: az átfedőn kívüli sáv húzását nem kapta meg a pásztázó"
    )
    assert abs(after[0] - before[0]) + abs(after[1] - before[1]) > 1, (
        f"#4083 {device}: az átfedőn kívüli sáv húzása nem pásztázott"
    )
    # A rontás-kontroll ugyanennek a valódi ablaknak a másik képén fut:
    # ott már nincs aktív overlay, tehát a képen végzett húzásnak továbbra
    # is a pásztázót kell mozgatnia. A pontot a kép geometriája adja.
    panel.setProperty("redeyeActive", False)
    panel.setProperty("retouchActive", False)
    panel.setProperty("textActive", False)
    viewer.setProperty("facesEditMode", False)
    viewer.setProperty("currentIndex", 1)
    _pump(qt_app, 12)
    zoom = _zoom(window, viewer, qt_app, target=1.05)
    image = _item(window, "viewerImage")
    pan_area = _item(window, "viewerPanArea")

    before = (float(viewer.property("panX")), float(viewer.property("panY")))
    image_pan_pressed, _ = _drag(window, image, pan_area, qt_app)
    after = (float(viewer.property("panX")), float(viewer.property("panY")))
    assert zoom > 1.01
    assert image_pan_pressed is True, "overlay nélküli képhúzáskor a pásztázó nem kapta meg az egeret"
    assert abs(after[0] - before[0]) + abs(after[1] - before[1]) > 1, (
        "az overlay nélküli képhúzás nem mozdította el a képet"
    )


def kettos_nezet_proba(
    qml_app_negyzet_kepek, qt_app, tmp_path, height_delta, layout
):
    window, _controller, _engine, viewer, _panel = _open_viewer(
        qml_app_negyzet_kepek, qt_app, tmp_path, height_delta
    )
    layout_button = _item(window, f"viewerLayout{layout.title()}")
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _point(layout_button),
    )
    _pump(qt_app)
    assert viewer.property("layoutMode") == layout
    viewer.setProperty("aktivOldal", "bal")
    zoom = _zoom(window, viewer, qt_app, target=1.3)

    # A divider közeli kattintás a jobb/felső kép saját geometriájából jön.
    # Bal fókusznál a nagyított bal kép nyers Image-doboza átlóghat a
    # középső résen, de a rajza a saját kereténél le van vágva. Ez a pont
    # ezért a jobb képen belül, a bal Image dobozán kívül látszik.
    image = _item(window, "viewerImage")
    left_image = _item(window, "viewerImageElotte")
    divider_point = _point(image, 0.05, 0.5)
    left_local = left_image.mapFromScene(divider_point)
    assert 0 <= left_local.x() < left_image.width()
    assert 0 <= left_local.y() < left_image.height()
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        divider_point,
    )
    _pump(qt_app)

    assert zoom > 1.01
    assert viewer.property("aktivOldal") == "jobb", (
        f"#{layout} nagyított nézet: az elválasztó melletti kattintás nem váltott fókuszt"
    )

    # A középre kattintás megőrzi az általános fókuszváltás őrét is.
    viewer.setProperty("aktivOldal", "bal")
    _pump(qt_app)
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _point(image),
    )
    _pump(qt_app)
    assert viewer.property("aktivOldal") == "jobb", (
        f"#{layout} nagyított nézet: a kép közepére kattintás nem váltott fókuszt"
    )
