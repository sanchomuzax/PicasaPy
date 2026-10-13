"""#4883 — a Csillagozott album nem szerkeszthető albumleírás.

A bal hasáb „Csillagozott fotók” sora ``]star`` tokennel dolgozik, de
ehhez NINCS ``[.album:]star]`` definíció a ``.picasa.ini``-ben. A Mappa/Album
menü „Leírás szerkesztése” tétele ilyenkor nem nyithat album-párbeszédet:
az üres ``albumProperties`` mentése semmit nem írna, a felhasználó mégis
úgy látná, hogy elmentette.

Spec: ``docs/specs/ui-audit-context-menus.md`` D.8 — a spec nem említ
albumleírást a Csillagozott albumhoz, ezért a tétel tiltott.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree
from picasapy.ini import update_document
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


def _csillagozott_nezet(window, controller, qt_app):
    mappa = Path(controller.watchedFolders[0])
    make_jpeg(mappa / "a.jpg", size=(160, 120))
    update_document(
        mappa / ".picasa.ini",
        lambda dokumentum: dokumentum.with_value("a.jpg", "star", "yes"),
    )
    with open_index(controller._db_path) as conn:
        sync_tree(conn, mappa)
    controller._reload_after_sync()
    qt_app.processEvents()

    _katt(window, _gyerek(window, "starredItem"))
    qt_app.processEvents()
    assert controller.currentAlbumToken == "]star"


def test_csillagozott_nezetben_a_leiras_szerkesztese_tetel_tiltott(
    qml_app, qt_app
):
    window, controller, _engine = qml_app
    _csillagozott_nezet(window, controller, qt_app)

    tetel = _gyerek(window, "menuFolderEditDescription")
    assert tetel.property("enabled") is False, (
        "a ]star nem létező album: a Leírás szerkesztése tétel tiltott legyen"
    )

    QMetaObject.invokeMethod(tetel, "click", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()

    dialog = window.findChild(QObject, "folderPropertiesDialog")
    assert dialog is None or dialog.property("opened") is False, (
        "a Csillagozott nézetből nem nyílhat album-leírás párbeszéd"
    )
