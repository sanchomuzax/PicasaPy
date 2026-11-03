"""A frissítési próba kattintás előtt valóban előtérbe hozza a PicasaPy ablakát (#6487).

A 2026-11-03-i v1.0.32 csomagolásban a #6472 kattintásos telepítőpróbája után
a Windows előtérzára miatt a sima `SetForegroundWindow` nem hozta előre a
PicasaPy ablakát; a próba a futtató terminálablakára kattintott, és 60 s-os
időtúllépéssel bukott, a kiadásból pedig kimaradt a telepítő.
"""

from __future__ import annotations

import importlib
import importlib.util
from pathlib import Path

import pytest

_UT = Path(__file__).resolve().parents[1] / "packaging" / "windows" / "csomag_meres.py"
_spec = importlib.util.spec_from_file_location("csomag_meres_6487", _UT)
csomag_meres = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(csomag_meres)
frissites_modul = importlib.import_module("csomag_meres_frissites")

PICASA = 101
TERMINAL = 202


class _HamisUser32:
    """Az előtérzárat utánozza: sima SetForegroundWindow hatástalan."""

    def __init__(self, *, zar_oldodik: bool = True) -> None:
        self.elotér = TERMINAL
        self.zar_oldodik = zar_oldodik
        self.csatolva = False
        self.hivasok: list[str] = []

    def GetForegroundWindow(self):  # noqa: N802
        return self.elotér

    def GetWindowThreadProcessId(self, hwnd, _ptr):  # noqa: N802
        return 7 if hwnd == TERMINAL else 9

    def AttachThreadInput(self, _sajat, _cel, csatol):  # noqa: N802
        self.csatolva = bool(csatol)
        self.hivasok.append(f"attach={bool(csatol)}")
        return 1

    def ShowWindow(self, _hwnd, _mod):  # noqa: N802
        return 1

    def BringWindowToTop(self, _hwnd):  # noqa: N802
        return 1

    def SetForegroundWindow(self, hwnd):  # noqa: N802
        self.hivasok.append("set")
        if self.csatolva and self.zar_oldodik:
            self.elotér = hwnd
        return 1

    def keybd_event(self, *_args):
        self.hivasok.append("alt")


class _HamisKernel32:
    def GetCurrentThreadId(self):  # noqa: N802
        return 5


def _ablakok(_pid):
    return {PICASA: {"cim": "PicasaPy", "ikon": True}}


def test_az_eloterzar_ellenere_eloterbe_hozza(monkeypatch):
    user32 = _HamisUser32()
    monkeypatch.setattr(frissites_modul, "_ablakikonok", _ablakok)
    monkeypatch.setattr(frissites_modul, "_szunet", lambda _s: None)

    hwnd = frissites_modul._eloterbe_hoz(1234, user32=user32, kernel32=_HamisKernel32())

    assert hwnd == PICASA
    assert user32.elotér == PICASA
    assert "attach=True" in user32.hivasok and user32.hivasok[-1] == "attach=False"


def test_ha_nem_hozhato_eloterbe_erthetoen_hibazik(monkeypatch):
    user32 = _HamisUser32(zar_oldodik=False)
    monkeypatch.setattr(frissites_modul, "_ablakikonok", _ablakok)
    monkeypatch.setattr(frissites_modul, "_szunet", lambda _s: None)

    with pytest.raises(RuntimeError, match="előtérbe"):
        frissites_modul._eloterbe_hoz(1234, user32=user32, kernel32=_HamisKernel32())


def test_mar_eloterben_levo_ablakhoz_nem_nyul(monkeypatch):
    user32 = _HamisUser32()
    user32.elotér = PICASA
    monkeypatch.setattr(frissites_modul, "_ablakikonok", _ablakok)

    assert frissites_modul._eloterbe_hoz(1234, user32=user32, kernel32=_HamisKernel32()) == PICASA
    assert user32.hivasok == []


def test_a_kattintas_ellenorzi_hogy_a_pont_a_picasapy_ablakara_esik():
    forras = Path(frissites_modul.__file__).read_text(encoding="utf-8")
    kattintas = forras.split("def _valodi_eger_kattintas", 1)[1].split("\ndef ", 1)[0]
    pont = forras.split("def _pont_folyamata", 1)[1].split("\ndef ", 1)[0]
    assert "_pont_folyamata(" in kattintas and "gazda != pid" in kattintas
    assert "WindowFromPoint" in pont
    assert "_eloterbe_hoz(pid)" in kattintas
