"""#6097: az első indításkori nyelvfelajánló ablak tényleg létrejön.

A párbeszéd a `PicasaStyle` modult importálja; a saját motorja importútvonal
nélkül nem találta meg, a `load` gyökérobjektum nélkül tért vissza, és a
kérdés csendben elmaradt (válasz: nem).
"""

from __future__ import annotations

from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

from picasapy.app import startup_language_prompt
from picasapy.app.application import allitsd_be_a_stilust


def test_a_nyelvfelajanlo_ablak_betoltodik(monkeypatch):
    app = QGuiApplication.instance() or QGuiApplication([])
    allitsd_be_a_stilust()
    gyokerek: list[int] = []

    class FigyeltMotor(QQmlApplicationEngine):
        def load(self, cim):
            super().load(cim)
            gyokerek.append(len(self.rootObjects()))

    monkeypatch.setattr(startup_language_prompt, "QQmlApplicationEngine", FigyeltMotor)
    startup_language_prompt.ask_startup_language_prompt("hu", timeout_ms=0)
    app.processEvents()

    assert gyokerek == [1]
