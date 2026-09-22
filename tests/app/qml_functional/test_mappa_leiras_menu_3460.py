"""#3460: a menüsor Mappa ▸ Leírás szerkesztése… tétele működik.

Eddig szürke helyőrző volt, pedig ugyanez a parancs (`album.fen`, #422) a
mappa helyi menüjéből működött. Most a megnyitott mappára ugyanazt a
párbeszédet nyitja; album és személy nézetében — ahol nincs „a" mappa —
tiltott.
"""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject, Qt


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


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
    assert tetel.property("enabled") is True
    _kattint(window, qt_app, "menuFolderEditDescription")
    parbeszed = _child(window, "folderPropertiesDialog")
    try:
        assert parbeszed.property("opened") is True
        assert parbeszed.property("mode") == "folder"
        assert parbeszed.property("folderPath") == mappa
    finally:
        QMetaObject.invokeMethod(parbeszed, "close", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()


def test_album_nezetben_a_tetel_tiltott(qml_app, qt_app):
    window, controller, _engine = qml_app
    _mappa_nezet(window, controller, qt_app)
    sav = window.property("menuBar")
    sav.setProperty("currentAlbumToken", "604c294a68b0de9cc9222c4714f289d5")
    qt_app.processEvents()
    assert _child(window, "menuFolderEditDescription").property("enabled") is False


def test_mappa_nelkul_a_tetel_tiltott(qml_app, qt_app):
    window, _controller, _engine = qml_app
    sav = window.property("menuBar")
    sav.setProperty("currentFolder", "")
    qt_app.processEvents()
    assert _child(window, "menuFolderEditDescription").property("enabled") is False
