"""Az „Új album" alapértelmezett neve a HONOSÍTÁSBÓL jön (#2911).

A mérés szerint az eredeti a nevet az `IDS_DEFAULT_ALBUM_NAME`
szöveg-erőforrásból tölti (`0x0055cfb2 push 0x8a`), tehát a felület
nyelvén jelenik meg — nálunk ugyanígy a `FileOpsDialogs` `Untitled`
feliratából, magyarul **„Névtelen"**.

⚠️ Külön modul, mert a `.qm` betöltése Qt-fordítót igényel; a QML-oldali
őr (`test_album_context_menu.py`) a felület SAJÁT feliratához hasonlít,
így egyik próba sem függ a másik környezetétől.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import picasapy.app

_I18N_DIR = Path(picasapy.app.__file__).parent / "i18n"


@pytest.fixture(scope="module")
def forditas():
    from PySide6.QtCore import QCoreApplication, QTranslator

    QCoreApplication.instance() or QCoreApplication([])
    translator = QTranslator()
    assert translator.load("picasapy_hu", str(_I18N_DIR)), (
        "a picasapy_hu.qm nem tölthető be — lefuttattad a pyside6-lrelease-t?"
    )
    return translator


def test_az_uj_album_neve_magyarul_Nevtelen(forditas):
    assert forditas.translate("FileOpsDialogs", "Untitled") == "Névtelen"
