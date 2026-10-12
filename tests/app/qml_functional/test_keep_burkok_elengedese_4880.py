"""A `_KEEP…` listában tartott QML-burok a motorral együtt elenged (#4880)."""

from __future__ import annotations

import sys

import shiboken6
from PySide6.QtCore import QObject

from tests.app.qml_functional.conftest import _build_qml_app

_KEEP_ALIVE: list = []


def test_a_lebontas_a_modul_burkait_kiuriti_es_ervenyteleniti(qt_app, tmp_path):
    modul = sys.modules[__name__]
    kiepitett = _build_qml_app(qt_app, tmp_path, keep_modul=modul)
    window, _controller, _engine = next(kiepitett)
    gyerek = window.findChild(QObject, "folderListView")
    assert gyerek is not None
    _KEEP_ALIVE.append(gyerek)

    try:
        next(kiepitett)
    except StopIteration:
        pass

    assert _KEEP_ALIVE == []
    assert not shiboken6.isValid(gyerek)
