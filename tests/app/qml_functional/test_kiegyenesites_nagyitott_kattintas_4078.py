"""#4078 — nagyításnál a Kiegyenesítés eszközsávja egérrel működjön."""

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, QRectF, Qt
from PySide6.QtGui import QGuiApplication, QWheelEvent
from PySide6.QtTest import QTest


def _item(window, name: str):
    item = window.findChild(QObject, name)
    assert item is not None, f"{name} nem található a főablakban"
    return item


def _pump(qt_app, count: int = 8) -> None:
    for _ in range(count):
        qt_app.processEvents()


def _varj_forgatasra(window, qt_app, fok: float, hatarido_ms: int = 5000) -> None:
    """A `rescan` aszinkron: a forgatás nem azonnal ér a nézőkép elemére."""
    kep = _item(window, "viewerImage")
    hatralevo = hatarido_ms
    while kep.property("rotation") != fok and hatralevo > 0:
        QTest.qWait(20)
        _pump(qt_app, 2)
        hatralevo -= 20
    assert kep.property("rotation") == fok


def _point(item, x: float = 0.5, y: float = 0.5) -> QPoint:
    scene = item.mapToScene(QPointF(item.width() * x, item.height() * y))
    return QPoint(round(scene.x()), round(scene.y()))


def _click(window, item, qt_app) -> None:
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _point(item),
    )
    _pump(qt_app)


def _zoom_slider_to(window, viewer, qt_app, target: float) -> float:
    """A látható zoomcsúszkán végzett egérkattintással állítja be a zoomot."""
    slider = _item(window, "zoomSlider")
    assert slider.property("visible") is True
    also = 0.0
    felso = 1.0
    mert = float(viewer.property("zoomFactor"))
    for _ in range(12):
        arany = (also + felso) / 2
        pont = _point(slider, arany, 0.5)
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            pont,
        )
        _pump(qt_app)
        mert = float(viewer.property("zoomFactor"))
        if mert < target:
            also = arany
        else:
            felso = arany
    return mert


def _open_viewer(qml_app, qt_app):
    window, controller, _engine = qml_app
    window.setProperty("width", 1280)
    window.setProperty("height", 1005)
    window.setProperty("viewerOpen", True)
    _pump(qt_app)
    viewer = _item(window, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    _pump(qt_app)
    return window, controller, viewer, _item(window, "viewerEditorPanel")


def _ensure_tilt(window, panel, qt_app) -> None:
    if panel.property("tiltActive") is not True:
        _click(window, _item(window, "editToolTilt"), qt_app)
    assert panel.property("tiltActive") is True
    assert not window.grabWindow().isNull(), "a Kiegyenesítés sávja nem rajzolódott ki"


def _target_mouse_area(item):
    areas = [
        child
        for child in item.findChildren(QObject)
        if child.metaObject().className().endswith("MouseArea")
    ]
    assert areas, f"{item.objectName()} saját egérterülete hiányzik"
    return areas[0]


def _press_release(window, item, pan_area, panel, qt_app):
    target_area = _target_mouse_area(item)
    point = _point(item)
    QTest.mouseMove(window, point, 5)
    QTest.mousePress(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        point,
    )
    _pump(qt_app, 2)
    pan_received = bool(pan_area.property("pressed"))
    target_received = bool(target_area.property("pressed"))
    QTest.mouseRelease(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        point,
    )
    _pump(qt_app)
    return {
        "pan_received": pan_received,
        "target_received": target_received,
        "tool_closed": panel.property("tiltActive") is False,
    }


def _drag_tilt_slider(window, viewer, qt_app):
    slider = _item(window, "tiltSlider")
    pan_area = _item(window, "viewerPanArea")
    start = _point(slider, float(slider.property("visualPosition")), 0.5)
    finish = _point(slider, 0.78, 0.5)
    before_value = float(slider.property("value"))
    before_pan = (float(viewer.property("panX")), float(viewer.property("panY")))

    QTest.mouseMove(window, start, 5)
    _pump(qt_app, 2)
    QTest.mousePress(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        start,
    )
    _pump(qt_app, 2)
    pan_received = bool(pan_area.property("pressed"))
    slider_received = bool(slider.property("pressed"))
    QTest.mouseMove(window, finish, 10)
    _pump(qt_app, 3)
    during_value = float(slider.property("value"))
    QTest.mouseRelease(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        finish,
    )
    _pump(qt_app)
    after_pan = (float(viewer.property("panX")), float(viewer.property("panY")))
    return {
        "pan_received": pan_received,
        "slider_received": slider_received,
        "value_delta": during_value - before_value,
        "pan_delta": (after_pan[0] - before_pan[0], after_pan[1] - before_pan[1]),
    }


def _toolbar_interactions(window, viewer, panel, qt_app, zoom_target: float):
    pan_area = _item(window, "viewerPanArea")
    outcomes = {"zoom": []}

    _ensure_tilt(window, panel, qt_app)
    outcomes["zoom"].append(_zoom_slider_to(window, viewer, qt_app, zoom_target))
    _pan_toolbar_into_view(window, viewer, qt_app)
    outcomes["apply"] = _press_release(
        window, _item(window, "tiltApplyButton"), pan_area, panel, qt_app
    )

    _ensure_tilt(window, panel, qt_app)
    outcomes["zoom"].append(_zoom_slider_to(window, viewer, qt_app, zoom_target))
    _pan_toolbar_into_view(window, viewer, qt_app)
    outcomes["cancel"] = _press_release(
        window, _item(window, "tiltCancelButton"), pan_area, panel, qt_app
    )

    _ensure_tilt(window, panel, qt_app)
    outcomes["zoom"].append(_zoom_slider_to(window, viewer, qt_app, zoom_target))
    _pan_toolbar_into_view(window, viewer, qt_app)
    outcomes["slider"] = _drag_tilt_slider(window, viewer, qt_app)
    return outcomes


def _assert_interactions_reach_toolbar(
    outcomes, label: str, zoom_target: float
) -> None:
    assert all(
        value == pytest.approx(zoom_target, abs=0.04)
        for value in outcomes["zoom"]
    ), outcomes
    for name in ("apply", "cancel"):
        result = outcomes[name]
        assert result["pan_received"] is False, f"{label}: {name} nyomását elnyelte a pásztázó"
        assert result["target_received"] is True, f"{label}: {name} saját egérterülete nem kapott nyomást"
        assert result["tool_closed"] is True, f"{label}: a {name} kattintása nem zárta be az eszközt"

    slider = outcomes["slider"]
    assert slider["pan_received"] is False, f"{label}: a pásztázó elkapta a csúszka húzását"
    assert slider["slider_received"] is True, f"{label}: a csúszka nem kapta meg a húzást"
    assert abs(slider["value_delta"]) > 0.2, f"{label}: a húzás nem mozdította el a csúszkát"
    assert slider["pan_delta"] == pytest.approx((0.0, 0.0), abs=0.01), (
        f"{label}: a csúszka húzása pásztázta a képet: {slider['pan_delta']}"
    )


@pytest.mark.parametrize("target", (1.05, 1.3, 2.0))
def test_nagyitott_nezetben_az_apply_cancel_es_tilt_csuszka_egerrel_mukodik(
    qml_app_negyzet_kepek, qt_app, target
):
    window, _controller, viewer, panel = _open_viewer(qml_app_negyzet_kepek, qt_app)
    outcomes = _toolbar_interactions(window, viewer, panel, qt_app, target)
    print(f"#4078 1up zoom={target:.2f}: {outcomes!r}")
    _assert_interactions_reach_toolbar(
        outcomes, f"1up zoom={target:.2f}", target
    )


@pytest.mark.parametrize(
    ("layout", "rotated"),
    (("aa", False), ("ab", False), ("1up", True)),
)
def test_nagyitott_toolbar_kattintas_kettos_nezetben_es_forgatva(
    qml_app_negyzet_kepek, qt_app, layout, rotated
):
    window, controller, _engine = qml_app_negyzet_kepek
    if rotated:
        from picasapy.ini import update_document

        photo_path = Path(str(controller.photos.filePathAt(0)))
        update_document(
            photo_path.parent / ".picasa.ini",
            lambda document: document.with_value(
                photo_path.name, "rotate", "rotate(1)"
            ),
            backup=False,
        )
        controller.rescan()

    window, _controller, viewer, panel = _open_viewer(qml_app_negyzet_kepek, qt_app)
    if layout != "1up":
        _click(window, _item(window, f"viewerLayout{layout.title()}"), qt_app)
        assert viewer.property("layoutMode") == layout
    if rotated:
        _varj_forgatasra(window, qt_app, 90)

    # A kettős nézetben a fókuszált félen lévő TapHandler a képhúzást
    # fókuszváltásként kezeli; itt az eseményút mérése a kis, de küszöb feletti
    # nagyításon történik. Az 1.3/2.0-as szinteket külön, 1-up esetben mérjük.
    zoom_target = 1.05
    outcomes = _toolbar_interactions(window, viewer, panel, qt_app, zoom_target)
    toolbar = _item(window, "editorToolBar")
    apply_button = _item(window, "tiltApplyButton")
    print(
        "#4078 módgeometria: "
        f"window=({window.width()}, {window.height()}), "
        f"toolbar visible={toolbar.property('visible')}, "
        f"toolbar scene={_item_rect(toolbar)}, apply scene={_item_rect(apply_button)}, "
        f"photoArea scene={_item_rect(_item(window, 'viewerPhotoArea'))}, "
        f"rotation={_item(window, 'viewerImage').property('rotation')}, "
        f"scale={_item(window, 'viewerImage').property('scale')}"
    )
    print(f"#4078 {layout=}, {rotated=}: {outcomes!r}")
    _assert_interactions_reach_toolbar(outcomes, f"{layout=} {rotated=}", zoom_target)


def _item_rect(item) -> QRectF:
    corners = [
        item.mapToScene(QPointF(x, y))
        for x, y in (
            (0, 0),
            (item.width(), 0),
            (0, item.height()),
            (item.width(), item.height()),
        )
    ]
    xs = [point.x() for point in corners]
    ys = [point.y() for point in corners]
    return QRectF(min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))


def _drag_pan(window, viewer, qt_app, delta: QPoint, start_fraction=(0.25, 0.25)):
    area = _item(window, "viewerPhotoArea")
    pan_area = _item(window, "viewerPanArea")
    start = _point(area, *start_fraction)
    finish = start + delta
    before = (float(viewer.property("panX")), float(viewer.property("panY")))
    QTest.mouseMove(window, start, 5)
    QTest.mousePress(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        start,
    )
    _pump(qt_app, 2)
    received = bool(pan_area.property("pressed"))
    last_at_press = (
        float(pan_area.property("lastX")),
        float(pan_area.property("lastY")),
    )
    QTest.mouseMove(window, finish, 10)
    _pump(qt_app, 3)
    last_after_move = (
        float(pan_area.property("lastX")),
        float(pan_area.property("lastY")),
    )
    QTest.mouseRelease(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        finish,
    )
    _pump(qt_app)
    after = (float(viewer.property("panX")), float(viewer.property("panY")))
    return {
        "received": received,
        "delta": (after[0] - before[0], after[1] - before[1]),
        "last_at_press": last_at_press,
        "last_after_move": last_after_move,
    }


def _pan_toolbar_into_view(window, viewer, qt_app) -> None:
    """Valódi képhúzással tegye a sáv teljes befoglaló téglalapját láthatóvá."""
    area = _item(window, "viewerPhotoArea")
    toolbar = _item(window, "editorToolBar")
    viewport = QRectF(0, 0, window.width(), window.height())
    clip = _item_rect(area).intersected(viewport)
    for _ in range(48):
        toolbar_rect = _item_rect(toolbar)
        visible = toolbar_rect.intersected(clip)
        if (
            visible.width() >= toolbar_rect.width() - 1
            and visible.height() >= toolbar_rect.height() - 1
        ):
            return

        dx = 0
        dy = 0
        if toolbar_rect.left() < clip.left():
            dx = 20
        elif toolbar_rect.right() > clip.right():
            dx = -20
        if toolbar_rect.top() < clip.top():
            dy = 20
        elif toolbar_rect.bottom() > clip.bottom():
            dy = -20
        assert dx or dy, f"a sávot nem lehet a látható képtérbe pásztázni: {toolbar_rect}"
        drag = _drag_pan(window, viewer, qt_app, QPoint(dx, dy), (0.25, 0.25))
        assert drag["received"] is True
        assert abs(drag["delta"][0]) + abs(drag["delta"][1]) > 0, (
            f"a képhúzás nem mozdította a sávot: {toolbar_rect}, {drag!r}"
        )
    raise AssertionError(
        f"48 valódi képhúzás után sem fért a sáv a látható képtérbe: "
        f"{_item_rect(toolbar)} vs. {clip}"
    )


def test_nagyitott_kephuzas_a_toolbaron_kivul_tovabbra_is_pasztaz(
    qml_app_negyzet_kepek, qt_app
):
    window, _controller, viewer, panel = _open_viewer(qml_app_negyzet_kepek, qt_app)
    _ensure_tilt(window, panel, qt_app)
    zoom = _zoom_slider_to(window, viewer, qt_app, 2.0)
    area = _item(window, "viewerPhotoArea")
    toolbar_rect = _item_rect(_item(window, "editorToolBar"))
    point = _point(area, 0.25, 0.25)
    assert not toolbar_rect.contains(point), "a pásztázás próbakattintása a sávra esik"
    drag = _drag_pan(window, viewer, qt_app, QPoint(35, 25))
    print(f"#4078 pásztázás zoom={zoom:.3f}: {drag!r}")
    assert zoom == pytest.approx(2.0, abs=0.04)
    assert drag["received"] is True, "a viewerPanArea nem kapta meg a sávon kívüli húzást"
    assert abs(drag["delta"][0]) + abs(drag["delta"][1]) > 1, (
        "a képhúzás nem mozdította el a képet"
    )


@pytest.mark.parametrize("layout", ("aa", "ab"))
def test_kettos_nezetben_a_nagyitott_kephuzas_tovabbra_is_pasztaz(
    qml_app_negyzet_kepek, qt_app, layout
):
    window, _controller, viewer, panel = _open_viewer(qml_app_negyzet_kepek, qt_app)
    _click(window, _item(window, f"viewerLayout{layout.title()}"), qt_app)
    assert viewer.property("layoutMode") == layout
    _ensure_tilt(window, panel, qt_app)
    zoom = _zoom_slider_to(window, viewer, qt_app, 1.3)
    drag = _drag_pan(window, viewer, qt_app, QPoint(35, 25), (0.25, 0.5))
    print(f"#4078 {layout} pásztázás zoom={zoom:.3f}: {drag!r}")
    assert zoom == pytest.approx(1.3, abs=0.04)
    assert drag["received"] is True, (
        f"{layout}: a nagyított képen a viewerPanArea nem kapta meg a húzást"
    )
    assert abs(drag["delta"][0]) + abs(drag["delta"][1]) > 1, (
        f"{layout}: a húzás nem mozdította el a képet"
    )


def test_a_reszben_lathato_apply_gomb_zoom_kozben_is_kattinthato(
    qml_app_negyzet_kepek, qt_app
):
    window, _controller, viewer, panel = _open_viewer(qml_app_negyzet_kepek, qt_app)
    _ensure_tilt(window, panel, qt_app)
    _zoom_slider_to(window, viewer, qt_app, 2.0)
    area = _item(window, "viewerPhotoArea")
    button = _item(window, "tiltApplyButton")
    pan_area = _item(window, "viewerPanArea")
    button_mouse_area = _target_mouse_area(button)
    viewport = QRectF(0, 0, window.width(), window.height())
    area_rect = _item_rect(area).intersected(viewport)

    visible_button = QRectF()
    print(
        f"#4078 részleges próba indul: toolbar={_item_rect(_item(window, 'editorToolBar'))}, "
        f"button={_item_rect(button)}, area={area_rect}, "
        f"image={_item_rect(_item(window, 'viewerImage'))}"
    )
    for _ in range(24):
        button_rect = _item_rect(button)
        visible_button = button_rect.intersected(area_rect)
        if 0 < visible_button.height() < button_rect.height() - 1:
            break
        _drag_pan(window, viewer, qt_app, QPoint(0, -30), (0.4, 0.4))
        area_rect = _item_rect(area).intersected(viewport)

    image_rect = _item_rect(_item(window, "viewerImage"))
    button_rect = _item_rect(button)
    print(
        f"#4078 részleges próba vége: toolbar={_item_rect(_item(window, 'editorToolBar'))}, "
        f"button={button_rect}, visible={visible_button}, area={area_rect}, "
        f"image={image_rect}, pan={(viewer.property('panX'), viewer.property('panY'))}"
    )
    assert image_rect.bottom() > area_rect.bottom(), (
        "a méréshez a kinagyított kép aljának ki kell lógnia a photoArea-ból"
    )
    assert 0 < visible_button.height() < button_rect.height() - 1, (
        f"nem sikerült a gomb részben látható állapotát előállítani: "
        f"gomb={button_rect}, látható={visible_button}"
    )

    point = QPoint(round(visible_button.center().x()), round(visible_button.center().y()))
    QTest.mousePress(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        point,
    )
    _pump(qt_app, 2)
    pan_received = bool(pan_area.property("pressed"))
    button_received = bool(button_mouse_area.property("pressed"))
    QTest.mouseRelease(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        point,
    )
    _pump(qt_app)
    print(
        f"#4078 részben látszó Apply: gomb={button_rect}, látható={visible_button}, "
        f"{pan_received=}, {button_received=}, bezárt={panel.property('tiltActive') is False}"
    )
    assert pan_received is False
    assert button_received is True
    assert panel.property("tiltActive") is False


@pytest.mark.parametrize("target", (1.05, 1.3, 2.0))
def test_a_zoomcsuszka_valodi_kattintasai_elirik_a_kert_nagyitast(
    qml_app_negyzet_kepek, qt_app, target
):
    window, _controller, viewer, _panel = _open_viewer(qml_app_negyzet_kepek, qt_app)
    _click(window, _item(window, "editToolTilt"), qt_app)
    assert not window.grabWindow().isNull()
    mert = _zoom_slider_to(window, viewer, qt_app, target)
    print(f"#4078 zoomcsúszka: cél={target:.2f}, mért={mert:.3f}")
    assert mert == pytest.approx(target, abs=0.04)


def test_nagyitva_a_kiegyenesites_alkalmaz_gombja_valodi_kattintasra_bezar(
    qml_app, qt_app
):
    window, _controller, _engine = qml_app
    window.setProperty("width", 1280)
    window.setProperty("height", 1005)
    window.setProperty("viewerOpen", True)
    _pump(qt_app)

    viewer = _item(window, "photoViewer")
    panel = _item(window, "viewerEditorPanel")
    _click(window, _item(window, "editToolTilt"), qt_app)
    assert panel.property("tiltActive") is True
    assert not window.grabWindow().isNull(), "a főablak nem rajzolódott ki"

    # A zoomot valódi Ctrl+görgő-esemény állítja; addig görgetünk, amíg a
    # pásztázó ténylegesen aktív küszöbe fölé nem jutunk.
    area = _item(window, "viewerPhotoArea")
    zoom_point = area.mapToScene(QPointF(area.width() / 2, area.height() / 2))

    zoom = float(viewer.property("zoomFactor"))
    for _ in range(24):
        wheel = QWheelEvent(
            zoom_point,
            zoom_point,
            QPoint(0, 0),
            QPoint(0, 120),
            Qt.MouseButton.NoButton,
            Qt.KeyboardModifier.ControlModifier,
            Qt.ScrollPhase.NoScrollPhase,
            False,
        )
        QGuiApplication.sendEvent(window, wheel)
        _pump(qt_app, 1)
        zoom = float(viewer.property("zoomFactor"))
        if zoom > 1.01:
            break
    assert zoom > 1.01, f"a valódi Ctrl+görgő nem nagyított: zoom={zoom:.3f}"

    pan_area = _item(window, "viewerPanArea")
    photo_area = _item(window, "viewerPhotoArea")
    toolbar = _item(window, "editorToolBar")
    common_parent = photo_area.parentItem()
    sibling_names = [item.objectName() for item in common_parent.childItems()]
    apply_button = _item(window, "tiltApplyButton")
    apply_mouse_areas = [
        child
        for child in apply_button.findChildren(QObject)
        if child.metaObject().className().endswith("MouseArea")
    ]
    assert apply_mouse_areas, "az Alkalmaz gomb egérterülete hiányzik"
    apply_mouse_area = apply_mouse_areas[0]

    print(
        "#4078 eseménymérés: "
        f"zoom={zoom:.3f}; pan parent={pan_area.parentItem().objectName()!r}, "
        f"z={pan_area.property('z')}, méret=({pan_area.width():.1f},"
        f"{pan_area.height():.1f}); photoArea parent azonos="
        f"{pan_area.parentItem() == common_parent}, photoArea z={photo_area.property('z')}, "
        f"testvér-sorrend={sibling_names}; toolbar parent="
        f"{toolbar.parentItem().objectName()!r}, z={toolbar.property('z')}; "
        f"pan geometriája tartalmazza a gombközepet="
        f"{pan_area.contains(pan_area.mapFromScene(QPointF(_point(apply_button))))}"
    )

    target = _point(apply_button)
    QTest.mousePress(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        target,
    )
    _pump(qt_app, 2)
    pan_received_press = bool(pan_area.property("pressed"))
    toolbar_received_press = bool(apply_mouse_area.property("pressed"))
    QTest.mouseRelease(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        target,
    )
    _pump(qt_app)

    print(
        "#4078 kattintás útja: "
        f"pan kapta={pan_received_press}, Alkalmaz MouseArea kapta="
        f"{toolbar_received_press}, tiltActive utána={panel.property('tiltActive')}"
    )
    assert not pan_received_press, "a viewerPanArea kapta el az Alkalmaz lenyomását"
    assert toolbar_received_press, "az Alkalmaz saját egérterülete nem kapott lenyomást"
    assert panel.property("tiltActive") is False, (
        "a nagyított Kiegyenesítés Alkalmaz gombjának valódi kattintása nem zárta be az eszközt"
    )
