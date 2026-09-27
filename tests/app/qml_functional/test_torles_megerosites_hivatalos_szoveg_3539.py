"""#3539 — a törlés-/eltávolítás-megerősítések a Picasa HIVATALOS szövegét
mutatják (cím, üzenet, igen-gomb), a `docs/specs/picasa-fen-dialogs.md`
3.3.1 szakasza (`0x005fdc30` szövegválasztó) szerint.

## A négy fájltörlés-ág (`FileOpsDialogs.qml` `deleteConfirmDialog`)

A cím mind a négy ágon `DeleteMessage::DeleteItemsTitle` ("Delete Items");
az üzenet és az igen-gomb a darabszám (1 / több) és a lomtár elérhetősége
szerint dől el: `DeleteSingle`/`DeleteMultiple` (lomtár van),
`NoUndoSingle`/`NoUndoMultiple` (nincs lomtár — a korábbi saját szöveg és a
#3573-ban tévesen idekötött `CThumbUI::ConfirmImmediateDeletion::Message`
helyett).

## Albumból eltávolítás — ÚJ megerősítés

A korábbi állapotban az albumból eltávolítás AZONNAL futott, megerősítés
nélkül (mérve, 2026-09-24) — ez a jegy vezeti be a `RemoveSingle`/
`RemoveMultiple` megerősítést, a "Remove from album without confirmation"
beállítással elnyomhatóan (ld. `test_qml_options_dialog.py`
`TestGeneralTabLiveRemoveFromAlbumConfirmSuppression`).

## Emberek-album eltávolítás

A korábbi saját "arc-címke" szöveg helyett a `RemoveSinglePeople`/
`RemoveMultiplePeople` hivatalos szöveg (ami NEM az arc-címkét, hanem "a
kijelölt személyt/személyeket" mondja — ez az eredeti szóhasználata).

⚠️ A várt szövegek KIÍRT LITERÁLOK (a #1576 tanulsága) — a fixture nem
telepít QTranslator-t, ezért az angol forrásszöveg látszik.
"""

from __future__ import annotations

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt

from picasapy.index import open_index, sync_tree
from support.qml_halasztott import epitsd_fel_ha_fileops

_TOKEN = "604c294a68b0de9cc9222c4714f289d5"
_ROY_ID = "b8e4117cf1d6615b"
_ROY = "Roy Avery"
_RECT = "3f840000c3509f84"


def _gyerek(window, nev):
    epitsd_fel_ha_fileops(window, nev)
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"a(z) {nev} nem található"
    return elem


def _epitsd_fel(window, burok_nev):
    burok = window.findChild(QObject, burok_nev)
    assert burok is not None, f"a(z) {burok_nev} DeferredDialog nincs meg"
    QMetaObject.invokeMethod(burok, "ensure", Qt.ConnectionType.DirectConnection)


def _kijelol(window, qt_app, sorok):
    window.setProperty("selectedIndexes", list(sorok))
    window.setProperty("selectedIndex", sorok[0])
    qt_app.processEvents()


def _cimke_szovege(window, prefix):
    return _gyerek(window, prefix + "MessageLabel").property("text")


def _nas_kornyezet(monkeypatch, tmp_path):
    """A lomtár-hiányos (NAS) ág szimulálása — a `test_fileops_controller.py`
    `test_false_when_no_path_has_a_trash` mintája."""
    topdir = tmp_path / "nas"
    topdir.mkdir()
    monkeypatch.setattr(
        "picasapy.fileops.trash._device_of",
        lambda p: 1 if str(p).startswith(str(topdir)) else 2,
    )
    monkeypatch.setattr("picasapy.fileops.trash._mount_point", lambda p: topdir)
    monkeypatch.setattr("picasapy.fileops.trash._access", lambda path, mode: False)
    return topdir


def _album_nezet(lib, tmp_path, controller, qt_app):
    (lib / ".picasa.ini").write_text(
        f"[.album:{_TOKEN}]\n"
        f"name=Nyaralás\n"
        f"token={_TOKEN}\n"
        f"[a.jpg]\n"
        f"albums={_TOKEN}\n"
        f"[b.jpg]\n"
        f"albums={_TOKEN}\n",
        encoding="utf-8",
    )
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    controller._reload_after_sync()
    controller.showAlbum(_TOKEN)
    qt_app.processEvents()


def _szemely_nezet(lib, tmp_path, controller, qt_app):
    (lib / ".picasa.ini").write_text(
        f"[Contacts2]\n{_ROY_ID}={_ROY};;\n"
        f"[a.jpg]\nfaces=rect64({_RECT}),{_ROY_ID};\n"
        f"[b.jpg]\nfaces=rect64({_RECT}),{_ROY_ID};\n",
        encoding="utf-8",
    )
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    controller._reload_after_sync()
    controller.showPerson(_ROY)
    qt_app.processEvents()


class TestFajlTorlesNegyAg:
    """`deleteConfirmDialog.openFor(paths)` — a négy DeleteMessage-ág."""

    def _nyit(self, window, qt_app, paths):
        dialog = _gyerek(window, "deleteConfirmDialog")
        QMetaObject.invokeMethod(
            dialog, "openFor", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", paths),
        )
        qt_app.processEvents()
        return dialog

    def test_egy_fajl_lomtarba(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        kep = str(tmp_path / "kepek" / "a.jpg")
        dialog = self._nyit(window, qt_app, [kep])

        assert dialog.property("title") == "Delete Items"
        assert dialog.property("yesText") == "Delete Image"
        szoveg = _cimke_szovege(window, "confirm")
        assert szoveg == (
            "Are you sure you want to send the selected file to the "
            "Recycle Bin? (It will also be removed from any albums in "
            "which it appears)"
        )

    def test_tobb_fajl_lomtarba(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        dialog = self._nyit(window, qt_app, [str(lib / "a.jpg"), str(lib / "b.jpg")])

        assert dialog.property("title") == "Delete Items"
        assert dialog.property("yesText") == "Delete Items"
        szoveg = _cimke_szovege(window, "confirm")
        assert szoveg == (
            "Are you sure you want to send the 2 selected item(s) to the "
            "Recycle Bin?\n(They will also be removed from any albums in "
            "which they appear)"
        )

    def test_egy_fajl_nincs_lomtar(self, qml_app, qt_app, tmp_path, monkeypatch):
        window, controller, _engine = qml_app
        topdir = _nas_kornyezet(monkeypatch, tmp_path)
        kep = topdir / "a.jpg"
        kep.write_bytes(b"kep")
        dialog = self._nyit(window, qt_app, [str(kep)])

        assert dialog.property("title") == "Delete Items"
        assert dialog.property("yesText") == "Delete File"
        szoveg = _cimke_szovege(window, "confirm")
        assert szoveg == (
            "Are you sure you want to permanently delete the selected "
            "file? (This cannot be undone.)"
        )

    def test_tobb_fajl_nincs_lomtar(self, qml_app, qt_app, tmp_path, monkeypatch):
        window, controller, _engine = qml_app
        topdir = _nas_kornyezet(monkeypatch, tmp_path)
        a, b = topdir / "a.jpg", topdir / "b.jpg"
        a.write_bytes(b"kep")
        b.write_bytes(b"kep")
        dialog = self._nyit(window, qt_app, [str(a), str(b)])

        assert dialog.property("title") == "Delete Items"
        assert dialog.property("yesText") == "Delete Files"
        szoveg = _cimke_szovege(window, "confirm")
        assert szoveg == (
            "Are you sure you want to delete 2 selected file(s)? (This "
            "cannot be undone.)"
        )


class TestAlbumbolEltavolitasUjMegerosites:
    """A #3539 előtt ez az út AZONNAL futott — most megerősítést kér."""

    def test_egy_kep_szovege_es_megerositese(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        _album_nezet(lib, tmp_path, controller, qt_app)
        _kijelol(window, qt_app, [0])  # a.jpg

        menu = _gyerek(window, "photoContextMenu")
        menu.removeFromAlbumRequested.emit()
        qt_app.processEvents()

        dialog = _gyerek(window, "removeFromAlbumDialog")
        assert dialog.property("visible") is True, (
            "az albumból eltávolításnak megerősítést kell kérnie"
        )
        assert dialog.property("title") == "Remove Items"
        assert dialog.property("yesText") == "Remove Image"
        assert _cimke_szovege(window, "removeFromAlbum") == (
            "Are you sure you want to remove the selected image from the "
            "current album?"
        )
        ini = (lib / ".picasa.ini").read_text(encoding="utf-8")
        assert f"[a.jpg]\nalbums={_TOKEN}" in ini, (
            "a kép NEM eshet ki az albumból megerősítés ELŐTT"
        )

        QMetaObject.invokeMethod(
            dialog, "confirmed", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        ini = (lib / ".picasa.ini").read_text(encoding="utf-8")
        assert "[a.jpg]" not in ini, (
            "a megerősítés UTÁN ki kellett esnie a képnek az albumból (az "
            "[a.jpg] szakasz csak az `albums=` kulcsot tartalmazta)"
        )

    def test_tobb_kep_szovege(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        _album_nezet(lib, tmp_path, controller, qt_app)
        _kijelol(window, qt_app, [0, 1])  # a.jpg + b.jpg

        menu = _gyerek(window, "photoContextMenu")
        menu.removeFromAlbumRequested.emit()
        qt_app.processEvents()

        dialog = _gyerek(window, "removeFromAlbumDialog")
        assert dialog.property("title") == "Remove Items"
        assert dialog.property("yesText") == "Remove Images"
        assert _cimke_szovege(window, "removeFromAlbum") == (
            "Are you sure you want to remove the 2 selected image(s) from "
            "the current album?"
        )

    def test_elnyomhato_a_beallitassal(self, qml_app, qt_app, tmp_path):
        """A "Remove from album without confirmation" (`removeFromAlbum`
        döntés-kulcs) elnyomja a megerősítést — a #367 törlés-elnyomás
        mintája szerint."""
        window, controller, engine = qml_app
        lib = tmp_path / "kepek"
        _album_nezet(lib, tmp_path, controller, qt_app)
        confirm_settings = engine.rootContext().contextProperty("confirmSettings")
        assert confirm_settings is not None
        confirm_settings.setSuppressed("removeFromAlbum", True)
        _kijelol(window, qt_app, [0])

        menu = _gyerek(window, "photoContextMenu")
        menu.removeFromAlbumRequested.emit()
        qt_app.processEvents()

        assert _gyerek(window, "removeFromAlbumDialog").property(
            "visible"
        ) is False
        ini = (lib / ".picasa.ini").read_text(encoding="utf-8")
        assert "[a.jpg]" not in ini, (
            "az elnyomott döntés-kulcs mellett is le kellett futnia az "
            "eltávolításnak"
        )


class TestEmberekAlbumEltavolitasHivatalosSzoveg:
    """`removePeopleFacesDialog` — a korábbi saját "arc-címke" szöveg
    helyett a `RemoveSinglePeople`/`RemoveMultiplePeople` hivatalos alak."""

    def test_egy_szemely(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        _szemely_nezet(lib, tmp_path, controller, qt_app)
        _kijelol(window, qt_app, [0])

        menu = _gyerek(window, "photoContextMenu")
        menu.removeFromPeopleAlbumRequested.emit()
        qt_app.processEvents()

        dialog = _gyerek(window, "removePeopleFacesDialog")
        assert dialog.property("visible") is True
        assert dialog.property("title") == "Remove People"
        assert dialog.property("yesText") == "Remove Person"
        assert _cimke_szovege(window, "removePeopleFaces") == (
            "Are you sure you want to remove the selected person from the "
            "current album?"
        )

    def test_tobb_szemely(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        _szemely_nezet(lib, tmp_path, controller, qt_app)
        _kijelol(window, qt_app, [0, 1])

        menu = _gyerek(window, "photoContextMenu")
        menu.removeFromPeopleAlbumRequested.emit()
        qt_app.processEvents()

        dialog = _gyerek(window, "removePeopleFacesDialog")
        assert dialog.property("title") == "Remove People"
        assert dialog.property("yesText") == "Remove People"
        assert _cimke_szovege(window, "removePeopleFaces") == (
            "Are you sure you want to remove the 2 selected people from "
            "the current album?"
        )
