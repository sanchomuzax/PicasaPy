"""#3455: a menütételek gyorsbillentyűi egy JOBBRA IGAZÍTOTT oszlopban.

A feliratok `qsTr("…") + "\\tCtrl+S"` alakban hordozzák a gyorsbillentyűt.
A tabulátort a menütétel eddig szövegként rajzolta: a gyorsbillentyű a
felirat hosszától függő helyre került, a hosszú tételeknél ki is lógott a
menüből (a tulajdonos képernyőképén a „Forgatás balra" `Ctrl+Shift+R`-je
nem látszott, a „Törlés lemezről" `Ctrl+Delete`-je levágódott). Az eredeti
Picasa (Windows-menü) a gyorsbillentyűket közös, jobbra igazított oszlopba
teszi.

A menü csak NYITVA méri hűen a tételeket, ezért a teszt ténylegesen
megnyitja.
"""

from __future__ import annotations

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPointF, Qt

_TETELEK_GYORSBILLENTYUVEL = (
    "contextMenuOpen",
    "contextMenuRotateRight",
    "contextMenuRotateLeft",
    "contextMenuOpenFile",
    "contextMenuSave",
    "contextMenuDelete",
    "contextMenuProperties",
)


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _megnyit(window, qt_app):
    QMetaObject.invokeMethod(
        window, "openPhotoContextMenu", Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", 0), Q_ARG("QVariant", _child(window, "photoGrid")),
        Q_ARG("QVariant", 5), Q_ARG("QVariant", 5),
    )
    for _ in range(5):
        qt_app.processEvents()


def _bezar(window, qt_app):
    QMetaObject.invokeMethod(
        _child(window, "photoContextMenu"), "close", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()


def _gyorsbillentyu_jobb_szele(tetel):
    """A tétel gyorsbillentyű-részének jobb széle a TÉTEL koordinátáiban."""
    resz = _child(tetel, "menuTetelGyorsbillentyu")
    assert resz.property("text"), f"{tetel.objectName()}: üres gyorsbillentyű-rész"
    jobb = resz.mapToItem(tetel, QPointF(resz.property("width"), 0))
    return jobb.x()


def test_a_gyorsbillentyuk_jobb_szele_egy_vonalban_all(qml_app, qt_app):
    window, _controller, _engine = qml_app
    _megnyit(window, qt_app)
    try:
        szelek = {nev: _gyorsbillentyu_jobb_szele(_child(window, nev))
                  for nev in _TETELEK_GYORSBILLENTYUVEL}
        assert max(szelek.values()) - min(szelek.values()) <= 1.0, szelek
    finally:
        _bezar(window, qt_app)


def test_egy_gyorsbillentyu_sem_log_ki_a_tetelbol(qml_app, qt_app):
    window, _controller, _engine = qml_app
    _megnyit(window, qt_app)
    try:
        for nev in _TETELEK_GYORSBILLENTYUVEL:
            tetel = _child(window, nev)
            assert _gyorsbillentyu_jobb_szele(tetel) <= tetel.property("width") + 0.5, nev
    finally:
        _bezar(window, qt_app)


def test_a_felirat_nem_tartalmaz_tabulatort(qml_app, qt_app):
    """A felirat-rész csak a feliratot rajzolja — a gyorsbillentyű nem
    kerülhet bele másodszor."""
    window, _controller, _engine = qml_app
    _megnyit(window, qt_app)
    try:
        tetel = _child(window, "contextMenuSave")
        felirat = _child(tetel, "menuTetelFelirat").property("text")
        assert "\t" not in felirat and "Ctrl" not in felirat, felirat
        assert _child(tetel, "menuTetelGyorsbillentyu").property("text") == "Ctrl+S"
    finally:
        _bezar(window, qt_app)
