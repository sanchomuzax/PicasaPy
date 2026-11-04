"""A QML gyorsítótár előállítása első indítás előtt (#6374)."""

from __future__ import annotations

import os
from hashlib import sha1
import re
import subprocess
import sys
import types
from pathlib import Path

import pytest


def _profilhoz_kornyezet(env: dict[str, str], profil: Path) -> None:
    """A Qt cache/config útvonalait a tesztprofil alá tereli platform szerint."""
    if os.name == "nt":
        ideiglenes = profil / "Temp"
        ideiglenes.mkdir(parents=True, exist_ok=True)
        env.update(
            {
                "USERPROFILE": str(profil),
                "APPDATA": str(profil / "AppData" / "Roaming"),
                "LOCALAPPDATA": str(profil / "AppData" / "Local"),
                "TEMP": str(ideiglenes),
                "TMP": str(ideiglenes),
            }
        )
    else:
        env.update(
            {
                "XDG_CACHE_HOME": str(profil / "cache"),
                "XDG_CONFIG_HOME": str(profil / "config"),
                "XDG_DATA_HOME": str(profil / "data"),
            }
        )


def test_a_qml_kapcsolo_a_korai_indulas_elott_ter_vissza(monkeypatch):
    from picasapy.app import __main__ as belepo

    meghivasok = []
    hamis_modul = types.ModuleType("picasapy.app.qml_precompile")
    hamis_modul.main = lambda: meghivasok.append("forditas") or 17
    monkeypatch.setitem(sys.modules, "picasapy.app.qml_precompile", hamis_modul)
    monkeypatch.setattr(sys, "argv", ["picasapy", "--qml-elofordit"])
    monkeypatch.setattr(
        belepo,
        "start_early_startup",
        lambda _argv: pytest.fail("az előfordítás ne indítsa el a normál indulást"),
    )

    assert belepo.main() == 17
    assert meghivasok == ["forditas"]


def test_a_qml_eloforditas_izolalt_profilban_cachet_ir_settings_nelkul(tmp_path):
    repo = Path(__file__).resolve().parents[2]
    profil = tmp_path / "profil"
    env = os.environ.copy()
    env.update(
        {
            "PYTHONPATH": str(repo / "src"),
            "QT_QPA_PLATFORM": "offscreen",
            "QT_QUICK_BACKEND": "software",
            "PICASAPY_LANG": "en",
        }
    )
    _profilhoz_kornyezet(env, profil)
    for variable in (
        "QML_DISK_CACHE_PATH",
        "QML_DISABLE_DISK_CACHE",
        "QML_FORCE_DISK_CACHE",
        "QML_DISK_CACHE",
    ):
        env.pop(variable, None)

    result = subprocess.run(
        [sys.executable, "-m", "picasapy.app", "--qml-elofordit"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert re.fullmatch(r"QML-előfordítás: \d+ fájl, \d+ hibás, [\d.]+ s\s*", result.stdout)
    assert "Traceback" not in result.stderr, result.stderr
    assert len(list(profil.rglob("*.qmlc"))) > 0
    assert not list(profil.rglob("PicasaPy.conf"))
    assert not list(profil.rglob("indulas-*.txt"))


def test_a_repo_indito_is_csak_eloforditja_a_qml_t(tmp_path):
    """A repó gyökerében lévő `picasapy` indító közvetlenül a `run`-t hívja.

    A Package-mérés `@python,picasapy` futtatója így indít; a kapcsoló kezelése
    nélkül a teljes program indult el, és a mérés 180 s után időtúllépéssel bukott."""
    repo = Path(__file__).resolve().parents[2]
    profil = tmp_path / "profil"
    env = os.environ.copy()
    env.update(
        {
            "QT_QPA_PLATFORM": "offscreen",
            "QT_QUICK_BACKEND": "software",
            "PICASAPY_LANG": "en",
        }
    )
    _profilhoz_kornyezet(env, profil)
    for variable in (
        "QML_DISK_CACHE_PATH",
        "QML_DISABLE_DISK_CACHE",
        "QML_FORCE_DISK_CACHE",
        "QML_DISK_CACHE",
    ):
        env.pop(variable, None)
    result = subprocess.run(
        [sys.executable, str(repo / "picasapy"), "--qml-elofordit"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "QML-előfordítás:" in result.stdout
    assert not list(profil.rglob("indulas-*.txt"))


def test_a_valodi_app_motor_nem_irja_ujra_az_eloreallitott_qml_cachet(tmp_path):
    """A teljes app QML-betöltése az előfordítás cache-ét használja (#6374)."""
    repo = Path(__file__).resolve().parents[2]
    profile = tmp_path / "profile"
    library = tmp_path / "library"
    profile.mkdir()
    library.mkdir()
    env = os.environ.copy()
    env.update(
        {
            "PYTHONPATH": str(repo / "src"),
            "QT_QPA_PLATFORM": "offscreen",
            "QT_QUICK_BACKEND": "software",
            "PICASAPY_LANG": "en",
        }
    )
    for variable in (
        "QML_DISK_CACHE_PATH",
        "QML_DISABLE_DISK_CACHE",
        "QML_FORCE_DISK_CACHE",
        "QML_DISK_CACHE",
    ):
        env.pop(variable, None)
    _profilhoz_kornyezet(env, profile)

    eloforditas = subprocess.run(
        [sys.executable, "-m", "picasapy.app", "--qml-elofordit"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        check=False,
    )
    assert eloforditas.returncode == 0, eloforditas.stdout + eloforditas.stderr

    def qml_cache_allapot():
        return {
            str(path.relative_to(profile)): (path.stat().st_mtime_ns, path.stat().st_size)
            for path in profile.rglob("*.qmlc")
        } | {
            str(path.relative_to(profile)): (path.stat().st_mtime_ns, path.stat().st_size)
            for path in profile.rglob("*.jsc")
        }

    elotte = qml_cache_allapot()
    assert elotte, "az előfordítás nem készített QML-cache-t"
    main_cache = sha1(
        (repo / "src/picasapy/app/qml/Main.qml").resolve().as_posix().encode("utf-8")
    ).hexdigest() + ".qmlc"
    assert any(Path(nev).name == main_cache for nev in elotte), (
        "a Main.qml előre fordított cache-bejegyzése hiányzik"
    )
    selection_cache = sha1(
        (repo / "src/picasapy/app/qml/selection.js")
        .resolve()
        .as_posix()
        .encode("utf-8")
    ).hexdigest() + ".jsc"
    assert any(Path(nev).name == selection_cache for nev in elotte), (
        "a selection.js előre fordított JavaScript-cache-bejegyzése hiányzik"
    )
    indulas = subprocess.run(
        [sys.executable, str(repo / "picasapy"), "--indulasellenorzes", str(library)],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
        check=False,
    )
    kimenet = indulas.stdout + indulas.stderr
    assert indulas.returncode == 0, kimenet
    assert "startup-smoke passed: main window shown after splash" in kimenet
    utana = qml_cache_allapot()

    modositott = [
        (nev, elotte.get(nev), adat)
        for nev, adat in utana.items()
        if elotte.get(nev) != adat
    ]
    assert utana == elotte, (
        "a valódi app QML-betöltése újraírta az előfordított cache-t: "
        f"előtte={len(elotte)}, utána={len(utana)}, "
        f"módosult/új={modositott[:20]}, "
        f"eltűnt={sorted(set(elotte) - set(utana))[:20]}"
    )


def test_a_js_cache_kulcs_jsc_vegjun_perjeles_windows_utvonalon():
    from hashlib import sha1
    from pathlib import PureWindowsPath

    from picasapy.app import qml_precompile

    ut = PureWindowsPath(
        r"C:\Program Files\PicasaPy\_internal\picasapy\app\qml\selection.js"
    )
    vart = sha1(
        b"C:/Program Files/PicasaPy/_internal/picasapy/app/qml/selection.js"
    ).hexdigest()
    assert qml_precompile._qml_cache_nev_utbol(ut) == vart + ".jsc"


def test_a_repo_gyokerben_nem_marad_cache_konyvtar():
    repo = Path(__file__).resolve().parents[2]

    assert not (repo / "cache").exists(), "a QML-cache ne a repó gyökerében jöjjön létre"
