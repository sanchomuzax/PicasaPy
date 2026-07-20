"""QML-funkcionális tesztek: lebegő „Teljesítmény-monitor" panel (#211).

A panel a controller perf*-tulajdonságaira köt (ImportProgressPanel
mintája, #209); a be/ki kapcsolást a Súgó menü `menuHelpPerfMonitor`
tétele (vagy közvetlenül a controller.togglePerfMonitor()) vezérli.
"""

import time

from PySide6.QtCore import QObject


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
            deadline = time.monotonic() + 3.0
            while (
                controller.perfCpuPercent == 0.0 and controller.perfRssMb == 0.0
            ) and time.monotonic() < deadline:
                qt_app.processEvents()
                time.sleep(0.05)
            assert controller.perfRssMb > 0.0, "nem érkezett élő minta"
        finally:
            controller.setPerfMonitorEnabled(False)

    def test_disabling_stops_collector_and_resets_display(self, qml_app, qt_app):
        window, controller, _lib, _engine = qml_app
        controller.setPerfMonitorEnabled(True)
        deadline = time.monotonic() + 3.0
        while controller.perfRssMb == 0.0 and time.monotonic() < deadline:
            qt_app.processEvents()
            time.sleep(0.05)
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
