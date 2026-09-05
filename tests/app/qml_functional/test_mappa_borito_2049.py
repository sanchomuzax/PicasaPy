"""#2049: a bal hasáb fasorain fotó-kupac áll a mappaikon helyett.

A kapcsoló az eredetiben `Preferences` ▸ `ShowAlbumThumbnails2`,
alapértéke **0** (`0x00761870`) — nálunk is kikapcsolva indul, ezért a
próbák a MENÜBŐL kapcsolják be, nem a vezérlő állapotát írják át.
"""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, Qt
from PySide6.QtQuick import QQuickItem


def _walk(item: QQuickItem):
    for gy in item.childItems():
        yield gy
        yield from _walk(gy)


def _nevvel_kezdodo(window, elotag: str) -> list:
    return [
        it
        for it in _walk(window.contentItem())
        if (it.objectName() or "").startswith(elotag)
    ]


def _trigger(root, nev):
    """A menütétel aktiválása — a VALÓDI kattintás két lépése (#1454): a
    `toggle()` IMPERATÍVAN írja a `checked`-et, és csak utána dördül el a
    `triggered`. Csak a jelzést kibocsátani a pipa viselkedését méretlenül
    hagyná — pedig épp ott volt hiba."""
    elem = root.findChild(QObject, nev)
    assert elem is not None, f"nincs meg a menütétel: {nev}"
    if elem.property("checkable"):
        QMetaObject.invokeMethod(elem, "toggle", Qt.ConnectionType.DirectConnection)
    QMetaObject.invokeMethod(elem, "triggered", Qt.ConnectionType.DirectConnection)
    return elem


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        try:
            if feltetel():
                return True
        except (AttributeError, TypeError, RuntimeError):
            pass
        qt_app.processEvents()
        time.sleep(0.005)
    return False


class TestAKapcsolo:
    def test_alapbol_KI_van_kapcsolva(self, qml_app, qt_app):
        window, _controller, _e = qml_app
        menu = window.findChild(QObject, "menuViewAlbumThumbnails")
        assert menu is not None, "nincs meg a menüpont a Nézet ▸ Mappanézet alatt"
        assert menu.property("checked") is False, (
            "a mappa-borítók alapból BE vannak kapcsolva — az eredeti "
            "ShowAlbumThumbnails2 alapértéke 0"
        )

    def test_a_menupont_atbillenti(self, qml_app, qt_app):
        window, _controller, _e = qml_app
        menu = _trigger(window, "menuViewAlbumThumbnails")
        qt_app.processEvents()
        assert _var(qt_app, lambda: menu.property("checked") is True), (
            "a menüpont nem kapcsolta be a borítókat"
        )

    def test_ketszer_kattintva_visszakapcsol(self, qml_app, qt_app):
        """#1464/#1468 rádió-csapda: a MÁR aktív tételre kattintva a pipa
        nem ragadhat be."""
        window, _controller, _e = qml_app
        menu = _trigger(window, "menuViewAlbumThumbnails")
        assert _var(qt_app, lambda: menu.property("checked") is True)
        _trigger(window, "menuViewAlbumThumbnails")
        assert _var(qt_app, lambda: menu.property("checked") is False), (
            "a második kattintás nem kapcsolta vissza"
        )


class TestAFasorBoritoja:
    def test_kikapcsolva_NINCS_boritokep(self, qml_app, qt_app):
        window, _controller, _e = qml_app
        assert _var(qt_app, lambda: len(_nevvel_kezdodo(window, "folderRowCover")) > 0), (
            "egyetlen fasor sem épült fel"
        )
        latszo = [
            k
            for k in _nevvel_kezdodo(window, "folderRowCoverImage")
            if k.isVisible()
        ]
        assert not latszo, "kikapcsolt állapotban is látszik borító"

    def test_kikapcsolva_a_szolgaltato_MEG_SEM_SZOLAL(self, qml_app, qt_app):
        """Üres forrással a kép `status`-a `Null` marad — a borító
        előállítása (négy JPEG dekódolása mappánként) el sem indul."""
        window, _controller, _e = qml_app
        assert _var(
            qt_app, lambda: len(_nevvel_kezdodo(window, "folderRowCoverImage")) > 0
        )
        for kep in _nevvel_kezdodo(window, "folderRowCoverImage"):
            assert kep.property("source").toString() == "", (
                f"kikapcsolva is kér borítót: {kep.property('source').toString()}"
            )

    def test_bekapcsolva_a_kepes_mappa_BORITOT_ker(self, qml_app, qt_app):
        window, controller, _e = qml_app
        _trigger(window, "menuViewAlbumThumbnails")
        qt_app.processEvents()

        lib = str(Path(controller.watchedFolders[0]))
        kerok = [
            k
            for k in _nevvel_kezdodo(window, "folderRowCoverImage")
            if k.property("source").toString().startswith("image://foldercover/")
        ]
        assert _var(qt_app, lambda: bool(kerok) or _ujra(window, kerok)), (
            f"bekapcsolva sem kér egyetlen sor sem borítót (könyvtár: {lib})"
        )


def _ujra(window, kerok) -> bool:
    kerok[:] = [
        k
        for k in _nevvel_kezdodo(window, "folderRowCoverImage")
        if k.property("source").toString().startswith("image://foldercover/")
    ]
    return bool(kerok)
