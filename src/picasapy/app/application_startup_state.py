"""Az indulás első lépései: napló, argumentumok, állapot (#5958, #6155, #6367).

Az `application.run()` és az `application.py` méretkorlátja (#5958, #6155)
miatt külön modulban; a `run()` sorrendje változatlan: előbb a napló és a
kapcsolók, aztán (a `run()`-ban) az idővonal, végül az állapot."""

from __future__ import annotations

from types import SimpleNamespace

from .startup_diagnostics import StartupProgressLog, process_age_ms


def _startup_step_read_arguments(argv: list[str], early_startup):
    """A korai napló és a CI-kapcsolók (`--onellenorzes`, `--indulasellenorzes`)."""
    from .application_services import argv_indulasellenorzes, argv_onellenorzes

    progress_log = (
        early_startup.progress_log if early_startup is not None else StartupProgressLog()
    )
    progress_log.mark("Python- és PySide6-modulok betöltése befejeződött")
    # #6344: ami ELŐTTE volt (indító, DLL-ek, víruskereső), az csak így látszik
    age_ms = process_age_ms()
    if age_ms is not None:
        progress_log.mark(f"A folyamat indulása óta eltelt: {age_ms} ms")
    from picasapy import __version__ as _app_version

    progress_log.mark(f"PicasaPy-verzió: {_app_version}")
    onellenorzes, argv = argv_onellenorzes(argv)
    startup_smoke, argv = argv_indulasellenorzes(argv)
    progress_log.mark("Indulási argumentumok beolvasva")
    return SimpleNamespace(
        progress_log=progress_log,
        onellenorzes=onellenorzes,
        startup_smoke=startup_smoke,
        argv=argv,
        early_startup=early_startup,
    )


def _startup_step_prepare_state(elso, argv: list[str], timeline, launch_arguments, library_argv):
    """Az indulás állapota a megnyitandó fájlokkal és könyvtárakkal."""
    early_startup = elso.early_startup
    return SimpleNamespace(
        argv=argv,
        progress_log=elso.progress_log,
        timeline=timeline,
        onellenorzes=elso.onellenorzes,
        startup_smoke=elso.startup_smoke,
        launch_arguments=launch_arguments,
        library_argv=library_argv,
        early_qt_app=early_startup is not None,
        qml_splash_enabled=(
            early_startup.qml_splash_enabled if early_startup is not None else True
        ),
    )


def _zard_be_az_induloablakot(early_startup) -> None:
    """A korai indulóablak bezárása, ha az indulás idő előtt véget ér (#6367)."""
    if early_startup is None:
        return
    hang_traceback = getattr(early_startup, "hang_traceback", None)
    if hang_traceback is not None:
        hang_traceback.cancel()
    if early_startup.splash is not None:
        early_startup.splash.close()
