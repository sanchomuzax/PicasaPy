"""#1608 — a menüsáv `Delete` billentyűje NÉZETFÜGGŐ (adatvesztés-javítás).

## Az eredeti — bizonyíték

`docs/specs/picasa-gyorsbillentyuk.md` 5. szakasza (két független forrás):
a hivatalos szövegforrás ugyanarra a `Delete` billentyűre teszi az
`IDS_DELETE_FROM_DISK` („Törlés lemezről") és az `IDS_REMOVE_FROM_LABEL`
(„Eltávolítás az albumból") tételt, és a #1154 rekord-mérése szerint a
`0x9c9a` parancsazonosító nézetfüggő: mappa → lemezről törlés (Lomtár),
album → eltávolítás az albumból, Emberek-album → eltávolítás az Emberek
albumból. Az utóbbi kettőnél **a fájl a lemezen marad**.

## Nálunk — a MAI állapot (a javítás előtt MÉRVE, 2026-08-27)

`PicasaMenuBar.qml` `shortcutDeleteFromDisk` feltétel nélkül
`bar.deleteRequested()`-et hívott, tehát album-nézetben is a lomtárba
tette a fájlt. Ez ADATVESZTÉS.

## A teszt mércéje

⚠️ Valódi billentyűesemény megy az ablakra (a #1417/#1418 mintája), nem a
kezelő közvetlen hívása — a #1148/#1200 pont ettől a rövidítéstől maradt
zöld egy hatástalan funkció fölött.

⚠️ A „lemezen marad" állítást a LEMEZEN mérjük: a művelet után a fájl
`Path.exists()`-ét nézzük, nem a hívás visszatérését.

⚠️ **Kétirányú őr.** A mappa-nézeti ág külön tesztben KÖVETELI a törlést —
enélkül a „soha ne törölj" megoldás is átmenne rajta.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Q_ARG, QEvent, QMetaObject, QObject, Qt
from PySide6.QtGui import QKeyEvent

from picasapy.index import open_index, sync_tree

_TOKEN = "604c294a68b0de9cc9222c4714f289d5"
_ROY_ID = "b8e4117cf1d6615b"
_ROY = "Roy Avery"
_RECT = "3f840000c3509f84"


def _gyerek(window, nev):
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"a(z) {nev} nem található"
    return elem


def _nem_nyilt_meg(window) -> bool:
    """#1612 óta a törlés-megerősítő HALASZTOTT: ha a Delete nem a lemezről
    törlés ágára ment, a párbeszéd létre sem jön. A hiánya erősebb állítás,
    mint a `visible is False` — de mindkettőt elfogadjuk, mert a párbeszédet
    egy korábbi lépés már felépíthette ugyanabban a tesztben."""
    par = window.findChild(QObject, "deleteConfirmDialog")
    return par is None or par.property("visible") is False


def _fokusz(elem, qt_app):
    elem.setProperty("focus", True)
    QMetaObject.invokeMethod(
        elem, "forceActiveFocus", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()


def _delete_billentyu(window, qt_app):
    """PUSZTA `Delete` az ablakra — ezt köti a menüsáv Shortcutja."""
    qt_app.sendEvent(
        window,
        QKeyEvent(
            QEvent.Type.KeyPress,
            Qt.Key.Key_Delete,
            Qt.KeyboardModifier.NoModifier,
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

    A helyes ágon soha nem nyílik meg, tehát ez ott nem csinál semmit; a
    HIBÁS ágon viszont végigviszi a törlést, és így a hívó „a fájl a
    lemezen maradt" állítása valódi mérés lesz."""
    confirm = window.findChild(QObject, "deleteConfirmDialog")
    if confirm is None or not confirm.property("visible"):
        return  # #1612: halasztott — létre sem jött, tehát nem is nyílt meg
    assert confirm.property("trashAvailable"), (
        "a teszt-környezetben nincs lomtár — a mérés nem érvényes"
    )
    QMetaObject.invokeMethod(
        confirm, "confirmed", Qt.ConnectionType.DirectConnection
    )
    _varj(controller, qt_app)


def _album_nezet(lib, tmp_path, controller, qt_app):
    """Album a `qml_app` fixture mappájában (a.jpg tag), majd album-nézet.

    A `test_album_context_menu.py` `_add_album_membership` mintája.
    """
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
    """Egy névvel taggelt arc az a.jpg-n, majd Emberek-album nézet.

    A `test_people_controller.py` `library` fixture-ének mintája.
    """
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

    def test_delete_a_mappa_nezetben_torlest_kerdez(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        assert controller.currentAlbumToken == ""
        assert controller.currentPersonName == ""
        _kijelol(window, qt_app)
        assert _nem_nyilt_meg(window)

        _delete_billentyu(window, qt_app)

        assert _gyerek(window, "deleteConfirmDialog").property("visible") is True, (
            "mappa-nézetben a Delete-nek TOVÁBBRA IS a lemezről törlést "
            "kell kérdeznie (#1608 nem szüntetheti meg a mappa-ágat)"
        )

    def test_a_mappa_nezet_a_kijelolt_fajlt_celozza(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _kijelol(window, qt_app)

        _delete_billentyu(window, qt_app)

        confirm = _gyerek(window, "deleteConfirmDialog")
        utak = confirm.property("paths")
        if hasattr(utak, "toVariant"):
            utak = utak.toVariant()
        vart = Path(controller.watchedFolders[0]) / "a.jpg"
        assert [Path(p) for p in utak] == [vart]

    def test_megerositve_a_fajl_TENYLEG_eltunik_a_lemezrol(
        self, qml_app, qt_app, tmp_path
    ):
        """A destruktív ág VÉGIG él: a `Delete` → megerősítés úton a fájl
        eltűnik a lemezről (a `test_torles_frissites_1181.py` mintája —
        valódi lomtár-művelet, nem mock)."""
        window, controller, _engine = qml_app
        kep = tmp_path / "kepek" / "a.jpg"
        assert kep.exists()
        _kijelol(window, qt_app)

        _delete_billentyu(window, qt_app)

        confirm = _gyerek(window, "deleteConfirmDialog")
        assert confirm.property("trashAvailable"), (
            "a teszt-környezetben nincs lomtár — a mérés nem érvényes"
        )
        QMetaObject.invokeMethod(
            confirm, "confirmed", Qt.ConnectionType.DirectConnection
        )
        _varj(controller, qt_app)

        assert not kep.exists(), (
            "mappa-nézetben a Delete + megerősítés NEM törölte a fájlt — "
            "a lemezről törlés ága elromlott"
        )


class TestAlbumNezetbenNemTorol:
    """Album-nézet: a fájl a LEMEZEN MARAD, csak az albumból esik ki."""

    def test_a_fajl_a_lemezen_marad(self, qml_app, qt_app, tmp_path):
        """⚠️ A `Delete` leütése ÖNMAGÁBAN sosem töröl — a hibás ágon is
        csak egy megerősítőt nyit. Ezért a teszt VÉGIGVISZI a felhasználó
        útját: ha megerősítő nyílt, azt le is nyomja. Enélkül a „lemezen
        marad" állítás foga nélkül maradna (a fájl a hibás kódnál is
        megvolna a művelet felénél)."""
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        _album_nezet(lib, tmp_path, controller, qt_app)
        assert controller.currentAlbumToken == _TOKEN
        kep = lib / "a.jpg"
        assert kep.exists()
        _kijelol(window, qt_app)

        _delete_billentyu(window, qt_app)
        _megerositi_ha_nyilt(window, controller, qt_app)

        assert kep.exists(), (
            "ADATVESZTÉS: album-nézetben a Delete letörölte a fájlt a "
            "lemezről — az eredeti csak az albumból veszi ki"
        )

    def test_nem_nyilik_torles_megerosito(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        _album_nezet(tmp_path / "kepek", tmp_path, controller, qt_app)
        _kijelol(window, qt_app)

        _delete_billentyu(window, qt_app)

        assert _nem_nyilt_meg(window), "album-nézetben a Delete a lemezről törlést kérdezte"

    def test_a_kep_kiesik_az_albumbol(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        _album_nezet(lib, tmp_path, controller, qt_app)
        _kijelol(window, qt_app)

        _delete_billentyu(window, qt_app)

        ini = (lib / ".picasa.ini").read_text(encoding="utf-8")
        assert f"albums={_TOKEN}" not in ini, (
            "album-nézetben a Delete-nek ki kell vennie a képet az albumból"
        )


class TestEmberekAlbumbanNemTorol:
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

        _delete_billentyu(window, qt_app)
        # ugyanaz a fogas mérce, mint az album-ágon: a felhasználó útját
        # végigvisszük, hogy a „lemezen marad" ne üres állítás legyen
        _megerositi_ha_nyilt(window, controller, qt_app)

        assert kep.exists(), (
            "ADATVESZTÉS: Emberek-albumban a Delete letörölte a fájlt"
        )
        assert _nem_nyilt_meg(window)
        assert _gyerek(window, "removePeopleFacesDialog").property(
            "visible"
        ) is True, (
            "Emberek-albumban a Delete-nek az »Eltávolítás az Emberek "
            "albumból« megerősítőt kell nyitnia"
        )


class TestAMenuteteFeliratKovetiANezetet:
    """A Fájl ▸ menütétel felirata a nézettel együtt vált.

    A várt szövegek KIÍRT LITERÁLOK (a #1576 első köre épp azért nyelte el
    a hibát, mert a termék konstansából vette a várt értéket). A fixture
    nem telepít QTranslator-t, ezért itt az ANGOL forrásszöveg látszik; a
    magyar feliratot a `tests/app/test_album_delete_feliratok_1608.py`
    méri a `.ts`-ből."""

    def test_mappa_nezetben_torles_lemezrol(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        tetel = _gyerek(window, "menuFileDelete")
        assert tetel.property("text") == "Delete from Disk\tDelete"

    def test_album_nezetben_eltavolitas_az_albumbol(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        _album_nezet(tmp_path / "kepek", tmp_path, controller, qt_app)
        tetel = _gyerek(window, "menuFileDelete")
        assert tetel.property("text") == "Remove from Album\tDelete"

    def test_emberek_albumban_a_sajat_felirata(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        _szemely_nezet(tmp_path / "kepek", tmp_path, controller, qt_app)
        tetel = _gyerek(window, "menuFileDelete")
        assert tetel.property("text") == "Remove from People Album\tDelete"


class TestAMenutetelUgyanaztCsinaljaMintABillentyu:
    """A menütételre KATTINTVA is a nézetfüggő út fut (nem csak a
    billentyűn keresztül) — a felirat és a művelet nem csúszhat el."""

    def test_a_menutetel_album_nezetben_nem_torol(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        _album_nezet(lib, tmp_path, controller, qt_app)
        _kijelol(window, qt_app)
        tetel = _gyerek(window, "menuFileDelete")

        QMetaObject.invokeMethod(
            tetel, "triggered", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        assert (lib / "a.jpg").exists()
        assert _nem_nyilt_meg(window)
        ini = (lib / ".picasa.ini").read_text(encoding="utf-8")
        assert f"albums={_TOKEN}" not in ini


class TestANezetVISSZAVALTASA_IS_Kovetkezik:
    """A nézetből KILÉPVE a felirat és a művelet is visszaáll.

    Ez a `currentPersonName` jelzés-hibájának a másik iránya: ha a
    tulajdonság csak befelé frissül, a mappába visszatérő felhasználó
    „Eltávolítás az Emberek albumból" feliratot látna, és a `Delete`
    NEM törölne. A #1608 mellékleletje: a `currentPersonName` `notify`-ja
    eredetileg a `peopleChanged` volt, ami nézetváltáskor nem megy ki."""

    def test_emberek_albumbol_mappara_visszaterve_ujra_torol(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        lib = tmp_path / "kepek"
        _szemely_nezet(lib, tmp_path, controller, qt_app)
        assert _gyerek(window, "menuFileDelete").property("text") == (
            "Remove from People Album\tDelete"
        )

        controller.selectFolder(str(lib))
        qt_app.processEvents()

        assert controller.currentPersonName == ""
        assert _gyerek(window, "menuFileDelete").property("text") == (
            "Delete from Disk\tDelete"
        ), "a mappába visszatérve a felirat az Emberek-albumén maradt"
        _kijelol(window, qt_app)
        _delete_billentyu(window, qt_app)
        assert _gyerek(window, "deleteConfirmDialog").property(
            "visible"
        ) is True, (
            "a mappába visszatérve a Delete nem törölt — a nézet-jelzés "
            "csak befelé frissült"
        )


class TestAHelyiMenuEmberekTeteleELETRE_KELT:
    """MELLÉKLELET (#1608): a helyi menü #422-es Emberek-tétele HALOTT volt.

    Mérve (2026-08-27, a javítás előtt): Emberek-album nézetben a
    `contextMenuRemoveFromPeopleAlbum` `visible` értéke **False** maradt,
    mert a `currentPersonName` `notify`-ja a `peopleChanged` volt — az
    pedig csak az Emberek-LISTA frissülésekor megy ki, nem nézetváltáskor.
    A tétel így csak egy véletlen háttér-szinkron után jelent meg.

    A `menuFileDelete` nézetfüggése ugyanezen a jelzésen áll, ezért az őr
    ide tartozik: ha a jelzés visszaromlik, mindkettő elnémul."""

    def test_a_szemely_tetel_latszik_az_emberek_albumban(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _engine = qml_app
        _szemely_nezet(tmp_path / "kepek", tmp_path, controller, qt_app)
        _kijelol(window, qt_app)
        grid = _gyerek(window, "photoGrid")
        QMetaObject.invokeMethod(
            window, "openPhotoContextMenu", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 0), Q_ARG("QVariant", grid),
            Q_ARG("QVariant", 5), Q_ARG("QVariant", 5),
        )
        qt_app.processEvents()
        try:
            tetel = _gyerek(window, "contextMenuRemoveFromPeopleAlbum")
            assert tetel.property("visible") is True, (
                "az Emberek-album helyi menüjének tétele nem látszik — a "
                "nézet-jelzés (personViewChanged) visszaromlott"
            )
        finally:
            menu = _gyerek(window, "photoContextMenu")
            QMetaObject.invokeMethod(
                menu, "close", Qt.ConnectionType.DirectConnection
            )
            qt_app.processEvents()

