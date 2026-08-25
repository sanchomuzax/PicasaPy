"""QML-funkcionális tesztek: lebegő „Teljesítmény-monitor" panel (#211).

A panel a controller perf*-tulajdonságaira köt (ImportProgressPanel
mintája, #209); a be/ki kapcsolást a Súgó menü `menuHelpPerfMonitor`
tétele (vagy közvetlenül a controller.togglePerfMonitor()) vezérli.
"""

import time
from pathlib import Path

from PySide6.QtCore import QObject

from picasapy.app import perf_controller


#: #1463: a mintavételi ütem 1 mp (`perf_controller._SAMPLE_INTERVAL_S`),
#: és a `PerfCollector._run` az ELSŐ minta előtt is végigvárja az ütemet.
#: A korábbi 3 mp-es határidő tehát mindössze három ütemnyi tartalékot
#: adott — terhelt, négymagos futón ez kevés volt. A határidő SZÁNDÉKOSAN
#: bőkezű: az őr foga nem az ablak szűkösségén múlik, hanem azon, hogy a
#: minta megérkezik-e egyáltalán. Ha a gyűjtő szál el sem indul, a
#: várakozás akkor is elbukik — csak később.
_MINTA_HATARIDO_S = 60.0


def _var_elso_mintara(controller, qt_app, masodperc: float = _MINTA_HATARIDO_S):
    """Megvárja az első élő mintát a `PerfCollector` háttérszálából.

    Nem fali-óra alapú fogadás: a VALÓDI feltételt (`perfRssMb > 0`)
    figyeli, és amint teljesül, azonnal továbbenged. Az időkorlát csak
    a végtelen várakozást zárja ki."""
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if controller.perfRssMb > 0.0:
            return True
        time.sleep(0.02)
    qt_app.processEvents()
    return controller.perfRssMb > 0.0


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


class TestPerfMonitorPanel:
    def test_hidden_and_disabled_by_default(self, qml_app, qt_app):
        window, controller, _lib, _engine = qml_app
        panel = _child(window, "perfMonitorPanel")
        assert panel.property("visible") is False
        assert controller.perfMonitorEnabled is False

    def test_menu_toggle_shows_and_hides_panel(self, qml_app, qt_app):
        window, controller, _lib, _engine = qml_app
        panel = _child(window, "perfMonitorPanel")
        menu_item = _child(window, "menuHelpPerfMonitor")
        assert menu_item.property("checked") is False

        controller.togglePerfMonitor()
        assert controller.perfMonitorEnabled is True
        assert panel.property("visible") is True
        assert menu_item.property("checked") is True

        controller.togglePerfMonitor()
        assert controller.perfMonitorEnabled is False
        assert panel.property("visible") is False

    def test_close_button_disables_monitor(self, qml_app, qt_app):
        """A panel × gombja a QML-ben a closeRequested jelzést emittálja,
        amit a Main.qml a controller.setPerfMonitorEnabled(false)-ra köt —
        itt közvetlenül a QML-jelzést váltjuk ki (invokeMethod), a valós
        gombkattintást szimulálva."""
        from PySide6.QtCore import QMetaObject

        window, controller, _lib, _engine = qml_app
        controller.setPerfMonitorEnabled(True)
        assert controller.perfMonitorEnabled is True
        panel = _child(window, "perfMonitorPanel")
        QMetaObject.invokeMethod(panel, "closeRequested")
        qt_app.processEvents()
        assert controller.perfMonitorEnabled is False
        assert panel.property("visible") is False

    def test_enabling_starts_background_collector(self, qml_app, qt_app):
        """A tényleges (nem mock-olt) PerfCollector-szál valódi mintát
        küld — a #211 DoD: a monitor élőben mutatja a terhelést."""
        window, controller, _lib, _engine = qml_app
        controller._perf_collector = None  # tiszta induló állapot
        controller.setPerfMonitorEnabled(True)
        try:
            assert _var_elso_mintara(controller, qt_app), (
                "nem érkezett élő minta a PerfCollector háttérszálából"
            )
        finally:
            controller.setPerfMonitorEnabled(False)

    def test_disabling_stops_collector_and_resets_display(self, qml_app, qt_app):
        window, controller, _lib, _engine = qml_app
        controller.setPerfMonitorEnabled(True)
        # #1463: a minta bevárása ITT is állítás. Korábban a 3 mp-es
        # határidő némán lejárhatott, és a kikapcsolás egy már amúgy is
        # nulla kijelzőt „állított vissza" — a teszt hamis zöldet adott,
        # mert nem volt mit nullázni.
        assert _var_elso_mintara(controller, qt_app), (
            "nem érkezett élő minta, tehát a kikapcsolás nem is tudna "
            "nullázni semmit — az alábbi állítások üresek lennének"
        )
        controller.setPerfMonitorEnabled(False)
        assert controller.perfCpuPercent == 0.0
        assert controller.perfRssMb == 0.0
        assert controller._perf_collector is None

    def test_save_diagnostics_writes_jsonl(self, qml_app, qt_app, tmp_path, monkeypatch):
        window, controller, _lib, _engine = qml_app
        monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
        path_str = controller.saveDiagnostics()
        assert path_str
        from pathlib import Path

        path = Path(path_str)
        assert path.exists()
        assert path.parent == tmp_path / "picasapy" / "perf"
        first_line = path.read_text(encoding="utf-8").splitlines()[0]
        assert '"type": "session"' in first_line

    def test_saved_path_click_invokes_open_diagnostics_folder(
        self, qml_app, qt_app, monkeypatch
    ):
        """#217: a mentés-visszajelző zöld útvonal-szöveg kattintható —
        kattintásra a controller.openDiagnosticsFolder()-t hívja a QML
        (TapHandler), a panel `lastSavedPath` property-jével."""
        window, controller, _lib, _engine = qml_app
        panel = _child(window, "perfMonitorPanel")
        panel.setProperty("lastSavedPath", "/tmp/kepzelt/diag.jsonl")

        calls = []
        monkeypatch.setattr(
            perf_controller, "_platform", lambda: "linux"
        )
        monkeypatch.setattr(
            "picasapy.app.perf_controller.reveal_in_file_manager",
            lambda path: calls.append(path),
        )

        from PySide6.QtCore import QMetaObject

        # a valódi kattintást az útvonal-szöveg saját, paraméter nélküli
        # `openSavedPathFolder()` függvényének közvetlen meghívásával
        # szimuláljuk (a panel × gombjának teszt-mintája szerint, ld.
        # test_close_button_disables_monitor) — a beépített
        # TapHandler.tapped() fix (QEventPoint, MouseButton) szignatúrája
        # invokeMethod-dal nem hívható paraméterek nélkül.
        saved_path_text = _child(window, "perfPanelSavedPath")
        QMetaObject.invokeMethod(saved_path_text, "openSavedPathFolder")
        qt_app.processEvents()

        assert calls == [Path("/tmp/kepzelt/diag.jsonl")]

    def test_open_diagnostics_folder_linux_calls_reveal(
        self, qml_app, qt_app, tmp_path, monkeypatch
    ):
        """#217: Linuxon a meglévő #112-es mintát (`reveal_in_file_manager`,
        vagyis `xdg-open` a szülőmappára) használja."""
        window, controller, _lib, _engine = qml_app
        calls = []
        monkeypatch.setattr(
            perf_controller, "_platform", lambda: "linux"
        )
        monkeypatch.setattr(
            "picasapy.app.perf_controller.reveal_in_file_manager",
            lambda path: calls.append(path),
        )
        log_path = tmp_path / "perf" / "diag.jsonl"
        log_path.parent.mkdir()
        log_path.write_text("{}\n", encoding="utf-8")

        controller.openDiagnosticsFolder(str(log_path))

        assert calls == [log_path]

    def test_open_diagnostics_folder_windows_uses_explorer_select(
        self, qml_app, qt_app, tmp_path, monkeypatch
    ):
        """#217: Windowson az Intéző a fájlt kijelölve nyitja meg
        (`explorer /select,<út>`)."""
        window, controller, _lib, _engine = qml_app
        calls = []

        class _CompletedProcess:
            returncode = 1  # az Intéző /select sikeresen is gyakran 1-et ad vissza

        monkeypatch.setattr(
            perf_controller, "_platform", lambda: "win32"
        )
        monkeypatch.setattr(
            "picasapy.app.perf_controller._run",
            lambda args, **kwargs: calls.append(args) or _CompletedProcess(),
        )
        log_path = tmp_path / "perf" / "diag.jsonl"

        controller.openDiagnosticsFolder(str(log_path))

        assert calls == [["explorer", f"/select,{log_path}"]]

    def test_open_diagnostics_folder_reports_human_error(
        self, qml_app, qt_app, tmp_path, monkeypatch
    ):
        """Hiba esetén a felhasználó a globális hibasávon látja az okot."""
        window, controller, _lib, _engine = qml_app
        monkeypatch.setattr(
            perf_controller, "_platform", lambda: "linux"
        )

        def _raise(_path):
            raise OSError("a fájlkezelő megnyitása sikertelen (xdg-open hiányzik?)")

        monkeypatch.setattr(
            "picasapy.app.perf_controller.reveal_in_file_manager", _raise
        )

        controller.openDiagnosticsFolder(str(tmp_path / "diag.jsonl"))
        qt_app.processEvents()

        assert "xdg-open" in _child(window, "errorBannerText").property("text")

    def test_open_diagnostics_folder_empty_path_reports_error(self, qml_app, qt_app):
        """Hiányzó útvonalnál is a már létező hibasáv szólal meg."""
        window, controller, _lib, _engine = qml_app
        controller.openDiagnosticsFolder("")
        qt_app.processEvents()
        assert "Nincs elérhető naplófájl" in _child(window, "errorBannerText").property("text")

    def test_top_activity_reflects_sync_progress(self, qml_app, qt_app):
        window, controller, _lib, _engine = qml_app
        controller.setPerfMonitorEnabled(True)
        try:
            controller.syncProgress.emit("/kepek/2018", 3, 10, 2)
            qt_app.processEvents()
            assert "2018" in controller.perfTopActivity
            assert "/kepek" not in controller.perfTopActivity
        finally:
            controller.setPerfMonitorEnabled(False)
