"""#4420: a bejáró megvárja a párbeszédablak tényleges bezárását."""

from __future__ import annotations

from PySide6.QtCore import QObject, QTimer

from tests.app.qml_functional import _fomenu_4420_akciok as _akciok
from tests.app.qml_functional._fomenu_bejaro_4420 import _zarj_parbeszedeket


def test_parbeszed_bezarasara_varakozik_a_lathato_allapot_vegeig(
    qt_app, monkeypatch
):
    """A lassabban bezáródó párbeszédet ne jelentse nyitva maradónak."""
    from PySide6.QtQuick import QQuickWindow

    ablak = QQuickWindow()
    ablak.show()
    qt_app.processEvents()
    dialogus = QObject()
    dialogus.setObjectName("kesleltetettDialog")
    dialogus.setProperty("visible", True)
    monkeypatch.setattr(
        _akciok,
        "_lathato_dialogusok",
        lambda _ablak: [dialogus] if dialogus.property("visible") else [],
    )
    # Az Escape után a QML bezárási átmenete csak később tünteti el az ablakot.
    QTimer.singleShot(1250, lambda: dialogus.setProperty("visible", False))
    naplo = []
    try:
        _zarj_parbeszedeket(ablak, qt_app, naplo)
    finally:
        ablak.close()

    assert dialogus.property("visible") is False
    assert not any("nyitva maradt" in sor for sor in naplo), naplo
