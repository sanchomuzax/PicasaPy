"""A Recently Updated sor csak nem üres album esetén látszik (#6892)."""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QObject

from picasapy.index import queries
from tests.support.varakozas import hibaturo_feltetel, var_feltetelre


class _Clock:
    """A hétnapos kapu idejét adja a teszt szinkronjainak."""

    def __init__(self, timestamp: float):
        self.timestamp = timestamp

    def time(self) -> float:
        return self.timestamp


@pytest.mark.parametrize("delta_h", [-5, 0, 5])
def test_recently_updated_sor_koveti_az_elemszamot(
    qml_app, qt_app, monkeypatch, delta_h
):
    window, controller, _engine = qml_app
    celmagassag = window.height() + delta_h
    window.setHeight(celmagassag)
    assert var_feltetelre(
        qt_app,
        hibaturo_feltetel(lambda: window.height() == celmagassag),
        5.0,
    ), "az ablak nem vette fel a tesztmagasságot"

    row = window.findChild(QObject, "recentlyUpdatedItem")
    header = window.findChild(QObject, "albumsHeader")
    assert row is not None, "recentlyUpdatedItem nem található"
    assert header is not None, "albumsHeader nem található"
    assert controller.recentlyUpdatedCount > 0
    assert row.isVisible(), "friss képnél a Recently Updated sornak látszania kell"
    assert header.property("text").endswith("(2)")

    eredeti_ido = queries.time
    most = time.time()
    monkeypatch.setattr(queries, "time", _Clock(most + 8 * 24 * 60 * 60))
    controller._reload_after_sync()
    assert var_feltetelre(
        qt_app,
        hibaturo_feltetel(
            lambda: controller.recentlyUpdatedCount == 0
            and not row.isVisible()
            and header.property("text").endswith("(1)")
        ),
        5.0,
    ), "a hét napnál régebbi képek után a Recently Updated sornak el kell tűnnie"

    monkeypatch.setattr(queries, "time", eredeti_ido)
    controller._reload_after_sync()
    assert var_feltetelre(
        qt_app,
        hibaturo_feltetel(
            lambda: controller.recentlyUpdatedCount > 0
            and row.isVisible()
            and header.property("text").endswith("(2)")
        ),
        5.0,
    ), "friss elem visszakerülésekor a Recently Updated sornak azonnal meg kell jelennie"
