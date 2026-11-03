"""#6475: a képernyőmentés után a bal hasáb Projektek része KIRAJZOLJA a
Képernyőfelvételek mappát (valódi mentés, valódi vezérlő, renderelt hasáb).
"""

from __future__ import annotations

import os
import time
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject
from PySide6.QtGui import QColor, QImage


def _var(qt_app, feltetel, masodperc: float = 15.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        if feltetel():
            return True
        qt_app.processEvents()
        time.sleep(0.02)
    return bool(feltetel())


def _projektek(pane) -> list:
    modell = pane.property("projectFolders")
    return modell.toVariant() if hasattr(modell, "toVariant") else list(modell or [])


def test_a_mentes_utan_a_projektek_alatt_kirajzolodik(qml_app, qt_app, tmp_path):
    from picasapy.app.screen_capture import save_screenshot

    window, controller, _engine = qml_app
    window.resize(1280, 800)
    cel = tmp_path / "Rendszerkepek" / "Picasa" / "Képernyőfelvételek"
    kep = QImage(320, 200, QImage.Format.Format_RGB888)
    kep.fill(QColor(30, 120, 200))
    ut = save_screenshot(kep, cel, "Jegyzettomb", datetime(2026, 11, 3, 10, 0))

    controller.indexScreenCapture(str(ut))

    pane = window.findChild(QObject, "folderPane")
    assert _var(qt_app, lambda: any(Path(p["path"]) == cel for p in _projektek(pane))), (
        "a Képernyőfelvételek nem jelent meg a hasáb Projektek részében"
    )
    ismetlo = window.findChild(QObject, "projectFolderRepeater")
    assert ismetlo.property("count") >= 1
    sor = next(p for p in _projektek(pane) if Path(p["path"]) == cel)
    assert sor["name"] == "Képernyőfelvételek"

    kimenet = os.environ.get("PICASAPY_RENDER_KIMENET")
    if kimenet:
        for _ in range(5):
            qt_app.processEvents()
        Path(kimenet).mkdir(parents=True, exist_ok=True)
        window.grabWindow().save(str(Path(kimenet) / "kepernyokep-projekt-6475.png"))
