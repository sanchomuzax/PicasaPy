"""#3448: az indexkép helyi menüjében a rejtett tételek NEM hagyhatnak rést.

A tulajdonos képernyőképén a „Hozzáadás albumhoz ▸" alatt kb. öt sornyi
üres hely állt: mappanézetben az album- és személy-album tételek
(`visible: false`) a Qt Quick menüjében megtartották a magasságukat. Az
eredeti Picasa ezeket a tételeket egyszerűen nem építi be a menübe
(`docs/specs/ui-audit-context-menus.md` B.3: a helyi menü KIVONÁSSAL
készül), tehát nem foglalhatnak helyet.

A menü csak NYITVA tükrözi hűen a tételek láthatóságát (zárva minden
gyerek `visible`-je hamis), ezért a teszt ténylegesen megnyitja.
"""

from __future__ import annotations

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt

_REJTETT_MAPPANEZETBEN = (
    "contextMenuRemoveFromAlbum",
    "contextMenuRemoveFromPeopleAlbum",
    "contextMenuAddToPeopleAlbum",
    "contextMenuMoveToNewPerson",
    "contextMenuSetAsPeopleAlbumThumbnail",
)


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _megnyit(window, qt_app, row=0):
    QMetaObject.invokeMethod(
        window, "openPhotoContextMenu", Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", row), Q_ARG("QVariant", _child(window, "photoGrid")),
        Q_ARG("QVariant", 5), Q_ARG("QVariant", 5),
    )
    qt_app.processEvents()


def _bezar(window, qt_app):
    QMetaObject.invokeMethod(
        _child(window, "photoContextMenu"), "close", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()


def test_a_rejtett_tetelek_magassaga_nulla(qml_app, qt_app):
    window, _controller, _engine = qml_app
    _megnyit(window, qt_app)
    try:
        for nev in _REJTETT_MAPPANEZETBEN:
            tetel = _child(window, nev)
            assert tetel.property("visible") is False, f"{nev} mappanézetben látszik"
            assert tetel.property("height") == 0, f"{nev} rejtve is {tetel.property('height')} magas"
    finally:
        _bezar(window, qt_app)


def test_a_forgatas_kozvetlenul_az_album_sor_utan_all(qml_app, qt_app):
    """A „Megjelenítés és szerkesztés" és a „Forgatás jobbra" között
    csak az album-sor és egy elválasztó állhat — öt üres sor nem."""
    window, _controller, _engine = qml_app
    _megnyit(window, qt_app)
    try:
        elso = _child(window, "contextMenuOpen")
        forgat = _child(window, "contextMenuRotateRight")
        sor = elso.property("height")
        assert sor > 0
        tavolsag = forgat.property("y") - elso.property("y")
        # Megnyitás + album-sor = 2 sor, plusz egy elválasztó (< 1 sor)
        assert tavolsag < 3 * sor, f"a forgatás {tavolsag / sor:.1f} sorral lejjebb van"
    finally:
        _bezar(window, qt_app)
