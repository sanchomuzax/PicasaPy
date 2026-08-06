"""QML-funkcionális tesztek: arc-téglalap SZERKESZTŐ mód a nézőben (#26,
2. kör) — rajzolás/átnevezés/törlés a `FacesOverlay`-en, `facesHelper`-en
át ütközésbiztosan az ini-be írva. A teljes appot építjük fel (`qml_app`
fixture) — a delegate-eken belüli tartalom (MEMORY 2026-07-31:
visible-öröklés csapda / dinamikus Repeater-elemek `findChild`-dal nem
érhetők el) helyett az overlay saját (nem-delegate) API-ját hívjuk:
`openEditorFor`/`commitEditor`/`removeFace` — ugyanúgy, ahogy a
`test_editor.py` a `CropOverlay`/`EditorPanel` függvényeit."""

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt


def _open_viewer(window, qt_app, index=0):
    window.setProperty("viewerOpen", True)
    viewer = window.findChild(QObject, "photoViewer")
    viewer.setProperty("currentIndex", index)
    qt_app.processEvents()
    return viewer


def _overlay(window):
    overlay = window.findChild(QObject, "facesOverlay")
    assert overlay is not None, "facesOverlay nem található"
    return overlay


def _invoke(obj, method, *args):
    qargs = [Q_ARG("QVariant", a) for a in args]
    return QMetaObject.invokeMethod(
        obj, method, Qt.ConnectionType.DirectConnection, *qargs
    )


class TestFacesEditToggle:
    def test_button_flips_edit_mode_and_visibility(self, qml_app, qt_app):
        window, _controller, _ = qml_app
        viewer = _open_viewer(window, qt_app)
        button = window.findChild(QObject, "facesEditToggleButton")
        assert button is not None, "facesEditToggleButton nem található"
        assert viewer.property("facesEditMode") is False
        QMetaObject.invokeMethod(button, "clicked")
        qt_app.processEvents()
        assert viewer.property("facesEditMode") is True
        # a szerkesztés bekapcsolása a láthatóságot is bekapcsolja
        assert viewer.property("facesVisible") is True

    def test_shift_f_toggles_edit_mode(self, qml_app, qt_app):
        window, _controller, _ = qml_app
        viewer = _open_viewer(window, qt_app)
        _invoke(viewer, "toggleFacesEdit")
        qt_app.processEvents()
        assert viewer.property("facesEditMode") is True


class TestAddFaceViaOverlay:
    def test_new_region_with_name_is_written_and_reflected(
        self, qml_app, qt_app, tmp_path
    ):
        window, _controller, _ = qml_app
        viewer = _open_viewer(window, qt_app)
        _invoke(viewer, "toggleFacesEdit")
        qt_app.processEvents()
        overlay = _overlay(window)

        _invoke(overlay, "openEditorFor", 0.1, 0.1, 0.4, 0.4, "", True)
        qt_app.processEvents()
        field = window.findChild(QObject, "faceNameField")
        assert field is not None, "faceNameField nem található"
        field.setProperty("text", "Anna")
        _invoke(overlay, "commitEditor")
        qt_app.processEvents()

        ini_text = (tmp_path / "kepek" / ".picasa.ini").read_text(encoding="utf-8")
        assert "[Contacts2]" in ini_text
        assert "Anna;;" in ini_text
        assert "[a.jpg]" in ini_text
        assert "faces=" in ini_text

        faces = overlay.property("faces")
        assert len(faces) == 1
        assert faces[0]["name"] == "Anna"

    def test_new_region_without_name_is_unidentified(
        self, qml_app, qt_app, tmp_path
    ):
        window, _controller, _ = qml_app
        viewer = _open_viewer(window, qt_app)
        _invoke(viewer, "toggleFacesEdit")
        qt_app.processEvents()
        overlay = _overlay(window)

        _invoke(overlay, "openEditorFor", 0.1, 0.1, 0.4, 0.4, "", True)
        qt_app.processEvents()
        _invoke(overlay, "commitEditor")
        qt_app.processEvents()

        faces = overlay.property("faces")
        assert len(faces) == 1
        assert faces[0]["name"] == ""


class TestRenameFaceViaOverlay:
    def test_existing_region_is_renamed(self, qml_app, qt_app, tmp_path):
        ini = tmp_path / "kepek" / ".picasa.ini"
        ini.write_text(
            "[a.jpg]\nfaces=rect64(3f845bcb59418507),ffffffffffffffff;\n",
            encoding="utf-8",
        )
        window, _controller, _ = qml_app
        viewer = _open_viewer(window, qt_app)
        _invoke(viewer, "toggleFacesEdit")
        qt_app.processEvents()
        overlay = _overlay(window)
        faces = overlay.property("faces")
        assert len(faces) == 1
        face = faces[0]

        _invoke(
            overlay, "openEditorFor",
            face["left"], face["top"], face["right"], face["bottom"], "", False,
        )
        qt_app.processEvents()
        field = window.findChild(QObject, "faceNameField")
        field.setProperty("text", "Béla")
        _invoke(overlay, "commitEditor")
        qt_app.processEvents()

        assert overlay.property("faces")[0]["name"] == "Béla"
        ini_text = ini.read_text(encoding="utf-8")
        assert "rect64(3f845bcb59418507)" in ini_text   # a régió megmaradt


class TestRemoveFaceViaOverlay:
    def test_region_is_removed(self, qml_app, qt_app, tmp_path):
        ini = tmp_path / "kepek" / ".picasa.ini"
        ini.write_text(
            "[Contacts2]\n8e62b2035b74b477=Kis Éva;;\n"
            "[a.jpg]\nfaces=rect64(3f845bcb59418507),8e62b2035b74b477;\n",
            encoding="utf-8",
        )
        window, _controller, _ = qml_app
        viewer = _open_viewer(window, qt_app)
        _invoke(viewer, "toggleFacesEdit")
        qt_app.processEvents()
        overlay = _overlay(window)
        face = overlay.property("faces")[0]

        _invoke(
            overlay, "removeFace",
            face["left"], face["top"], face["right"], face["bottom"],
        )
        qt_app.processEvents()

        assert overlay.property("faces") == []
        ini_text = ini.read_text(encoding="utf-8")
        assert "faces=" not in ini_text


class TestKnownNamesSuggestions:
    def test_known_names_lists_existing_contacts(self, qml_app, qt_app, tmp_path):
        ini = tmp_path / "kepek" / ".picasa.ini"
        ini.write_text("[Contacts2]\n8e62b2035b74b477=Kis Éva;;\n", encoding="utf-8")
        window, _controller, _ = qml_app
        viewer = _open_viewer(window, qt_app)
        _invoke(viewer, "toggleFacesEdit")
        qt_app.processEvents()
        overlay = _overlay(window)
        assert list(overlay.property("knownNames")) == ["Kis Éva"]
