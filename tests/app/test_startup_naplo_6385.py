"""#6385: az indulási napló minden futáskor elkészül, a veremkiírás leállítható."""

from __future__ import annotations


def test_az_indulasi_naplo_letrejon_es_az_elozo_futast_megorzi(tmp_path):
    from picasapy.app.startup_diagnostics import StartupRunLog

    naplo = StartupRunLog(tmp_path)
    naplo.write("Első indulás\n")
    naplo.close()

    elozo = tmp_path / "indulas-elozo.txt"
    utolso = tmp_path / "indulas-utolso.txt"
    assert utolso.read_text(encoding="utf-8") == "Első indulás\n"
    assert not elozo.exists()

    naplo = StartupRunLog(tmp_path)
    assert elozo.read_text(encoding="utf-8") == "Első indulás\n"
    naplo.write("Második indulás\n")
    naplo.close()

    assert utolso.read_text(encoding="utf-8") == "Második indulás\n"
    assert elozo.read_text(encoding="utf-8") == "Első indulás\n"


def test_az_idovonal_szakaszai_mar_az_indulas_alatt_beirodnak(tmp_path):
    from picasapy.app.application_services import _indulasi_idovonal
    from picasapy.app.startup_diagnostics import StartupRunLog

    naplo = StartupRunLog(tmp_path)
    timeline, _argv = _indulasi_idovonal(["picasapy"], run_log=naplo)
    timeline.mark("QML betöltése")

    tartalom = (tmp_path / "indulas-utolso.txt").read_text(encoding="utf-8")
    assert "QML betöltése" in tartalom
    assert "ms" in tartalom
    naplo.close()


def test_a_kesleltetett_veremkiiras_15_es_30_masodpercnel_is_kerheto():
    from picasapy.app.startup_diagnostics import StartupHangTraceback

    calls = []

    class Timer:
        def __init__(self, seconds, callback):
            self.seconds = seconds
            self.callback = callback
            self.cancelled = False

        def start(self):
            pass

        def cancel(self):
            self.cancelled = True

        def fire(self):
            self.callback()

    timers = []

    def timer_factory(seconds, callback):
        timer = Timer(seconds, callback)
        timers.append(timer)
        return timer

    diag = StartupHangTraceback(
        object(),
        dump_later=lambda seconds, **kwargs: calls.append((seconds, kwargs)),
        cancel_dump=lambda: None,
        timer_factory=timer_factory,
    )

    assert calls[0][0] == 15
    assert calls[0][1]["repeat"] is False
    timers[0].fire()
    assert calls[1][0] == 15
    assert calls[1][1]["repeat"] is False
    diag.cancel()


def test_a_fokocka_elott_a_veremkiiras_kikapcsolhato():
    from picasapy.app.startup_diagnostics import StartupHangTraceback

    calls = []
    timers = []

    class Timer:
        def __init__(self, seconds, callback):
            self.callback = callback
            self.cancelled = False
            timers.append(self)

        def start(self):
            pass

        def cancel(self):
            self.cancelled = True

    diag = StartupHangTraceback(
        object(),
        dump_later=lambda seconds, **kwargs: calls.append(seconds),
        cancel_dump=lambda: calls.append("cancel"),
        timer_factory=Timer,
    )

    diag.cancel()
    assert calls == [15, "cancel"]
    assert timers[0].cancelled


def test_a_korai_indulas_megnyitja_a_rotalo_naplot(tmp_path, monkeypatch, qt_app):
    from picasapy.app import platform_storage, startup_splash

    monkeypatch.setattr(
        platform_storage,
        "default_storage_paths",
        lambda _platform: type("Storage", (), {"data": tmp_path})(),
    )
    early = startup_splash.start_early_startup(["picasapy", "--onellenorzes"])
    try:
        assert (tmp_path / "indulas-utolso.txt").exists()
        tartalom = (tmp_path / "indulas-utolso.txt").read_text(encoding="utf-8")
        assert "Korai indulás elkezdődött" in tartalom
        assert "Tároló típusa:" in tartalom
        assert str(tmp_path) not in tartalom
    finally:
        early.hang_traceback.cancel()
        early.run_log.close()
        startup_splash.take_early_startup()
