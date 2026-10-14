"""Egységteszt a közös feltétel-várakozáshoz (#4970).

A segédnek három dolgot kell tudnia: a korlátot a környezeti szorzóval
növeli, hibás szorzó esetén az alapértéken marad, és a feltétel teljesülésekor
azonnal visszatér. Az órát és az alvást hamisítjuk, így a teszt nem függ a
gép terhelésétől.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from tests.support import varakozas
from tests.support.varakozas import (
    IDOSZORZO_ENV,
    hibaturo_feltetel,
    idoszorzo,
    var_feltetelre,
)


class _HamisOra:
    """Az `time.monotonic` és `time.sleep` helyettesítője: az alvás előreviszi az órát."""

    def __init__(self) -> None:
        self.most = 0.0
        self.alvasok = 0

    def monotonic(self) -> float:
        return self.most

    def sleep(self, masodperc: float) -> None:
        self.alvasok += 1
        self.most += masodperc


class _HamisQtApp:
    def __init__(self) -> None:
        self.esemenyciklusok = 0

    def processEvents(self) -> None:
        self.esemenyciklusok += 1


@pytest.fixture
def ora(monkeypatch):
    hamis = _HamisOra()
    monkeypatch.setattr(
        varakozas,
        "time",
        SimpleNamespace(monotonic=hamis.monotonic, sleep=hamis.sleep),
    )
    return hamis


@pytest.mark.parametrize("ertek", ["2", "2.0", " 2 "])
def test_a_szorzo_megnoveli_a_korlatot(monkeypatch, ertek):
    monkeypatch.setenv(IDOSZORZO_ENV, ertek)
    assert idoszorzo() == pytest.approx(2.0)


@pytest.mark.parametrize("ertek", ["", "nem-szam", "nan", "inf", "0", "-3"])
def test_hibas_szorzo_eseten_az_alap_1_0(monkeypatch, ertek):
    monkeypatch.setenv(IDOSZORZO_ENV, ertek)
    assert idoszorzo() == 1.0


def test_szorzo_nelkul_az_alap_1_0(monkeypatch):
    monkeypatch.delenv(IDOSZORZO_ENV, raising=False)
    assert idoszorzo() == 1.0


def test_a_korlat_a_szorzoval_nyulik(monkeypatch, ora):
    monkeypatch.setenv(IDOSZORZO_ENV, "3")
    qt_app = _HamisQtApp()

    eredmeny = var_feltetelre(qt_app, lambda: False, masodperc=2.0)

    assert eredmeny is False
    assert ora.most == pytest.approx(6.0, abs=0.05)


def test_hibas_szorzo_mellett_az_eredeti_korlat_ervenyes(monkeypatch, ora):
    monkeypatch.setenv(IDOSZORZO_ENV, "nem-szam")
    qt_app = _HamisQtApp()

    var_feltetelre(qt_app, lambda: False, masodperc=2.0)

    assert ora.most == pytest.approx(2.0, abs=0.05)


def test_alapertelmezett_korlat_tiz_masodperc(monkeypatch, ora):
    monkeypatch.delenv(IDOSZORZO_ENV, raising=False)

    var_feltetelre(_HamisQtApp(), lambda: False)

    assert ora.most == pytest.approx(10.0, abs=0.05)


def test_a_teljesulo_feltetelnel_azonnal_visszater(monkeypatch, ora):
    monkeypatch.delenv(IDOSZORZO_ENV, raising=False)
    qt_app = _HamisQtApp()
    hivasok = []

    def feltetel() -> bool:
        hivasok.append(1)
        return True

    assert var_feltetelre(qt_app, feltetel, masodperc=10.0) is True
    assert len(hivasok) == 1
    assert ora.alvasok == 0
    assert ora.most == 0.0


def test_a_feltetel_masodik_kiertekeleserre_teljesul_es_megall(monkeypatch, ora):
    monkeypatch.delenv(IDOSZORZO_ENV, raising=False)
    qt_app = _HamisQtApp()
    hivasok = []

    def feltetel() -> bool:
        hivasok.append(1)
        return len(hivasok) >= 2

    assert var_feltetelre(qt_app, feltetel, masodperc=10.0) is True
    assert len(hivasok) == 2
    assert ora.alvasok == 1


def test_az_esemenyciklus_porog_kozben_pörög(monkeypatch, ora):
    monkeypatch.delenv(IDOSZORZO_ENV, raising=False)
    qt_app = _HamisQtApp()

    var_feltetelre(qt_app, lambda: False, masodperc=0.1)

    assert qt_app.esemenyciklusok >= 1


def test_hibaturo_feltetel_a_hibat_hamisnak_veszi(monkeypatch, ora):
    monkeypatch.delenv(IDOSZORZO_ENV, raising=False)

    def hibas() -> bool:
        raise AttributeError("a widget még nincs kész")

    assert hibaturo_feltetel(hibas)() is False
    assert hibaturo_feltetel(lambda: True)() is True
    assert var_feltetelre(_HamisQtApp(), hibaturo_feltetel(hibas), masodperc=1.0) is False
