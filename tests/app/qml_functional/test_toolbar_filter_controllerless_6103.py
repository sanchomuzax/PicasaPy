"""A 6103-as szűrőkomponens vezérlő nélkül is felépül."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QUrl, qInstallMessageHandler
from PySide6.QtQml import QQmlComponent, QQmlEngine

import picasapy.app

_QML = Path(picasapy.app.__file__).parent / "qml"
_FILTER_CONTROLS = _QML / "PicasaPy" / "ToolbarFilterControls.qml"


def test_filter_controls_create_without_controller_reference_error(qt_app):
    uzenetek: list[str] = []
    korabbi = qInstallMessageHandler(
        lambda _tipus, _kontextus, uzenet: uzenetek.append(uzenet)
    )
    motor = QQmlEngine()
    motor.addImportPath(str(_QML))
    komponens = QQmlComponent(motor, QUrl.fromLocalFile(str(_FILTER_CONTROLS)))
    elem = None
    try:
        elem = komponens.create()
        referenciahibak = [
            uzenet for uzenet in uzenetek if "ReferenceError" in uzenet
        ]
    finally:
        if elem is not None:
            elem.deleteLater()
        motor.deleteLater()
        qInstallMessageHandler(korabbi)

    assert elem is not None, "a ToolbarFilterControls QML-komponens nem épült fel"
    assert not referenciahibak, "vezérlő nélkül ReferenceError: " + "; ".join(
        referenciahibak
    )
