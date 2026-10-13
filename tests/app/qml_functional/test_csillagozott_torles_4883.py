"""#4883 — a bal oldali Csillagozott album törlése csak a csillagot veszi le.

Spec: ``docs/specs/ui-audit-context-menus.md`` D.8. A binárisban a ``]star``
nem kap külön ágat: az általános album-eltávolítás fut, a fájl megmarad.
Ez a felületi út a csillag-szűrőtől külön mód; a szűrősáv nyitott kérdése
D.8.6 szerint változatlan marad.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QImage, QPainter
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree
from picasapy.ini import load_document, update_document
from support.jpeg_factory import make_jpeg
from support.qml_halasztott import epitsd_fel_ha_fileops


def _gyerek(window, nev):
    epitsd_fel_ha_fileops(window, nev)
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"a(z) {nev} nem található"
    return elem


def _katt(window, elem) -> None:
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        window, Qt.LeftButton, Qt.NoModifier, QPoint(int(pont.x()), int(pont.y()))
    )


def _fokusz(elem, qt_app) -> None:
    elem.setProperty("focus", True)
    QMetaObject.invokeMethod(
        elem, "forceActiveFocus", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()


def _csillagozott_nezet(window, controller, qt_app, fajlnevek):
    mappa = Path(controller.watchedFolders[0])
    ini = mappa / ".picasa.ini"

    def csillagoz(dokumentum):
        for fajlnev in fajlnevek:
            dokumentum = dokumentum.with_value(fajlnev, "star", "yes")
        return dokumentum

    update_document(ini, csillagoz)
    with open_index(controller._db_path) as conn:
        sync_tree(conn, mappa)
    controller._reload_after_sync()
    qt_app.processEvents()

    # A valódi bal oldali különleges albumot választja ki, nem a ★ szűrőt.
    _katt(window, _gyerek(window, "starredItem"))
    qt_app.processEvents()
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    return mappa, ini


def _csillag_ertek(ini: Path, fajlnev: str):
    szakasz = load_document(ini).section(fajlnev)
    return szakasz.get("star") if szakasz is not None else None


def _menu_nyit(window, qt_app, sor=0):
    grid = _gyerek(window, "photoGrid")
    QMetaObject.invokeMethod(
        window,
        "openPhotoContextMenu",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", sor),
        Q_ARG("QVariant", grid),
        Q_ARG("QVariant", 5),
        Q_ARG("QVariant", 5),
    )
    qt_app.processEvents()
    return _gyerek(window, "photoContextMenu")


def _menu_zar(window, qt_app):
    QMetaObject.invokeMethod(
        _gyerek(window, "photoContextMenu"), "close",
        Qt.ConnectionType.DirectConnection,
    )
    qt_app.processEvents()


def _megerosito(window):
    dialog = window.findChild(QObject, "removeFromAlbumDialog")
    assert dialog is not None and dialog.property("visible") is True, (
        "a Csillagozott album törlésének az 'Elemek eltávolítása' megerősítőt "
        "kell megnyitnia"
    )
    assert dialog.property("title") == "Remove Items"
    assert dialog.property("yesText") == "Remove Image"
    assert dialog.property("message") == (
        "Are you sure you want to remove the selected image from the "
        "current album?"
    )
    return dialog


def _megerosit_es_ellenoriz(window, qt_app, kep: Path, ini: Path, fajlnev: str):
    assert kep.exists(), "a fájlnak a megerősítés előtt is a lemezen kell maradnia"
    assert _csillag_ertek(ini, fajlnev) == "yes", (
        "a csillag a megerősítés előtt maradjon"
    )
    _katt(window, _gyerek(window, "removeFromAlbumYesButton"))

    hatarido = time.monotonic() + 3
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if _csillag_ertek(ini, fajlnev) is None:
            break
        QTest.qWait(50)

    assert kep.exists(), "a Csillagozott albumból eltávolítás nem törölhet fájlt"
    assert _csillag_ertek(ini, fajlnev) is None, "a star=yes kulcsnak el kell tűnnie"


def _viewer_menu_nyit(window, qt_app):
    nezo = _gyerek(window, "photoViewer")
    QMetaObject.invokeMethod(
        nezo,
        "openContextMenu",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", 5),
        Q_ARG("QVariant", 5),
    )
    qt_app.processEvents()
    return _gyerek(window, "viewerContextMenu")


def _kepmentes(menu_kep, dialog_kep, cel: Path):
    """A két eredeti felületi állapotot egy offscreen kiadásképpé fűzi."""
    menu = menu_kep.toImage() if hasattr(menu_kep, "toImage") else menu_kep
    dialog = dialog_kep.toImage() if hasattr(dialog_kep, "toImage") else dialog_kep
    kep = QImage(
        max(menu.width(), dialog.width()),
        menu.height() + dialog.height(),
        QImage.Format.Format_ARGB32,
    )
    kep.fill(Qt.transparent)
    festo = QPainter(kep)
    festo.drawImage(0, 0, menu)
    festo.drawImage(0, menu.height(), dialog)
    festo.end()
    assert kep.save(str(cel)), f"nem menthető a kiadáskép: {cel}"


@pytest.mark.parametrize("magassag_eltolas", [-5, 0, 5])
def test_csillagozott_delete_utak_a_csillagot_veszik_le_es_a_fajlok_maradnak(
    qml_app, qt_app, tmp_path, magassag_eltolas
):
    window, controller, _engine = qml_app
    window.resize(window.width(), window.height() + magassag_eltolas)
    qt_app.processEvents()
    mappa = Path(controller.watchedFolders[0])
    make_jpeg(mappa / "c.jpg", size=(160, 120))
    mappa, ini = _csillagozott_nezet(
        window, controller, qt_app, ["a.jpg", "b.jpg", "c.jpg"]
    )
    a, b, c = (mappa / f"{nev}.jpg" for nev in ("a", "b", "c"))
    assert a.exists() and b.exists() and c.exists()
    assert Path(controller.photos.filePathAt(0)) == a

    # Rács Delete (#1608): megerősítés után a kijelölt kép fájlja megmarad,
    # csak a csillag esik le.
    _fokusz(_gyerek(window, "photoGrid"), qt_app)
    QTest.keyClick(window, Qt.Key_Delete)
    qt_app.processEvents()
    _megerosito(window)
    _megerosit_es_ellenoriz(window, qt_app, a, ini, "a.jpg")

    # A feliratok a törlési művelettel együtt váltanak; a rács helyi menüje
    # az albumos sort mutatja, és nem kínál lemezes törlést.
    assert _gyerek(window, "menuFileDelete").property("text") == (
        "Remove from Album\tDelete"
    )
    _menu_nyit(window, qt_app)
    try:
        assert _gyerek(window, "contextMenuDelete").property("visible") is False
        assert _gyerek(window, "contextMenuRemoveFromAlbum").property("text") == (
            "Remove from Album\tCtrl+Delete"
        )
    finally:
        _menu_zar(window, qt_app)

    # Néző Ctrl+Delete: a D.8 album-eltávolító ága ugyanazt a megerősítést
    # nyitja, és a fájl megmarad.
    assert Path(controller.photos.filePathAt(0)) == b
    window.setProperty("viewerOpen", True)
    nezo = _gyerek(window, "photoViewer")
    nezo.setProperty("currentIndex", 0)
    qt_app.processEvents()
    _fokusz(nezo, qt_app)
    assert _gyerek(window, "shortcutDeleteFromDiskViewer").property("enabled") is True
    QTest.keyClick(window, Qt.Key_Delete, Qt.KeyboardModifier.ControlModifier)
    qt_app.processEvents()
    _megerosito(window)
    _megerosit_es_ellenoriz(window, qt_app, b, ini, "b.jpg")

    # A néző helyi menüje is az eredeti feliratot és műveletet használja;
    # a két offscreen állapotból kiadáskép készül.
    assert Path(controller.photos.filePathAt(0)) == c
    nezo.setProperty("currentIndex", 0)
    qt_app.processEvents()
    _fokusz(nezo, qt_app)
    _viewer_menu_nyit(window, qt_app)
    assert _gyerek(window, "viewerMenuDelete").property("text") == (
        "Remove from Album\tCtrl+Delete"
    )
    menu_kep = window.grabWindow()
    _katt(window, _gyerek(window, "viewerMenuDelete"))
    qt_app.processEvents()
    _megerosito(window)
    dialog_kep = window.grabWindow()
    _kepmentes(menu_kep, dialog_kep, tmp_path / "kep-4883.png")
    _megerosit_es_ellenoriz(window, qt_app, c, ini, "c.jpg")
