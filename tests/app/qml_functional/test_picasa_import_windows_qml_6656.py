"""#6656: a felismert Picasa-adatmappával egyetlen kattintás az import, átírás nélkül.

A tulajdonos Windowson „0 mappa frissült”-et kapott, és nem tudta, mit kell a
két útvonal-átíró mezőbe írni. A mezők megszűntek, az adatmappát a párbeszéd
magától kitölti; a mintaadatbázis útvonala a helyi mappa, ahogy ugyanazon a
gépen a Picasa látta.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMetaObject, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem

import picasapy.app as app_package
from picasapy.app.picasa_import_controller import PicasaImportController
from tests.app.qml_functional.test_picasa_manual_import_qml_4592 import (
    _elem,
    _kattint,
    _varj,
)
from tests.support.pmp_factory import build_pmp_column, build_thumb_index

_APP_DIR = Path(app_package.__file__).parent


def test_a_felismert_adatmappaval_kattintasra_atiras_nelkul_importal(qt_app, tmp_path, monkeypatch):
    from picasapy.pmpimport import remap as remap_modul

    monkeypatch.setattr(remap_modul.sys, "platform", "win32")
    helyi_kepek = tmp_path / "Pictures"
    helyi_kepek.mkdir()
    (helyi_kepek / "IMG_0001.jpg").write_bytes(b"minta")
    db3 = tmp_path / "Picasa2" / "db3"
    db3.mkdir(parents=True)
    (db3 / "thumbindex.db").write_bytes(
        build_thumb_index([(str(helyi_kepek), None), ("IMG_0001.jpg", 0)])
    )
    (db3 / "imagedata_tags.pmp").write_bytes(build_pmp_column(0x6, ["", "család"]))

    engine = QQmlEngine()
    engine.addImportPath(str(_APP_DIR / "qml"))
    from types import SimpleNamespace

    controller = PicasaImportController(felderito=lambda: (SimpleNamespace(picasa2_dir=db3),))
    engine.rootContext().setContextProperty("picasaImportController", controller)
    component = QQmlComponent(
        engine, QUrl.fromLocalFile(str(_APP_DIR / "qml" / "PicasaPy" / "PicasaDataImportDialog.qml"))
    )
    assert component.status() == QQmlComponent.Status.Ready, component.errorString()
    window = component.create()
    assert window is not None, component.errorString()
    QQmlEngine.setObjectOwnership(window, QQmlEngine.ObjectOwnership.CppOwnership)
    try:
        QMetaObject.invokeMethod(window, "open", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        # a felhasználó semmit nem ír be: az adatmappát a párbeszéd magától kitölti,
        # útvonal-átíró mező pedig nincs
        assert _elem(window, "picasaImportSourceFolderField").property("text") == str(db3)
        assert window.findChild(QQuickItem, "picasaImportDrivePrefixField") is None
        assert window.findChild(QQuickItem, "picasaImportLocalPrefixField") is None
        _kattint(window, _elem(window, "picasaImportStartButton"), qt_app)
        _varj(
            qt_app,
            lambda: not controller.running
            and (window.property("finished") or window.property("lastError")),
            "a kattintással indított átvétel nem fejeződött be",
        )
        assert window.property("lastError") == ""
        assert "1 folder(s) updated" in _elem(window, "picasaImportResult").property("text")
        assert "keywords=család" in (helyi_kepek / ".picasa.ini").read_text(encoding="utf-8")
    finally:
        controller.waitForBackgroundWorkers(5.0)
        window.close()
        qt_app.processEvents()
