"""Törlés után a következő kép marad kijelölve (#6848)."""

import os
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from tests.app.qml_functional._mappa_kep_menu_5150_helpers import app_epitese, elokeszit, varj
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    gyerek, jobbklikk_fotón, kattints,
)


@pytest.fixture
def app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path)


@pytest.mark.parametrize("magassag_elteres", (-5, 0, 5))
def test_torles_megerositese_es_a_kovetkezo_kep_kijelolese(
    app, qt_app, monkeypatch, tmp_path, magassag_elteres
):
    window, controller, _ = app
    source = elokeszit(window, qt_app, controller)
    vart_magassag = window.height() + magassag_elteres
    window.setHeight(vart_magassag)
    assert varj(qt_app, lambda: window.height() == vart_magassag)
    monkeypatch.setattr('picasapy.fileops.trash.find_trash_dir', lambda *_a, **_k: tmp_path / 'trash')
    original = Path(controller.photos.filePathAt(1))
    successor = Path(controller.photos.filePathAt(2))
    jobbklikk_fotón(window, qt_app, 1)
    kattints(window, qt_app, gyerek(window, 'contextMenuDelete'))
    dialog = gyerek(window, 'deleteConfirmDialog')
    assert varj(qt_app, lambda: dialog.property('visible'))
    assert dialog.property('title') == 'Delete Items'
    assert dialog.property('message') == (
        'Are you sure you want to send the selected file to the Recycle Bin? '
        '(It will also be removed from any albums in which it appears)'
    )
    assert gyerek(window, 'confirmRememberCheck').property('text') == (
        "Don't ask again, always remove"
    )
    assert gyerek(window, 'confirmYesButton').property('text') == 'Delete Image'
    assert gyerek(window, 'confirmNoButton').property('visible') is False
    assert gyerek(window, 'confirmCancelButton').property('visible') is True
    cancel = gyerek(window, 'confirmCancelButton')
    assert varj(qt_app, lambda: cancel.property('activeFocus') is True), (
        f"Cancel nem kapott fókuszt: fókuszkérés={dialog.property('focusCancelOnOpen')}, "
        f"gombfókusz={cancel.property('focus')}, "
        f"ablak fókuszelemm={window.property('activeFocusItem')}"
    )
    kep = os.environ.get("PICASAPY_6848_TORLES_KEP")
    if kep:
        assert cancel.window().grabWindow().save(kep)
    QTest.keyClick(window, Qt.Key.Key_Return)
    assert varj(qt_app, lambda: not dialog.property('visible'))
    assert original.exists(), 'Enter a biztonságos Cancel gomb helyett törölt'

    jobbklikk_fotón(window, qt_app, 1)
    kattints(window, qt_app, gyerek(window, 'contextMenuDelete'))
    assert varj(qt_app, lambda: dialog.property('visible'))
    kattints(window, qt_app, gyerek(window, 'confirmYesButton'))
    assert varj(qt_app, lambda: not original.exists() and controller.photos.rowCount() == 2)
    assert varj(qt_app, lambda: window.property('selectedIndex') >= 0 and
                Path(controller.photos.filePathAt(window.property('selectedIndex'))) == successor)
    assert len(list(source.glob('*.jpg'))) == 2
