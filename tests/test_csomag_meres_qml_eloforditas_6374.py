"""A csomagmérő a mért profil cache-ét melegíti, a frissítés idejét is kapuzza."""

from __future__ import annotations

import importlib
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys

from picasapy.app import qml_cache_warmup


_GYOKER = Path(__file__).resolve().parents[1]
_MERES_UT = _GYOKER / "packaging/windows/csomag_meres.py"
_SPEC = importlib.util.spec_from_file_location("csomag_meres_6374", _MERES_UT)
csomag_meres = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(csomag_meres)
ido_modul = importlib.import_module("csomag_meres_ido")


def test_a_meroseged_telepitett_picasapy_nelkul_is_importalhato():
    script = (
        "import sys; "
        f"sys.path.insert(0, {str(_MERES_UT.parent)!r}); "
        "from qml_cache_warmup import melegitsd_qml_cache; "
        "print(melegitsd_qml_cache.__name__)"
    )
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    eredmeny = subprocess.run(
        [sys.executable, "-S", "-c", script],
        cwd=_GYOKER,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    assert eredmeny.returncode == 0, eredmeny.stderr
    assert eredmeny.stdout.strip() == "melegitsd_qml_cache"


def test_a_melegites_ugyanazt_a_profilt_hasznalja_es_a_meres_elott_tortenik(
    monkeypatch, tmp_path
):
    env = {"LOCALAPPDATA": str(tmp_path / "local")}
    events = []
    monkeypatch.setattr(
        ido_modul,
        "_profil",
        lambda root, kepek=0: (events.append(("profil", root, kepek)) or env, root / "library"),
    )
    monkeypatch.setattr(
        qml_cache_warmup,
        "melegitsd_qml_cache",
        lambda command, passed_env, **_kw: events.append(
            ("qml", command, passed_env["LOCALAPPDATA"])
        ),
    )
    monkeypatch.setattr(ido_modul, "_bevar", lambda result: result)

    def inditas(command, root, **kw):
        events.append(("meres", command, root, kw["kepek"]))
        return {
            "kod": 0,
            "fal_mp": 0.1,
            "sorok": [],
            "indult": datetime.now(timezone.utc),
            "kimenet": "",
            "indulo_hatar_ms": None,
            "indulo_kep_kotelezo": False,
        }

    monkeypatch.setattr(ido_modul, "_egy_inditas", inditas)
    monkeypatch.setattr(ido_modul, "hatar_hiba", lambda *_args: None)
    monkeypatch.setattr(ido_modul, "indulo_kozepertek_hiba", lambda *_args: None)

    assert (
        csomag_meres._ido_futtato(
            "csomagolt", ["PicasaPy.exe"], 1, tmp_path, None, 2000, 5.0, None
        )
        == 0
    )
    assert events[0] == ("profil", tmp_path / "ido-csomagolt-2000kep", 2000)
    assert events[1] == ("qml", ["PicasaPy.exe"], str(tmp_path / "local"))
    assert events[2][0] == "meres"


def test_a_frisitesi_indulasi_meres_mindket_idot_kiirja_es_ot_mp_folott_pirossa(
    monkeypatch, tmp_path, capsys
):
    naplo = tmp_path / "indulas-utolso.txt"
    naplo.write_text(
        "  6100.0 ms  QML betöltése (Main.qml) (5300.0 ms)\n"
        "  7200.0 ms  az ablak első kirajzolt képkockája (400.0 ms)\n",
        encoding="utf-8",
    )

    assert csomag_meres._frissites_utana_indulasi_kapu(naplo) == 1
    output = capsys.readouterr().out
    assert "QML betöltése (Main.qml)" in output and "5300 ms" in output
    assert "főablak a splash után" in output and "7.20 s" in output
    assert "5.0 s" in output
