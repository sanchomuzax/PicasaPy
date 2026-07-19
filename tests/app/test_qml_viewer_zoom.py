"""QML-funkcionális tesztek: néző-zoom (#6) — fit / 1:1 / tetszőleges.

A zoom-állapotgép, a csúszka/gombok jelenléte, a Ctrl+görgős zoom útja
(wheelZoom), a pásztázás-korlátozás és a lapozáskori visszaállás — a
közös qml_app fixture-ön.
"""

from PySide6.QtCore import Q_ARG, QEventLoop, QMetaObject, QObject, Qt, QTimer


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _invoke(qt_app, obj, name, *args):
    QMetaObject.invokeMethod(
        obj, name, Qt.ConnectionType.DirectConnection,
        *[Q_ARG("QVariant", a) for a in args],
    )
    qt_app.processEvents()


def _wait_ms(qt_app, ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()
    qt_app.processEvents()


def _open_viewer(window, qt_app, index=0):
    window.setProperty("viewerOpen", True)
    viewer = _child(window, "photoViewer")
    viewer.setProperty("currentIndex", index)
    qt_app.processEvents()
    return viewer


def _wait_photo_loaded(window, qt_app):
    """A néző képének betöltéséig vár (paintedWidth > 0), max ~3 mp."""
    image = _child(window, "viewerImage")
    for _ in range(30):
        if image.property("paintedWidth") > 0:
            return image
        _wait_ms(qt_app, 100)
    raise AssertionError("a néző képe nem töltődött be")


class TestZoomStateMachine:
    def test_opens_in_fit_mode(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        viewer = _open_viewer(window, qt_app)
        assert viewer.property("zoomMode") == "fit"
        assert viewer.property("zoomFactor") == 1.0

    def test_set_zoom_custom_and_clamp(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        viewer = _open_viewer(window, qt_app)
        _invoke(qt_app, viewer, "setZoom", 2.5)
        assert viewer.property("zoomMode") == "custom"
        assert abs(viewer.property("zoomFactor") - 2.5) < 1e-6
        _invoke(qt_app, viewer, "setZoom", 99)
        assert viewer.property("zoomFactor") == 8.0
        _invoke(qt_app, viewer, "setZoom", 0.01)
        assert viewer.property("zoomFactor") == 0.25
        _invoke(qt_app, viewer, "zoomFit")
        assert viewer.property("zoomMode") == "fit"
        assert viewer.property("zoomFactor") == 1.0

    def test_zoom_actual_uses_source_pixels(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        viewer = _open_viewer(window, qt_app)
        image = _wait_photo_loaded(window, qt_app)
        _invoke(qt_app, viewer, "zoomActual")
        assert viewer.property("zoomMode") == "actual"
        expected = image.property("sourceSize").width() / image.property(
            "paintedWidth"
        )
        expected = min(8.0, max(0.25, expected))
        assert abs(viewer.property("zoomFactor") - expected) < 0.01

    def test_wheel_zoom_scales(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        viewer = _open_viewer(window, qt_app)
        _invoke(qt_app, viewer, "wheelZoom", 120)
        assert abs(viewer.property("zoomFactor") - 1.2) < 0.01
        _invoke(qt_app, viewer, "wheelZoom", -120)
        assert viewer.property("zoomMode") == "fit"   # ~1.0 → vissza fitre

    def test_navigation_resets_to_fit(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        viewer = _open_viewer(window, qt_app, 0)
        _invoke(qt_app, viewer, "setZoom", 3)
        viewer.setProperty("currentIndex", 1)
        qt_app.processEvents()
        assert viewer.property("zoomMode") == "fit"
        assert viewer.property("zoomFactor") == 1.0


class TestPan:
    def test_pan_clamped_to_image_bounds(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        viewer = _open_viewer(window, qt_app)
        _wait_photo_loaded(window, qt_app)
        _invoke(qt_app, viewer, "setZoom", 4)
        viewer.setProperty("panX", 999999)
        viewer.setProperty("panY", 999999)
        _invoke(qt_app, viewer, "clampPan")
        assert viewer.property("panX") < 999999
        assert viewer.property("panY") < 999999

    def test_fit_resets_pan(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        viewer = _open_viewer(window, qt_app)
        _invoke(qt_app, viewer, "setZoom", 4)
        viewer.setProperty("panX", 20)
        _invoke(qt_app, viewer, "zoomFit")
        assert viewer.property("panX") == 0
        assert viewer.property("panY") == 0

    def test_pan_area_only_active_when_zoomed(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        viewer = _open_viewer(window, qt_app)
        pan_area = _child(window, "viewerPanArea")
        assert pan_area.property("enabled") is False
        _invoke(qt_app, viewer, "setZoom", 2)
        assert pan_area.property("enabled") is True


class TestZoomBarAndPlaceholders:
    def test_zoom_bar_present_with_controls(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        _open_viewer(window, qt_app)
        assert _child(window, "viewerZoomBar").property("visible") is True
        for name in ("zoomFitButton", "zoomActualButton", "zoomSlider"):
            _child(window, name)

    def test_crop_mode_hides_bar_and_resets_zoom(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        viewer = _open_viewer(window, qt_app)
        _invoke(qt_app, viewer, "setZoom", 3)
        panel = _child(window, "viewerEditorPanel")
        panel.setProperty("cropActive", True)
        qt_app.processEvents()
        assert _child(window, "viewerZoomBar").property("visible") is False
        assert viewer.property("zoomFactor") == 1.0
        panel.setProperty("cropActive", False)
        qt_app.processEvents()

    def test_compare_placeholders_disabled(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        _open_viewer(window, qt_app)
        for name in ("compareButtonA", "compareButtonAB", "compareButtonAA"):
            button = _child(window, name)
            assert button.property("enabled") is False
