"""A könyvtár-vezérlő resync felelősségei (#6137)."""

from __future__ import annotations

import importlib
import sys

import os
import sqlite3
from pathlib import Path

from PySide6.QtCore import Qt, Slot
from picasapy.fileops import FolderRenameError, rename_folder
from picasapy.fileops.rename_folder import restore_folder_rename
from picasapy.index import folder_paths_under, open_index
from picasapy.index.queries import carry_pending_hidden
from picasapy.paths import normalize_path, path_key

from .exported_folders import (
    EXPORTED_FOLDERS_SETTINGS_KEY,
    existing_exported_folders,
)
from .formatting import to_local_path


def _legacy():
    """A régi modulból olvassa az örökölt, tesztek által foltozható neveket."""
    return sys.modules.get(
        f"{__package__}.library_controller"
    ) or importlib.import_module(".library_controller", __package__)


class LibraryResyncMixin:
    @Slot(str, str, result="QVariantMap")
    def renameFolder(self, folder_path: str, new_name: str) -> dict:
        """Mappanév módosítása úgy, hogy az index metaadatai is kövessék (#4482).

        A mappa a lemezen egyetlen átnevezéssel változik, majd az index
        meglévő `move_folder_tree` API-ja az összes útvonalat átírja. Ha az
        index frissítése hibázik, a lemezes átnevezés visszagördül; a watcher
        jelzése csak a QML-szál visszatérése után dolgozódik fel.
        """
        local_path = to_local_path(folder_path)
        if not local_path:
            return {"ok": False, "error": "A mappa útvonala hiányzik."}
        source = Path(normalize_path(local_path))
        for editor in getattr(self, "_edit_controllers", ()):
            active_path = getattr(editor, "_image_path", None)
            if active_path is None:
                continue
            try:
                inside_renamed_tree = Path(
                    normalize_path(active_path)
                ).is_relative_to(source)
            except (OSError, RuntimeError, ValueError):
                inside_renamed_tree = False
            if inside_renamed_tree:
                return {
                    "ok": False,
                    "error": (
                        "A mappa nem nevezhető át, amíg egy benne lévő kép "
                        "szerkesztés alatt áll. Zárja be a szerkesztőt, majd "
                        "próbálja újra."
                    ),
                }
        try:
            target = rename_folder(source, new_name)
        except (FolderRenameError, ValueError, OSError) as error:
            return {"ok": False, "error": str(error)}
        # A Path equality check is case-insensitive on Windows, but a
        # case-only rename still needs to update the index and UI paths.
        if str(target) == str(source):
            return {"ok": True, "path": str(source), "name": source.name}

        try:
            with open_index(self._db_path) as conn:
                _legacy().move_folder_tree(conn, source, target)
        except (ValueError, sqlite3.Error, OSError) as error:
            try:
                restore_folder_rename(target, source)
            except (FolderRenameError, OSError) as rollback_error:
                _legacy().logger.exception(
                    "#4482: az indexhiba után a mappát nem sikerült "
                    "visszaállítani (%s → %s)",
                    target,
                    source,
                )
                # Ha a lemez is elutasítja a visszaállítást, a meglévő
                # részfa-szinkron próbálja az indexet a tényleges állapothoz
                # igazítani; az eredeti hibaüzenet mellett ezt is jelezzük.
                self.resyncMovedFolder(str(source), str(target))
                return {
                    "ok": False,
                    "error": (
                        "Az index frissítése nem sikerült, és a mappa "
                        f"visszaállítása is hibázott: {rollback_error}. "
                        f"Az index újraolvasása elindult. Részlet: {error}"
                    ),
                }
            return {
                "ok": False,
                "error": (
                    "Az index frissítése nem sikerült; a mappa eredeti "
                    f"neve visszaállt. Részlet: {error}"
                ),
            }

        # Ha maga a figyelt gyökér változott meg, a perzisztens gyökérlista
        # és az OS-figyelő is az új útvonalra áll át.
        watched_root = self._find_root(str(source))
        if watched_root is not None and path_key(watched_root) == path_key(source):
            self._roots = [
                str(target) if path_key(root) == path_key(watched_root) else root
                for root in self._roots
            ]
            self._persist_roots()
            self._restart_watcher()

        # A kijelölt mappa és az alatta kiválasztott képútvonal is az új
        # előtagot kapja; a QML a friss modellekből olvassa újra a listát.
        current = Path(self._current_folder) if self._current_folder else None
        if current is not None:
            try:
                relative = current.relative_to(source)
            except ValueError:
                pass
            else:
                updated = str(target / relative)
                self._current_folder = updated
                if self._view_mode[0] == "folder":
                    self._view_mode = ("folder", updated)
                self._get_settings().setValue("session/lastFolder", updated)

        self._descriptions.clear()
        self._reload(preserve_scroll=True)
        self.statusChanged.emit()
        return {"ok": True, "path": str(target), "name": target.name}

    # SZÁNDÉKOSAN nincs `@Slot`: a hívó a `wire_fileops` PYTHON-oldali
    # kötése (`folderMoved` → itt), a QML soha nem hívja. Slotként a
    # `kepesseg_or.py` joggal jelezné felületről elérhetetlen képességnek.
    def resyncMovedFolder(self, old_path: str, new_path: str) -> None:  # noqa: N802
        """Egy ÁTHELYEZETT MAPPA két végének célzott újraolvasása (#1538).

        A `resyncFolder` itt két okból nem elég:

        1. **A mappa MAGA az érintett**, nem a szülője. A `wire_fileops`
           `refresh()`-e fájlutakra van szabva (`_watched_folder_of` a
           `.parent`-et veszi) — mappára alkalmazva a SZÜLŐT olvasná újra,
           az pedig nem-rekurzív, tehát az áthelyezett mappa sora létre sem
           jönne.
        2. **A részfa is mozdul.** A `sync_folder` egyetlen mappát olvas,
           az almappák sorai a régi (már nem létező) út alatt ragadnának.

        Ezért mindkét oldal RÉSZFAKÉNT megy be a szokásos célzott
        szinkronba (`_on_folders_dirty`):

        * az ÚJ oldal a lemezről (az indexben még nincs benne),
        * a RÉGI oldal az indexből (a lemezen már nincs meg).

        A takarítás így is mappánként, a `sync_folder` `folder_looks_offline`
        próbáján át történik: elérhetetlen (nem eltűnt) mappa sorai
        megmaradnak, offline jelöléssel — nem törlünk olyan sort, amiről
        nem tudjuk, hogy elavult.

        Mérés a javítás előtt (valódi vezérlő, produkciós időzítők; a
        részletek a `tests/app/test_mappa_athelyezes_resync_1538.py`
        docstringjében): figyelő nélkül az ÚJ hely 25 s alatt sem jelent
        meg, miközben a #1275 lekérdezés a RÉGI helyet 4,7 s alatt kiszedte
        az indexből — a felhasználó képei tehát az ötperces rescanig SEHOL
        nem voltak meg. Ugyanez EGY KÉPPEL 0,11 s."""
        regi = normalize_path(to_local_path(old_path))
        uj = normalize_path(to_local_path(new_path))
        if not regi or not uj:
            return
        # #1542: ha MAGA a figyelt gyökér mozdult el, előbb a HORGONYT
        # állítjuk helyre (index + `_roots` + `WatchedFolders.txt`), és
        # csak utána megy a szokásos célzott újraolvasás — különben az új
        # hely egyetlen gyökér alá sem esne, tehát a `_on_folders_dirty`
        # némán kihagyná.
        self._kovesd_a_gyoker_athelyezeset(regi, uj)
        # #4597: a még ini-be nem írt (2-es) rejtés az új útvonalra költözik
        with open_index(self._db_path) as conn:
            carry_pending_hidden(conn, regi, uj)
        mappak = _legacy()._dedupe_paths(
            (*self._reszfa_a_lemezen(uj), *self._reszfa_az_indexbol(regi))
        )
        if mappak:
            self._on_folders_dirty(mappak)

    # SZÁNDÉKOSAN nincs `@Slot` — ugyanazért, amiért a `resyncMovedFolder`-en
    # sincs: a hívó a `wire_fileops` PYTHON-oldali kötése (`folderDeleted` →
    # itt), a QML soha nem hívja. Slotként a `kepesseg_or.py` joggal jelezné
    # felületről elérhetetlen képességnek — a CI el is bukott rajta.
    def resyncDeletedFolder(self, path: str) -> None:  # noqa: N802
        """A LOMTÁRBA tett mappa kivezetése az indexből (#1638).

        A `resyncMovedFolder` (#1538) régi oldalával azonos út: a részfát az
        INDEXBŐL kérdezzük, mert a lemezen már nincs meg. Új oldal nincs,
        ezért annak a fele elmarad.

        A takarítás itt is mappánként, a `sync_folder` `folder_looks_offline`
        próbáján át történik: elérhetetlen (nem eltűnt) mappa sorai
        megmaradnak, offline jelöléssel — nem törlünk olyan sort, amiről nem
        tudjuk, hogy elavult."""
        regi = normalize_path(to_local_path(path))
        if not regi:
            return
        mappak = _legacy()._dedupe_paths(self._reszfa_az_indexbol(regi))
        if mappak:
            self._on_folders_dirty(mappak)

    def _kovesd_a_gyoker_athelyezeset(self, regi: str, uj: str) -> bool:
        """A FIGYELT GYÖKÉR áthelyezésének követése (#1542).

        Mérés a javítás előtt (valódi `AppController`, produkciós
        `FOLDER_POLL_MS`, kétszintű könyvtár, három kép; részletek a
        `tests/app/test_gyoker_athelyezes_kovetes_1542.py` docstringjében):
        a gyökér áthelyezése után a `_roots` és a `WatchedFolders.txt` a
        régi helyre mutatott, és **a produkciós alapbeállításban (figyelő
        és #1275 lekérdezés bekapcsolva) az index KIÜRÜLT: 3 mappa/3 fotó
        → 0/0**, a bal hasáb üres lett. A jegy leírásának az az állítása,
        hogy „nem vész el index", tehát HAMIS volt: a #1538 védelme csak a
        saját ágát fogja vissza, a lekérdezési kör viszont a látott (a
        lemezen valóban eltűnt) mappákat függetlenül kiveszi.

        A sorrend kötött, és mindegyik lépés az előző sikerére épül:

        1. az INDEX részfájának ÁTÍRÁSA az új útra (`move_folder_tree`) —
           sort nem töröl és nem hoz létre;
        2. a `_roots` és a `WatchedFolders.txt` átállítása;
        3. a figyelő újraindítása az új gyökérre;
        4. a látott mappa átvezetése, ha épp a mozgatott fát nézte.

        ## Mikor NEM követünk

        **Ha a régi hely helyén (ugyanazon a néven) MÁS mappa áll.** Ez nem
        elméleti: a felhasználó fájlkezelővel is mozgathat, és egy
        szinkron-kliens vagy az XDG újra létrehozhatja a nevet. A gyökér az
        egész könyvtár horgonya — ha a régi néven ÚJRA létezik mappa, akkor
        a figyelt út egy VALÓDI helyet nevez meg, és az átállítás azt
        jelentené, hogy némán abbahagyjuk egy létező mappa figyelését,
        ráadásul a régi mappa indexsorait egy MÁSIK fizikai mappára
        akasztjuk (útvonal szerint a kettő megkülönböztethetetlen). Ilyenkor
        inkább nem írunk, csak naplózunk — és marad a #1538 védelme: a régi
        oldal takarítása kimarad (`_reszfa_az_indexbol`).

        Ugyanígy nem követünk, ha az ÚJ hely nem létező mappa, vagy ha az
        index átírása ütközésbe fut — üres vagy hibás gyökérlistát semmilyen
        ágon nem írunk ki.

        Igazat ad, ha a gyökér ténylegesen követve lett."""
        gyoker = self._find_root(regi)
        if gyoker is None:
            return False  # nem a gyökér mozdult — a #1538 útja változatlan
        if not Path(uj).is_dir():
            _legacy().logger.warning(
                "#1542: a figyelt gyökér új helye nem létező mappa (%s) — a "
                "horgony változatlanul marad: %s",
                uj,
                gyoker,
            )
            return False
        if Path(regi).exists():
            _legacy().logger.warning(
                "#1542: a figyelt gyökér régi helyén (%s) ISMÉT áll valami — "
                "a horgonyt NEM állítjuk át %s-ra, mert az egy létező mappa "
                "figyelését hagyná abba némán.",
                regi,
                uj,
            )
            return False
        try:
            with open_index(self._db_path) as conn:
                _legacy().move_folder_tree(conn, regi, uj)
        except (ValueError, sqlite3.Error, OSError):
            # az index érintetlen maradt (a `move_folder_tree` vagy mindent
            # átír, vagy semmit) — horgonyt sem írunk át, hogy a kettő ne
            # csússzon szét
            _legacy().logger.exception(
                "#1542: az áthelyezett gyökér indexsorait nem sikerült "
                "átírni (%s → %s) — a horgony változatlan marad", regi, uj
            )
            return False
        # a lista ÚJ példányként áll össze (immutabilitás): a sorrend és a
        # többi gyökér érintetlen marad
        self._roots = [uj if root == gyoker else root for root in self._roots]
        try:
            self._persist_roots()
        except OSError:
            # az index már az új útra mutat, a memóriabeli lista is — a
            # fájl kiírása bukott meg. NEM némítjuk el: enélkül a következő
            # indulás a régi helyet keresné.
            _legacy().logger.exception(
                "#1542: a figyelt mappák fájlja nem íródott ki az áthelyezett "
                "gyökérrel (%s)", uj
            )
        self._restart_watcher()
        # #216: a régi úthoz tartozó leállítási jelző az új úton már nem
        # érvényes — enélkül az új gyökér első syncje azonnal leállna
        self._cancel_event(uj).clear()
        self._athelyezett_gyoker_nezete(regi, uj)
        self.statusChanged.emit()
        _legacy().logger.info("#1542: a figyelt gyökér követve: %s → %s", gyoker, uj)
        return True

    def _athelyezett_gyoker_nezete(self, regi: str, uj: str) -> None:
        """A LÁTOTT mappa átvezetése az áthelyezett gyökér alatt (#1542).

        Enélkül a rács a régi, már nem létező úton maradna (üres rács), és
        a `session/lastFolder` is oda mutatna — a következő indítás megint
        a semmit nyitná meg. Csak sima mappanézetben nyúlunk hozzá: keresés
        vagy album nézetben a bal hasáb mást mutat, ott nincs mit
        átvezetni."""
        latott = self._current_folder
        if not latott or self._view_mode[0] != "folder":
            return
        latott_path = Path(latott)
        regi_path = Path(regi)
        if latott_path != regi_path and not latott_path.is_relative_to(regi_path):
            return
        self.selectFolder(str(Path(uj) / latott_path.relative_to(regi_path)))

    def _reszfa_a_lemezen(self, folder: str) -> tuple[str, ...]:
        """Az áthelyezett mappa ÚJ oldala: maga a mappa és az almappái.

        A bejárás a GUI-szálon fut, de csak könyvtárbejegyzéseket olvas
        (fájlonkénti `stat` nélkül) — és ugyanez a hívási lánc épp az imént
        MOZGATTA át a teljes fát ugyanezen a szálon
        (`fileops_controller.moveFolder` → `shutil.move`), tehát a séta ára
        ehhez képest elenyésző. Hibás/eltűnt ágon az `os.walk` csendben
        kihagy — a hiányzó mappát a következő rescan rendezi."""
        utak = [folder]
        for szulo, alkonyvtarak, _fajlok in os.walk(folder):
            utak.extend(str(Path(szulo) / nev) for nev in alkonyvtarak)
        return tuple(utak)

    def _reszfa_az_indexbol(self, folder: str) -> tuple[str, ...]:
        """Az áthelyezett mappa RÉGI oldala: amit az index még ott tud.

        ⚠️ Ha MAGÁT a figyelt gyökeret helyezték át, a takarítás KIMARAD.
        A gyökér útvonala ilyenkor a figyelt mappák közt (és a
        `WatchedFolders.txt`-ben) még a régi helyre mutat: a teljes
        könyvtárat azon az alapon üríteni, hogy a program saját
        nyilvántartása szerint ott KELL lennie, kockázatosabb, mint egy
        ideig elavult sorokat mutatni.

        #1542: ez a védelem MEGMARAD, csak a hatóköre szűkült. A gyökér
        áthelyezését azóta a `_kovesd_a_gyoker_athelyezeset` KÖVETI — ha ez
        sikerül, a régi utak már át vannak írva, tehát ez a lekérdezés
        magától üres halmazt ad. A `_find_root`-os kapu így pontosan arra
        az esetre marad, amikor a követés NEM sikerült (a régi néven ismét
        áll egy mappa, az új hely nem létezik, vagy az index átírása
        ütközött) — ott továbbra sem takarítunk. Mutációval mérve: e kapu
        nélkül a bal hasáb ilyenkor teljesen kiürül."""
        if self._find_root(folder) is not None:
            return ()
        with open_index(self._db_path) as conn:
            return folder_paths_under(conn, folder)

    # -- #1539: a FRISSEN KIÍRT kimenet célzott újraolvasása -----------------
    #
    # A hibaosztály ugyanaz, mint a #1522-nél és a #1538-nál: a fájl a
    # lemezen van, de az INDEX nem tud róla, a `selectFolder` pedig kizárólag
    # az indexből olvas — a felhasználó üres mappát lát. A #1275 lekérdezés
    # itt nem segít: az a LÁTOTT mappát nézi, a kimenet viszont épp egy
    # MÁSIKBA megy.

    def _ensure_output_resync_wired(self) -> None:
        """A belső kimenet-jelzés bekötése — SORBA ÁLLÍTOTT kapcsolattal.

        A GUI-szálon hívandó, a háttérszál indítása ELŐTT (a
        `collage_save._ensure_worker_bridge` mintája). Idempotens."""
        if getattr(self, "_output_resync_wired", False):
            return
        self._output_resync_wired = True
        self._outputWritten.connect(
            self._on_output_written, Qt.ConnectionType.QueuedConnection
        )

    def noteOutputWritten(self, path) -> None:  # noqa: N802 — QML-stílusú név
        """Bejelenti, hogy egy FRISSEN KIÍRT fájl a lemezen van (#1539).

        HÁTTÉRSZÁLBÓL IS hívható: csak jelzést bocsát ki, az érdemi munka a
        GUI-szálon fut (`_on_output_written`). A hívónak előbb a GUI-szálon
        meg kell hívnia a `_ensure_output_resync_wired()`-et."""
        if not path:
            return
        self._outputWritten.emit(str(path))

    def _on_output_written(self, path: str) -> None:
        """A kimenet-jelzés fogadója — már a GUI-szálon.

        Két, egymást KIZÁRÓ ág: a figyelt gyökér alatti kimenetet a #1539
        célzott újraolvasása viszi (`resyncOutputFolder`), a figyelt körön
        kívülit pedig — de KIZÁRÓLAG akkor, ha nyilvántartott exportcél —
        a #1565 saját-gyökeres indexelése."""
        self.resyncOutputFolder(path)
        self.indexExportedFolder(path)

    # SZÁNDÉKOSAN nincs `@Slot`: a hívók PYTHON-oldaliak (a vezérlő saját
    # szeletei és a `wire_dedup`), a QML soha nem hívja. Slotként a
    # `kepesseg_or.py` joggal jelezné felületről elérhetetlen képességnek —
    # ugyanaz a döntés, mint a `resyncMovedFolder`-nél (#1538).
    def resyncOutputFolder(self, path) -> None:  # noqa: N802 — QML-stílusú név
        """Egy frissen kiírt FÁJL MAPPÁJÁNAK célzott újraolvasása (#1539).

        ⚠️ A paraméter **fájlút**, nem mappa — a `.parent` itt tehát HELYES,
        szemben a #1538-cal, ahol ugyanez a lépés csapda volt. Ott egy MAPPA
        érkezett, és a `.parent` a SZÜLŐJÉT olvasta volna újra; itt a
        kollázs, a film, a másolat és az elmozgatott duplikátum mind
        konkrét fájl, aminek a mappája pontosan a megváltozott könyvtár.
        Rekurzióra sincs szükség (a #1538 másik csapdája): a művelet
        EGYETLEN mappába ír, nem részfát mozgat.

        A figyelt körön kívülre írt kimenet SZÁNDÉKOSAN kimarad (a #1522
        azonos szabálya): egy exportcél miatt nem bővítjük a felhasználó
        figyelt mappáit, és a `sync_folder`-nek amúgy is kell egy gyökér,
        ami alá a mappa tartozik.

        ⚠️ Az itteni kapu KORAI KILÉPÉS, nem a helyesség őre: ugyanezt a
        `_root_for_folder` próbát a `_on_folders_dirty` worker-ága is
        elvégzi, tehát a sor kivétele a NYILVÁNTARTÁST nem rontaná el
        (mutációval mérve: mind a tíz teszt zöld marad nélküle). Azért van
        mégis itt, mert enélkül MINDEN figyelt körön kívüli export
        fölöslegesen ütemezne egy háttérszálat és egy index-megnyitást —
        és épp az a gyakori eset (az export alapértelmezett célja a figyelt
        gyökereken kívülre mutat). Ezt az `_on_folders_dirty` szintjén
        őrizzük teszttel (`test_a_kivulre_irt_kimenet_nem_utemez_munkat`).

        Ez a `wire_fileops.refresh()` vezérlő-oldali párja. Azért van két
        helyen, mert a `wire_fileops` egy KÜLSŐ QObject (`FileOpsController`)
        jelzéseit köti be, és csak a `watchedFolders` + `resyncFolder`
        felületet használja belőlünk; a kollázs, a film és a mentés viszont
        MAGÁNAK a vezérlőnek a szeletei, azoknak nincs mit bekötni."""
        helyi = to_local_path(path) or str(path)
        mappa = str(Path(normalize_path(helyi)).parent)
        if self._root_for_folder(mappa) is None:
            return  # figyelt körön kívül — a #1565 exportcél-ága viszi
        self.resyncFolder(mappa)

    # SZÁNDÉKOSAN nincs `@Slot`: a hívó PYTHON-oldali (`_on_output_written`),
    # a QML soha nem hívja — ugyanaz a döntés, mint a `resyncOutputFolder`-nél.
    def indexExportedFolder(self, path) -> None:  # noqa: N802 — QML-stílusú név
        """A NYILVÁNTARTOTT exportcél felvétele az indexbe, SAJÁT
        GYÖKÉRKÉNT (#1565).

        ## Miért kell külön ág

        Az export alapértelmezett célja (`<Képek>/Picasa/Exports`) MINDEN
        figyelt gyökéren kívül van, tehát a #1539 célzott újraolvasása oda
        nem nyúl (`resyncOutputFolder` gyökér-kapuja) — a `sync_folder`-nek
        amúgy is kell egy gyökér, ami alá a mappa tartozik. A bal hasáb
        „Exportált képek" sora viszont a FÁJLRENDSZERBŐL listáz, a
        `selectFolder` pedig KIZÁRÓLAG az indexből olvas: a felhasználó
        rákattint, és tartósan üres rácsot kap.

        Mérve (valódi vezérlő, produkciós időzítők, három kép a lemezen):
        **0 látszott** mindhárom időzítés-állásban — figyelővel BEKAPCSOLVA
        is, 25 s alatt sem. Ez különbözteti meg a #1522/#1538/#1539
        családtól: ott a figyelő behozta a kimenetet, itt soha nem hozza.

        ## Miért ez az irány, és nem a csomópont elvétele

        Az eredetiben az exportált mappa a KÖNYVTÁR RÉSZE. Az
        `IDS_EXPORTED_CATEGORY` (= „Exported Pictures" / „Exportált képek")
        a binárisban abban a kategória-táblában áll (`FUN_004a1560`), amely
        a `Folders on Disk` / `IDS_FOLDERS`, a `Projects (internal)` /
        `IDS_PROJECTS` és az `Other Stuff` / `IDS_DEFAULTCAT` párokat is
        felsorolja — vagyis ugyanolyan `P2category` **könyvtár-kategória**,
        mint a lemezen álló mappáké, nem külön nézet. A 859 fájlos valódi
        ini-korpuszban három mappa hordozza is ezt az értéket
        (`picasapy.ini.folder_category`).

        ## A kapu: NYILVÁNTARTOTT exportcél, nem „bármi, ami kívül van"

        A gyökér MAGA a célmappa, ahogy a `collage_save_render._index_saved_collage`
        teszi — így egyetlen mappa kerül be, nem részfa, és a felhasználó
        **figyelt mappáihoz nem nyúlunk**: a `WatchedFolders.txt` a könyvtár
        horgonya (#1542/#1560), egy exportcél miatt nem bővítjük. Az
        exportcélok ezért KÜLÖN kategória: a beállításokban élő, korlátos
        (`MAX_EXPORTED_FOLDERS`), létezésre szűrt nyilvántartásból
        (`exported_folders.py`, #457) dolgozunk — abba pedig csak az kerül,
        ahova a felhasználó ténylegesen exportált.

        Ez a kapu tartja meg a #1539 határát is: a figyelt körön kívülre
        mentett kollázs/film/másolat továbbra sem indexelődik, mert nincs
        benne a nyilvántartásban.

        ## A kétszeres indexelés — mérve, és itt NEM ártalom

        A #1539 kimondta, hogy a webexport kicsinyített példányainak
        indexelése ÁRTANA: ugyanaz a kép kétszer. Az exportált mappára a
        „kétszer" tényszerűen igaz (az eredeti a figyelt gyökér alatt, a
        méretezett másolat az exportcélban), de itt nem hiba, három okból:
        (1) az eredeti Picasa is pontosan ezt teszi — az exportált mappa
        könyvtár-kategóriát kap; (2) a #1539 óta a figyelt gyökér ALÁ
        exportált kép már ma is bejön a másolatával együtt
        (`test_a_figyelt_gyoker_ala_exportalt_kep_megjelenik`: 2 kép + 1
        export = 3 sor), tehát a mostani állapot nem „egyszeres", hanem
        következetlen — ugyanaz az export a cél HELYÉTŐL függően viselkedik
        másképp; (3) a webexport `thumbnail/` és
        `image/` mappája gépi segédanyag egy HTML-oldalhoz, az exportált
        mappa viszont a felhasználó által megnevezett, önállóan böngészendő
        album.

        ## A gyökér-kapu KORAI KILÉPÉS, nem a helyesség őre

        A figyelt gyökér alatti célt a #1539 ága már elviszi, tehát a
        `_root_for_folder` sor kivétele az eredményt nem rontaná el — csak
        minden ilyen export fölöslegesen nyitna egy második index-
        kapcsolatot ugyanarra a mappára. Ezt ezért KÜLÖN állítás őrzi
        (`test_a_figyelt_gyoker_alatti_exportcel_nem_indexelodik_ketszer`):
        nélküle a sor mérhetően, némán eltávolítható volt.

        A hiba nem buktathat el semmit: a képek a lemezen vannak, egy
        index-gond miatt nem mondunk kudarcot (a `_index_saved_collage`
        azonos szabálya)."""
        helyi = to_local_path(path) or str(path)
        if not helyi:
            return
        mappa = Path(normalize_path(helyi)).parent
        if self._root_for_folder(str(mappa)) is not None:
            return  # figyelt gyökér alatt — azt a #1539 ága vitte
        if path_key(str(mappa)) not in self._exported_folder_keys():
            return  # nem nyilvántartott exportcél — a #1539 határa marad
        try:
            with open_index(self._db_path) as conn:
                scan_options = {}
                enabled_filetypes = getattr(
                    self, "_filetype_scan_snapshot", None
                )
                if enabled_filetypes is not None:
                    scan_options["enabled_filetypes"] = enabled_filetypes
                _legacy().sync_folder(conn, mappa, mappa, **scan_options)
        except Exception:  # noqa: BLE001 - index-gond nem buktathat exportot
            _legacy().logger.warning(
                "Az exportcél nem került az indexbe: %s", mappa, exc_info=True
            )
            return
        # a rács a `syncFinished`-re olvassa újra a feedet (`_reload_after_sync`)
        self.syncFinished.emit()

    def _exported_folder_keys(self) -> set[str]:
        """A nyilvántartott, MA IS LÉTEZŐ exportcélok összehasonlítható
        kulcsai (#1565).

        `path_key`-jel, mert az összehasonlítás másik oldala egy
        normalizált út: a nyilvántartásba a felhasználó által választott
        alak kerül, ami ugyanarra a mappára mutathat más írásmóddal."""
        return {
            path_key(mappa)
            for mappa in existing_exported_folders(
                self._get_settings().value(EXPORTED_FOLDERS_SETTINGS_KEY)
            )
        }
