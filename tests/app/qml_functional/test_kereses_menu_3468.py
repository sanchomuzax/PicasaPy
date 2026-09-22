"""#3468: az indexkép helyi menüjének keresés-része az eredeti szerint.

`docs/specs/ui-audit-context-menus.md` D: a keresés alapból LAPOS
„Keresés a lemezen" (Ctrl+Enter); almenüvé csak akkor válik, ha EGYETLEN kép
van kijelölve, és annak van visszaállítható eredetije — az almenü kéttételes
(„Fájl a lemezen", „Eredeti a lemezen"). A „Keresés a Picasában" album-nézetben
külön, lapos tétel. Hasonlóság-keresés a helyi menüben nincs (a keresősáv
Ctrl+F7 parancsa). A törlés felirata „Törlés a lemezről", billentyű-szövege
„Ctrl+Törlés".

A menü csak NYITVA tükrözi hűen a tételek láthatóságát, ezért a teszt
megnyitja, és a tételeket olvassa.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt, QTranslator

_QM = (
    Path(__file__).resolve().parents[3]
    / "src" / "picasapy" / "app" / "i18n" / "picasapy_hu.qm"
)


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _megnyit(window, qt_app, sorok):
    window.setProperty("selectedIndexes", list(sorok))
    window.setProperty("selectedIndex", sorok[0])
    QMetaObject.invokeMethod(
        window, "openPhotoContextMenu", Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", sorok[0]), Q_ARG("QVariant", _child(window, "photoGrid")),
        Q_ARG("QVariant", 5), Q_ARG("QVariant", 5),
    )
    for _ in range(5):
        qt_app.processEvents()


def _bezar(window, qt_app):
    QMetaObject.invokeMethod(
        _child(window, "photoContextMenu"), "close", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()


def _lathato(window, nev) -> bool:
    return _child(window, nev).property("visible") is True


def _eredetik(controller):
    """Minden kép kap mentett eredetit a `.picasaoriginals`-ban."""
    for sor in range(controller.photos.rowCount()):
        ut = Path(controller.photos.filePathAt(sor))
        eredeti = ut.parent / ".picasaoriginals" / ut.name
        eredeti.parent.mkdir(exist_ok=True)
        eredeti.write_bytes(ut.read_bytes())


def test_eredeti_nelkul_lapos_kereses(qml_app, qt_app):
    window, _controller, _engine = qml_app
    _megnyit(window, qt_app, [0])
    try:
        assert _lathato(window, "contextMenuLocate")
        assert not _lathato(window, "contextMenuLocateMenuTetel")
        assert _child(window, "contextMenuLocateMenuTetel").property("height") == 0
    finally:
        _bezar(window, qt_app)


def test_egy_visszaallithato_kepnel_ketteteles_almenu(qml_app, qt_app):
    window, controller, _engine = qml_app
    _eredetik(controller)
    _megnyit(window, qt_app, [0])
    try:
        assert _lathato(window, "contextMenuLocateMenuTetel")
        assert not _lathato(window, "contextMenuLocate")
        assert _child(window, "contextMenuLocate").property("height") == 0
        almenu = _child(window, "contextMenuLocateMenu")
        assert almenu.property("count") == 2
        assert almenu.findChild(QObject, "contextMenuLocateFile") is not None
        assert almenu.findChild(QObject, "contextMenuLocateOriginal") is not None
        assert almenu.findChild(QObject, "contextMenuLocateInPicasa") is None
    finally:
        _bezar(window, qt_app)


def test_tobb_kepnel_lapos_akkor_is_ha_van_eredeti(qml_app, qt_app):
    window, controller, _engine = qml_app
    _eredetik(controller)
    _megnyit(window, qt_app, [0, 1])
    try:
        assert _lathato(window, "contextMenuLocate")
        assert not _lathato(window, "contextMenuLocateMenuTetel")
    finally:
        _bezar(window, qt_app)


def test_mappanezetben_nincs_kereses_a_picasaban(qml_app, qt_app):
    window, _controller, _engine = qml_app
    _megnyit(window, qt_app, [0])
    try:
        assert not _lathato(window, "contextMenuLocateInPicasa")
    finally:
        _bezar(window, qt_app)


def test_a_hasonlosag_kereses_nincs_a_helyi_menuben(qml_app):
    window, _controller, _engine = qml_app
    assert window.findChild(QObject, "contextMenuFindSimilar") is None
    # a funkció megmarad: a keresősáv Ctrl+F7 billentyűje
    assert window.findChild(QObject, "findSimilarShortcut") is not None


@pytest.mark.parametrize(
    ("forras", "vart"),
    [
        ("Add to Album", "Hozzáadás az albumhoz"),
        ("Delete from Disk", "Törlés a lemezről"),
        ("Ctrl+Delete", "Ctrl+Törlés"),
        ("Locate on Disk", "Keresés a lemezen"),
    ],
)
def test_a_magyar_feliratok(qt_app, forras, vart):
    fordito = QTranslator()
    assert fordito.load(str(_QM))
    assert fordito.translate("PhotoContextMenu", forras) == vart


def test_a_torles_billentyuszovege_forditott(qml_app):
    window, _controller, _engine = qml_app
    menu = _child(window, "photoContextMenu")
    tetel = _child(window, "contextMenuDelete")
    assert tetel.property("text").endswith("\t" + menu.property("_torlesBillentyu"))
