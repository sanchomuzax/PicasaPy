"""A QML gyorsítótár előállítása első indítás előtt (#6374)."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import types
from pathlib import Path

import pytest


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
    cache = profil / "cache"
    config = profil / "config"
    env = os.environ.copy()
    env.update(
        {
            "PYTHONPATH": str(repo / "src"),
            "QT_QPA_PLATFORM": "offscreen",
            "QT_QUICK_BACKEND": "software",
            "XDG_CACHE_HOME": str(cache),
            "XDG_CONFIG_HOME": str(config),
            "XDG_DATA_HOME": str(profil / "data"),
            "PICASAPY_LANG": "en",
        }
    )

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
    assert result.stderr == ""
    assert len(list(cache.rglob("*.qmlc"))) > 0
    assert not (config / "PicasaPy" / "PicasaPy.conf").exists()
    assert not list(profil.rglob("indulas-*.txt"))
