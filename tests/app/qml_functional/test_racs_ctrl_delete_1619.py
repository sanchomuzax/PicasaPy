"""#1619 — a RÁCS `Ctrl+Delete`-je is nézetfüggő (adatvesztés-javítás).

A #1608 ugyanennek a hibaosztálynak a **menüsáv** felőli felét javította
(puszta `Delete`); ez itt a **másik belépő**: a rács `Ctrl+Delete`-je és a
kép helyi menüje. Más fájl, más kódút — külön mérés, külön őr.

## Az eredeti — bizonyíték

`docs/specs/picasa-gyorsbillentyuk.md`:

* **5. szakasz** — a `0x9c9a` parancs jelentése NÉZETFÜGGŐ: mappában
  „Törlés lemezről" (Lomtár), albumban „Eltávolítás az albumból",
  Emberek-albumban „Eltávolítás az Emberek albumból". Az utóbbi kettőnél
  **a fájl a lemezen marad**.
* **4. szakasz** — a helyi menük rekordtáblái: a mappa-nézetbeli kép
  menüje (`0x00730790`) `Ctrl+Delete` = „Törlés a lemezről"; az
  album-nézetbelié (`0x00731050`) **ugyanaz a `cmd 0x9c9a`**, csak a
  felirata „Eltávolítás az albumból"; az Emberek-albumé (`0x007355c0`)
  „Eltávolítás az Emberek albumból". Vagyis nézetenként **EGYETLEN**
  ilyen tétel van, **átcímkézve** — az eredeti album-nézetben egyáltalán
  nem kínál lemezről törlést a kép helyi menüjében.
* `docs/specs/ui-audit-context-menus.md` 6.1 ezt a string-tábla felől is
  megerősíti: `AlbumPhoto::ID_FILE_DELETEFROMDISK` felirata **„Remove
  from Album"** — ugyanaz a parancsrekesz, más felirattal.

## Nálunk — a MAI állapot (a javítás előtt MÉRVE, 2026-08-27)

| nézet | rács `Ctrl+Delete` | helyi menü |
|---|---|---|
| mappa | lemezről törlés (helyes) | „Törlés lemezről\\tCtrl+Delete" |
| album | **lemezről törlés** (ADATVESZTÉS) | „Törlés lemezről\\tCtrl+Delete" **és** „Eltávolítás az albumból" (kettő!) |
| Emberek | **lemezről törlés** (ADATVESZTÉS) | „Törlés lemezről\\tCtrl+Delete" **és** „Eltávolítás az Emberek albumból" |

## A teszt mércéje

⚠️ **Valódi billentyűesemény** megy az ablakra (a #1417/#1418/#1608
mintája), nem a kezelő közvetlen hívása — és a helyi menü ágán a
**menüpontot ténylegesen aktiváljuk**.

⚠️ A „lemezen marad" állítást a LEMEZEN mérjük, és a felhasználó útját
**végigvisszük**: a puszta billentyűleütés a HIBÁS ágon sem töröl
azonnal, csak megerősítőt nyit. Ha megerősítő nyílt, a teszt **le is
nyomja** — enélkül az állításnak nem volna foga (ez a #1608 tanulsága).

⚠️ **Kétirányú őr.** A mappa-nézeti ág külön tesztekben KÖVETELI a
törlést — enélkül a „soha ne törölj" változat is átmenne.

⚠️ A várt feliratok **kiírt literálok**, nem a termék konstansából
származnak (#1576 tanulsága). A fixture nem telepít QTranslator-t, ezért
az angol forrásszöveg látszik.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Q_ARG, QEvent, QMetaObject, QObject, Qt
from PySide6.QtGui import QKeyEvent

from picasapy.index import open_index, sync_tree
from support.qml_halasztott import epitsd_fel_ha_fileops

_TOKEN = "604c294a68b0de9cc9222c4714f289d5"
_ROY_ID = "b8e4117cf1d6615b"
_ROY = "Roy Avery"
_RECT = "3f840000c3509f84"


def _gyerek(window, nev):
    epitsd_fel_ha_fileops(window, nev)  # #1612: halasztott párbeszédek
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"a(z) {nev} nem található"
    return elem


def _fokusz(elem, qt_app):
    elem.setProperty("focus", True)
    QMetaObject.invokeMethod(
        elem, "forceActiveFocus", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()


def _ctrl_delete(window, qt_app):
    """`Ctrl+Delete` az ablakra — ezt köti a rács `shortcutDeleteFromDiskGrid`."""
    qt_app.sendEvent(
        window,
        QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_Delete,
            Qt.KeyboardModifier.ControlModifier,
        ),
    )
    qt_app.processEvents()


def _varj(controller, qt_app, korok=100):
    """Háttérmunkák bevárása (a `test_torles_frissites_1181.py` mintája)."""
    for _ in range(korok):
        qt_app.processEvents()
        if controller.waitForBackgroundWorkers(0.05):
            break
    qt_app.processEvents()


def _kijelol(window, qt_app, sor=0):
    window.setProperty("selectedIndexes", [sor])
    window.setProperty("selectedIndex", sor)
    qt_app.processEvents()
    _fokusz(_gyerek(window, "photoGrid"), qt_app)


def _megerositi_ha_nyilt(window, controller, qt_app):
    """Ha a lemezről törlés megerősítője nyitva áll, LENYOMJA.

    A helyes ágon soha nem nyílik meg, tehát ott ez nem csinál semmit; a
    HIBÁS ágon viszont végigviszi a törlést, és így a hívó „a fájl a
    lemezen maradt" állítása valódi mérés lesz (#1608 tanulsága)."""
    confirm = _gyerek(window, "deleteConfirmDialog")
    if not confirm.property("visible"):
        return
    assert confirm.property("trashAvailable"), (
        "a teszt-környezetben nincs lomtár — a mérés nem érvényes"
    )
    QMetaObject.invokeMethod(
        confirm, "confirmed", Qt.ConnectionType.DirectConnection
    )
    _varj(controller, qt_app)


def _menu_nyit(window, qt_app, sor=0):
    """A kép helyi menüjét TÉNYLEGESEN felnyitja — zárt popupban a
    `visible` minden gyereken hamis (ld. #422 tesztjeinek tanulságát)."""
    grid = _gyerek(window, "photoGrid")
    QMetaObject.invokeMethod(
        window, "openPhotoContextMenu", Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", sor), Q_ARG("QVariant", grid),
        Q_ARG("QVariant", 5), Q_ARG("QVariant", 5),
    )
    qt_app.processEvents()


def _menu_zar(window, qt_app):
    menu = _gyerek(window, "photoContextMenu")
    QMetaObject.invokeMethod(menu, "close", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def _aktival(tetel, qt_app):
    """A menüpontra KATTINTÁS hatása — a `triggered` jelzés kibocsátása."""
    QMetaObject.invokeMethod(
        tetel, "triggered", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()


def _album_nezet(lib, tmp_path, controller, qt_app):
    """Album a `qml_app` fixture mappájában (a.jpg tag), majd album-nézet."""
    (lib / ".picasa.ini").write_text(
        f"[.album:{_TOKEN}]\n"
        f"name=Nyaralás\n"
        f"token={_TOKEN}\n"
        f"[a.jpg]\n"
        f"albums={_TOKEN}\n",
        encoding="utf-8",
    )
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    controller._reload_after_sync()
    controller.showAlbum(_TOKEN)
    qt_app.processEvents()


def _szemely_nezet(lib, tmp_path, controller, qt_app):
    """Egy névvel taggelt arc az a.jpg-n, majd Emberek-album nézet."""
    (lib / ".picasa.ini").write_text(
        f"[Contacts2]\n{_ROY_ID}={_ROY};;\n"
        f"[a.jpg]\nfaces=rect64({_RECT}),{_ROY_ID};\n",
        encoding="utf-8",
    )
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    controller._reload_after_sync()
    controller.showPerson(_ROY)
    qt_app.processEvents()


class TestMappaNezetbenTOVABBRA_IS_Torol:
    """Ellenkező irányú őr: a mappa-nézeti ág nem romolhat el.

    Ez a fél KÖVETELI a törlést — enélkül a „soha ne töröljünk"
    egyszerűsítés is átmenne a jegy album-ági tesztjein."""

    def test_ctrl_delete_a_mappa_nezetben_torlest_kerdez(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        assert controller.currentAlbumToken == ""
        assert controller.currentPersonName == ""
        _kijelol(window, qt_app)
        confirm = _gyerek(window, "deleteConfirmDialog")
        assert confirm.property("visible") is False

        _ctrl_delete(window, qt_app)

        assert confirm.property("visible") is True, (
            "mappa-nézetben a rács Ctrl+Delete-jének TOVÁBBRA IS a "
            "lemezről törlést kell kérdeznie"
        )

    def test_a_mappa_nezet_a_kijelolt_fajlt_celozza(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app)

        _ctrl_delete(window, qt_app)

        utak = _gyerek(window, "deleteConfirmDialog").property("paths")
        if hasattr(utak, "toVariant"):
            utak = utak.toVariant()
        vart = Path(controller.watchedFolders[0]) / "a.jpg"
        assert [Path(p) for p in utak] == [vart]

    def test_megerositve_a_fajl_TENYLEG_eltunik_a_lemezrol(
        self, qml_app, qt_app, tmp_path
    ):
        """A destruktív ág VÉGIG él: `Ctrl+Delete` → megerősítés úton a
        fájl eltűnik a lemezről (valódi lomtár-művelet, nem mock)."""
        window, controller, _engine = qml_app
        kep = tmp_path / "kepek" / "a.jpg"
        assert kep.exists()
        _kijelol(window, qt_app)

        _ctrl_delete(window, qt_app)
        confirm = _gyerek(window, "deleteConfirmDialog")
        assert confirm.property("trashAvailable"), (
            "a teszt-környezetben nincs lomtár — a mérés nem érvényes"
        )
        QMetaObject.invokeMethod(
            confirm, "confirmed", Qt.ConnectionType.DirectConnection
        )
        _varj(controller, qt_app)

        assert not kep.exists(), (
            "mappa-nézetben a Ctrl+Delete + megerősítés NEM törölte a "
            "fájlt — a lemezről törlés ága elromlott"
        )

    def test_a_helyi_menupont_mappaban_TOVABBRA_IS_torol(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        kep = tmp_path / "kepek" / "a.jpg"
        _kijelol(window, qt_app)

        _aktival(_gyerek(window, "contextMenuDelete"), qt_app)

        confirm = _gyerek(window, "deleteConfirmDialog")
        assert confirm.property("visible") is True
        QMetaObject.invokeMethod(
            confirm, "confirmed", Qt.ConnectionType.DirectConnection
        )
        _varj(controller, qt_app)
        assert not kep.exists(), (
            "mappa-nézetben a helyi menü »Törlés lemezről« tétele nem "
            "törölt — a lemezről törlés ága elromlott"
        )


class TestAlbumNezetbenNemTorolARacsBillentyuje:
    """Album-nézet: a fájl a LEMEZEN MARAD, csak az albumból esik ki."""

    def test_a_fajl_a_lemezen_marad(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        _album_nezet(lib, tmp_path, controller, qt_app)
        assert controller.currentAlbumToken == _TOKEN
        kep = lib / "a.jpg"
        assert kep.exists()
        _kijelol(window, qt_app)

        _ctrl_delete(window, qt_app)
        _megerositi_ha_nyilt(window, controller, qt_app)

        assert kep.exists(), (
            "ADATVESZTÉS: album-nézetben a rács Ctrl+Delete-je letörölte a "
            "fájlt a lemezről — az eredeti csak az albumból veszi ki"
        )

    def test_nem_nyilik_torles_megerosito(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        _album_nezet(tmp_path / "kepek", tmp_path, controller, qt_app)
        _kijelol(window, qt_app)

        _ctrl_delete(window, qt_app)

        assert _gyerek(window, "deleteConfirmDialog").property(
            "visible"
        ) is False, (
            "album-nézetben a rács Ctrl+Delete-je a lemezről törlést kérdezte"
        )

    def test_a_kep_kiesik_az_albumbol(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        _album_nezet(lib, tmp_path, controller, qt_app)
        _kijelol(window, qt_app)

        _ctrl_delete(window, qt_app)

        ini = (lib / ".picasa.ini").read_text(encoding="utf-8")
        assert f"albums={_TOKEN}" not in ini, (
            "album-nézetben a Ctrl+Delete-nek ki kell vennie a képet az "
            "albumból"
        )


class TestEmberekAlbumbanNemTorolARacsBillentyuje:
    """Emberek-album: ugyanaz, de az arc-címkét veszi le (megerősítéssel)."""

    def test_a_fajl_a_lemezen_marad_es_a_megerosito_nyilik(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        _szemely_nezet(lib, tmp_path, controller, qt_app)
        assert controller.currentPersonName == _ROY
        kep = lib / "a.jpg"
        _kijelol(window, qt_app)

        _ctrl_delete(window, qt_app)
        _megerositi_ha_nyilt(window, controller, qt_app)

        assert kep.exists(), (
            "ADATVESZTÉS: Emberek-albumban a rács Ctrl+Delete-je letörölte "
            "a fájlt"
        )
        assert _gyerek(window, "deleteConfirmDialog").property(
            "visible"
        ) is False
        assert _gyerek(window, "removePeopleFacesDialog").property(
            "visible"
        ) is True, (
            "Emberek-albumban a Ctrl+Delete-nek az »Eltávolítás az Emberek "
            "albumból« megerősítőt kell nyitnia"
        )


class TestAHelyiMenuNezetenkentEGYETLEN_AtcimkezettTetel:
    """A kép helyi menüje nézetenként EGY ilyen tételt kínál.

    Az eredeti (spec 4.: `0x00730790` / `0x00731050` / `0x007355c0`)
    ugyanazt a `cmd 0x9c9a`-t hordozza mindhárom menüben, csak a felirata
    más — album- és Emberek-nézetben tehát NINCS „Törlés lemezről" tétel.
    A várt feliratok KIÍRT LITERÁLOK (#1576)."""

    def test_mappa_nezetben_csak_a_torles_lemezrol(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _menu_nyit(window, qt_app)
        try:
            torles = _gyerek(window, "contextMenuDelete")
            assert torles.property("visible") is True
            assert torles.property("text") == "Delete from Disk\tCtrl+Delete"
            assert _gyerek(window, "contextMenuRemoveFromAlbum").property(
                "visible"
            ) is False
            assert _gyerek(
                window, "contextMenuRemoveFromPeopleAlbum"
            ).property("visible") is False
        finally:
            _menu_zar(window, qt_app)

    def test_album_nezetben_nincs_torles_lemezrol_tetel(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        _album_nezet(tmp_path / "kepek", tmp_path, controller, qt_app)
        _menu_nyit(window, qt_app)
        try:
            assert _gyerek(window, "contextMenuDelete").property(
                "visible"
            ) is False, (
                "album-nézetben az eredeti NEM kínál lemezről törlést a kép "
                "helyi menüjében (spec 4., 0x00731050)"
            )
            eltavolit = _gyerek(window, "contextMenuRemoveFromAlbum")
            assert eltavolit.property("visible") is True
            assert eltavolit.property("text") == (
                "Remove from Album\tCtrl+Delete"
            ), "az átcímkézett tétel viszi a Ctrl+Delete-et (azonos cmd)"
        finally:
            _menu_zar(window, qt_app)

    def test_emberek_albumban_nincs_torles_lemezrol_tetel(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        _szemely_nezet(tmp_path / "kepek", tmp_path, controller, qt_app)
        _menu_nyit(window, qt_app)
        try:
            assert _gyerek(window, "contextMenuDelete").property(
                "visible"
            ) is False, (
                "Emberek-albumban az eredeti NEM kínál lemezről törlést "
                "(spec 4., 0x007355c0)"
            )
            eltavolit = _gyerek(window, "contextMenuRemoveFromPeopleAlbum")
            assert eltavolit.property("visible") is True
            assert eltavolit.property("text") == (
                "Remove from People Album\tCtrl+Delete"
            )
        finally:
            _menu_zar(window, qt_app)


class TestAHelyiMenupontraKattintva:
    """A menüpont AKTIVÁLÁSA ugyanazt teszi, amit a billentyű — a felirat
    és a művelet nem csúszhat el egymástól."""

    def test_album_nezetben_a_menupont_nem_torol(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        _album_nezet(lib, tmp_path, controller, qt_app)
        _kijelol(window, qt_app)

        _aktival(_gyerek(window, "contextMenuRemoveFromAlbum"), qt_app)
        _megerositi_ha_nyilt(window, controller, qt_app)

        assert (lib / "a.jpg").exists()
        assert _gyerek(window, "deleteConfirmDialog").property(
            "visible"
        ) is False
        ini = (lib / ".picasa.ini").read_text(encoding="utf-8")
        assert f"albums={_TOKEN}" not in ini

    def test_emberek_albumban_a_menupont_nem_torol(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        _szemely_nezet(lib, tmp_path, controller, qt_app)
        _kijelol(window, qt_app)

        _aktival(
            _gyerek(window, "contextMenuRemoveFromPeopleAlbum"), qt_app
        )
        _megerositi_ha_nyilt(window, controller, qt_app)

        assert (lib / "a.jpg").exists()
        assert _gyerek(window, "removePeopleFacesDialog").property(
            "visible"
        ) is True


class TestANezetVISSZAVALTASA_IS_Kovetkezik:
    """A nézetből kilépve a rács Ctrl+Delete-je újra lemezről töröl."""

    def test_albumbol_mappara_visszaterve_ujra_torol(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        _album_nezet(lib, tmp_path, controller, qt_app)
        assert controller.currentAlbumToken == _TOKEN

        controller.selectFolder(str(lib))
        qt_app.processEvents()
        assert controller.currentAlbumToken == ""

        _kijelol(window, qt_app)
        _ctrl_delete(window, qt_app)

        assert _gyerek(window, "deleteConfirmDialog").property(
            "visible"
        ) is True, (
            "a mappába visszatérve a Ctrl+Delete nem törölt — a "
            "nézet-jelzés csak befelé frissült"
        )
