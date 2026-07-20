"""QML-funkcionális tesztek: lebegő „Importálás" folyamat-panel (#209).

A panel a controller import*-tulajdonságaira köt; a haladást a
syncProgress jelzés hajtja (worker-szálból queued — itt a tesztben azonos
szálról direktben fut le, a kötések szinkron frissülnek).
"""

from PySide6.QtCore import QObject


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


class TestImportPanel:
    def test_hidden_by_default(self, qml_app, qt_app):
        window, controller, _lib, _engine = qml_app
        panel = _child(window, "importProgressPanel")
        assert panel.property("visible") is False

    def test_appears_on_progress_with_new_photos(self, qml_app, qt_app):
        # #216 óta a jelzések csak FIGYELT gyökér alatti mappára hatnak —
        # a tesztek ezért a valódi könyvtár (lib) útvonalait használják
        window, controller, lib, _engine = qml_app
        panel = _child(window, "importProgressPanel")
        # csendes (semmi újat nem hozó) rescan-haladás: a panel NEM ugrik fel
        controller.syncProgress.emit(str(lib / "regi"), 1, 10, 0)
        assert panel.property("visible") is False
        # új fotókat hozó haladás: a panel megjelenik, az adatok kötve
        controller.syncProgress.emit(str(lib / "nyaralas"), 3, 10, 42)
        assert panel.property("visible") is True
        assert _child(window, "importPanelFolder").property("text") == "nyaralas"
        counts = _child(window, "importPanelCounts").property("text")
        assert "3" in counts and "10" in counts and "42" in counts
        # a haladás-sáv kitöltése a kész/összes arányt követi
        fill = _child(window, "importPanelBarFill")
        assert fill.property("width") > 0
        # lezárás: syncFinished → a panel eltűnik, az állapot nulláz
        controller.syncFinished.emit()
        qt_app.processEvents()
        assert panel.property("visible") is False
        assert controller.importNewCount == 0

    def test_forced_visible_when_root_added(self, qml_app, qt_app):
        window, controller, lib, _engine = qml_app
        panel = _child(window, "importProgressPanel")
        # új gyökér importja (forced): új fotó nélkül is látszik a haladás
        controller._import_forced = True
        controller.syncProgress.emit(str(lib / "a"), 1, 500, 0)
        assert panel.property("visible") is True
        controller.syncFinished.emit()
        qt_app.processEvents()
        assert panel.property("visible") is False

    def test_manual_close_hides_until_next_scan(self, qml_app, qt_app):
        window, controller, lib, _engine = qml_app
        panel = _child(window, "importProgressPanel")
        controller.syncProgress.emit(str(lib / "b"), 2, 5, 7)
        assert panel.property("visible") is True
        # kézi bezárás: a panel eltűnik, de a futó szkennelés haladása
        # nem hozza vissza
        controller.dismissImportPanel()
        assert panel.property("visible") is False
        controller.syncProgress.emit(str(lib / "c"), 3, 5, 9)
        assert panel.property("visible") is False
        # a szkennelés vége nullázza a bezárt állapotot: a KÖVETKEZŐ
        # érdemi szkennelés újra megjelenítheti
        controller.syncFinished.emit()
        qt_app.processEvents()
        controller.syncProgress.emit(str(lib / "d"), 1, 5, 3)
        assert panel.property("visible") is True
        controller.syncFinished.emit()
        qt_app.processEvents()

    def test_real_scan_of_new_root_reports_progress(
        self, qml_app, qt_app, tmp_path
    ):
        """Valódi (háttérszálas) import: új gyökér hozzáadása után érkezik
        haladás-jelzés, és a végén a panel eltűnik."""
        from PySide6.QtCore import QEventLoop, QTimer

        from support.jpeg_factory import make_jpeg

        window, controller, _lib, _engine = qml_app
        new_root = tmp_path / "uj-gyoker"
        (new_root / "alma").mkdir(parents=True)
        make_jpeg(new_root / "alma" / "uj.jpg", size=(64, 64))

        progress_calls = []
        controller.syncProgress.connect(
            lambda *args: progress_calls.append(args)
        )
        loop = QEventLoop()
        controller.syncFinished.connect(loop.quit)
        controller.addWatchedFolder(str(new_root))
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
        qt_app.processEvents()
        assert progress_calls, "nem érkezett haladás-jelzés"
        folder, done, total, new_photos = progress_calls[-1]
        assert folder.endswith("alma")
        assert done == total == 1
        assert new_photos == 1
        panel = _child(window, "importProgressPanel")
        assert panel.property("visible") is False
