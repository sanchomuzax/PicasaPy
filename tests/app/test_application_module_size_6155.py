"""Az alkalmazásindító részei maradjanak a Python-modulplafon alatt (#6155)."""

from pathlib import Path
from contextlib import nullcontext
from types import SimpleNamespace


_APP = Path(__file__).resolve().parents[2] / "src" / "picasapy" / "app"


def test_application_modules_stay_under_the_size_limit():
    modules = sorted(_APP.glob("application*.py"))
    assert modules, "nem található application modul"

    oversized = {
        module.name: len(module.read_text(encoding="utf-8").splitlines())
        for module in modules
        if len(module.read_text(encoding="utf-8").splitlines()) > 700
    }
    assert not oversized, f"az application modulok túllépik a 700 soros plafont: {oversized}"


def test_qml_helper_reads_legacy_app_dir_at_call_time(monkeypatch, tmp_path):
    """A régi monkeypatch-célpontot a segédmodul futás közben olvassa (#6155)."""
    import picasapy.app.application as application
    from picasapy.app import application_startup_qml

    class Engine:
        loaded = None

        def load(self, path):
            self.loaded = path

        def rootObjects(self):
            return [object()]

    class ProgressLog:
        def mark(self, _message):
            pass

    class ScreenCaptureController:
        def shutdown(self):
            raise AssertionError("a sikeres betöltés nem állíthatja le a vezérlőt")

    monkeypatch.setattr(application, "_APP_DIR", tmp_path)
    engine = Engine()
    state = SimpleNamespace(
        engine=engine,
        progress_log=ProgressLog(),
        screen_capture_controller=ScreenCaptureController(),
        timeline=SimpleNamespace(phase=lambda _name: nullcontext()),
    )

    assert application_startup_qml._startup_step_load_qml(state) is None
    assert Path(engine.loaded) == tmp_path / "qml" / "Main.qml"
