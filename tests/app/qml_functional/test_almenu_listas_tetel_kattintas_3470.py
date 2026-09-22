"""#3470: az almenük LISTÁBÓL épülő tételei valódi kattintásra is működnek.

A közös `PicasaMenu.qml` belső `id: menu`-je a `Repeater`-delegáltakban
elfedte a befoglaló helyi menü azonos nevű `id`-jét: a delegált a
beágyazott almenün kereste a jelet (`TypeError: … is not a function`), és
egy albumra/gyűjteményre kattintva semmi nem történt. A korábbi tesztek a
jelet közvetlenül bocsátották ki, ezért nem látták — itt a tétel
`click()`-je fut, a menü saját névterében (a beágyazott menü tételei
`findChild`-dal nem érhetők el).
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMetaObject, Qt, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlExpression, qmlContext

_KEEPALIVE: list[object] = []
_TOKEN = "604c294a68b0de9cc9222c4714f289d5"


@pytest.fixture
def qml_engine(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    yield engine
    engine.deleteLater()


def _menu(engine, komponens: str, beallitas: str):
    component = QQmlComponent(engine)
    component.setData(
        (
            "import QtQuick\nimport PicasaPy 1.0\n"
            f"{komponens} {{ {beallitas} }}\n"
        ).encode("utf-8"),
        QUrl(),
    )
    root = component.create()
    assert [e.toString() for e in component.errors()] == []
    QQmlEngine.setObjectOwnership(root, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.extend((component, root))
    return root


def _almenu(root, nev):
    from PySide6.QtCore import QObject

    obj = root.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def _kattint(almenu, tetel_nev) -> bool:
    kifejezes = QQmlExpression(qmlContext(almenu), almenu, (
        "(function () { for (var i = 0; i < count; ++i)"
        f"  if (itemAt(i).objectName === '{tetel_nev}') {{ itemAt(i).click(); return true }}"
        "  return false })()"
    ))
    ertek, hiba = kifejezes.evaluate()
    assert not hiba, kifejezes.error()
    return bool(ertek)


ESETEK = (
    pytest.param(
        "PhotoContextMenu",
        f'albums: [{{"token": "{_TOKEN}", "name": "Nyaralás"}}]',
        "contextMenuAddToAlbum", f"contextMenuAddToAlbumItem_{_TOKEN}",
        "addToAlbumRequested", _TOKEN,
        id="kep-album",
    ),
    pytest.param(
        "ViewerContextMenu",
        f'albums: [{{"token": "{_TOKEN}", "name": "Nyaralás"}}]',
        "viewerMenuAddToAlbum", f"viewerMenuAddToAlbumItem_{_TOKEN}",
        "addToAlbumRequested", _TOKEN,
        id="nezegeto-album",
    ),
    pytest.param(
        "FolderContextMenu",
        'customCollections: [{"name": "Család"}]',
        "folderContextMenuMoveToCollection",
        "folderContextMenuMoveToCollectionItem_Család",
        "moveToCollectionRequested", "Család",
        id="mappa-gyujtemeny",
    ),
    pytest.param(
        "PhotoContextMenu",
        'personName: "Anna"; people: [{"name": "Anna"}, {"name": "Béla"}]',
        "contextMenuAddToPeopleAlbumMenu", "contextMenuAddToPeopleAlbumItem_Béla",
        "moveToPersonRequested", "Béla",
        id="kep-szemely",
    ),
)


@pytest.mark.parametrize(
    ("komponens", "beallitas", "almenu_nev", "tetel_nev", "jel", "vart"), ESETEK
)
def test_a_listas_tetel_kattintasra_eleri_a_hivot(
    qml_engine, qt_app, komponens, beallitas, almenu_nev, tetel_nev, jel, vart
):
    root = _menu(qml_engine, komponens, beallitas)
    kapott: list[str] = []
    getattr(root, jel).connect(kapott.append)
    QMetaObject.invokeMethod(root, "open", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()
    try:
        assert _kattint(_almenu(root, almenu_nev), tetel_nev), f"{tetel_nev} nincs a menüben"
        qt_app.processEvents()
    finally:
        QMetaObject.invokeMethod(root, "close", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
    assert kapott == [vart]


def _delegalt_menutetelek(forras: str):
    """A `delegate: MenuItem {…}` / `delegate: PicasaMenuItem {…}` blokkok
    szövege, zárójel-számlálással (a blokk a nyitó `{`-tól a párjáig)."""
    import re

    for talalat in re.finditer(r"delegate:\s*(?:Picasa)?MenuItem\s*\{", forras):
        melyseg, i = 0, talalat.end() - 1
        while i < len(forras):
            melyseg += {"{": 1, "}": -1}.get(forras[i], 0)
            if melyseg == 0:
                break
            i += 1
        yield forras[talalat.start():i + 1]


def test_menuteteles_delegaltban_nincs_csupasz_menu_hivatkozas():
    """Forrás-őr a teljes QML-fán: a delegált `MenuItem`-ben a `menu.` a
    tétel SAJÁT almenüjét jelenti, nem a befoglaló helyi menüt — a hívás
    `helyiMenu.`-n át menjen. (A kommentsorokat kihagyjuk.)"""
    import re
    from pathlib import Path

    import picasapy.app.application as app_module

    hibak = []
    for ut in sorted((app_module._APP_DIR / "qml").rglob("*.qml")):
        for blokk in _delegalt_menutetelek(ut.read_text(encoding="utf-8")):
            for sor in blokk.splitlines():
                kod = sor.split("//", 1)[0]
                if re.search(r"(?<![\w.])menu\.", kod):
                    hibak.append(f"{Path(ut).name}: {sor.strip()}")
    assert hibak == []
