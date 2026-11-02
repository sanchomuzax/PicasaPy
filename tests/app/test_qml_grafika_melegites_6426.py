"""#6426 — a telepítés a valódi Qt Quick grafikus útvonalat is bemelegíti."""

from __future__ import annotations

from pathlib import Path
import types
import sys

import pytest


def test_a_grafika_kapcsolo_a_normal_indulas_elott_ter_vissza(monkeypatch):
    from picasapy.app import __main__ as belepo

    meghivasok = []
    hamis_modul = types.ModuleType("picasapy.app.qml_precompile")
    hamis_modul.grafika_main = lambda: meghivasok.append("grafika") or 17
    monkeypatch.setitem(sys.modules, "picasapy.app.qml_precompile", hamis_modul)
    monkeypatch.setattr(sys, "argv", ["picasapy", "--qml-grafika-melegites"])
    monkeypatch.setattr(
        belepo,
        "start_early_startup",
        lambda _argv: pytest.fail("a grafikai előmelegítés ne indítsa el a normál appot"),
    )

    assert belepo.main() == 17
    assert meghivasok == ["grafika"]


def test_a_grafikai_elomelegites_ugyanazt_a_windowsos_grafikai_utvonalat_hasznalja(
    monkeypatch, tmp_path
):
    from picasapy.app import qml_cache_warmup

    env = {
        "TEMP": str(tmp_path),
        "QT_QPA_PLATFORM": "offscreen",
        "QT_QUICK_BACKEND": "software",
    }
    hivasok = []

    def futtatas(command, *, env, **_kwargs):
        hivasok.append((command, env.copy()))
        naplo = Path(env["PICASAPY_QML_GRAFIKA_MELEGITES_NAPLO"])
        naplo.write_text("grafikai előmelegítés kész: 1 képkocka\n", encoding="utf-8")
        return types.SimpleNamespace(returncode=0)

    monkeypatch.setattr(qml_cache_warmup, "_run", futtatas)

    assert qml_cache_warmup.melegitsd_qml_grafikat(["PicasaPy.exe"], env)
    command, passed_env = hivasok[0]
    assert command == ["PicasaPy.exe", "--qml-grafika-melegites"]
    assert "QT_QPA_PLATFORM" not in passed_env
    assert "QT_QUICK_BACKEND" not in passed_env
    assert env["QT_QPA_PLATFORM"] == "offscreen"


def test_a_grafikai_elomelegito_kivetelt_naploz_es_az_eloirt_koddal_kilep(
    monkeypatch, tmp_path
):
    from picasapy.app import qml_precompile

    naplo = tmp_path / "grafika.txt"
    monkeypatch.setenv(qml_precompile.GRAFIKA_NAPLO_ENV, str(naplo))
    kilepesek = []
    monkeypatch.setattr(qml_precompile, "_kilepes", kilepesek.append)
    monkeypatch.setattr(qml_precompile, "_inditsd_a_hataridot", lambda: None)
    monkeypatch.setattr(
        qml_precompile,
        "_melegitsd_grafikat",
        lambda: (_ for _ in ()).throw(RuntimeError("render")),
    )

    assert qml_precompile.grafika_main() == qml_precompile.KIVETEL_KOD
    assert kilepesek == [qml_precompile.KIVETEL_KOD]
    assert "RuntimeError" in naplo.read_text(encoding="utf-8")


def test_a_grafikai_elomelegito_egy_rejtett_qt_quick_kepkockara_var(
    monkeypatch, tmp_path
):
    from picasapy.app import qml_precompile

    naplo = tmp_path / "grafika.txt"
    monkeypatch.setenv(qml_precompile.GRAFIKA_NAPLO_ENV, str(naplo))
    monkeypatch.setenv(qml_precompile.HATARIDO_ENV, "15")

    qml_precompile._melegitsd_grafikat()

    assert "grafikai előmelegítés kész: 1 képkocka" in naplo.read_text(
        encoding="utf-8"
    )
