"""A `_KEEP…` listában tartott QML-burok a motorral együtt elenged (#4880)."""

from __future__ import annotations

import shiboken6
from PySide6.QtCore import QObject

from tests.app.qml_functional.conftest import _build_qml_app

_KEEP_ALIVE: list = []
_KEEP_MAS_MOTOR: list = []


def test_a_lebontas_a_motor_burkait_kiveszi_es_ervenyteleniti(qt_app, tmp_path):
    kiepitett = _build_qml_app(qt_app, tmp_path)
    window, _controller, _engine = next(kiepitett)
    gyerek = window.findChild(QObject, "folderListView")
    assert gyerek is not None
    _KEEP_ALIVE.append(gyerek)
    idegen = QObject()  # nem a motoré: ezt nem bánthatja
    _KEEP_MAS_MOTOR.append(idegen)

    try:
        next(kiepitett)
    except StopIteration:
        pass

    assert gyerek not in _KEEP_ALIVE
    assert not shiboken6.isValid(gyerek)
    assert _KEEP_MAS_MOTOR == [idegen] and shiboken6.isValid(idegen)
    _KEEP_MAS_MOTOR.clear()
