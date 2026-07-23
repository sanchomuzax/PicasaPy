"""A telepített `picasapy` parancs belépési pontja (__main__.main, #4).

A teszt nem indít valódi Qt-alkalmazást — az `application.run`-t helyettesíti,
így gyors és headless-biztos (nincs szükség QT_QPA_PLATFORM=offscreen-re).
"""

from picasapy.app import __main__ as entrypoint


def test_main_calls_run_with_sys_argv(monkeypatch):
    captured = {}

    def fake_run(argv):
        captured["argv"] = argv
        return 0

    monkeypatch.setattr(entrypoint, "run", fake_run)
    monkeypatch.setattr(
        entrypoint.sys, "argv", ["picasapy", "/mnt/nas/fotok"]
    )

    assert entrypoint.main() == 0
    assert captured["argv"] == ["picasapy", "/mnt/nas/fotok"]


def test_main_returns_runs_exit_code(monkeypatch):
    monkeypatch.setattr(entrypoint, "run", lambda argv: 3)
    monkeypatch.setattr(entrypoint.sys, "argv", ["picasapy"])

    assert entrypoint.main() == 3
