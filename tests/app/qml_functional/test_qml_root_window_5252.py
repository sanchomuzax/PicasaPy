"""#5252: a fixture felszabadítja a főablak Python-wrapperét is."""

from __future__ import annotations

import sys

import shiboken6
import pytest
from PySide6.QtCore import QMetaObject

import conftest
from conftest import _build_qml_app


def test_teardown_ervenyteleniti_a_gyokerablak_burkat(qt_app, tmp_path, monkeypatch):
    eredeti_ervenytelenites = shiboken6.invalidate
    ervenytelenitett = []

    def naploz_ervenytelenitest(obj):
        ervenytelenitett.append(obj)
        eredeti_ervenytelenites(obj)

    monkeypatch.setattr(shiboken6, "invalidate", naploz_ervenytelenitest)
    alkalmazas = _build_qml_app(qt_app, tmp_path, keep_modul=sys.modules[__name__])
    window, _controller, _engine = next(alkalmazas)

    try:
        next(alkalmazas)
    except StopIteration:
        pass

    assert any(obj is window for obj in ervenytelenitett), (
        "a qml_app teardown nem érvénytelenítette a root window wrapperét"
    )
    assert not shiboken6.isValid(window)


def test_root_objects_rossz_tipusa_ertheto_hibat_ad():
    with pytest.raises(RuntimeError, match="QQuickWindow"):
        conftest._validated_qml_root_window([QMetaObject()])


def test_root_objects_ervenytelen_ablakburka_ertheto_hibat_ad(qt_app):
    from PySide6.QtQuick import QQuickWindow

    window = QQuickWindow()
    shiboken6.delete(window)

    with pytest.raises(RuntimeError, match="érvénytelen"):
        conftest._validated_qml_root_window([window])
