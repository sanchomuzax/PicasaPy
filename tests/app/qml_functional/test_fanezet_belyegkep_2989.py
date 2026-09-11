"""#2989: a FANÉZETBEN a bélyegkép a kapcsolótól függetlenül látszik.

A tulajdonos 3. felvételén
(`research/#2984-indexkepek-mappa-ikonokon/3-fastrukturaju-mappanezet-indexkepek-mindig.png`)
az „Indexképek megjelenítése a könyvtárban" menütétel **SZÜRKE**, a
bélyegképek mégis ott vannak a fasorokon. Tehát a `ShowAlbumThumbnails2`
kizárólag az egydimenziós listára vonatkozik — a fában a kép mindig jön.

Nálunk a #2049 óta a fasor is a kapcsolóra kötött, a menütétel pedig
mindig kattintható volt; ez a két eltérés a jegy 2. és 3. pontja.
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
    return [
        it
        for it in _walk(window.contentItem())
        if (it.objectName() or "").startswith(elotag)
    ]


def _trigger(root, nev):
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


class TestAMenuteteltALetiltas:
    def test_egydimenzios_nezetben_ENGEDELYEZETT(self, qml_app, qt_app):
        window, _controller, _e = qml_app
        tetel = window.findChild(QObject, "menuViewAlbumThumbnails")
        assert tetel is not None
        assert tetel.property("enabled") is True

    def test_fanezetben_SZURKE(self, qml_app, qt_app):
        window, _controller, _e = qml_app
        tetel = window.findChild(QObject, "menuViewAlbumThumbnails")
        _trigger(window, "menuViewTreeView")
        assert _var(qt_app, lambda: tetel.property("enabled") is False), (
            "a fanézetben is kattintható maradt az „Indexképek megjelenítése "
            "a könyvtárban"
        )

    def test_vissza_a_listara_ujra_ENGEDELYEZETT(self, qml_app, qt_app):
        window, _controller, _e = qml_app
        tetel = window.findChild(QObject, "menuViewAlbumThumbnails")
        _trigger(window, "menuViewTreeView")
        assert _var(qt_app, lambda: tetel.property("enabled") is False)
        _trigger(window, "menuViewFlatFolderView")
        assert _var(qt_app, lambda: tetel.property("enabled") is True), (
            "a listanézetben szürke maradt a tétel"
        )


class TestAFasorKepe:
    def test_a_KIKAPCSOLT_kapcsolo_mellett_is_KER_kepet(self, qml_app, qt_app):
        """A fasor forrása nem az `albumThumbs`-tól függ (#2989/2.)."""
        window, _controller, _e = qml_app
        tetel = window.findChild(QObject, "menuViewAlbumThumbnails")
        assert tetel.property("checked") is False, "a kapcsoló nem KI-ben indul"

        _trigger(window, "menuViewTreeView")
        assert _var(
            qt_app,
            lambda: any(
                k.property("source").toString().startswith("image://foldercover/")
                for k in _nevvel_kezdodo(window, "hierFolderCoverImage")
            ),
        ), "kikapcsolt kapcsolóval egyetlen fasor sem kér bélyegképet"
