"""#4558: Shiftre a kilenc kétmódú csempe BÉLYEGKÉPE is a másodlagosra vált.

Eredeti (`ui-audit-editor.md`, „A második tokent a SHIFT billentyű
kapcsolja”): a csempe felirata ÉS bélyegképe az erőforrás-név `_mod%s`
utótagjával váltja a másodlagosat. Nálunk eddig csak a felirat és a hívás
váltott, a `thumbSource` az elsődleges effektnél maradt.

⚠️ Ez a teszt a bélyegkép-URL KULCSÁT méri (melyik effektet kéri a csempe).
A renderelt képek eltérését a `tests/app/test_shift_belyegkep_katalogus_4558.py`
méri; a spec szerint azonos kezelőjű párokat (`unsharp`/`unsharp2`,
`glow`/`glow2`) ott név szerint kezeljük — itt is csak a kulcsváltás a tét.
"""

from __future__ import annotations

import time

import numpy as np
import pytest
from PIL import Image
from PySide6.QtCore import QObject, Qt
from PySide6.QtTest import QTest

from tests.app.qml_functional.conftest import _build_qml_app

#: (fül, objektumnév, elsődleges, másodlagos)
CSEMPEK = [
    (2, "effectUnsharp", "unsharp2", "unsharp"),
    (2, "effectGrain2", "picnikgrain", "grain"),
    (2, "effectTint", "picniktint", "tint"),
    (2, "effectGlow2", "glow2", "glow"),
    (2, "effectDirTint", "dir_tint", "radtint"),
    (3, "effectHeatMap", "heatmap", "nightvision"),
    (4, "effectVignette", "vignette", "matte"),
    (4, "effectPixelate", "pixelate", "picnikfocalpixelate"),
    (4, "effectBorder", "border", "roundededges"),
]


def _kepeket_keszit(konyvtar):
    y, x = np.indices((200, 320), dtype=np.uint16)
    rgb = np.empty((200, 320, 3), dtype=np.uint8)
    rgb[..., 0] = (x * 3 + y) % 256
    rgb[..., 1] = (y * 2 + x // 2) % 256
    rgb[..., 2] = ((x // 16 + y // 16) % 2) * 220 + 20
    Image.fromarray(rgb, "RGB").save(
        konyvtar / "a.jpg", format="JPEG", quality=95, subsampling=0
    )


@pytest.fixture
def app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app, tmp_path, kepeket_keszit=_kepeket_keszit, valodi_belyegkep=True
    )


def _varj(qt_app, feltetel, uzenet, masodperc=5.0):
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return
        time.sleep(0.02)
    raise AssertionError(uzenet)


def _kulcs(csempe) -> str:
    """Az `image://effectthumb/<fotó>/<kulcs>?filters=…` URL effekt-kulcsa."""
    forras = csempe.property("thumbSource")
    forras = forras.toString() if hasattr(forras, "toString") else str(forras)
    return forras.split("?", 1)[0].rsplit("/", 1)[-1]


@pytest.mark.parametrize("ful,objektum,elso,masodik", CSEMPEK)
def test_shiftre_a_csempe_belyegkepe_a_masodlagosra_valt(
    app, qt_app, ful, objektum, elso, masodik
):
    ablak, _vezerlo, _engine = app
    ablak.setProperty("viewerOpen", True)
    nezo = ablak.findChild(QObject, "photoViewer")
    assert nezo is not None
    nezo.setProperty("currentIndex", 0)
    panel = ablak.findChild(QObject, "viewerEditorPanel")
    assert panel is not None
    panel.setProperty("activeTab", ful)
    _varj(qt_app, lambda: ablak.findChild(QObject, objektum) is not None,
          f"nincs {objektum} csempe")
    csempe = ablak.findChild(QObject, objektum)
    _varj(qt_app, lambda: _kulcs(csempe) == elso,
          f"Shift nélkül nem az elsődleges ({elso}) a bélyegkép: {_kulcs(csempe)!r}")

    QTest.keyPress(ablak, Qt.Key.Key_Shift)
    try:
        _varj(qt_app, lambda: _kulcs(csempe) == masodik,
              f"Shifttel nem a másodlagos ({masodik}) a bélyegkép: {_kulcs(csempe)!r}")
    finally:
        QTest.keyRelease(ablak, Qt.Key.Key_Shift)
    _varj(qt_app, lambda: _kulcs(csempe) == elso,
          f"Shift felengedése után nem állt vissza ({elso}): {_kulcs(csempe)!r}")
