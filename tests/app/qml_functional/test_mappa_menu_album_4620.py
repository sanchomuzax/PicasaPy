"""#4620: a felső Mappa menü műveletei ne érjék el az előző mappát albumból."""

from __future__ import annotations

from PySide6.QtCore import QObject


_ALBUM_TOKEN = "604c294a68b0de9cc9222c4714f289d5"
_MAPPA_MUVELETEK = (
    "menuFolderLocate",
    "menuFolderRemoveFromPicasa",
    "menuFolderMove",
    "menuFolderDelete",
)


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def test_mappa_menu_muveletek_album_es_mappanezetben(qml_app, qt_app):
    window, controller, _engine = qml_app
    korabbi_mappa = controller.currentFolder
    assert korabbi_mappa, "a funkcionális próba mappanézetből indul"
    alapmagassag = int(window.height())

    for eltolás in (-5, 0, 5):
        window.setHeight(alapmagassag + eltolás)
        qt_app.processEvents()
        assert int(window.height()) == alapmagassag + eltolás

        # Mappanézetben a négy művelet továbbra is a megnyitott mappára él.
        assert controller.currentAlbumToken == ""
        for nev in _MAPPA_MUVELETEK:
            assert _child(window, nev).property("enabled") is True

        # Az album megnyitása után a controller a korábbi mappa útvonalát
        # megtartja; a Mappa menü műveletei ettől még legyenek tiltva.
        controller.showAlbum(_ALBUM_TOKEN)
        qt_app.processEvents()
        assert controller.currentAlbumToken == _ALBUM_TOKEN
        assert controller.currentFolder == korabbi_mappa
        for nev in _MAPPA_MUVELETEK:
            assert _child(window, nev).property("enabled") is False, nev

        # Visszatéréskor a mappanézet műveletei ismét aktívak.
        controller.clearFilter()
        qt_app.processEvents()
        assert controller.currentAlbumToken == ""
        assert controller.currentFolder == korabbi_mappa
        for nev in _MAPPA_MUVELETEK:
            assert _child(window, nev).property("enabled") is True
