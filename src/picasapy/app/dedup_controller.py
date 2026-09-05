"""DedupController: a duplikátum-kezelő ablak (`DedupDialog.qml`, #287)
QML-hídja a `picasapy.dedup.find_duplicates` mag fölött.

Önálló QObject — a `FolderTreeController`/`DiscoveryController` mintáját
követve NEM az `AppController` mixinje, hogy a `controller.py` (forró
fájl, ld. CONTRIBUTING.md) csak a végleges, minimális bekötést kapja.

#294 — SKÁLÁZÓDÁS. A keresés korábban feltétel nélkül a TELJES indexelt
könyvtárra futott; egy 140 000 képes gyűjteményen ez gyakorlatilag soha
nem ért véget, és a párbeszédablak közben némán állt. Négy dolog változott:

1. **Hatókör** (`scanSelection` / `scanFolder` / `scanForDuplicates`): a UI
   alapból a kijelölésre vagy az aktuális mappára (+almappákra) keres, a
   teljes könyvtár tudatosan választható.
2. **Haladás-jelzés és megszakítás** (`scanProgress`, `cancelScan`) a
   `sync_tree` (#209/#216) mintája szerint. A jelzések a worker-szálról
   mennek ki — a Qt queued kézbesítéssel sorolja őket a GUI-szálra,
   ugyanúgy, ahogy a `scanFinished`-et is.
3. **dHash-gyorsítótár az indexben** (`picasapy.index.hashes`): a lenyomat
   kulcsa a `(útvonal, mtime_ns, méret)` hármas, így az ismételt keresés
   csak az új/megváltozott képeket dekódolja.
4. A dHash maga redukált JPEG-dekódolással készül (`dedup/phash.py`).

#298 — BÉLYEGKÉP-REGISZTRÁCIÓ. A vezérlő korábban `register_photos`-t
hívott, ami LECSERÉLTE a provider teljes regisztrációját: ha a dedup
eredménye nem esett egybe a fő rács tartalmával, a rács `image://thumbs/<id>`
URL-jei feloldhatatlanná váltak (szürke placeholder-cellák). Helyette az
`register_additional_photos`/`unregister_additional_photos` páros megy,
SAJÁT (negatív) id-tartománnyal — az Import-forrás ág (`import_source_
controller.py`) mintájára —, és a dialógus bezárásakor (`releaseThumbnails`)
vagy új keresés indításakor a bejegyzések eltűnnek.

A csoportokat (és minden elemüket) QML-nek MINDIG listaként (dict-ek
listája) adjuk át, SOHA Python tuple-ként — a tuple QML-ben nem tömb, a
`.length` undefined lenne (ld. MEMORY.md tanulság).

Alapértelmezett, NEM-destruktív feloldás (#287 DoD): a csoport minden
tagja — a megtartandó kivételével — a forrásmappájának "Duplikátumok"
alkönyvtárába kerül (`moveOthersToDuplicatesFolder`). A Kukába törlés
(`deleteOthers`) csak explicit felhasználói döntésre történik."""

from __future__ import annotations

import dataclasses
import logging
import sqlite3
import threading
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from picasapy.dedup import find_duplicates
from picasapy.dedup.phash import compute_dhash
from picasapy.fileops import delete_to_trash, move_photo
from picasapy.index import (
    IndexFastKeySource,
    PhotoRecord,
    all_photos,
    load_dhashes,
    open_index,
    photos_under_folder,
    save_dhashes,
)

from .formatting import to_local_path
from .worker_thread import BackgroundWorkerMixin
from .display_mode_paint import current_display_mode_suffix

# A nem-destruktív áthelyezés célmappájának neve, forrásmappánként —
# létrehozva, ha még nincs (ld. `_move_one`).
DUPLICATES_SUBFOLDER_NAME = "Duplikátumok"

# #1697: a felhasználói jelentés szerint a `Duplikátumok` mappából ismét
# lefuttatott áthelyezés `Duplikátumok/Duplikátumok` beágyazott szerkezetet
# hozott létre — a mappa nincs kizárva a beolvasásból (ez SZÁNDÉKOS, ld.
# `_is_duplicates_collector` docstringje), ezért közönséges fotómappaként
# újra feldolgozható. EZ A FUNKCIÓ (a másodpéldányok gyűjtőmappába
# áthelyezése) a MI kiegészítésünk, nem a Picasa viselkedésének másolása —
# a Picasa `ID_DUPES` parancsa csak SZŰRŐ, fájlműveletet nem végez (ld.
# `docs/specs/picasa-kereses-modok.md`). A beágyazás elleni védelem tehát
# saját döntés: ha a forrásmappa NEVE (nem az, hogy mi hoztuk-e létre) már
# a gyűjtőmappáé, a fájl HELYBEN MARAD, és a felhasználó a meglévő
# `operationFailed` csatornán EGYÉRTELMŰ üzenetet kap — néma hatástalanság
# éppolyan hiba lenne, mint a néma beágyazás.
_ALREADY_IN_COLLECTOR_MESSAGE = (
    'This picture is already inside a "Duplikátumok" folder; leaving it '
    "in place instead of nesting the folder inside itself."
)

# #298: a dedup-előnézetek SAJÁT id-tartománya a thumbnail-providerben.
# A valódi indexbeli fotók id-je mindig pozitív; az Import-forrás előnézete
# a -1-től lefelé tartó sávot használja (`import_source_controller.py`),
# ezért a dedup ennél jóval lejjebb kezd — a két dialógus így egyszerre is
# nyitva lehet anélkül, hogy egymás bejegyzéseit felülírnák.
DEDUP_THUMB_ID_BASE = -1_000_000

# Ennyi frissen kiszámolt lenyomat után írunk az indexbe. A köteges mentés
# egyrészt olcsóbb, másrészt a megszakított keresés munkája sem vész el:
# a legközelebbi futás onnan folytatja, ahol ez abbamaradt.
_HASH_FLUSH_SIZE = 200

_log = logging.getLogger(__name__)


def _is_duplicates_collector(folder: Path) -> bool:
    """Igaz, ha `folder` SAJÁT NEVE megegyezik a duplikátum-gyűjtőmappa
    nevével — kis-nagybetű-független teljes egyezéssel (Windowson a
    `duplikátumok` és a `Duplikátumok` UGYANAZ a könyvtár, #1682).

    A NÉVRE illesztünk, nem arra, hogy MI hoztuk-e létre a mappát: a
    felhasználó saját kezűleg készített `Duplikátumok` mappájára is ugyanez
    a védelem vonatkozzon (#1697)."""
    return folder.name.casefold() == DUPLICATES_SUBFOLDER_NAME.casefold()


def _photo_path(photo: PhotoRecord) -> str:
    """A fotó teljes (abszolút) elérési útja — ez a kulcs a
    `find_duplicates` bemenetéhez és a csoportok elem-azonosításához."""
    return str(Path(photo.folder_path) / photo.name)


def _fajl_azonossagok(
    photos: tuple[PhotoRecord, ...],
) -> dict[str, tuple[str, int, int]]:
    """Útvonal → `(útvonal, mtime_ns, méret)` a `photo_hashes` KÉT
    gyorstárához (#294 dHash és #1494 gyorskulcs).

    EGYETLEN forrás mindkettőnek, és ez nem stílus-kérdés: a két érték egy
    soron osztozik, és minden írás NULL-ozza a párját, ha a sorban tárolt
    azonosság nem egyezik a most beírttal. Két külön mérésből (indexbeli
    rekord kontra friss `stat()`) a szinkron óta megváltozott fájlokra a
    kettő eltérne, és a két gyorstár körönként váltakozva ürítené egymást.

    A mérce a LEMEZ mai állapota — a `.stat()` —, nem az indexbeli rekord:
    a rekord az utolsó szinkroné, és egy azóta kicserélt fájlra a tárolt
    (idegen) kulcsot adná vissza. Elérhetetlen fájlnál (levált NAS-mount,
    időközben törölt kép) marad a rekord értéke: lekérdezésre az is jó, és
    a hash-ek úgyis `None`-t adnak majd rá, tehát írás nem lesz belőle."""
    azonossagok: dict[str, tuple[str, int, int]] = {}
    for photo in photos:
        path = _photo_path(photo)
        try:
            adat = Path(path).stat()
            azonossagok[path] = (path, adat.st_mtime_ns, adat.st_size)
        except OSError:
            azonossagok[path] = (path, photo.mtime_ns, photo.size)
    return azonossagok


def _thumb_url(photo_id: int | None) -> str:
    """A `thumbs` image-provider URL-je (ld. `thumbnail_provider.py`) —
    üres string, ha a fájl nincs az indexben (ilyenkor a QML placeholder
    marad, `Image.source` üres stringre nem próbál betölteni)."""
    if photo_id is None:
        return ""
    # #1656: a megjelenítési mód cimkéje — enélkül a párbeszéd
    # bélyegképein a mód hatástalan maradna
    return f"image://thumbs/{photo_id}{current_display_mode_suffix()}"


def _group_dict(
    kind: str,
    paths: tuple[Path, ...],
    thumb_ids: dict[str, int],
    max_distance: int | None,
) -> dict:
    """Egy duplikátum-csoport QML-barát alakja: sima `dict`, a tagok is
    `dict`-ek listájaként (nem tuple)."""
    items = [
        {
            "path": str(path),
            "thumbUrl": _thumb_url(thumb_ids.get(str(path))),
        }
        for path in paths
    ]
    return {
        "kind": kind,
        # -1: nincs értelmezhető távolság (pontos duplikátum) — a QML
        # ebből dönti el, hogy mutassa-e a "hasonlóság" feliratot
        "maxDistance": max_distance if max_distance is not None else -1,
        "items": items,
    }


def _build_groups(report, thumb_ids: dict[str, int]) -> list[dict]:
    """A `DuplicateReport` (exact + similar csoportok) egyetlen, QML-nek
    adható listává lapítva — előbb a pontos, aztán a hasonló csoportok."""
    groups = [
        _group_dict("exact", group.paths, thumb_ids, None)
        for group in report.exact_groups
    ]
    groups += [
        _group_dict("similar", group.paths, thumb_ids, group.max_distance)
        for group in report.similar_groups
    ]
    return groups


def _grouped_paths(report) -> list[str]:
    """A találatokban ténylegesen szereplő útvonalak (sorrendtartóan,
    ismétlés nélkül) — csak ezekhez kell bélyegképet regisztrálni, nem a
    teljes átvizsgált halmazhoz."""
    seen: dict[str, None] = {}
    for group in (*report.exact_groups, *report.similar_groups):
        for path in group.paths:
            seen.setdefault(str(path), None)
    return list(seen)


class DedupController(BackgroundWorkerMixin, QObject):
    """A `DedupDialog.qml` háttér-hídja: keresés indítása és a csoportok
    feloldása (áthelyezés vagy törlés)."""

    scanStarted = Signal()
    # (fázis-token, kész, összes) — a fázis technikai azonosító
    # (`picasapy.dedup.api.PHASE_*`), az emberi szöveget a QML adja hozzá
    scanProgress = Signal(str, int, int)
    scanFinished = Signal(list)  # csoportok (dict-ek listája)
    scanCancelled = Signal()  # a felhasználó megszakította a keresést
    scanFailed = Signal(str)  # hibaüzenet (pl. olvashatatlan index)
    # (feloldott elem útvonala) — a QML ebből törli a sorból, ÉS a #1539 óta
    # a `wire_dedup` ebből olvassa újra a FORRÁSMAPPÁT: a feloldott kép
    # (kukázva vagy elmozgatva) onnan mindkét ágon eltűnt.
    itemResolved = Signal(str)
    # #1539: (forrás_út, új_út) — a duplikátum ÁTHELYEZVE a „Duplikátumok"
    # almappába. Külön jelzés az `itemResolved` mellé, mert az csak a
    # forrást ismeri: a CÉLMAPPA frissen létrehozott, sosem indexelt
    # könyvtár, azt is újra kell olvasni, különben a képek eltűnnek.
    photoRelocated = Signal(str, str)
    operationFailed = Signal(str, str)  # (útvonal, hibaüzenet)

    def __init__(self, db_path: Path, provider) -> None:
        """`provider`: a `ThumbnailProvider` (vagy teszthez `None`) — a
        találatokat ITT regisztráljuk nála (`register_additional_photos`,
        #298), hogy a csoportok `thumbUrl`-jei feloldhatók legyenek
        anélkül, hogy a fő rács regisztrációja sérülne."""
        super().__init__()
        self._db_path = Path(db_path)
        self._provider = provider
        # a futó keresés megszakító-jelzője (None: nincs futó keresés)
        self._stop_event: threading.Event | None = None
        # a providernél jelenleg regisztrált dedup-bejegyzések id-jei
        self._registered_ids: tuple[str, ...] = ()

    # -- keresés ----------------------------------------------------------

    @Slot()
    def scanForDuplicates(self) -> None:
        """A TELJES indexelt könyvtár duplikátum-keresése.

        Nagy gyűjteményen ez hosszú művelet — a UI-ban ezért tudatos
        választás (figyelmeztetéssel), nem alapértelmezés (#294). A hívás
        azonnal visszatér, az eredmény a `scanFinished`-ben érkezik."""
        self._start(lambda conn: all_photos(conn))

    @Slot(str)
    def scanFolder(self, folder: str) -> None:
        """Keresés egy mappában ÉS az almappáiban (#294) — a dialógus
        alapértelmezett hatóköre. `folder` `file://` URL is lehet (a QML
        oldalról ez a szokásos alak)."""
        target = to_local_path(folder)
        if not target:
            self.scanFailed.emit(
                self.tr("Choose a folder to search for duplicates in.")
            )
            return
        self._start(lambda conn: photos_under_folder(conn, target))

    @Slot(list)
    def scanSelection(self, paths: list) -> None:
        """Keresés a megadott (kijelölt) képek között (#294).

        Kettőnél kevesebb kép között nem lehet duplikátum — ilyenkor
        azonnal üres eredményt adunk, futás nélkül."""
        wanted = {to_local_path(str(path)) for path in paths}
        wanted.discard("")
        if len(wanted) < 2:
            self.scanStarted.emit()
            self.scanFinished.emit([])
            return
        self._start(
            lambda conn: tuple(
                photo for photo in all_photos(conn) if _photo_path(photo) in wanted
            )
        )

    @Slot()
    def cancelScan(self) -> None:
        """A folyamatban lévő keresés megszakítása. A worker a következő
        ellenőrzési ponton tisztán leáll, és `scanCancelled`-t bocsát ki;
        a már kiszámolt lenyomatok az indexben maradnak."""
        if self._stop_event is not None:
            self._stop_event.set()

    @Slot()
    def releaseThumbnails(self) -> None:
        """A dedup-bélyegképek elengedése a providerből (#298) — a QML a
        dialógus bezárásakor hívja. A fő rács regisztrációját nem érinti."""
        if self._provider is None:
            self._registered_ids = ()
            return
        self._provider.unregister_additional_photos(self._registered_ids)
        self._registered_ids = ()

    def _start(self, select_photos) -> None:
        """A keresés elindítása HÁTTÉRSZÁLON. `select_photos`: a hatókört
        megvalósító lekérdezés (nyitott kapcsolatot kap)."""
        self.cancelScan()  # egyszerre csak egy keresés fusson
        stop_event = threading.Event()
        self._stop_event = stop_event
        self.scanStarted.emit()
        # #438: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430) —
        # a `_stop_event` a megszakítási jelző marad, ez csak a szál
        # bevárhatóságát adja hozzá.
        self._start_background(
            self._run_scan, args=(select_photos, stop_event), name="picasapy-dedup"
        )

    def _run_scan(self, select_photos, stop_event: threading.Event) -> None:
        """A worker-szál törzse: lekérdezés → keresés → jelzés.

        A kapcsolat a keresés teljes idejére nyitva marad (ugyanezen a
        szálon jött létre, ezért szál-biztos): így a frissen számolt
        lenyomatok kötegenként az indexbe kerülhetnek, és egy megszakított
        futás munkája sem vész el."""
        try:
            with open_index(self._db_path) as conn:
                photos = tuple(select_photos(conn))
                report = self._find(conn, photos, stop_event)
        except Exception as error:  # noqa: BLE001 — index-hiba se fagyassza a UI-t
            _log.exception("duplikátum-keresés hiba: %s", self._db_path)
            self.scanFailed.emit(str(error))
            return
        finally:
            if self._stop_event is stop_event:
                self._stop_event = None

        if report.cancelled:
            self.scanCancelled.emit()
            return
        thumb_ids = self._register_thumbnails(report, photos)
        self.scanFinished.emit(_build_groups(report, thumb_ids))

    def _find(self, conn, photos: tuple[PhotoRecord, ...], stop_event):
        """A tényleges keresés gyorsítótárazott lenyomatokkal.

        A cache kulcsa a fájl azonossága (`útvonal, mtime_ns, méret`), így
        egy változatlan kép soha nem dekódolódik újra — ez teszi az
        ismételt keresést azonnal indulóvá (#294).

        Ugyanez a gyorstár szolgálja ki a PONTOS réteg Picasa-gyorskulcsát
        is (#1494, `originfast`): a második körben a változatlan képek
        fájlvégeit sem kell újra beolvasni."""
        keys = _fajl_azonossagok(photos)
        cached = load_dhashes(conn, tuple(keys.values()))
        pending: list[tuple[str, int, int, int]] = []

        def flush() -> None:
            """A dHash-köteg kiírása ÉS commitolása.

            Index-hiba (zárolás, tele lemez) nem buktathatja meg a KÉSZ
            keresést: a gyorstár kényelmi szolgáltatás, a jelentés
            helyessége nem függ tőle — védelem nélkül a `_run_scan`
            `except`-je `scanFailed`-et emittálna egy kész eredmény
            helyett (#1494 átnézés, 5. lelet)."""
            if not pending:
                return
            koteg = tuple(pending)
            pending.clear()
            try:
                save_dhashes(conn, koteg)
                conn.commit()
            except sqlite3.Error:
                _log.warning("#294: a dHash-ek mentése nem sikerült", exc_info=True)
                try:
                    conn.rollback()
                except sqlite3.Error:
                    _log.warning("#294: a visszagörgetés sem sikerült", exc_info=True)

        def dhash_source(path: Path) -> int | None:
            key = keys.get(str(path))
            if key is not None and key in cached:
                return cached[key]
            value = compute_dhash(path)
            if value is not None and key is not None:
                pending.append((*key, value))
                if len(pending) >= _HASH_FLUSH_SIZE:
                    flush()
            return value

        gyorskulcs = IndexFastKeySource(conn, keys)

        try:
            return find_duplicates(
                list(keys),
                progress=lambda phase, done, total: self._emit_progress(
                    phase, done, total, stop_event
                ),
                should_stop=stop_event.is_set,
                dhash_source=dhash_source,
                fast_key_source=gyorskulcs,
            )
        finally:
            # mindkét `flush()` commitol ÉS elnyeli a saját hibáját, tehát
            # innen se kész eredményt elvivő kivétel, se bent maradó írási
            # zár nem indulhat (#1494 átnézés, 2./5. lelet)
            gyorskulcs.flush()
            flush()

    def _emit_progress(self, phase: str, done: int, total: int, stop_event) -> bool:
        """Haladás-jelzés a worker-szálról (a Qt a GUI-szálra sorolja);
        a visszatérési érték a mag megszakítás-szerződése (#216)."""
        self.scanProgress.emit(phase, done, total)
        return stop_event.is_set()

    def _register_thumbnails(self, report, photos) -> dict[str, int]:
        """A találatok bélyegképeinek regisztrálása a providernél SAJÁT
        (negatív) id-tartományban (#298), a korábbi dedup-bejegyzések
        egyidejű elengedésével. Visszaadja az útvonal → dedup-id térképet,
        amiből a `thumbUrl`-ek készülnek."""
        by_path = {_photo_path(photo): photo for photo in photos}
        paths = [path for path in _grouped_paths(report) if path in by_path]
        thumb_ids = {
            path: DEDUP_THUMB_ID_BASE - index for index, path in enumerate(paths)
        }
        if self._provider is None:
            return {}
        records = tuple(
            dataclasses.replace(by_path[path], id=thumb_ids[path]) for path in paths
        )
        self._provider.unregister_additional_photos(self._registered_ids)
        self._provider.register_additional_photos(records)
        self._registered_ids = tuple(str(record.id) for record in records)
        return thumb_ids

    # -- csoport feloldása ------------------------------------------------

    @Slot(list, str)
    def deleteOthers(self, paths: list, keep_path: str) -> None:
        """A csoport minden tagját Kukába helyezi, KIVÉVE a megtartandót
        (`keep_path`). Destruktívabb út — a UI-ban csak explicit
        felhasználói döntésre elérhető, az alapértelmezés a
        `moveOthersToDuplicatesFolder`."""
        for path in paths:
            if path == keep_path:
                continue
            try:
                delete_to_trash(Path(path))
            except OSError as error:
                self.operationFailed.emit(path, str(error))
                continue
            self.itemResolved.emit(path)

    @Slot(list, str)
    def moveOthersToDuplicatesFolder(self, paths: list, keep_path: str) -> None:
        """Nem-destruktív alapértelmezés (#287 DoD): a csoport minden
        tagja — a megtartandó kivételével — a saját forrásmappájának
        "Duplikátumok" alkönyvtárába kerül (mappánként létrehozva, ha még
        nincs). Így a különböző mappákból származó duplikátumok is a
        saját kontextusukban maradnak, nem egy közös, helyfüggetlen
        gyűjtőmappában.

        #1697: ha a FORRÁSMAPPA maga már a gyűjtőmappa (a felhasználó a
        `Duplikátumok` mappában futtatja a feloldást), az áthelyezés nem
        hoz létre beágyazott `Duplikátumok/Duplikátumok` szerkezetet — a
        fájl helyben marad, és `operationFailed`-en egyértelmű üzenetet
        kap a felhasználó (ld. `_is_duplicates_collector`)."""
        for path in paths:
            if path == keep_path:
                continue
            source = Path(path)
            if _is_duplicates_collector(source.parent):
                self.operationFailed.emit(path, self.tr(_ALREADY_IN_COLLECTOR_MESSAGE))
                continue
            dest_folder = source.parent / DUPLICATES_SUBFOLDER_NAME
            try:
                dest_folder.mkdir(exist_ok=True)
                moved = move_photo(source, dest_folder)
            except OSError as error:
                self.operationFailed.emit(path, str(error))
                continue
            # #1539: a CÉLMAPPA frissen jött létre, tehát az indexben nincs
            # benne. A `move_photo` a tényleges (ütközésnél átnevezett)
            # célutat adja vissza — azt küldjük ki, nem a kiszámítottat.
            self.photoRelocated.emit(path, str(moved))
            self.itemResolved.emit(path)
