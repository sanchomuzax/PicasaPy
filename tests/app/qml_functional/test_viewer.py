"""QML-funkcionális tesztek: néző (viewer) — verzió-felirat, forgatás,
arc-overlay, feliratszerkesztés, mappaleírás, splash (#155: a korábbi
`test_qml_functional.py` egyik szelete, processzenkénti izolációhoz)."""

from PySide6.QtCore import QObject

from picasapy.version import version_string


def _viewer_image(window):
    image = window.findChild(QObject, "viewerImage")
    assert image is not None, "viewerImage nem található"
    return image


def _do_photo_op(controller, qt_app, action) -> None:
    """#141: a csillag/felirat/forgatás háttérszálon fut (NAS-írás +
    célzott index-UPDATE) — megvárja a `photoOpFinished` jelzést, majd
    lefuttat egy processEvents-et, hogy a QML-kötések is frissüljenek."""
    from PySide6.QtCore import QEventLoop, QTimer

    loop = QEventLoop()
    controller.photoOpFinished.connect(loop.quit)
    action()
    QTimer.singleShot(2000, loop.quit)
    loop.exec()
    qt_app.processEvents()


class TestVersionLabel:
    def test_header_shows_version_string(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        label = window.findChild(QObject, "versionLabel")
        assert label is not None, "versionLabel nem található"
        assert label.property("text") == version_string()


class TestViewerRotation:
    def test_rotate_applies_to_open_viewer(self, qml_app, qt_app):
        # A felhasználó által talált hiba: a rácsban forgott a thumb, de a
        # megnyitott néző képe nem — a kötésnek a modell-frissítésre kell
        # reagálnia, nem a (változatlan) státuszsorra.
        window, controller, _ = qml_app
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()
        _do_photo_op(controller, qt_app, lambda: controller.rotateRight(0))
        image = _viewer_image(window)
        assert image.property("iniSteps") == 1
        assert image.property("rotation") == 90

    def test_rotation_follows_navigation(self, qml_app, qt_app):
        window, controller, _ = qml_app
        _do_photo_op(controller, qt_app, lambda: controller.rotateRight(0))  # a.jpg elforgatva, b.jpg nem
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()
        assert _viewer_image(window).property("rotation") == 90
        viewer.setProperty("currentIndex", 1)
        qt_app.processEvents()
        assert _viewer_image(window).property("rotation") == 0


class TestViewerFacesOverlay:
    """#147: a mentett faces= régiók kapcsolható overlay-je a nézőben —
    csak olvasás, felismerés nélkül; a nevek a [Contacts2] szekcióból."""

    def test_hidden_by_default(self, qml_app, qt_app, tmp_path):
        ini = tmp_path / "kepek" / ".picasa.ini"
        ini.write_text(
            "[a.jpg]\nfaces=rect64(3f845bcb59418507),8e62b2035b74b477;\n",
            encoding="utf-8",
        )
        window, _controller, _ = qml_app
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()

        overlay = window.findChild(QObject, "facesOverlay")
        assert overlay is not None, "facesOverlay nem található"
        assert overlay.property("visible") is False

    def test_toggle_shows_frame_with_resolved_name(self, qml_app, qt_app, tmp_path):
        ini = tmp_path / "kepek" / ".picasa.ini"
        ini.write_text(
            "[Contacts2]\n"
            "8e62b2035b74b477=Kis Éva;;\n"
            "[a.jpg]\n"
            "faces=rect64(3f845bcb59418507),8e62b2035b74b477;\n",
            encoding="utf-8",
        )
        window, _controller, _ = qml_app
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()

        viewer.setProperty("facesVisible", True)
        qt_app.processEvents()

        overlay = window.findChild(QObject, "facesOverlay")
        assert overlay.property("visible") is True
        faces = overlay.property("faces")
        assert len(faces) == 1
        assert faces[0]["name"] == "Kis Éva"

        viewer.setProperty("facesVisible", False)
        qt_app.processEvents()
        assert overlay.property("visible") is False

    def test_toggle_button_flips_faces_visible(self, qml_app, qt_app, tmp_path):
        ini = tmp_path / "kepek" / ".picasa.ini"
        ini.write_text(
            "[a.jpg]\nfaces=rect64(3f845bcb59418507),ffffffffffffffff;\n",
            encoding="utf-8",
        )
        window, _controller, _ = qml_app
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()

        button = window.findChild(QObject, "facesToggleButton")
        assert button is not None, "facesToggleButton nem található"
        from PySide6.QtCore import QMetaObject

        assert viewer.property("facesVisible") is False
        QMetaObject.invokeMethod(button, "clicked")
        qt_app.processEvents()
        assert viewer.property("facesVisible") is True


class TestCaptionEditing:
    def test_caption_field_updates_after_set_caption(self, qml_app, qt_app):
        # A felirat-mező kötésének a modell revíziójára kell reagálnia,
        # ahogy a forgatás-kötés is (lásd photo.iniSteps fent).
        window, controller, _ = qml_app
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()
        field = window.findChild(QObject, "captionField")
        assert field is not None, "captionField nem található"
        _do_photo_op(controller, qt_app, lambda: controller.setCaption(0, "teszt felirat"))
        assert field.property("text") == "teszt felirat"

    def test_caption_field_empty_for_other_photo(self, qml_app, qt_app):
        window, controller, _ = qml_app
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()
        _do_photo_op(controller, qt_app, lambda: controller.setCaption(0, "teszt felirat"))
        viewer.setProperty("currentIndex", 1)
        qt_app.processEvents()
        field = window.findChild(QObject, "captionField")
        assert field.property("text") == ""


class TestFolderDescriptionField:
    def test_header_component_binds_description(self, qml_app, qt_app):
        # A fejléc a feedben (#64) delegate-ként él; a leírás-kötést a
        # komponensen önállóan ellenőrizzük (offscreen a ListView-delegate
        # létrejötte nem garantált).
        import picasapy.app.application as app_module
        from PySide6.QtCore import QUrl
        from PySide6.QtQml import QQmlComponent

        window, controller, engine = qml_app
        comp = QQmlComponent(
            engine,
            QUrl.fromLocalFile(
                str(app_module._APP_DIR / "qml" / "PicasaPy" / "LightboxHeader.qml")
            ),
        )
        header = comp.createWithInitialProperties(
            {"folderName": "kepek", "description": "teszt leírás"}
        )
        assert comp.errors() == []
        assert header is not None
        field = header.findChild(QObject, "folderDescriptionField")
        assert field is not None, "folderDescriptionField nem található"
        assert field.property("text") == "teszt leírás"

    def test_description_slot_round_trip(self, qml_app, qt_app):
        # A feed-fejléc útvonala: setFolderDescriptionOf → ini →
        # folderDescriptionOf (a QML-kötés ezt olvassa).
        window, controller, _ = qml_app
        controller.setFolderDescription("teszt leírás")
        qt_app.processEvents()
        assert (
            controller.folderDescriptionOf(controller.currentFolder)
            == "teszt leírás"
        )


class TestSplashWiring:
    """#189 bekötés: a splash a Main.qml legfelső rétegén ül, és a
    startupStatus.ready-re eltűnik (a fixture kész állapotból indul)."""

    def test_splash_present_and_hidden_when_ready(self, qml_app, qt_app):
        window, _, _ = qml_app
        splash = window.findChild(QObject, "splashScreen")
        assert splash is not None, "splashScreen nem található a Main.qml-ben"
        qt_app.processEvents()
        assert splash.property("ready") is True
        assert splash.property("visible") is False
