"""#3464: a „Hozzáadás az Emberek albumhoz" a MEGLÉVŐ személyek almenüje.

Az eredetiben (`docs/specs/picasa-arcfelismeres.md` 17.2) a `0xa0cd` tétel
futásidőben töltött almenü: a meglévő személyek listája, és egy névre
kattintva az arc ahhoz a személyhez kerül — ugyanaz a művelet, mint az
„Áthelyezés új személyhez…", csak meglévő célszeméllyel. A jelenlegi
személy nincs a listán; személyek nélkül az almenü tiltott.
"""

from __future__ import annotations

import time

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPoint, QPointF, QUrl, Qt
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtQml import QQmlExpression, qmlContext
from PySide6.QtTest import QTest

from picasapy.index import open_index, people_in_index, sync_tree
from picasapy.ini import contacts_of, load_document, parse_faces

_ANNA = "1111111111111111"
_BELA = "2222222222222222"
_INI = (
    "[Contacts2]\n"
    f"{_ANNA}=Anna;;\n"
    f"{_BELA}=Béla;;\n"
    "[a.jpg]\n"
    f"faces=rect64(1e00280045006e00),{_ANNA}\n"
    "[b.jpg]\n"
    f"faces=rect64(1e00280045006e00),{_BELA}\n"
)


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _almenu_js(window, js):
    """JS az almenü SAJÁT névterében: a beágyazott `Menu` tételei nem
    érhetők el `findChild`-dal, csak a `count`/`itemAt()` páron át
    (ld. `test_megjelenitesi_mod_menu_1575.py`)."""
    almenu = _child(window, "contextMenuAddToPeopleAlbumMenu")
    kifejezes = QQmlExpression(qmlContext(almenu), almenu, js)
    ertek, hiba = kifejezes.evaluate()
    assert not hiba, kifejezes.error()
    return ertek


def _almenu_tetelek(window):
    ertek = _almenu_js(window, (
        "(function () { var r = [];"
        "  for (var i = 0; i < count; ++i) r.push(itemAt(i).objectName);"
        "  return r.join('|'); })()"
    ))
    return str(ertek).split("|") if ertek else []


def _almenu_kattint(window, nev):
    """A tétel VALÓDI kattintása (`click()`), nem a jel közvetlen hívása."""
    _almenu_js(window, (
        "(function () { for (var i = 0; i < count; ++i)"
        f"  if (itemAt(i).objectName === '{nev}') {{ itemAt(i).click(); return true }}"
        "  return false })()"
    ))


def _szemely_nezet(window, controller, qt_app, tmp_path, szemely="Anna"):
    lib = tmp_path / "kepek"
    # A korábbi teszt-index adatbázisa már létrehozhatja a mappát.
    lib.mkdir(exist_ok=True)
    for nev in ("a.jpg", "b.jpg"):
        kep = QImage(8, 8, QImage.Format.Format_RGB32)
        kep.fill(0xFF336699)
        assert kep.save(str(lib / nev)), f"a tesztkép nem menthető: {nev}"
    (lib / ".picasa.ini").write_text(_INI, encoding="utf-8")
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    controller._reload_after_sync()
    controller.showPerson(szemely)
    for _ in range(5):
        qt_app.processEvents()
    return lib


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


def _arcok(lib, foto):
    doc = load_document(lib / ".picasa.ini")
    nevek = {c.person_id.casefold(): c.name for c in contacts_of(doc)}
    raw = doc.section(foto).get("faces") or ""
    return sorted(nevek.get(f.contact_id.casefold(), "") for f in parse_faces(raw))


def _varj(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.01)
    qt_app.processEvents()
    return bool(feltetel())


def _menu_tetel_kattintas(tetel: QQuickItem, qt_app) -> None:
    """Valódi egérkattintás a menüsor felépült, tényleges közepére."""
    popup = tetel.window()
    assert isinstance(popup, QQuickWindow), "a menüpont popup ablaka hiányzik"
    popup.requestActivate()
    assert _varj(qt_app, popup.isActive), "a fotómenü popup ablaka nem aktív"
    pont = tetel.mapToScene(
        QPointF(tetel.width() / 2, tetel.height() / 2)
    ).toPoint()
    QTest.mouseClick(
        popup,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(pont.x(), pont.y()),
    )


def test_az_almenu_a_tobbi_szemelyt_sorolja(qml_app, qt_app, tmp_path):
    window, controller, _engine = qml_app
    _szemely_nezet(window, controller, qt_app, tmp_path)
    _megnyit(window, qt_app)
    try:
        almenu = _child(window, "contextMenuAddToPeopleAlbum")
        assert almenu.property("enabled") is True
        assert _almenu_tetelek(window) == ["contextMenuAddToPeopleAlbumItem_Béla"]
    finally:
        _bezar(window, qt_app)


def test_egy_nevre_kattintva_az_arc_atkerul(qml_app, qt_app, tmp_path):
    window, controller, _engine = qml_app
    lib = _szemely_nezet(window, controller, qt_app, tmp_path)
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    _megnyit(window, qt_app)
    try:
        _almenu_kattint(window, "contextMenuAddToPeopleAlbumItem_Béla")
        for _ in range(5):
            qt_app.processEvents()
    finally:
        _bezar(window, qt_app)
    assert _arcok(lib, "a.jpg") == ["Béla"]


def test_szemelyek_nelkul_az_almenu_tiltott(qml_app, qt_app, tmp_path):
    """Egyetlen személy van, és épp őt nézzük: nincs hova áthelyezni."""
    window, controller, _engine = qml_app
    _szemely_nezet(window, controller, qt_app, tmp_path, szemely="Anna")
    menu = _child(window, "photoContextMenu")
    menu.setProperty("people", [{"name": "Anna", "count": 1}])
    _megnyit(window, qt_app)
    try:
        assert _child(window, "contextMenuAddToPeopleAlbum").property("enabled") is False
        assert _almenu_tetelek(window) == []
    finally:
        _bezar(window, qt_app)


def test_a_menu_kattintasa_beallitja_es_ujraolvashatoan_tarolja_a_boritot(
    qml_app, qt_app, tmp_path
):
    """A valódi menükattintás után a kiválasztás a .picasa.ini-ből visszaolvasható."""
    window, controller, _engine = qml_app
    _szemely_nezet(window, controller, qt_app, tmp_path)
    eredeti_magassag = window.height()
    try:
        for eltolás in (-5, 0, 5):
            window.setHeight(eredeti_magassag + eltolás)
            assert _varj(
                qt_app,
                lambda eltolás=eltolás: window.height()
                == eredeti_magassag + eltolás,
            ), f"a főablak magassága nem állt be ({eltolás:+} px)"
            _megnyit(window, qt_app)
            try:
                tetel = _child(window, "contextMenuSetAsPeopleAlbumThumbnail")
                assert tetel.property("enabled") is True, "az indexképtétel letiltva maradt"
                assert tetel.property("placeholder") is False, "az indexképtétel helyőrző maradt"
                _menu_tetel_kattintas(tetel, qt_app)
                assert _varj(
                    qt_app,
                    lambda: _child(window, "photoContextMenu").property("visible")
                    is False,
                ), "a kattintás nem zárta be a fotó helyi menüjét"
            finally:
                _bezar(window, qt_app)
    finally:
        window.setHeight(eredeti_magassag)

    with open_index(tmp_path / "index.db") as conn:
        anna = next(person for person in people_in_index(conn) if person.name == "Anna")
    assert anna.thumbnail_path == str(tmp_path / "kepek" / "a.jpg"), (
        "a kiválasztott személy-album borítója nem olvasható vissza a .picasa.ini-ből"
    )
    anna_model = next(person for person in controller.people if person["name"] == "Anna")
    assert QUrl(anna_model["thumbnailUrl"]).toLocalFile() == str(
        tmp_path / "kepek" / "a.jpg"
    ), "a mentett borító nem jut el a személylista képmodelljéig"
