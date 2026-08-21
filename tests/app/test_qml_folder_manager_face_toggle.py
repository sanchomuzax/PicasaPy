"""QML-funkcionális teszt: a Mappakezelő NEGYEDIK, a Scan Always/Once/
Remove hármastól FÜGGETLEN kapcsolója — az arcfelismerés be/ki (#449),
`FolderStatePanel.qml`. Arcfelismerés-motor MÉG NINCS a projektben: a
kapcsoló ma csak a `FRExcludeFolders.txt`-be írt SZÁNDÉKOT tükrözi — a
megerősítő dialógus megnyílását és a controller-hívást ellenőrizzük,
valódi ideiglenes könyvtárfán, mock nélkül."""

from PySide6.QtCore import QMetaObject, QObject, Qt


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _click(obj):
    QMetaObject.invokeMethod(obj, "clicked", Qt.ConnectionType.DirectConnection)


def _toggle_face_detection(window):
    """A checkbox kattintás-logikáját hívja meg közvetlenül (`toggle()`) —
    a MouseArea `clicked(mouse)` szignálja kötelező paramétert visz, amit
    a QMetaObject.invokeMethod nem tud üresen megadni."""
    QMetaObject.invokeMethod(
        _child(window, "faceDetectionToggle"),
        "toggle",
        Qt.ConnectionType.DirectConnection,
    )


class TestFaceDetectionToggle:
    def test_enabled_by_default_for_watched_folder(self, qml_app, qt_app):
        window, controller, lib, _engine = qml_app
        dialog = _child(window, "folderManagerDialog")
        dialog.setProperty("selectedPath", str(lib))
        qt_app.processEvents()

        assert controller.faceDetectionEnabledFor(str(lib)) is True
        toggle = _child(window, "faceDetectionToggle")
        assert toggle.property("enabledForSelection") is True

    def test_disabling_asks_for_confirmation_only_at_ok(self, qml_app, qt_app):
        window, controller, lib, _engine = qml_app
        dialog = _child(window, "folderManagerDialog")
        dialog.setProperty("selectedPath", str(lib))
        qt_app.processEvents()

        _toggle_face_detection(window)
        qt_app.processEvents()

        confirm_dialog = _child(window, "faceDetectionConfirmDialog")
        assert confirm_dialog.property("visible") is False
        assert controller.faceDetectionEnabledFor(str(lib)) is True

        _click(_child(window, "folderManagerOkButton"))
        qt_app.processEvents()

        assert confirm_dialog.property("visible") is True
        # a KIKAPCSOLÁS még nem történt meg — csak megerősítés után
        assert controller.faceDetectionEnabledFor(str(lib)) is True

        message = _child(window, "faceDetectionConfirmMessageLabel")
        assert message.property("text") == (
            "Are you sure you want to remove all faces and name tags "
            "from excluded folders?"
        )

    def test_confirming_disables_face_detection_only(self, qml_app, qt_app):
        """A kikapcsolás a három scan-állapottól FÜGGETLEN: a mappa
        MARAD figyelt (watchedFolders), csak az arcfelismerésből esik ki."""
        window, controller, lib, _engine = qml_app
        dialog = _child(window, "folderManagerDialog")
        dialog.setProperty("selectedPath", str(lib))
        qt_app.processEvents()

        _toggle_face_detection(window)
        qt_app.processEvents()
        _click(_child(window, "folderManagerOkButton"))
        qt_app.processEvents()
        _click(_child(window, "faceDetectionConfirmYesButton"))
        qt_app.processEvents()

        assert controller.faceDetectionEnabledFor(str(lib)) is False
        assert str(lib) in controller.watchedFolders
        assert dialog.property("selectedState") == "always"

        toggle = _child(window, "faceDetectionToggle")
        assert toggle.property("enabledForSelection") is False

    def test_canceling_confirmation_keeps_face_detection_enabled(
        self, qml_app, qt_app
    ):
        window, controller, lib, _engine = qml_app
        dialog = _child(window, "folderManagerDialog")
        dialog.setProperty("selectedPath", str(lib))
        qt_app.processEvents()

        _toggle_face_detection(window)
        qt_app.processEvents()
        _click(_child(window, "folderManagerOkButton"))
        qt_app.processEvents()
        _click(_child(window, "faceDetectionConfirmNoButton"))
        qt_app.processEvents()

        assert controller.faceDetectionEnabledFor(str(lib)) is True

    def test_re_enabling_needs_no_confirmation(self, qml_app, qt_app):
        window, controller, lib, _engine = qml_app
        dialog = _child(window, "folderManagerDialog")
        dialog.setProperty("selectedPath", str(lib))
        qt_app.processEvents()
        controller.setFaceDetectionEnabled(str(lib), False)
        qt_app.processEvents()

        _toggle_face_detection(window)
        qt_app.processEvents()

        assert controller.faceDetectionEnabledFor(str(lib)) is False
        _click(_child(window, "folderManagerOkButton"))
        qt_app.processEvents()
        assert controller.faceDetectionEnabledFor(str(lib)) is True
        confirm_dialog = _child(window, "faceDetectionConfirmDialog")
        assert confirm_dialog.property("visible") is False


class TestFaceToggleLabelAndEnablement:
    """#543: a `stringres` szerint a kapcsoló FELIRATA is vált
    (`CFolderMgrDialog::hasfr` / `::nofr`), és „Remove from Picasa"
    állapotú mappán a kapcsoló szürke (nincs mihez arcadatot rendelni)."""

    def test_a_felirat_valt_a_kizartsaggal(self, qml_app, qt_app):
        window, controller, lib, _engine = qml_app
        dialog = _child(window, "folderManagerDialog")
        dialog.setProperty("selectedPath", str(lib))
        qt_app.processEvents()

        label = _child(window, "faceDetectionToggleLabel")
        assert label is not None
        assert "On" in label.property("text")

        controller.setFaceDetectionEnabled(str(lib), False)
        qt_app.processEvents()
        assert "Off" in label.property("text")

    def test_remove_allapotu_mappan_a_kapcsolo_szurke(self, qml_app, qt_app, tmp_path):
        window, _controller, _lib, _engine = qml_app
        dialog = _child(window, "folderManagerDialog")
        unwatched = tmp_path / "nem-figyelt"
        unwatched.mkdir()
        dialog.setProperty("selectedPath", str(unwatched))
        qt_app.processEvents()

        toggle = _child(window, "faceDetectionToggle")
        assert toggle is not None
        assert toggle.property("enabled") is False

    def test_kizart_szulo_gyereken_a_kapcsolo_nem_kattinthato(
        self, qml_app, qt_app
    ):
        window, controller, lib, _engine = qml_app
        child = lib / "gyerek"
        child.mkdir()
        controller.addWatchedFolder(str(child))
        controller.setFaceDetectionEnabled(str(lib), False)
        dialog = _child(window, "folderManagerDialog")
        dialog.setProperty("selectedPath", str(child))
        qt_app.processEvents()

        toggle = _child(window, "faceDetectionToggle")
        assert toggle.property("enabled") is False
