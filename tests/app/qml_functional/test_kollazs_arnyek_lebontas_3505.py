"""#3505 — a kollázslap árnyék-kötése a lebontáskor ne írjon hibát.

## A mérés

A napló sora: `CollageSheet.qml:94: TypeError: Property 'collageShadowSprite'
of object TypeError: Type error is not a function`.

- A teszt ÉLETE alatt a hiba NEM jelenik meg: a `qml_warnings` őr pontosan
  erre a mintára hasalna el, és a próbák zöldek; célzott méréssel is (a
  piszkozat visszaállítása után, telepített üzenetkezelővel) a lapon
  `shadowVisible == True` és az árnyék-csempe megvan — **az árnyék nem
  marad el**.
- A sor a folyamat LEGVÉGÉN jön, amikor a Python-oldali vezérlő már
  lebomlott, de a QML-elem még egyszer újraértékeli a kötését: a
  `controller` ekkor egy félig lebontott objektum, aminek a metódusa már
  nem hívható (a nevét sem tudja kiírni — innen a „TypeError: Type
  error" az objektum helyén).

## A javítás

A kötés csak akkor hívja a slotot, ha az tényleg függvény. Ez a mért
helyzetet fedi le: egy vezérlő, aminek nincs (már) `collageShadowSprite`
metódusa. A próba ugyanezt állítja elő a futó lapon: a lap vezérlőjét
egy ilyen objektumra cseréli, és a naplót figyeli.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import (
    Property, QMetaObject, QObject, Qt, qInstallMessageHandler,
)

from tests.app.qml_functional.test_collage_draft_restore_1051 import (  # noqa: F401
    VISSZAALLIT, _gomb, draft, draft_dir,
)


class _FeligLebontott(QObject):
    """A lebontás pillanatának mása: az árnyék ADATA még olvasható (a lap
    a régi értéket tartja), a csempét adó metódus viszont már nincs."""

    @Property("QVariantMap", constant=True)
    def collageShadow(self):  # noqa: N802 — a valódi vezérlő neve
        return {"offsetX": 0.01, "offsetY": 0.01, "blur": 0.01,
                "opacity": 0.5, "alpha": 128}


def _lap(window):
    lapok = [
        o for o in window.findChildren(QObject)
        if o.metaObject().className().startswith("CollageSheet")
    ]
    assert len(lapok) == 1, lapok
    return lapok[0]


#: a piszkozat-fixture a #1051 próbáiból jön (importálva)
@pytest.mark.usefixtures("draft")
def test_a_visszaallitott_lapon_az_arnyek_megvan(qml_app, qt_app):
    window, _controller, _ = qml_app
    QMetaObject.invokeMethod(
        _gomb(window, VISSZAALLIT), "clicked", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()

    lap = _lap(window)

    assert lap.property("shadowVisible") is True
    assert lap.property("shadowSprite")


@pytest.mark.usefixtures("draft")
def test_slot_nelkuli_vezerlonel_nincs_hiba(qml_app, qt_app):
    """A lebontás pillanatának mása: a vezérlő él, de a metódusa nincs."""
    window, _controller, _ = qml_app
    QMetaObject.invokeMethod(
        _gomb(window, VISSZAALLIT), "clicked", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()
    lap = _lap(window)
    uzenetek = []
    regi = qInstallMessageHandler(lambda _t, _c, m: uzenetek.append(m))
    helyettes = _FeligLebontott()
    try:
        lap.setProperty("controller", helyettes)
        qt_app.processEvents()
    finally:
        qInstallMessageHandler(regi)

    assert not [m for m in uzenetek if "collageShadowSprite" in m], uzenetek
    assert not lap.property("shadowSprite")
