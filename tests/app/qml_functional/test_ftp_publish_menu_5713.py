"""A Tools ▸ Experimental FTP-parancs valódi kattintással FTP-módban nyit (#5713)."""

# rontás-kontroll: PicasaMenuBar.qml.menuToolsPublishFtp = hiányzik → 3 failed

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QSettings
from tests.app.qml_functional.conftest import _build_qml_app
from tests.app.qml_functional._felsomenupontok_helpers_4329 import (
    _kattints as _menu_kattintas,
    _objektum,
)
from tests.support.jpeg_factory import make_minta_jpeg
from tests.support.varakozas import var_feltetelre

KIADASKEP_MAPPA = "PICASAPY_5713_KIADASKEP_MAPPA"


class _Secrets:
    def __init__(self):
        self.data = {}

    def get_password(self, service, account):
        return self.data.get((service, account))

    def set_password(self, service, account, password):
        self.data[(service, account)] = password

    def delete_password(self, service, account):
        self.data.pop((service, account), None)


@pytest.fixture
def qml_app(qt_app, tmp_path, request):
    def kepeket_keszit(folder):
        make_minta_jpeg(folder / "a.jpg", size=(320, 240), seed=71)
        make_minta_jpeg(folder / "b.jpg", size=(320, 240), seed=72)

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=kepeket_keszit,
        belyegkep_meret=256,
        valodi_belyegkep=True,
        keep_modul=request.module,
    )
@pytest.mark.parametrize("delta", (-5, 0, 5))
def test_eszközok_menu_kattintas_ftp_modban_nyitja_a_kozos_exportot(
    qml_app, qt_app, tmp_path, delta
):
    window, app_controller, engine = qml_app
    from picasapy.app.webexport_controller import WebExportController
    from picasapy.webexport.ftp_publish import FtpAccountStore

    settings = QSettings(
        str(tmp_path / "webexport.ini"), QSettings.Format.IniFormat
    )
    store = FtpAccountStore(settings, _Secrets())
    account = store.save_account(
        account_id="",
        name="Tesztfiók",
        domain="ftp.example.test",
        user="galeria",
        root="/galeria",
        password="nem-valodi-jelszo",
    )
    store.select_account(account.account_id)
    web_export_controller = WebExportController(
        photo_source=lambda: app_controller.photos.photos,
        settings=settings,
        ftp_account_store=store,
    )
    engine.rootContext().setContextProperty(
        "webExportController", web_export_controller
    )
    window.setHeight(window.height() + delta)
    qt_app.processEvents()
    menu_bar = window.property("menuBar")
    tools = _objektum(window, "menuTools")
    tools_header = next(
        item
        for item in menu_bar.findChildren(QObject)
        if "MenuBarItem" in item.metaObject().className()
        and item.property("text") in {"&Tools", "Eszközök"}
    )
    _menu_kattintas(qt_app, tools_header)
    assert var_feltetelre(qt_app, lambda: tools.property("opened") is True, 3)

    experimental = window.findChild(QObject, "menuToolsExperimental")
    assert experimental is not None
    experimental.open()
    assert var_feltetelre(
        qt_app, lambda: experimental.property("opened") is True, 3
    )

    ftp_item = _objektum(window, "menuToolsPublishFtp")
    _menu_kattintas(qt_app, ftp_item)
    assert var_feltetelre(
        qt_app,
        lambda: _objektum(window, "webExportDialog") is not None
        and _objektum(window, "webExportDialog").property("visible"),
        3,
    )
    dialog = _objektum(window, "webExportDialog")
    assert dialog.property("ftpMode") is True
    assert dialog.property("selectedFtpAccountId") == account.account_id
    assert dialog.property("templateId")
    assert _objektum(dialog, "webExportFtpAccountRow").property("visible") is True

    capture_dir = os.environ.get(KIADASKEP_MAPPA)
    if delta == 0 and capture_dir:
        target = Path(capture_dir)
        target.mkdir(parents=True, exist_ok=True)
        main_capture = window.grabWindow()
        dialog_capture = dialog.grabWindow()
        assert not main_capture.isNull(), "a főablak kiadásképe üres"
        assert not dialog_capture.isNull(), "az FTP-párbeszéd kiadásképe üres"
        assert main_capture.save(str(target / "picasapy_ftp_fokepernyo_5713.png"))
        assert dialog_capture.save(str(target / "picasapy_ftp_parbeszed_5713.png"))
