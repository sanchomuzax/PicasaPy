"""#3460/#4630: a menüsor Mappa/Album ▸ Leírás szerkesztése… tétele működik.

Eddig szürke helyőrző volt, pedig ugyanez a parancs (`album.fen`, #422) a
mappa helyi menüjéből működött. Mappanézetben a megnyitott mappára nyitja a
párbeszédet; albumnézetben a #4630 szerint aktív és az album tulajdonságaira
vált. Személynézetben — ahol nincs „a" mappa vagy album — tiltott.
"""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject, Qt


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _mappa_menu(window):
    for obj in window.findChildren(QObject):
        if obj.property("title") == "F&older":
            return obj
    raise AssertionError("a felső Mappa menü nem található")


def _kattint(window, qt_app, nev):
    QMetaObject.invokeMethod(_child(window, nev), "click", Qt.ConnectionType.DirectConnection)
    for _ in range(5):
        qt_app.processEvents()


def _mappa_nezet(window, controller, qt_app):
    """A fixture a könyvtár mappáját nyitja meg — erre vonatkozik a tétel."""
    qt_app.processEvents()
    return controller.property("currentFolder")


def test_mappanezetben_a_tetel_a_megnyitott_mappa_parbeszedet_nyitja(qml_app, qt_app):
    window, controller, _engine = qml_app
    mappa = _mappa_nezet(window, controller, qt_app)
    assert mappa
    tetel = _child(window, "menuFolderEditDescription")
    alapmagassag = int(window.height())
    for eltolás in (-5, 0, 5):
        window.setHeight(alapmagassag + eltolás)
        qt_app.processEvents()
        assert int(window.height()) == alapmagassag + eltolás
        assert _mappa_menu(window).property("title") == "F&older"
        assert tetel.property("enabled") is True
        assert tetel.property("text") == "&Edit Description..."
        _kattint(window, qt_app, "menuFolderEditDescription")
        parbeszed = _child(window, "folderPropertiesDialog")
        try:
            assert parbeszed.property("opened") is True
            assert parbeszed.property("mode") == "folder"
            assert parbeszed.property("folderPath") == mappa
        finally:
            QMetaObject.invokeMethod(parbeszed, "close", Qt.ConnectionType.DirectConnection)
            qt_app.processEvents()


def test_album_nezetben_a_tetel_aktiv(qml_app, qt_app):
    window, controller, _engine = qml_app
    _mappa_nezet(window, controller, qt_app)
    sav = window.property("menuBar")
    sav.setProperty("currentAlbumToken", "604c294a68b0de9cc9222c4714f289d5")
    alapmagassag = int(window.height())
    for eltolás in (-5, 0, 5):
        window.setHeight(alapmagassag + eltolás)
        qt_app.processEvents()
        assert int(window.height()) == alapmagassag + eltolás
        assert _child(window, "menuFolderEditDescription").property("enabled") is True


def test_mappa_nelkul_a_tetel_tiltott(qml_app, qt_app):
    window, _controller, _engine = qml_app
    sav = window.property("menuBar")
    sav.setProperty("currentFolder", "")
    qt_app.processEvents()
    assert _child(window, "menuFolderEditDescription").property("enabled") is False
