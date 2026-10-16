"""QML-funkcionális tesztek: arc-téglalap SZERKESZTŐ mód a nézőben (#26,
2. kör) — rajzolás/átnevezés/törlés a `FacesOverlay`-en, `facesHelper`-en
át útvonalanként sorosan, az észlelt változásokat újrajátszva az ini-be írva.
A sikeres ujjlenyomat-ellenőrzés utáni külső írás nincs kizárva. A teljes appot építjük fel (`qml_app`
fixture) — a delegate-eken belüli tartalom (MEMORY 2026-07-31:
visible-öröklés csapda / dinamikus Repeater-elemek `findChild`-dal nem
érhetők el) helyett az overlay saját (nem-delegate) API-ját hívjuk:
`openEditorFor`/`commitEditor`/`removeFace` — ugyanúgy, ahogy a
`test_editor.py` a `CropOverlay`/`EditorPanel` függvényeit."""

import time

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QRectF, Qt


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


def _make_visible(overlay):
    """A néző-overlay a teszt-ablakban zárt néző alatt él, tehát rejtett —
    a QML-ben a `visible` a SZÜLŐTŐL öröklődik, így a gyerekei is annak
    látszanak. A megjelenés-vizsgálathoz kézzel láthatóvá tesszük."""
    overlay.setProperty("width", 400.0)
    overlay.setProperty("height", 300.0)
    overlay.setProperty("visible", True)


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

    def test_new_region_without_name_does_not_change_ini(
        self, qml_app, qt_app, tmp_path
    ):
        ini = tmp_path / "kepek" / ".picasa.ini"
        ini.write_bytes(b"[a.jpg]\r\nstar=yes\r\n; megorzendo\r\n")
        before = ini.read_bytes()
        window, _controller, _ = qml_app
        viewer = _open_viewer(window, qt_app)
        _invoke(viewer, "toggleFacesEdit")
        qt_app.processEvents()
        overlay = _overlay(window)

        overlay.setProperty("draftRect", QRectF(40, 30, 80, 70))
        _invoke(overlay, "openDraftEditor")
        qt_app.processEvents()
        draft_label = window.findChild(QObject, "faceDraftAddName")
        assert draft_label.property("visible") is True
        field = window.findChild(QObject, "faceNameField")
        field.setProperty("text", "   ")
        _invoke(overlay, "commitEditor")
        qt_app.processEvents()

        assert overlay.property("faces") == []
        assert ini.read_bytes() == before
        assert window.findChild(QObject, "faceDraftRect").property("visible") is False
        assert draft_label.property("visible") is False
        editor = window.findChild(QObject, "faceNameEditor")
        assert editor.property("visible") is False


class TestRenameFaceViaOverlay:
    def test_existing_region_is_renamed(self, qml_app, qt_app, tmp_path):
        ini = tmp_path / "kepek" / ".picasa.ini"
        ini.write_text(
            "[Contacts2]\n8e62b2035b74b477=Anna;;\n"
            "[a.jpg]\nfaces=rect64(3f845bcb59418507),8e62b2035b74b477;\n",
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
            face["left"], face["top"], face["right"], face["bottom"],
            face["name"], False,
        )
        qt_app.processEvents()
        field = window.findChild(QObject, "faceNameField")
        field.setProperty("text", "Béla")
        _invoke(overlay, "commitEditor")
        qt_app.processEvents()

        assert overlay.property("faces")[0]["name"] == "Béla"
        ini_text = ini.read_text(encoding="utf-8")
        assert "rect64(3f845bcb59418507)" in ini_text   # a régió megmaradt

    def test_clearing_existing_name_removes_ini_entry(
        self, qml_app, qt_app, tmp_path
    ):
        ini = tmp_path / "kepek" / ".picasa.ini"
        ini.write_text(
            "[Contacts2]\n8e62b2035b74b477=Anna;;\n"
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
            overlay, "openEditorFor",
            face["left"], face["top"], face["right"], face["bottom"],
            face["name"], False,
        )
        qt_app.processEvents()
        window.findChild(QObject, "faceNameField").setProperty("text", "  ")
        _invoke(overlay, "commitEditor")
        qt_app.processEvents()

        assert overlay.property("faces") == []
        assert "faces=" not in ini.read_text(encoding="utf-8")


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


class TestManualAddWorkflow:
    """#26: az eredeti KÉTLÉPÉSES volt (`manual_add::instructions`):
    1) húzd meg a négyszöget és igazítsd az oldalait,
    2) kattints a „Név hozzáadása" feliratra a négyszög alatt.

    A LÁTHATÓSÁGOT itt nem mérjük: a QML-ben a `visible` a szülőtől
    öröklődik, a néző pedig ezekben a tesztekben zárva van — a viselkedést
    ellenőrizzük, ami amúgy is a lényeg.
    """

    @pytest.mark.parametrize("height_delta", [-5, 0, 5])
    def test_the_instructions_exist_in_the_people_panel(
        self, qml_app, qt_app, height_delta
    ):
        window, _controller, _engine = qml_app
        window.resize(window.width(), window.height() + height_delta)
        viewer = _open_viewer(window, qt_app)
        _invoke(viewer, "beginManualFaceAdd")

        hint = None
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            qt_app.processEvents()
            panel = window.findChild(QObject, "viewerPeoplePanel")
            if panel is not None:
                hint = panel.findChild(QObject, "peoplePanelManualInstructions")
                if hint is not None and hint.property("visible"):
                    break
            time.sleep(0.01)

        assert hint is not None
        assert hint.property("visible")
        assert "Add a name" in hint.property("text")

    def test_the_draft_survives_the_drag_and_gets_handles(self, qml_app, qt_app):
        """A húzás UTÁN a téglalap megmarad és igazítható — nem ugrik fel
        azonnal a névkérő."""
        window, _controller, _engine = qml_app
        overlay = _overlay(window)
        overlay.setProperty("width", 400.0)
        overlay.setProperty("height", 300.0)
        overlay.setProperty("editMode", True)

        overlay.setProperty("draftRect", QRectF(10.0, 10.0, 80.0, 80.0))
        qt_app.processEvents()

        assert overlay.property("hasDraft") is True
        assert overlay.findChild(QObject, "faceDraftAddName") is not None
        # a fogantyúk Repeater-delegátumok — findChild-dal nem érhetők el
        # (MEMORY 2026-07-31); a viselkedésüket a `resizeDraft` tesztje fedi
        # a névkérő NEM nyílt ki magától
        assert overlay.property("pendingIsNew") is False

    def test_a_tiny_draft_is_not_a_face(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        overlay = _overlay(window)
        overlay.setProperty("editMode", True)

        overlay.setProperty("draftRect", QRectF(10.0, 10.0, 2.0, 2.0))
        qt_app.processEvents()

        assert overlay.property("hasDraft") is False

    def test_the_add_name_step_opens_the_editor(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        overlay = _overlay(window)
        overlay.setProperty("width", 400.0)
        overlay.setProperty("height", 300.0)
        overlay.setProperty("editMode", True)
        overlay.setProperty("draftRect", QRectF(40.0, 30.0, 80.0, 60.0))
        qt_app.processEvents()

        QMetaObject.invokeMethod(
            overlay, "openDraftEditor", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        assert overlay.property("pendingIsNew") is True
        # a régió RELATÍV koordinátákká vált (a rect64-íráshoz)
        pending = overlay.property("pendingRect")
        assert abs(pending.x() - 0.1) < 1e-6
        assert abs(pending.y() - 0.1) < 1e-6

    def test_resizing_a_handle_changes_the_draft(self, qml_app, qt_app):
        """Az eredeti utasítása: „oldalainak mozgatásával pontosíthatja az
        alakját"."""
        window, _controller, _engine = qml_app
        overlay = _overlay(window)
        overlay.setProperty("width", 400.0)
        overlay.setProperty("height", 300.0)
        overlay.setProperty("draftRect", QRectF(40.0, 30.0, 80.0, 60.0))

        _invoke(overlay, "resizeDraft", "e", 200.0, 0.0)
        qt_app.processEvents()

        draft = overlay.property("draftRect")
        assert abs(draft.width() - 160.0) < 1e-6
        assert abs(draft.x() - 40.0) < 1e-6
