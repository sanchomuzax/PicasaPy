"""A Mappakezelő OK-jának MENTÉSI ÚTJA: sorrend és kapu (#1334).

Az eredeti Picasa OK-kezelője (`0x007c4df0`) egyetlen mentő függvényt hív
(`0x005cef20`), és az **meghatározott sorrendben** dolgozik:

1. `watchedfolders.txt` (`0x005cf49b`),
2. `]album:removed` sírkövek (`0x005cf500`),
3. `frexcludefolders.txt` (`0x005cf529`) — **kapuzva**: csak akkor, ha a
   hozzáadandó VAGY az eltávolítandó lista nem üres,
4. záró lépés: a nézet frissítése (`0x005cf535`).

Nálunk EDDIG nem volt mentési út: a párbeszéd OK-ja tételenként hívta a
vezérlőt, és minden hívás azonnal, a többitől függetlenül írt fájlt (a
`watchedfolders.txt` annyiszor, ahány mappa változott). Ez a teszt a
sorrendet és a kaput állítja — nem csak azt, hogy a fájlok elkészülnek.

Levezetés: `docs/specs/picasa-mappakezelo.md` 17. szakasz.
"""

import pytest

from support.jpeg_factory import make_jpeg


@pytest.fixture
def vezerlo(qt_app, tmp_path):
    """Vezérlő VALÓDI listafájlokkal, ideiglenes könyvtárban.

    ⚠️ A `watched_file`/`exclude_file` kötelezően `tmp_path` alatt van: a
    tesztek soha nem írhatnak a felhasználó valódi Picasa-adatmappájába
    (a `user_folder_guard` fixture-őr ezt figyeli is)."""
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache
    from PySide6.QtCore import QSettings

    lib = tmp_path / "kepek"
    lib.mkdir()
    make_jpeg(lib / "a.jpg", size=(32, 24))
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db",
        (str(lib),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
        exclude_file=tmp_path / "FRExcludeFolders.txt",
    )
    ctl._reload()
    yield ctl, lib, tmp_path
    assert ctl.waitForBackgroundWorkers(30.0), (
        "háttérszál nem állt le a controller teardownban (#430/#438)"
    )


class TestMentesiUtSorrend:
    """A tiszta mentési út (a `0x005cef20` megfelelője) — sorrend-őr."""

    def test_a_negy_lepes_sorrendje_kotott(self):
        from picasapy.app.folder_manager_save import (
            STEP_EXCLUDE,
            STEP_FINISH,
            STEP_TOMBSTONE,
            STEP_WATCHED,
            FolderManagerSavePlan,
            save_folder_manager,
        )

        naplo = []
        terv = FolderManagerSavePlan(
            watched=("/a",),
            tombstones=("/b",),
            faces_excluded=("/c",),
            faces_added=("/c",),
        )
        lepesek = save_folder_manager(
            terv,
            write_watched=lambda mappak: naplo.append(("watched", mappak)),
            write_tombstones=lambda mappak: naplo.append(("tombstone", mappak)),
            write_faces=lambda mappak: naplo.append(("frexclude", mappak)),
            finish=lambda: naplo.append(("finish", ())),
        )

        assert lepesek == (STEP_WATCHED, STEP_TOMBSTONE, STEP_EXCLUDE, STEP_FINISH)
        assert [nev for nev, _ in naplo] == [
            "watched",
            "tombstone",
            "frexclude",
            "finish",
        ]

    def test_a_lepesek_a_terv_adatait_kapjak(self):
        from picasapy.app.folder_manager_save import (
            FolderManagerSavePlan,
            save_folder_manager,
        )

        naplo = {}
        terv = FolderManagerSavePlan(
            watched=("/a", "/b"),
            tombstones=("/regi",),
            faces_excluded=("/arc",),
            faces_removed=("/vissza",),
        )
        save_folder_manager(
            terv,
            write_watched=lambda mappak: naplo.setdefault("watched", mappak),
            write_tombstones=lambda mappak: naplo.setdefault("tombstone", mappak),
            write_faces=lambda mappak: naplo.setdefault("frexclude", mappak),
            finish=lambda: None,
        )

        assert naplo["watched"] == ("/a", "/b")
        assert naplo["tombstone"] == ("/regi",)
        assert naplo["frexclude"] == ("/arc",)


class TestFrexcludeKapu:
    """A kapu: a `frexcludefolders.txt` csak akkor íródik, ha a KÉT
    lista (hozzáadandó / eltávolítandó) bármelyike nem üres."""

    def test_ures_listaknal_nem_irodik(self):
        from picasapy.app.folder_manager_save import (
            STEP_EXCLUDE,
            STEP_FINISH,
            STEP_TOMBSTONE,
            STEP_WATCHED,
            FolderManagerSavePlan,
            save_folder_manager,
        )

        irtak = []
        lepesek = save_folder_manager(
            FolderManagerSavePlan(watched=("/a",), faces_excluded=("/regi-kizart",)),
            write_watched=lambda mappak: None,
            write_tombstones=lambda mappak: None,
            write_faces=lambda mappak: irtak.append(mappak),
            finish=lambda: None,
        )

        assert irtak == [], "üres-üres esetben nem szabad írni a frexclude fájlt"
        assert lepesek == (STEP_WATCHED, STEP_TOMBSTONE, STEP_FINISH)
        assert STEP_EXCLUDE not in lepesek

    @pytest.mark.parametrize(
        ("hozzaadando", "eltavolitando"),
        [(("/uj",), ()), ((), ("/regi",)), (("/uj",), ("/regi",))],
    )
    def test_barmelyik_lista_nyitja(self, hozzaadando, eltavolitando):
        from picasapy.app.folder_manager_save import (
            STEP_EXCLUDE,
            FolderManagerSavePlan,
            save_folder_manager,
        )

        lepesek = save_folder_manager(
            FolderManagerSavePlan(
                faces_added=hozzaadando, faces_removed=eltavolitando
            ),
            write_watched=lambda mappak: None,
            write_tombstones=lambda mappak: None,
            write_faces=lambda mappak: None,
            finish=lambda: None,
        )

        assert STEP_EXCLUDE in lepesek


def _naplozo(monkeypatch, naplo):
    """A vezérlő tényleges íróit naplózóra cseréli — így a SORREND a
    valódi OK-úton mérhető, nem csak a tiszta függvényben.

    MINDKÉT modult lefedjük: a mentési útét
    (`folder_manager_save_controller`) és a tételes, azonnali írásokét
    (`library_controller`) — különben egy visszaszivárgó azonnali írás
    észrevétlen maradna."""
    import picasapy.app.folder_manager_save_controller as fmsc
    import picasapy.app.library_controller as lc

    valodi_watched = fmsc.write_watched_folders
    valodi_exclude = fmsc.write_exclude_folders
    valodi_sirko = fmsc.add_removed_folder
    valodi_scanlist = lc.write_scan_list

    def watched(path, folders):
        naplo.append("watchedfolders")
        valodi_watched(path, folders)

    def exclude(path, folders):
        naplo.append("frexclude")
        valodi_exclude(path, folders)

    def sirko(conn, path):
        naplo.append("tombstone")
        valodi_sirko(conn, path)

    def scanlist(path, *args, **kwargs):
        naplo.append("scanlist")
        valodi_scanlist(path, *args, **kwargs)

    for modul in (fmsc, lc):
        monkeypatch.setattr(modul, "write_watched_folders", watched)
        monkeypatch.setattr(modul, "write_exclude_folders", exclude)
    monkeypatch.setattr(fmsc, "add_removed_folder", sirko)
    monkeypatch.setattr(lc, "write_scan_list", scanlist)


class TestVezerloOkUtja:
    """A vezérlő OK-útja: egyetlen mentés, a mért sorrendben."""

    def test_a_valodi_iras_sorrendje(self, vezerlo, monkeypatch, qt_app):
        ctl, lib, tmp_path = vezerlo
        masik = tmp_path / "masik"
        masik.mkdir()
        naplo = []
        _naplozo(monkeypatch, naplo)

        ctl.beginFolderManagerSave()
        try:
            ctl.addWatchedFolder(str(masik))
            ctl.setFaceDetectionEnabled(str(lib), False)
            ctl.removeFolder(str(lib))
        finally:
            ctl.commitFolderManagerSave()
        assert ctl.waitForBackgroundWorkers(30.0)
        qt_app.processEvents()

        assert naplo == ["watchedfolders", "tombstone", "frexclude"], (
            f"a mentés sorrendje nem a mért: {naplo}"
        )

    def test_a_watchedfolders_egyszer_irodik(self, vezerlo, monkeypatch, qt_app):
        """⚠️ Ma tételenként íródott — három mappaváltás három írás volt."""
        ctl, _lib, tmp_path = vezerlo
        naplo = []
        _naplozo(monkeypatch, naplo)

        ctl.beginFolderManagerSave()
        try:
            for nev in ("egy", "ketto", "harom"):
                mappa = tmp_path / nev
                mappa.mkdir()
                ctl.addWatchedFolder(str(mappa))
        finally:
            ctl.commitFolderManagerSave()
        assert ctl.waitForBackgroundWorkers(30.0)
        qt_app.processEvents()

        assert naplo.count("watchedfolders") == 1, (
            f"a figyelt mappák fájlja {naplo.count('watchedfolders')}-szor íródott"
        )

    def test_ures_ok_nem_nyul_a_frexcludehoz(self, vezerlo, qt_app):
        """A kapu a valódi fájlon: arc-változás nélkül az `mtime` marad."""
        ctl, _lib, tmp_path = vezerlo
        frexclude = tmp_path / "FRExcludeFolders.txt"
        frexclude.write_text("/regi\n", encoding="utf-8")
        elotte = frexclude.stat().st_mtime_ns

        ctl.beginFolderManagerSave()
        ctl.commitFolderManagerSave()
        qt_app.processEvents()

        assert frexclude.stat().st_mtime_ns == elotte, (
            "a frexcludefolders.txt üres-üres esetben is íródott"
        )
        assert frexclude.read_text(encoding="utf-8") == "/regi\n"

    def test_ures_ok_nem_nyul_a_scanlisthez(self, vezerlo, qt_app):
        """A `scanlist.txt` a mentési útból NEM érhető el (17.2).

        ⚠️ Amit ez a teszt NEM állít: nálunk a `scanlist.txt` a
        HÁROMÁLLAPOTÚ választó tárhelye, és a `setFolderManagerState`
        továbbra is írja, ha a felhasználó ténylegesen állapotot vált —
        ld. a jegy zárójelentését."""
        ctl, _lib, tmp_path = vezerlo
        scanlist = tmp_path / "scanlist.txt"
        scanlist.write_text("", encoding="utf-8")
        elotte = scanlist.stat().st_mtime_ns

        ctl.beginFolderManagerSave()
        ctl.commitFolderManagerSave()
        qt_app.processEvents()

        assert scanlist.stat().st_mtime_ns == elotte, (
            "a mentési út hozzányúlt a scanlist.txt-hez"
        )

    def test_a_zaro_lepes_lefut(self, vezerlo, qt_app):
        ctl, _lib, _tmp_path = vezerlo
        from picasapy.app.folder_manager_save import STEP_FINISH, STEP_WATCHED

        ctl.beginFolderManagerSave()
        lepesek = ctl.commitFolderManagerSave()
        qt_app.processEvents()

        assert list(lepesek)[0] == STEP_WATCHED
        assert list(lepesek)[-1] == STEP_FINISH


class TestQmlOkGomb:
    """A vezérlőre KATTINTUNK: a párbeszéd OK gombja tényleg a mentési
    utat futtatja (nem elég, hogy a slot létezik)."""

    def test_ok_gomb_a_mentesi_utat_futtatja(self, qml_app, qt_app):
        from PySide6.QtCore import QMetaObject, QObject, Qt

        from picasapy.app.folder_manager_save import (
            STEP_EXCLUDE,
            STEP_FINISH,
            STEP_TOMBSTONE,
            STEP_WATCHED,
        )

        window, controller, lib, _engine = qml_app
        dialog = window.findChild(QObject, "folderManagerDialog")
        assert dialog is not None
        dialog.setProperty("selectedPath", str(lib))
        qt_app.processEvents()

        QMetaObject.invokeMethod(
            window.findChild(QObject, "faceDetectionToggle"),
            "toggle",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()
        QMetaObject.invokeMethod(
            window.findChild(QObject, "folderManagerOkButton"),
            "clicked",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()
        QMetaObject.invokeMethod(
            window.findChild(QObject, "faceDetectionConfirmYesButton"),
            "clicked",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        assert controller._fm_last_steps == [
            STEP_WATCHED,
            STEP_TOMBSTONE,
            STEP_EXCLUDE,
            STEP_FINISH,
        ]
