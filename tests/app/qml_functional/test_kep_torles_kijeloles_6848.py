"""Törlés után a következő kép marad kijelölve (#6848)."""

from pathlib import Path

import pytest

from tests.app.qml_functional._mappa_kep_menu_5150_helpers import app_epitese, elokeszit, varj
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    gyerek, jobbklikk_fotón, kattints,
)


@pytest.fixture
def app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path)


def test_torles_utan_kovetkezo_kep_kijelolve(app, qt_app, monkeypatch, tmp_path):
    window, controller, _ = app
    source = elokeszit(window, qt_app, controller)
    monkeypatch.setattr('picasapy.fileops.trash.find_trash_dir', lambda *_a, **_k: tmp_path / 'trash')
    original = Path(controller.photos.filePathAt(1))
    successor = Path(controller.photos.filePathAt(2))
    jobbklikk_fotón(window, qt_app, 1)
    kattints(window, qt_app, gyerek(window, 'contextMenuDelete'))
    dialog = gyerek(window, 'deleteConfirmDialog')
    assert varj(qt_app, lambda: dialog.property('visible'))
    kattints(window, qt_app, gyerek(window, 'confirmYesButton'))
    assert varj(qt_app, lambda: not original.exists() and controller.photos.rowCount() == 2)
    assert varj(qt_app, lambda: window.property('selectedIndex') >= 0 and
                Path(controller.photos.filePathAt(window.property('selectedIndex'))) == successor)
    assert len(list(source.glob('*.jpg'))) == 2
