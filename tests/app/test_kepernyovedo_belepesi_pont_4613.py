"""A `picasapy --screensaver` belépési pont: főablak nélkül, a mentett
képernyővédő-beállításokkal vetít, és bármely bevitelre kilép (#4613)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPointF, QSettings, Qt
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QTest
from support.fixture_guards import qml_warning_guard
from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_feltetelre

import picasapy.app.application as app_module
from picasapy.app import screensaver_mode
from picasapy.app.screensaver_controller import load_screensaver_slides
from picasapy.index import open_index, sync_tree


@pytest.fixture(autouse=True)
def qml_warnings():
    yield from qml_warning_guard()


@pytest.fixture
def library(tmp_path):
    lib = tmp_path / "kepek"
    (lib / "nyar").mkdir(parents=True)
    (lib / "tel").mkdir()
    make_jpeg(lib / "nyar" / "a.jpg", size=(320, 160))
    make_jpeg(lib / "nyar" / "b.jpg", size=(100, 100))
    make_jpeg(lib / "tel" / "c.jpg", size=(120, 90))
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, lib)
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    return lib, db, settings


def test_kapcsolo_felismerese_es_eltavolitasa():
    assert screensaver_mode.argv_kepernyovedo(["picasapy", "--screensaver"]) == (
        True, ["picasapy"],
    )
    assert screensaver_mode.argv_kepernyovedo(["picasapy", "/kepek"]) == (
        False, ["picasapy", "/kepek"],
    )


def test_mentett_forras_szerint_valogat(library):
    lib, db, settings = library
    settings.setValue("screensaver/sources", [f"folder:{lib / 'tel'}"])

    slides = load_screensaver_slides(db, settings, (str(lib),))

    assert [photo.name for photo in slides] == ["c.jpg"]


def test_mentes_nelkul_a_figyelt_gyokerekbol_vetit(library):
    lib, db, settings = library
    slides = load_screensaver_slides(db, settings, (str(lib),))
    assert sorted(photo.name for photo in slides) == ["a.jpg", "b.jpg", "c.jpg"]


def test_hid_a_mentett_beallitasokat_adja(library, qt_app):
    lib, db, settings = library
    settings.setValue("screensaver/effect", "kenburns")
    settings.setValue("screensaver/seconds", 7)
    settings.setValue("screensaver/showCaptions", False)
    bridge = screensaver_mode.ScreensaverRunBridge(
        load_screensaver_slides(db, settings, (str(lib),)), settings
    )
    assert bridge.property("effect") == "kenburns"
    assert bridge.property("seconds") == 7
    assert bridge.property("showCaptions") is False
    assert bridge.property("photos").rowCount() == 3


def _load_window(qt_app, library):
    lib, db, settings = library
    bridge = screensaver_mode.ScreensaverRunBridge(
        load_screensaver_slides(db, settings, (str(lib),)), settings
    )
    engine = QQmlApplicationEngine()
    window = app_module.load_screensaver_window(engine, bridge)
    assert window is not None
    finished = []
    bridge.finished.connect(lambda: finished.append(True))
    slideshow = window.findChild(QObject, "slideshowView")
    assert varj_feltetelre(qt_app, lambda: slideshow.property("visible") is True, 3.0)
    assert slideshow.property("screensaverMode") is True
    assert varj_feltetelre(
        qt_app, lambda: slideshow.property("screensaverInputArmed") is True, 3.0
    )
    return engine, window, bridge, finished


def _teardown(qt_app, engine, window):
    window.close()
    engine.deleteLater()
    qt_app.processEvents()


def test_onallo_ablak_vetit_es_billentyure_kilep(qt_app, library):
    engine, window, _bridge, finished = _load_window(qt_app, library)
    assert window.objectName() == "screensaverWindow"

    QTest.keyClick(window, Qt.Key.Key_X)
    qt_app.processEvents()

    assert finished == [True]
    _teardown(qt_app, engine, window)


def test_onallo_ablak_egermozgasra_kilep(qt_app, library):
    engine, window, _bridge, finished = _load_window(qt_app, library)

    QTest.mouseMove(window, QPointF(window.width() / 3, window.height() / 3).toPoint())
    qt_app.processEvents()

    assert finished == [True]
    _teardown(qt_app, engine, window)


def test_futtatas_ures_forrasnal_uzenettel_kilep(tmp_path, monkeypatch, capsys):
    """Kép nélkül nem nyit ablakot: érthető üzenet, nem nulla kilépési kód."""
    monkeypatch.setattr(screensaver_mode, "_prepare", lambda argv: (None, None, ()))
    assert screensaver_mode.run_screensaver(["picasapy"]) == 1
    assert "képernyővédő" in capsys.readouterr().err


def test_application_run_a_kapcsolora_a_kepernyovedot_inditja(monkeypatch):
    calls = []
    monkeypatch.setattr(
        screensaver_mode, "run_screensaver", lambda argv: calls.append(argv) or 5
    )
    assert app_module.run(["picasapy", "--screensaver"]) == 5
    assert calls == [["picasapy"]]


def test_qml_fajl_a_csomagban_van():
    qml = Path(screensaver_mode.__file__).parent / "qml" / "ScreensaverWindow.qml"
    assert qml.is_file()


def test_elokeszites_nem_kerdez_nyelvet_es_nem_ir_beallitast(
    library, tmp_path, monkeypatch, qt_app
):
    """Tétlenségkor indulva nem nyílhat párbeszéd (első indítási nyelvkérdés),
    és a beállításokat csak olvassa."""
    lib, db, settings = library
    settings.setValue("screensaver/sources", [f"folder:{lib / 'nyar'}"])
    settings.sync()
    elotte = Path(settings.fileName()).read_bytes()

    def _tilos(*_args, **_kwargs):
        raise AssertionError("a képernyővédő nem kérdezhet nyelvet")

    monkeypatch.setattr(app_module, "_ask_first_run_language", _tilos)
    monkeypatch.setattr(app_module, "_data_dir", lambda: db.parent)
    monkeypatch.setattr(app_module, "_resolve_roots", lambda argv: (str(lib),))
    monkeypatch.setattr(screensaver_mode, "_settings", lambda: settings)

    _app, _settings, slides = screensaver_mode._prepare(["picasapy"])

    assert sorted(photo.name for photo in slides) == ["a.jpg", "b.jpg"]
    settings.sync()
    assert Path(settings.fileName()).read_bytes() == elotte


def test_betoltes_nem_modositja_az_index_fajlt(library):
    lib, db, settings = library
    elotte = db.read_bytes()
    assert load_screensaver_slides(db, settings, (str(lib),))
    assert db.read_bytes() == elotte


@pytest.mark.parametrize("verzio", [0, 1, 9999])
def test_ismeretlen_semaju_indexnel_nincs_traceback_es_egyes_kod(
    library, tmp_path, monkeypatch, qt_app, capsys, verzio
):
    import sqlite3

    lib, db, settings = library
    with sqlite3.connect(db) as raw:
        raw.execute(f"PRAGMA user_version={verzio}")
    elotte = db.read_bytes()
    monkeypatch.setattr(app_module, "_data_dir", lambda: db.parent)
    monkeypatch.setattr(app_module, "_resolve_roots", lambda argv: (str(lib),))
    monkeypatch.setattr(screensaver_mode, "_settings", lambda: settings)

    assert screensaver_mode.run_screensaver(["picasapy"]) == 1

    err = capsys.readouterr().err
    assert "sémaverzió" in err
    assert "Traceback" not in err
    assert db.read_bytes() == elotte, "a séma-eltérés nem indíthat migrációt"


def test_az_indulas_kapcsoloja_egyezik_a_figyelo_kapcsolojaval():
    """Az `application.py` import nélkül olvasható másolata (#1653) nem
    térhet el a figyelő által írt kapcsolótól."""
    from picasapy.app import application, screensaver_idle

    assert application.KEPERNYOVEDO_KAPCSOLO == screensaver_idle.SCREENSAVER_FLAG
