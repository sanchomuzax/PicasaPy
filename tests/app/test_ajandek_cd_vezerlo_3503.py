"""#3503 — az Ajándék CD a KÉPTÁLCA elemeiből készül, háttérszálon.

A lemezkép tartalmát a `tests/burn/test_ajandek_cd_3503.py` méri; itt a
vezérlő szerződése: a tálca mappákon átnyúló elemei kerülnek a lemezre, a
mappanév a honosított „Pictures", és a vége jelzés megmondja, hová került
a kép.
"""

from pathlib import Path

import pytest
from PySide6.QtCore import QEventLoop, QSettings, QTimer

from picasapy.index import open_index, sync_tree
from picasapy.thumbs import ThumbnailCache
from support.jpeg_factory import make_jpeg


@pytest.fixture
def library(tmp_path):
    first = tmp_path / "elso"
    second = tmp_path / "masodik"
    first.mkdir()
    second.mkdir()
    make_jpeg(first / "a.jpg", size=(32, 24))
    make_jpeg(second / "b.jpg", size=(32, 24))
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, first)
        sync_tree(conn, second)
    return tmp_path, first, second, db


@pytest.fixture
def controller(qt_app, library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider

    tmp_path, first, second, db = library
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    return AppController(db, (str(first), str(second)), provider, settings=settings)


def _tartsd_mindkettot(controller, qt_app, first, second):
    controller.selectFolder(str(first))
    qt_app.processEvents()
    sorok = [
        sor for sor in range(controller.photos.rowCount())
        if Path(controller.photos.filePathAt(sor)).parent in (first, second)
    ]
    controller.holdRows(sorok)
    qt_app.processEvents()


def _varj(controller, qt_app, muvelet, timeout_ms=20000):
    loop = QEventLoop()
    eredmeny = {}

    def _kesz(ut, darab, hibas):
        eredmeny.update(ut=ut, darab=darab, hibas=hibas)
        loop.quit()

    controller.ajandekCdKesz.connect(_kesz)
    try:
        muvelet()
        if not eredmeny:
            QTimer.singleShot(timeout_ms, loop.quit)
            loop.exec()
    finally:
        controller.ajandekCdKesz.disconnect(_kesz)
    qt_app.processEvents()
    assert eredmeny, "az ajandekCdKesz jelzés nem érkezett meg az időkorlát alatt"
    return eredmeny


def test_a_talca_elemei_kerulnek_a_lemezkepre(controller, qt_app, library):
    tmp_path, first, second, _ = library
    _tartsd_mindkettot(controller, qt_app, first, second)
    assert controller.heldCount == 2
    cel = tmp_path / "ki" / "ajandek.iso"

    eredmeny = _varj(
        controller, qt_app,
        lambda: controller.ajandekCdIrasa(0, "Család", str(cel)),
    )

    assert eredmeny == {"ut": str(cel), "darab": 2, "hibas": 0}
    assert cel.stat().st_size > 0


def test_iso_kiterjesztes_nelkul_is_iso_lesz(controller, qt_app, library):
    tmp_path, first, second, _ = library
    _tartsd_mindkettot(controller, qt_app, first, second)

    eredmeny = _varj(
        controller, qt_app,
        lambda: controller.ajandekCdIrasa(1, "X", str(tmp_path / "lemez")),
    )

    assert eredmeny["ut"] == str(tmp_path / "lemez.iso")


def test_ures_talcanal_nincs_lemezkep(controller, qt_app, library):
    tmp_path, *_ = library
    cel = tmp_path / "ures.iso"

    eredmeny = _varj(
        controller, qt_app, lambda: controller.ajandekCdIrasa(0, "X", str(cel))
    )

    assert eredmeny == {"ut": "", "darab": 0, "hibas": 0}
    assert not cel.exists()


def test_a_mappanev_honositott(controller, qt_app, library):
    """Magyar Picasával kiírt lemezen `Képek` mappa van, nem `Pictures`
    (`il_BurnPanel::picfolder`, spec 4.) — a fordítónak FUTÁSIDŐBEN kell
    megtalálnia a szöveget a vezérlő saját szeletéből."""
    import shutil
    import subprocess

    from PySide6.QtCore import QCoreApplication, QTranslator

    import picasapy.app.application as app_module

    tmp_path, first, second, _ = library
    forditas = QTranslator()
    assert forditas.load(str(app_module._APP_DIR / "i18n" / "picasapy_hu.qm"))
    QCoreApplication.installTranslator(forditas)
    try:
        _tartsd_mindkettot(controller, qt_app, first, second)
        cel = tmp_path / "hu.iso"
        _varj(controller, qt_app, lambda: controller.ajandekCdIrasa(0, "X", str(cel)))
    finally:
        QCoreApplication.removeTranslator(forditas)

    hetz = shutil.which("7z") or shutil.which("7za")
    assert hetz, "nincs `7z` a gépen — a lemezkép ellenőrzése így nem mérés"
    lista = subprocess.run(
        [hetz, "l", "-slt", str(cel)], capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=60,
    ).stdout
    assert "Path = Képek" in lista
    assert "Path = Pictures" not in lista


def test_varatlan_hibanal_is_jelez(controller, qt_app, library, monkeypatch):
    """Az átnézés lelete: egy nem várt kivétel (pl. `OverflowError` egy túl
    nagy filmnél) után is ki kell mennie a jelzésnek — különben a panel
    „dolgozik" állapotban ragad, és a „Lemezre írás" nem nyomható többé."""
    import picasapy.app.ajandek_cd_controller as modul

    tmp_path, first, second, _ = library
    _tartsd_mindkettot(controller, qt_app, first, second)

    def _elszall(*_a, **_k):
        raise OverflowError("int too big to convert")

    monkeypatch.setattr(modul, "ajandek_cd_lemezkep", _elszall)

    eredmeny = _varj(
        controller, qt_app,
        lambda: controller.ajandekCdIrasa(0, "X", str(tmp_path / "x.iso")),
    )

    assert eredmeny == {"ut": "", "darab": 0, "hibas": 2}


def test_az_alaphely_url(controller):
    """Kézzel fűzött `"file://" + út` Windowson érvénytelen (#1009) — a
    kiinduló mappa kész URL-ként jön."""
    url = controller.ajandekCdAlapHely()

    assert url.isLocalFile()
