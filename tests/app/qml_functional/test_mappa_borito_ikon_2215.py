"""#2215 — bekapcsolt indexképeknél a sor NEM maradhat üresen.

A #2049 QML-őre csak azt mérte, hogy a sor **kér-e** borítót. Azt nem,
hogy a felhasználó **lát-e** valamit. Emiatt maradt észrevétlen, hogy
borító nélküli mappán a mappaikon is eltűnik: a szolgáltató 1×1 átlátszó
képet adott, ami sikeresen betöltődik, tehát a `boritoLatszik` igaz lett.

A felhasználó jelentette (2026-09-03): bekapcsolt kapcsoló mellett a bal
hasáb sorain nincs semmi.
"""

from __future__ import annotations

import time

from PySide6.QtCore import QMetaObject, QObject, Qt
from PySide6.QtQuick import QQuickItem


def _walk(item: QQuickItem):
    for gy in item.childItems():
        yield gy
        yield from _walk(gy)


def _nevvel_kezdodo(window, elotag: str) -> list:
    talalt = []
    gyoker = window.contentItem() if hasattr(window, "contentItem") else window
    for elem in _walk(gyoker):
        nev = elem.objectName()
        if nev and nev.startswith(elotag):
            talalt.append(elem)
    return talalt


def _trigger(root, nev):
    obj = root.findChild(QObject, nev)
    assert obj is not None, f"nincs ilyen elem: {nev}"
    QMetaObject.invokeMethod(obj, "triggered", Qt.ConnectionType.DirectConnection)


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


class TestASorSOSEM_marad_uresen:
    """A lényeg: van ikon VAGY van borító — de valami mindig látszik."""

    def test_bekapcsolva_minden_sorON_van_valami(self, qml_app, qt_app):
        window, _controller, _e = qml_app
        assert _var(
            qt_app, lambda: len(_nevvel_kezdodo(window, "folderRowCover")) > 0
        ), "egyetlen fasor sem épült fel"

        _trigger(window, "menuViewAlbumThumbnails")
        qt_app.processEvents()
        # a borítók aszinkron töltődnek — hagyunk időt a `status` beállására
        _var(qt_app, lambda: False, 1.0)

        uresek = []
        for tarolo in _nevvel_kezdodo(window, "folderRowCover"):
            if not tarolo.isVisible():
                continue
            latszo = [
                gy
                for gy in _walk(tarolo)
                if gy.isVisible() and gy.width() > 0 and gy.height() > 0
            ]
            if not latszo:
                uresek.append(tarolo.objectName())
        assert not uresek, (
            "bekapcsolt indexképeknél üresen maradt sorok (se ikon, se "
            f"borító): {uresek[:5]}"
        )

    def test_bekapcsolva_is_LATSZIK_ikon_ott_ahol_nincs_borito(
        self, qml_app, qt_app
    ):
        """Ahol a borító nem jött létre, a mappaikonnak kell látszania."""
        window, _controller, _e = qml_app
        assert _var(
            qt_app, lambda: len(_nevvel_kezdodo(window, "folderRowIcon")) > 0
        )
        _trigger(window, "menuViewAlbumThumbnails")
        qt_app.processEvents()
        _var(qt_app, lambda: False, 1.0)

        hibas = []
        for tarolo in _nevvel_kezdodo(window, "folderRowCover"):
            if not tarolo.isVisible():
                continue
            if tarolo.property("boritoLatszik"):
                continue  # itt valódi borító van — rendben
            ikonok = [
                gy for gy in _walk(tarolo) if gy.objectName() == "folderRowIcon"
            ]
            if ikonok and not ikonok[0].isVisible():
                hibas.append(tarolo.objectName())
        assert not hibas, (
            "borító nélküli sorokon a mappaikon is el van rejtve: "
            f"{hibas[:5]}"
        )


class TestAKikapcsoltAllapotValtozatlan:
    """⚠️ A javítás nem billentheti át a kikapcsolt alapállapotot."""

    def test_kikapcsolva_a_mappaikon_latszik(self, qml_app, qt_app):
        window, _controller, _e = qml_app
        assert _var(
            qt_app, lambda: len(_nevvel_kezdodo(window, "folderRowIcon")) > 0
        )
        latszo = [
            i for i in _nevvel_kezdodo(window, "folderRowIcon") if i.isVisible()
        ]
        assert latszo, "kikapcsolt állapotban egyetlen mappaikon sem látszik"
