"""A betöltött teszt- és segédmodulok QML-burkainak takarítása (#4897)."""

from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType

import shiboken6
from PySide6.QtCore import QObject

from support.keep_burkok import tesztmodulok_listait_elenged


def test_a_betoltott_tesztsegedeit_is_elengedi_a_kulso_moduloket_nem(
    monkeypatch, tmp_path
):
    tesztsegéd = ModuleType("tests.support.betoltott_seged")
    tesztsegéd.__file__ = str(
        Path(__file__).parent / "support" / "betoltott_seged.py"
    )
    tesztburok = QObject()
    tesztsegéd._KEEP_ALIVE = [tesztburok]

    kulso_modul = ModuleType("kulso.modul")
    kulso_modul.__file__ = str(tmp_path / "kulso_modul.py")
    kulso_burok = QObject()
    kulso_modul._KEEP_ALIVE = [kulso_burok]

    monkeypatch.setitem(sys.modules, tesztsegéd.__name__, tesztsegéd)
    monkeypatch.setitem(sys.modules, kulso_modul.__name__, kulso_modul)
    ervenytelenitett = []
    monkeypatch.setattr(shiboken6, "invalidate", ervenytelenitett.append)

    elengedett = tesztmodulok_listait_elenged()

    assert elengedett == 1
    assert tesztsegéd._KEEP_ALIVE == []
    assert ervenytelenitett == [tesztburok]
    assert kulso_modul._KEEP_ALIVE == [kulso_burok]
    assert shiboken6.isValid(kulso_burok)
