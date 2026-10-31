"""Regresszióőrök a kattintás előtti animációs várakozáshoz (#6318)."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF

from tests.support import qt_wait


class _FakeApp:
    def processEvents(self):
        pass


class _FakeClock:
    def __init__(self):
        self.ido = 0.0
        self.szunetek = []

    def monotonic(self):
        return self.ido

    def sleep(self, masodperc):
        self.szunetek.append(masodperc)
        self.ido += masodperc


class _FakeWindow:
    def width(self):
        return 800

    def height(self):
        return 600


class _FakeItem:
    def __init__(self, positions, clock=None):
        self.positions = iter(positions)
        self.last_position = QPointF(0, 0)
        self.sample_count = 0
        self.clock = clock
        self.sample_times = []

    def isVisible(self):
        return True

    def boundingRect(self):
        return QRectF(0, 0, 10, 10)

    def mapToScene(self, point):
        self.sample_count += 1
        if self.clock is not None:
            self.sample_times.append(self.clock.monotonic())
        try:
            self.last_position = next(self.positions)
        except StopIteration:
            pass
        return self.last_position + point

    def objectName(self):
        return "animatedTarget"


def test_varj_ablakon_belulre_megvarja_a_stabil_helyzetet(monkeypatch):
    ora = _FakeClock()
    monkeypatch.setattr(qt_wait, "time", ora)
    item = _FakeItem(
        [
            QPointF(900, 100),
            QPointF(100, 100),
            QPointF(120, 100),
            QPointF(140, 100),
            QPointF(160, 100),
            QPointF(160, 100),
            QPointF(160, 100),
        ],
        clock=ora,
    )

    assert qt_wait.varj_ablakon_belulre(
        _FakeApp(), _FakeWindow(), item, masodperc=1.0
    )
    assert item.sample_count == 7
    assert all(
        kovetkezo - elozo >= 0.049
        for elozo, kovetkezo in zip(
            item.sample_times, item.sample_times[1:], strict=False
        )
    )
    assert len(ora.szunetek) >= 2
    assert sum(ora.szunetek) >= 0.2


def test_varj_kattinthatora_idotullepesi_uzenete_helyet_es_ablakmeretet_ad(
    monkeypatch,
):
    monkeypatch.setattr(qt_wait.QCoreApplication, "instance", lambda: _FakeApp())
    monkeypatch.setattr(qt_wait, "time", _FakeClock())
    item = _FakeItem([QPointF(900, 700)])

    try:
        qt_wait.varj_kattinthatora(_FakeWindow(), item, masodperc=0.0)
    except AssertionError as error:
        uzenet = str(error)
    else:
        raise AssertionError("a látható ablakon kívüli kattintási cél elfogadható")

    assert "határidőn belül sem került az ablakon belülre" in uzenet
    assert "helyzet=" in uzenet
    assert "ablak=800x600" in uzenet
