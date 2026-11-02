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


def test_a_grafikai_elomelegito_kivetelt_naploz_es_az_eloirt_koddal_kilep(monkeypatch, tmp_path):
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


def test_a_grafikai_elomelegito_egy_rejtett_qt_quick_kepkockara_var(monkeypatch, tmp_path):
    from picasapy.app import qml_precompile

    naplo = tmp_path / "grafika.txt"
    monkeypatch.setenv(qml_precompile.GRAFIKA_NAPLO_ENV, str(naplo))
    monkeypatch.setenv(qml_precompile.HATARIDO_ENV, "15")

    qml_precompile._melegitsd_grafikat()

    assert "grafikai előmelegítés kész: 1 képkocka" in naplo.read_text(encoding="utf-8")


_QML_GYOKER = Path(__file__).resolve().parents[2] / "src" / "picasapy" / "app" / "qml"


def _app_qt_moduljai() -> set[str]:
    import re

    minta = re.compile(r"^import\s+(Qt[A-Za-z0-9.]*)", re.M)
    modulok: set[str] = set()
    for fajl in _QML_GYOKER.rglob("*.qml"):
        modulok.update(minta.findall(fajl.read_text(encoding="utf-8")))
    return modulok


def _elomelegito_importjai(qml: bytes) -> set[str]:
    import re

    return set(re.findall(r"^import\s+(\S+)", qml.decode("utf-8"), re.M))


def test_a_grafikai_elomelegito_az_app_minden_qt_moduljat_betolti():
    """Az első valódi indulásnál a hidegen töltődő modul-DLL-ek adták a késést."""
    from picasapy.app import qml_precompile

    hianyzik = _app_qt_moduljai() - _elomelegito_importjai(qml_precompile._grafika_qml())
    assert not hianyzik, f"az előmelegítő nem tölti be: {sorted(hianyzik)}"


def test_a_tartalek_elomelegito_csak_az_alapmodulokat_tolti_be():
    from picasapy.app import qml_precompile

    assert _elomelegito_importjai(qml_precompile._grafika_qml(teljes=False)) == {
        "QtQuick",
        "QtQuick.Controls",
    }


def test_az_elomelegito_komponens_a_hianyzo_modult_kihagyja(qt_app):
    """Helyben a QtLocation nincs telepítve; a komponens ettől még betölthető."""
    from PySide6.QtCore import QUrl
    from PySide6.QtQml import QQmlComponent, QQmlEngine

    from picasapy.app import qml_precompile

    engine = QQmlEngine()
    engine.addImportPath(qml_precompile._qml_import_path())
    component = qml_precompile._grafika_komponens(engine, QQmlComponent, QUrl)
    assert component.status() != QQmlComponent.Status.Error
    betoltve = qml_precompile._betoltheto_modulok(engine, QQmlComponent, QUrl)
    assert {"QtQuick.Layouts", "QtQuick.Dialogs", "QtQml"} <= set(betoltve)


def test_a_tartalek_elomelegito_qml_hiba_nelkul_betoltheto(qt_app):
    from PySide6.QtCore import QUrl
    from PySide6.QtQml import QQmlComponent, QQmlEngine

    from picasapy.app import qml_precompile

    engine = QQmlEngine()
    engine.addImportPath(qml_precompile._qml_import_path())
    component = QQmlComponent(engine)
    component.setData(qml_precompile._grafika_qml(teljes=False), QUrl())
    assert component.status() != QQmlComponent.Status.Error, [
        hiba.toString() for hiba in component.errors()
    ]


def test_a_betukeszlet_melegites_minden_csaladot_betolt(monkeypatch):
    """Windowson az első indulásnál a Qt egyenként betölti az összes
    betűkészlet-családot (CI-napló, #6426); a telepítő ezt előre elvégzi."""
    from picasapy.app import qml_precompile

    betoltve = []

    class HamisAdatbazis:
        @staticmethod
        def families():
            return ["Arial", "Nirmala UI", "Yu Gothic"]

        @staticmethod
        def styles(csalad):
            betoltve.append(csalad)
            return ["Regular"]

    naplo = []
    monkeypatch.setattr(qml_precompile, "_grafika_naplozz", naplo.append)

    assert qml_precompile._melegitsd_betukeszleteket(HamisAdatbazis) == 3
    assert betoltve == ["Arial", "Nirmala UI", "Yu Gothic"]
    assert any("3 betűkészlet-család" in sor for sor in naplo)


def test_a_betukeszlet_melegites_hibaja_nem_allitja_meg_a_melegitest(monkeypatch):
    from picasapy.app import qml_precompile

    class HibasAdatbazis:
        @staticmethod
        def families():
            raise RuntimeError("nincs betűkészlet-adatbázis")

    naplo = []
    monkeypatch.setattr(qml_precompile, "_grafika_naplozz", naplo.append)

    assert qml_precompile._melegitsd_betukeszleteket(HibasAdatbazis) == 0
    assert any("betűkészlet" in sor for sor in naplo)


def test_a_melegites_a_splash_kepet_is_elkesziti(monkeypatch):
    """Az első indulásnál a splash elkészítése 1,5 s volt (máskor 0,4 s): a
    saját betűkészlet és a logó első betöltése. A telepítő ezt is előre végzi."""
    from picasapy.app import qml_precompile, startup_splash

    hivasok = []
    monkeypatch.setattr(
        startup_splash, "_create_splash_pixmap", lambda verzio, **_k: hivasok.append(verzio)
    )
    naplo = []
    monkeypatch.setattr(qml_precompile, "_grafika_naplozz", naplo.append)

    assert qml_precompile._melegitsd_splash_kepet() is True
    assert len(hivasok) == 1
    assert any("splash" in sor for sor in naplo)


def test_a_splash_melegites_hibaja_nem_allitja_meg(monkeypatch):
    from picasapy.app import qml_precompile, startup_splash

    def hibas(_verzio, **_k):
        raise OSError("nincs logó")

    monkeypatch.setattr(startup_splash, "_create_splash_pixmap", hibas)
    naplo = []
    monkeypatch.setattr(qml_precompile, "_grafika_naplozz", naplo.append)

    assert qml_precompile._melegitsd_splash_kepet() is False
    assert any("kimaradt" in sor for sor in naplo)
