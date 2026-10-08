"""#4687: naplózott indulási szakaszok és támogatott Qt-verzió jelzése."""

from datetime import datetime, timezone
from pathlib import Path


def test_pyside6_verziotartomany_egyezik_a_fuggosegkorlattal():
    from picasapy.app.startup_diagnostics import pyside6_is_supported

    assert pyside6_is_supported("6.11.3")
    assert not pyside6_is_supported("6.12.0")
    assert not pyside6_is_supported("7.0.0")


def test_a_verziojelentes_tartalmazza_a_pyside_qt_es_a_javitasi_utmutatast():
    from picasapy.app.startup_diagnostics import runtime_version_messages

    messages = runtime_version_messages("6.12.0", "6.12.0")

    assert any("PySide6 6.12.0" in message and "Qt 6.12.0" in message for message in messages)
    assert any("PySide6<6.12" in message for message in messages)


def test_az_indulasi_fustproba_kapcsoloja_nem_lesz_figyelt_konyvtar():
    from picasapy.app.application import argv_indulasellenorzes

    assert argv_indulasellenorzes(
        ["picasapy", "--indulasellenorzes", r"C:\Kepek"]
    ) == (True, ["picasapy", r"C:\Kepek"])


def test_a_windows_csomagolt_telepites_utan_is_valos_indulas_van():
    repo = Path(__file__).resolve().parents[2]
    workflow = (repo / ".github/workflows/package.yml").read_text(encoding="utf-8")

    assert "Telepítő telepítése és valós indulási füstpróba" in workflow
    assert "PICASAPY_INSTALLED_EXE" in workflow
    assert 'cases = ("clean", "existing_faces")' in workflow
    assert '("source", [sys.executable' in workflow
    assert '("packaged", [str(executable)])' in workflow
    assert '"--indulasellenorzes"' in workflow
    assert "A főablak a splash után megjelent" in workflow


def test_a_fazisnaplo_a_hibanaplo_elerhetove_valasa_elott_is_megorizi_az_idot(tmp_path):
    from picasapy.app.startup_diagnostics import StartupProgressLog

    times = iter(
        (
            datetime(2026, 10, 8, 12, 0, 0, tzinfo=timezone.utc),
            datetime(2026, 10, 8, 12, 0, 1, tzinfo=timezone.utc),
        )
    )
    progress = StartupProgressLog(now=lambda: next(times))
    progress.mark("Splash létrehozása")
    target = tmp_path / "errorlog.txt"
    progress.install(target)
    progress.mark("QML betöltve")

    content = target.read_text(encoding="utf-8")
    assert "2026-10-08T12:00:00.000+00:00 INFO picasapy.startup: Splash létrehozása" in content
    assert "2026-10-08T12:00:01.000+00:00 INFO picasapy.startup: QML betöltve" in content


def test_konzol_nelkul_is_tovabbindul_a_fagyasztott_alkalmazas(monkeypatch):
    import sys

    from picasapy.app.startup_diagnostics import write_console

    monkeypatch.setattr(sys, "stdout", None)
    monkeypatch.setattr(sys, "stderr", None)

    write_console("runtime version")
    write_console("unsupported runtime", error=True)


def test_a_korai_hibanaplo_azonnal_ir_es_adatgyoker_valtaskor_atviszi_a_szakaszokat(
    tmp_path,
):
    from picasapy.app.startup_diagnostics import StartupProgressLog

    progress = StartupProgressLog()
    progress.mark("PySide6 és Qt verziója")
    early_log = tmp_path / "alap-adatok" / "errorlog.txt"
    progress.install(early_log)

    assert "PySide6 és Qt verziója" in early_log.read_text(encoding="utf-8")

    final_log = tmp_path / "athelyezett-adatok" / "errorlog.txt"
    progress.install(final_log)
    assert "PySide6 és Qt verziója" in final_log.read_text(encoding="utf-8")
