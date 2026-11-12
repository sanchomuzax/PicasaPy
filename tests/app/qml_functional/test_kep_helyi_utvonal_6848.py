"""A helyi menü útvonalmásolása a kijelölt képek számától függ (#6848)."""

import os

import pytest

from tests.app.qml_functional._mappa_kep_menu_5150_helpers import app_epitese, elokeszit
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    gyerek, jobbklikk_fotón, kijelol, zar,
)


@pytest.fixture
def app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path)


def test_teljes_utvonal_csak_egyetlen_kepnel_lathato(app, qt_app):
    window, controller, _ = app
    elokeszit(window, qt_app, controller)
    eredeti_magassag = window.height()
    for elteres in (-5, 0, 5):
        window.setHeight(eredeti_magassag + elteres)
        qt_app.processEvents()
        for sorok in ([0], [0, 1]):
            kijelol(window, qt_app, sorok)
            menu = jobbklikk_fotón(window, qt_app, 0)
            masolas = gyerek(window, 'contextMenuCopyFullPath')
            torles = gyerek(window, 'contextMenuDelete')
            kep = os.environ.get('PICASAPY_6848_KEP')
            if kep and elteres == 0 and len(sorok) == 2:
                assert masolas.window().grabWindow().save(kep)
            assert masolas.property('visible') is (len(sorok) == 1)
            if len(sorok) == 1:
                assert masolas.property('y') > torles.property('y')
            else:
                assert masolas.property('height') == 0
            zar(qt_app, menu)
