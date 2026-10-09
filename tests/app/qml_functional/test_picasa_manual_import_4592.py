"""#4592: kézi Picasa2 mappa és meghajtó-leképezés kattintásos próbája."""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

import picasapy.app as app_package
from picasapy.app.picasa_import_controller import PicasaImportController
from tests.support.pmp_factory import build_pmp_column, build_thumb_index

_APP_DIR = Path(app_package.__file__).parent


def _elem(root, name: str):
    result = root.findChild(QQuickItem, name)
    assert result is not None, f"{name} nem található"
    return result


def _varj(qt_app, condition, message: str, timeout: float = 3.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if condition():
            return
        time.sleep(0.02)
    qt_app.processEvents()
    assert condition(), message


def _kattint(window, item, qt_app) -> None:
    assert item.property("enabled") is True, f"{item.objectName()} le van tiltva"
    assert item.property("visible") is True, f"{item.objectName()} nem látszik"
    assert item.width() > 0 and item.height() > 0, (
        f"{item.objectName()} nem kattintható"
    )
    center = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    qt_app.processEvents()


def _szoveget_beallit(window, field, value: str, qt_app) -> None:
    _kattint(window, field, qt_app)
    field.setProperty("text", value)
    qt_app.processEvents()


def _minta_db3(db3: Path) -> None:
    db3.mkdir()
    (db3 / "thumbindex.db").write_bytes(
        build_thumb_index(
            [
                (r"C:\Users\anna\Pictures", None),
                ("IMG_0001.jpg", 0),
            ]
        )
    )
    (db3 / "imagedata_tags.pmp").write_bytes(
        build_pmp_column(0x6, ["", "család"])
    )


def test_kattintassal_importal_kezzel_valasztott_mappabol_es_terkepezessel(
    qt_app, tmp_path
):
    db3 = tmp_path / "kézzel választott Picasa2"
    _minta_db3(db3)
    helyi_kepek = tmp_path / "saját képek"
    helyi_kepek.mkdir()
    (helyi_kepek / "IMG_0001.jpg").write_bytes(b"minta")

    engine = QQmlEngine()
    engine.addImportPath(str(_APP_DIR / "qml"))
    controller = PicasaImportController(felderito=lambda: ())
    engine.rootContext().setContextProperty("picasaImportController", controller)
    component = QQmlComponent(
        engine,
        QUrl.fromLocalFile(
            str(_APP_DIR / "qml" / "PicasaPy" / "PicasaDataImportDialog.qml")
        ),
    )
    assert component.status() == QQmlComponent.Status.Ready, component.errorString()
    window = component.create()
    assert window is not None, component.errorString()
    assert not component.errors(), component.errors()
    QQmlEngine.setObjectOwnership(window, QQmlEngine.ObjectOwnership.CppOwnership)

    try:
        QMetaObject.invokeMethod(window, "open", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        eredeti_magassag = window.height()
        source = _elem(window, "picasaImportSourceFolderField")
        drive = _elem(window, "picasaImportDrivePrefixField")
        local = _elem(window, "picasaImportLocalPrefixField")
        import_button = _elem(window, "picasaImportStartButton")

        for eltolas in (-5, 0, 5):
            window.resize(window.width(), eredeti_magassag + eltolas)
            qt_app.processEvents()
            for item in (source, drive, local, import_button):
                assert item.property("visible") is True, (
                    f"{item.objectName()} nem látszik {eltolas:+} px ablakmagasságnál"
                )
                top = item.mapToScene(QPointF(0, 0)).y()
                assert top >= 0 and top + item.height() <= window.height(), (
                    f"{item.objectName()} kilóg az ablakból {eltolas:+} px-nél"
                )

        window.resize(window.width(), eredeti_magassag)
        browse = _elem(window, "picasaImportBrowseButton")
        _kattint(window, browse, qt_app)
        folder_dialog = window.findChild(
            QObject, "picasaImportSourceFolderDialog"
        )
        assert folder_dialog is not None, "a mappaválasztó nem épült fel"
        _varj(
            qt_app,
            lambda: folder_dialog.property("visible") is True,
            "a Tallózás nem nyitotta meg a mappaválasztót",
        )
        folder_dialog.setProperty("selectedFolder", QUrl.fromLocalFile(str(db3)))
        assert QMetaObject.invokeMethod(
            folder_dialog, "accepted", Qt.ConnectionType.DirectConnection
        )
        _varj(
            qt_app,
            lambda: Path(str(source.property("text"))) == db3,
            "a kiválasztott Picasa2 mappa nem került a mezőbe",
        )

        _szoveget_beallit(window, drive, r"C:\Users\anna\Pictures", qt_app)
        _szoveget_beallit(window, local, str(helyi_kepek), qt_app)
        _kattint(window, import_button, qt_app)
        _varj(
            qt_app,
            lambda: not controller.running
            and (window.property("finished") or window.property("lastError")),
            "a kattintással indított kézi átvétel nem fejeződött be",
        )

        assert window.property("lastError") == ""
        assert window.property("finished") is True
        assert "1 folder(s) updated" in _elem(
            window, "picasaImportResult"
        ).property("text")
        ini = (helyi_kepek / ".picasa.ini").read_text(encoding="utf-8")
        assert "keywords=család" in ini
    finally:
        controller.waitForBackgroundWorkers(5.0)
        window.close()
        qt_app.processEvents()
