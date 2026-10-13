"""#4597 — a `folderHideFailed` jelzés a felületen: a hibasáv szövege és
jellege (tájékoztatás / hiba) mindegyik okra."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject

_OKOK = {
    "offline-unhide": ("cannot be shown again while it is unavailable", True),
    "write-failed-unhide": ("could not be shown again", False),
    "write-failed-hide": ("could not be marked for Picasa", True),
    "hidden-move": ("cannot be moved into a collection", True),
}


@pytest.mark.parametrize("ok", sorted(_OKOK))
def test_hibasav_az_okot_mutatja(qml_app, qt_app, ok):
    window, controller, _engine = qml_app
    controller.folderHideFailed.emit("/valami", ok)
    qt_app.processEvents()
    szoveg = window.findChild(QObject, "errorBannerText").property("text")
    sav = window.findChild(QObject, "errorBanner")
    reszlet, tajekoztatas = _OKOK[ok]
    assert reszlet in szoveg, szoveg
    assert bool(sav.property("notice")) is tajekoztatas
