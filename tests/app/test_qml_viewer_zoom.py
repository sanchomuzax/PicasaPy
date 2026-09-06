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
        _invoke(qt_app, viewer, "setZoomValue", 0.75)
        assert viewer.property("zoomMode") == "custom"
        # #2492: a csúszka NORMALIZÁLT [0, 1], a szorzót a MÉRT képlet adja
        # (`0,5 ≤ v ≤ 1: r · 2^(4(v−0,5))`). A 0,75 tehát a valódi méret
        # kétszerese, bármi is `r`.
        kettoszeres = viewer.property("zoomFactor")
        # `r` = a valódi méret aránya: a MÉRT rögzített pont v = 0,5-nél
        _invoke(qt_app, viewer, "setZoomValue", 0.5)
        r = viewer.property("zoomFactor")
        assert abs(kettoszeres - 2 * r) < 1e-6
        _invoke(qt_app, viewer, "setZoomValue", 0.75)
        # ⚠️ MÉRT vágás [0, 1]-re (`0x005d13a9` / `0x005d13c6`)
        _invoke(qt_app, viewer, "setZoomValue", 99)
        assert viewer.property("zoomValue") == 1.0
        assert abs(viewer.property("zoomFactor") - 4 * r) < 1e-6   # 400 %
        _invoke(qt_app, viewer, "setZoomValue", -5)
        assert viewer.property("zoomValue") == 0.0
        assert viewer.property("zoomFactor") == 1.0                # illesztés
        _invoke(qt_app, viewer, "zoomFit")
        assert viewer.property("zoomMode") == "fit"
        assert viewer.property("zoomFactor") == 1.0

    def test_zoom_actual_uses_the_FILE_pixels(self, qml_app, qt_app):
        """⚠️ #2492: KORÁBBAN ez a teszt a `sourceSize.width`-hez
        hasonlított — vagyis a HIBÁT rögzítette szerződésként.

        A `sourceSize` a `PhotoViewer.qml`-ben BEÁLLÍTOTT 2560-as plafon
        (a Qt olvasáskor a beállított értéket adja vissza), nem a kép
        mérete. Az „1:1" ezért a valódi mérettől függetlenül 2560-cal
        számolt, és többszörösen nagyított — a tulajdonos ezt jelentette.

        Az eredeti `1to1` buboréksúgója: „Display Photo at actual size" —
        tehát a FÁJL képpontjai a mérce."""
        window, controller, _lib, _engine = qml_app
        viewer = _open_viewer(window, qt_app)
        image = _wait_photo_loaded(window, qt_app)
        _invoke(qt_app, viewer, "zoomActual")
        assert viewer.property("zoomMode") == "actual"

        model = controller.property("photos")
        varhato = model.pixelWidthAt(viewer.property("currentIndex")) / image.property(
            "paintedWidth"
        )
        assert abs(viewer.property("zoomFactor") - varhato) < 0.01

    def test_wheel_zoom_scales(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        viewer = _open_viewer(window, qt_app)
        # #2492: a görgő a NORMALIZÁLT értéket lépteti (kattanásonként
        # 0,05), és a mért vágás miatt 0 alá nem megy.
        _invoke(qt_app, viewer, "wheelZoom", 120)
        assert abs(viewer.property("zoomValue") - 0.05) < 1e-9
        _invoke(qt_app, viewer, "wheelZoom", -120)
        assert viewer.property("zoomMode") == "fit"   # vissza az illesztésre
        assert viewer.property("zoomValue") == 0.0

    def test_navigation_resets_to_fit(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        viewer = _open_viewer(window, qt_app, 0)
        _invoke(qt_app, viewer, "setZoomValue", 0.75)
        viewer.setProperty("currentIndex", 1)
        qt_app.processEvents()
        assert viewer.property("zoomMode") == "fit"
        assert viewer.property("zoomFactor") == 1.0


class TestPan:
    def test_pan_clamped_to_image_bounds(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        viewer = _open_viewer(window, qt_app)
        _wait_photo_loaded(window, qt_app)
        _invoke(qt_app, viewer, "setZoomValue", 0.75)
        viewer.setProperty("panX", 999999)
        viewer.setProperty("panY", 999999)
        _invoke(qt_app, viewer, "clampPan")
        assert viewer.property("panX") < 999999
        assert viewer.property("panY") < 999999

    def test_fit_resets_pan(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        viewer = _open_viewer(window, qt_app)
        _invoke(qt_app, viewer, "setZoomValue", 0.75)
        viewer.setProperty("panX", 20)
        _invoke(qt_app, viewer, "zoomFit")
        assert viewer.property("panX") == 0
        assert viewer.property("panY") == 0

    def test_pan_area_only_active_when_zoomed(self, qml_app, qt_app):
        """⚠️ #2492: a próba a csúszka JOBB VÉGÉRE megy, nem a 0,75-re.

        A pásztázás akkor él, ha a kép nagyobb a látótérnél
        (`zoomFactor > 1.01`). A fixtúra képei (320 × 160, 100 × 100)
        KISEBBEK a nézetnél, tehát a valódi méretük (`r`) 1 ALATT van — a
        0,75-ös csúszkaállás náluk még mindig kicsinyít. A csúszka jobb
        vége a MÉRT `4·r`, ami már nagyít.

        Korábban a `sourceSize`-alapú, hibás `r` (2560-ból) minden képnél
        nagynak látszott, ezért ment át a 0,75 — a próba a HIBÁRA
        támaszkodott."""
        window, _controller, _lib, _engine = qml_app
        viewer = _open_viewer(window, qt_app)
        _wait_photo_loaded(window, qt_app)
        pan_area = _child(window, "viewerPanArea")
        assert pan_area.property("enabled") is False
        _invoke(qt_app, viewer, "setZoomValue", 1.0)
        assert viewer.property("zoomFactor") > 1.01, (
            "a próba előfeltétele nem teljesült: a csúszka jobb vége sem "
            f"nagyít ({viewer.property('zoomFactor'):.2f})"
        )
        assert pan_area.property("enabled") is True


class TestZoomBarAndPlaceholders:
    """#2564: a hármas az ALSÓ ESZKÖZSÁVBAN ül (`trayViewerZoomRow`), a
    fotó fölött már csak a MI két arc-gombunk lebeg (`viewerFacesBar`).
    A LÁTHATÓSÁGI SZABÁLY változatlan: videón és vágás közben nincs
    nagyítás — csak a hordozója más."""

    def test_zoom_bar_present_with_controls(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        _open_viewer(window, qt_app)
        assert _child(window, "trayViewerZoomRow").property("visible") is True
        for name in ("zoomFitButton", "zoomActualButton", "zoomSlider"):
            _child(window, name)

    def test_crop_mode_hides_bar_and_resets_zoom(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        viewer = _open_viewer(window, qt_app)
        _invoke(qt_app, viewer, "setZoomValue", 0.75)
        panel = _child(window, "viewerEditorPanel")
        panel.setProperty("cropActive", True)
        qt_app.processEvents()
        assert _child(window, "trayViewerZoomRow").property("visible") is False
        assert _child(window, "viewerFacesBar").property("visible") is False
        assert viewer.property("zoomFactor") == 1.0
        panel.setProperty("cropActive", False)
        qt_app.processEvents()

    def test_compare_placeholders_disabled(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        _open_viewer(window, qt_app)
        for name in ("compareButtonA", "compareButtonAB", "compareButtonAA"):
            button = _child(window, name)
            assert button.property("enabled") is False


class TestZoomClipping:
    def test_photo_area_clips_zoomed_image(self, qml_app, qt_app):
        # felhasználói hibajelzés (#6 után): a nagyított kép kirajzolódott a
        # bal paneli/felső sáv fölé — a képterület clipje a regressziós őr
        window, _controller, _lib, _engine = qml_app
        _open_viewer(window, qt_app)
        area = _child(window, "viewerPhotoArea")
        assert area.property("clip") is True
