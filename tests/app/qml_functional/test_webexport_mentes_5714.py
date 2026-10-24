"""#5714: a webexport célmappája és sablonja a következő párbeszédben is él."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, QSettings, Qt

from picasapy.app.webexport_controller import WebExportController
from support.qt_wait import hangos_hurok


def test_uj_vezerlo_es_parbeszed_visszaallitja_a_cel_es_sablon(
    qml_app, tmp_path
):
    ablak, app_vezerlo, engine = qml_app
    beallitas = app_vezerlo._get_settings()
    cel = tmp_path / "sajat-webexport"

    elso = WebExportController(
        photo_source=lambda: app_vezerlo.photos.photos,
        settings=beallitas,
    )
    loop = hangos_hurok(elso.webExportFinished)
    elso.generateWebExport(str(cel), "feher", "Nyaralás", 3, False)
    loop.exec()
    assert elso.waitForExport(30.0)
    beallitas.sync()

    uj_beallitas = QSettings(beallitas.fileName(), QSettings.Format.IniFormat)
    uj_vezerlo = WebExportController(
        photo_source=lambda: app_vezerlo.photos.photos,
        settings=uj_beallitas,
    )
    engine.rootContext().setContextProperty("webExportController", uj_vezerlo)

    QMetaObject.invokeMethod(
        ablak, "openWebExport", Qt.ConnectionType.DirectConnection
    )
    parbeszed = ablak.findChild(QObject, "webExportDialog")
    assert parbeszed is not None
    assert Path(parbeszed.property("targetFolder")) == cel
    assert parbeszed.property("templateId") == "feher"
