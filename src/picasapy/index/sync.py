"""Ismételhető szinkron: fájlrendszer-scan + .picasa.ini → SQLite index.

A 7. rögzített döntés (ismételhető migráció) miatt a szinkron idempotens:
upsert a meglévő sorokra (stabil id-k), a fájlrendszerről eltűnt fájlok és
mappák törlése. Az ini az igazságforrás — minden futás a friss tartalmát
veszi át.
"""

from __future__ import annotations

import logging
import os
import re
import sqlite3
import stat as stat_module
import time
from collections.abc import Callable
from pathlib import Path

from picasapy.ini import IniDocument, load_document, read_folder_date_override
from picasapy.ini.albums import albums_of, parse_album_refs
from picasapy.metadata import EMPTY_METADATA, read_file_metadata
from picasapy.paths import normalize_path
from picasapy.scanner import (
    PICASA_INI_NAME,
    FolderScan,
    MediaFile,
    scan_folder,
    scan_tree,
)

_ROTATE = re.compile(r"^rotate\((\d+)\)$")

# #143: az inkrementális kihagyás frissesség-védőablaka. A mappa- és
# ini-mtime felbontása durva lehet (SMB/FAT: 2 s; ext4 is csak jiffy-pontos),
# ezért az ennél frissebb mappát sosem hagyjuk ki — különben egy, a mentett
# mtime-mal azonos időbélyegű változás észrevétlen maradna.
_SKIP_SAFETY_NS = 2_000_000_000

# #143: a scan-állapot segédtáblája. Szándékosan nem a schema.py-ban él
# (sémaverziót csak az integrátor oszt ki): tisztán eldobható cache —
# hiánya vagy törlése csak egy teljes újra-stat-olást jelent, adatvesztést nem.
_SCAN_STATE_DDL = (
    "CREATE TABLE IF NOT EXISTS folder_scan_state ("
    " path TEXT PRIMARY KEY,"
    " mtime_ns INTEGER NOT NULL,"
    " ini_mtime_ns INTEGER)"
)

logger = logging.getLogger(__name__)

# #209: streamelt sync — mappánkénti haladás-jelzés. Paraméterek:
# (mappa útvonala, kész mappák száma, összes ismert mappa, az eddig talált
# ÚJ fotók kumulált száma). FIGYELEM: a callback a sync_tree hívási szálán
# fut — az app-ban ez a háttér-worker szála, NEM a GUI-szál; a hívó dolga
# a szál-átadás (pl. Qt queued signal) és a ritkítás.
#
# #216: a callback VISSZATÉRÉSI ÉRTÉKE megszakítás-kérés — igaz érték esetén
# a sync a mappa-határon tisztán leáll (a már commitolt mappák megmaradnak,
# a takarítás kimarad). A None/False (a korábbi, érték nélküli callbackek)
# nem szakít meg — visszafelé kompatibilis.
SyncProgressCallback = Callable[[str, int, int, int], object]


def sync_tree(
    conn: sqlite3.Connection,
    root: str | Path,
    exclude: tuple[str | Path, ...] = (),
    incremental: bool = True,
    progress: SyncProgressCallback | None = None,
    should_stop: Callable[[], bool] | None = None,
) -> None:
    """A gyökér alatti könyvtár teljes szinkronja az indexbe.

    Az index kanonikus (feloldott, abszolút) útvonalakra kulcsol, ezért a
    gyökeret belépéskor normalizáljuk. Mappánként commitolunk: nagy (100k+)
    könyvtárnál nem nő össze a WAL, és megszakadás után a futás onnan
    folytatható, ahol tartott (a szinkron mappánként idempotens).

    Az `exclude`-ban felsorolt mappák (és alfáik) kimaradnak az indexből
    (#145, FRExcludeFolders.txt — ld. `picasapy.scanner.exclude` a fázis-1
    szintű, ideiglenes egyszerűsítés indoklásáért).

    Ismert korlátok:
    - RAW és videó fájloknál nincs EXIF/IPTC-olvasás (a Pillow nem dekódolja
      őket) → taken_at/orientation/méret üres marad; RAW-támogatás később.
    - A változás-detektálás (mtime_ns, size) páros: egy mtime-őrző, azonos
      méretű IPTC-átírást (pl. exiftool -P) nem vesz észre. A Picasa maga
      mindig frissíti az mtime-ot, így ez a gyakorlatban nem fordul elő.
    - A keywords_file vesszővel join-olt lista: vesszőt tartalmazó kulcsszó
      nem bontható vissza veszteség nélkül (FTS-t és megjelenítést nem zavar).

    #143 — inkrementális rescan (`incremental=True`, alapértelmezés): egy
    mappa fájljainak stat-olása kimarad, ha a mappa mtime-ja ÉS az ini
    mtime-ja megegyezik az indexben tárolt állapottal, és mindkettő idősebb
    a frissesség-védőablaknál. Dokumentált kompromisszum (a NAS-rescan
    nagyságrendi gyorsítása fejében): a mappa mtime-ját nem érintő, helyben
    történt fájl-átírást a rescan nem vesz észre — azt a watcher-ág, illetve
    egy `incremental=False` teljes sync fedi le.

    #209 — streamelt haladás: ha a `progress` callback meg van adva, MINDEN
    mappa feldolgozása (vagy kihagyása) után meghívjuk
    `(mappa, kész, összes, új_fotók_kumulált)` argumentumokkal. A mappánkénti
    commit miatt a már jelzett mappák fotói ekkor MÁR olvashatók az indexből
    (másik kapcsolaton is) — erre épül a fokozatos UI-megjelenítés. A callback
    szál-kontextusa a hívóé (worker-szál!), ld. `SyncProgressCallback`.

    #216/#1161 — tiszta megszakítás mappa-határon: a futás leáll, ha a
    `should_stop` igazat ad (a mappa feldolgozása ELŐTT és közvetlenül az
    írás commitja ELŐTT ellenőrizve), vagy
    ha a `progress` callback igaz értékkel tér vissza (a mappa commitja UTÁN).
    Megszakadt futásnál a takarítás (`_prune_folders`) kimarad — a hiányos
    „látott" halmaz érvényes mappákat törölne; a már commitolt mappák
    megmaradnak (konzisztens, folytatható állapot).
    """
    root_path = Path(normalize_path(root))
    _ensure_scan_state(conn)
    # #1249: a sírkövek mindig kizárnak — a hívónak nem kell tudnia róluk
    exclude = tuple(exclude) + removed_folder_paths(conn)
    skip = _make_skip(conn) if incremental else None
    # #358: az `excluded_names` a #349 NÉV-kizárólista miatt kihagyott
    # mappákat gyűjti — ha ez nem üres, a gyökér scandirje bizonyíthatóan
    # lefutott (a gyökér tehát elérhető), csak minden talált tartalom
    # kizárt nevű mappa alatt van. Ez különbözteti meg a védő-heurisztikát
    # a ténylegesen elérhetetlen gyökértől (ld. lent).
    excluded_names: list[Path] = []
    scans = scan_tree(root_path, exclude=exclude, skip=skip, excluded_names=excluded_names)
    done = 0
    new_total = 0
    cancelled = False
    for scan in scans:
        if should_stop is not None and should_stop():
            cancelled = True
            break
        done += 1
        if scan.skipped:
            # változatlan mappa: az indexbeli állapot érvényes; a haladás-
            # számláló ettől még lép (a hívó ritkítja a jelzés-árat)
            if progress is not None and progress(
                str(scan.path), done, len(scans), new_total
            ):
                cancelled = True
                break
            continue
        new_total += _sync_folder(conn, scan)
        if should_stop is not None and should_stop():
            # Az olvasás alatt változhatott a Mappakezelő kizárási
            # generációja. A jelen mappa még nem commitolt írásait eldobjuk,
            # különben egy frissen kizárt ágat visszaírhatna a stale worker.
            conn.rollback()
            cancelled = True
            break
        if incremental:
            _store_scan_state(conn, scan)
        conn.commit()
        if progress is not None and progress(
            str(scan.path), done, len(scans), new_total
        ):
            cancelled = True
            break
    if cancelled:
        # megszakítva: a folyamatban lévő mappa commitja már lefutott, a
        # takarítás viszont TILOS — a hívó (pl. remove_root) takarít, ha kell
        conn.commit()
        return
    seen_paths = {str(scan.path) for scan in scans}
    if seen_paths or excluded_names or not _has_indexed_folders(conn, root_path):
        # Nem üres scan, vagy a gyökér az indexben is üres volt eddig, vagy
        # (#358) a scan a #349 NÉV-kizárólista miatt lett üres — ezekben az
        # esetekben a gyökér bizonyítottan elérhető volt, nincs mit óvni, a
        # takarítás biztonságosan lefuthat (a kizárt nevű mappák alatti
        # indexbejegyzések is eltűnnek, pont ez a #349 célja).
        _prune_folders(conn, root_path, seen_paths)
    else:
        # #132: az üres scan-eredmény megkülönböztethetetlen attól, hogy a
        # gyökér ténylegesen elérhetetlen (pl. lecsatolt NAS-mount, amely
        # üres könyvtárként van jelen). Ha korábban NEM volt üres az
        # indexben tárolt részfa, a takarítást konzervatívan kihagyjuk —
        # inkább maradjon egy ideig elavult bejegyzés, mint hogy a NAS
        # visszatérése után órákig tartó teljes újraépítés legyen és a
        # stabil rekord-id-k elvesszenek. Tényleges törléshez explicit
        # eltávolítás szükséges (Mappakezelő → „Eltávolítás a Picasából").
        logger.warning(
            "A gyökér elérhetetlennek tűnik (üres scan-eredmény, de az "
            "indexben van hozzá tartozó tartalom): %s — a takarítás "
            "kimaradt.",
            root_path,
        )
    conn.commit()


def sync_folder(
    conn: sqlite3.Connection,
    root: str | Path,
    folder: str | Path,
    exclude: tuple[str | Path, ...] = (),
    should_stop: Callable[[], bool] | None = None,
) -> None:
    """Egyetlen mappa nem-rekurzív szinkronja (watcher-ág, #143).

    A watcher mappa-pontos jelzést ad — nincs ok a teljes részfa
    újrabejárására. A mappa almappáihoz nem nyúl; ha a mappa eltűnt,
    kizárt vagy médiamentes lett, a sora (és a fotói) kikerülnek az
    indexből. A `root` a védőkorlát: csak a figyelt gyökér alatti mappa
    szinkronizálható.

    #216: ha a `should_stop` igazat ad (a mappa a hívás pillanatában már
    eltávolított gyökérhez tartozik), a sync ír-módosít nélkül visszatér —
    az egyetlen mappa maga a „mappa-határ"."""
    if should_stop is not None and should_stop():
        return  # megszakítva még a scan előtt — az index érintetlen
    root_path = Path(normalize_path(root))
    folder_path = Path(normalize_path(folder))
    if not folder_path.is_relative_to(root_path):
        raise ValueError(
            f"A mappa nem a figyelt gyökér alatt van: {folder_path} ∉ {root_path}"
        )
    _ensure_scan_state(conn)
    # #1249: a sírkövek itt is kizárnak (a watcher-ág is ide fut)
    exclude = tuple(exclude) + removed_folder_paths(conn)
    exclude_paths = tuple(Path(normalize_path(item)) for item in exclude)
    excluded = any(
        folder_path == item or item in folder_path.parents for item in exclude_paths
    )
    scan = None if excluded else scan_folder(folder_path)
    gyoker_baja = "" if excluded or scan is not None else _gyoker_baja(root_path)
    if gyoker_baja:
        # #1560: a takarítás bizonyítéka a GYÖKÉR. Ha az nem tudja
        # bizonyítani, hogy a tároló ott van, alatta SEMMILYEN sort nem
        # veszünk ki — ld. a `_gyoker_baja` docstringjét. A hibázás ára
        # aszimmetrikus: egy elavult sor átmeneti kényelmetlenség, a
        # kiürült index viszont a felhasználó teljes nyilvántartása.
        row = conn.execute(
            "SELECT id FROM folders WHERE path = ?", (str(folder_path),)
        ).fetchone()
        if row is not None:
            # a felhasználó ne néma üres rácsot lásson: a meglévő #459/5
            # jelölés (halvány, dőlt sor + súgószöveg + tájékoztató sáv)
            # kimondja, hogy a mappa most nem érhető el. A jelölés
            # visszafordítható: az első sikeres scan törli (`_sync_folder`).
            _set_folder_offline(conn, row["id"], True)
        logger.warning(
            "#1560: a figyelt gyökér (%s) %s — a(z) %s mappa indexsorait "
            "NEM takarítjuk.",
            root_path,
            gyoker_baja,
            folder_path,
        )
        conn.commit()
        return
    if scan is None:
        # #459/5: a `scan_folder` a nem elérhető mappára is None-t ad — a
        # törlés előtt megkérdezzük, hogy tényleg eltűnt-e. A kizárt mappa
        # (#145) ettől függetlenül kikerül: ott nem elérhetőségről van szó.
        row = None if excluded else conn.execute(
            "SELECT id FROM folders WHERE path = ?", (str(folder_path),)
        ).fetchone()
        if (
            row is not None
            and _has_photos(conn, row["id"])
            and folder_looks_offline(folder_path)
        ):
            _set_folder_offline(conn, row["id"], True)
            logger.warning(
                "A mappa jelenleg nem elérhető, az indexben marad: %s",
                folder_path,
            )
        else:
            _remove_folder(conn, folder_path)
    else:
        _sync_folder(conn, scan)
        _store_scan_state(conn, scan)
    conn.commit()


def _gyoker_baja(root_path: Path) -> str:
    """Üres szöveg, ha a figyelt gyökér BIZONYÍTJA, hogy a tároló ott van;
    különben a baj rövid megnevezése — naplózásra (#1560).

    ## Miért a gyökér a takarítás bizonyítéka

    A `folder_looks_offline` (#459/5) egyetlen mappáról dönt, és a hiányzó
    mappát eltűntnek veszi. Ez a mappa-szintű próba önmagában két, MÉRT
    adatvesztést enged át — mindkettőben a `sync_folder` vette ki a
    sorokat, miközben a képek a lemezen sértetlenek voltak:

    * **a figyelt gyökeret fájlkezelővel áthelyezték** (#1560): a #1275
      tízmásodperces lekérdezése 9,2 s alatt 3 mappa / 3 fotóról 0 / 0-ra
      ürítette az indexet;
    * **a NAS lecsatolódott**: a csatolási pont üres könyvtárként ott
      marad, tehát a gyökér sora túléli — az ALMAPPÁI viszont nem, mert
      azokra a `folder_looks_offline` `FileNotFoundError`-t kap.

    A közös ok: a mappa hiánya önmagában nem bizonyíték. Csak akkor jelent
    valódi hiányt, ha a GYÖKÉR igazolja, hogy a tároló olvasható és nem
    üres. Pontosan ez a `sync_tree` #132-es szabálya is — a `sync_folder`
    eddig egyszerűen nem követte; ez a függvény hozza össze a kettőt.

    Két baj van, és a jegy kifejezetten kéri az elhatárolásukat:

    * **eltűnt** (`watched_root_missing`): ENOENT/ENOTDIR, vagy az út már
      nem könyvtár — a horgony maga nincs meg;
    * **elérhetetlen** (`folder_looks_offline`): a gyökér olvasása
      elhasal (ESTALE, ENOTCONN, elvett jog), vagy teljesen üres — így néz
      ki egy lecsatolt mount.

    A kettő KÖVETKEZMÉNYE azonos (nem takarítunk), a naplóüzenetük más. A
    védelem szigorúan HOZZÁAD: nincs olyan ág, ahol miatta törlődne sor,
    ami eddig megmaradt volna. És nem is fagyasztja be az indexet: amint a
    gyökér ismét olvasható és nem üres, a takarítás magától újraindul (ld.
    `test_a_visszateres_utan_a_takaritas_ismet_fut`).
    """
    if watched_root_missing(root_path):
        return "nincs meg a lemezen"
    if folder_looks_offline(root_path):
        return "jelenleg nem elérhető (üres vagy olvashatatlan)"
    return ""


def watched_root_missing(root: str | Path) -> bool:
    """Igaz, ha MAGA a figyelt gyökér ELTŰNT a lemezről (#1560).

    A `_gyoker_baja` két próbája közül ez az egyik; a másik a
    `folder_looks_offline`. A kettő elhatárolása szándékos és szűk:

    * **eltűnt** — `FileNotFoundError`/`NotADirectoryError` (ENOENT,
      ENOTDIR), vagy az út létezik ugyan, de már NEM könyvtár. A horgony
      maga nincs meg: ilyet lát a program, ha a felhasználó a fő
      képmappáját fájlkezelővel áthelyezte vagy átnevezte.
    * **elérhetetlen** — **minden más `OSError`** (lecsatolt mount,
      `ESTALE`, `ENOTCONN`, elvett jog). Erre ez a függvény HAMISAT ad: az
      eset nem ide tartozik, hanem a `folder_looks_offline`-hoz.

    Az elhatárolásnak a NAPLÓÜZENETRE van hatása, a döntésre nincs: a
    `_gyoker_baja` mindkét bajra visszatartja a takarítást. Külön mégis
    érdemes tartani őket, mert a két ok mást jelent a felhasználónak (az
    egyiket ő maga okozta, a másik a tárolóé), és mert egy jövőbeli
    „keressük meg az új helyet" lépés (a #1542 `move_folder_tree`-je) csak
    az ELTŰNT ágon indulhat el — az elérhetetlen mountot megkeresni nem
    kell, vissza fog jönni.
    """
    try:
        stat = os.stat(root)
    except (FileNotFoundError, NotADirectoryError):
        return True  # a horgony tényleg nincs meg
    except OSError:
        # elérhetetlen (levált mount, ESTALE, jogosultság): NEM eltűnt —
        # innen a #459/5 ága viszi tovább
        return False
    return not stat_module.S_ISDIR(stat.st_mode)


def folder_looks_offline(folder_path: Path) -> bool:
    """Igaz, ha a mappa jelenleg NEM ELÉRHETŐNEK látszik (#459/5).

    A #132 gyökér-szintű védelmének mappa-szintű párja. A megkülönböztetés
    szándékosan szűk, hogy a „a felhasználó kiürítette a mappát" eset NE
    minősüljön offline-nak:

    - a `scandir` hibára fut (ESTALE/EIO/EACCES/ENOTCONN — levált mount,
      megszűnt hálózati megosztás, elvett jog) → offline;
    - a mappa létezik, de TELJESEN üres (nulla bejegyzés) → offline: a
      levált NAS-mount pontosan így néz ki (üres könyvtárként ott marad),
      míg a kiürített fotómappában rendszerint ott marad legalább a
      `.picasa.ini` vagy más fájl;
    - a mappa nem létezik, vagy létezik és van benne bármi (csak épp
      média nincs) → NEM offline, a takarítás futhat.

    A tévedés iránya tudatos: inkább maradjon egy ideig egy „jelenleg nem
    elérhető" jelölésű üres mappa a listában, mint hogy egy levált NAS
    fotói (és a stabil rekord-id-k) elvesszenek. A jelölés a következő
    sikeres scannel magától eltűnik, a végleges eltávolítás pedig explicit
    (Mappakezelő → „Eltávolítás a Picasából").
    """
    try:
        with os.scandir(folder_path) as it:
            return next(iter(it), None) is None
    except FileNotFoundError:
        return False  # ténylegesen eltűnt mappa — nem offline, takarítható
    except NotADirectoryError:
        return False
    except OSError:
        return True  # elérhetetlen (levált mount, jogosultság, I/O hiba)


def _has_photos(conn: sqlite3.Connection, folder_id: int) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM photos WHERE folder_id = ? LIMIT 1", (folder_id,)
        ).fetchone()
        is not None
    )


def _set_folder_offline(conn: sqlite3.Connection, folder_id: int, offline: bool) -> None:
    """Az offline jelölés írása — csak tényleges változásnál (a fölösleges
    UPDATE-ek WAL-hízást okoznának minden szinkronban)."""
    conn.execute(
        "UPDATE folders SET offline = ? WHERE id = ? AND offline IS NOT ?",
        (int(offline), folder_id, int(offline)),
    )


def _remove_folder(conn: sqlite3.Connection, folder_path: Path) -> None:
    """Egy mappa sorának (és fotóinak, scan-állapotának) törlése. Explicit
    photos-törlés a folders előtt, hogy az FTS-triggerek lefussanak."""
    row = conn.execute(
        "SELECT id FROM folders WHERE path = ?", (str(folder_path),)
    ).fetchone()
    if row is not None:
        conn.execute("DELETE FROM photos WHERE folder_id = ?", (row["id"],))
        conn.execute("DELETE FROM folders WHERE id = ?", (row["id"],))
    conn.execute(
        "DELETE FROM folder_scan_state WHERE path = ?", (str(folder_path),)
    )


def _ensure_scan_state(conn: sqlite3.Connection) -> None:
    """A scan-állapot cache-tábla lusta létrehozása (ld. _SCAN_STATE_DDL)."""
    conn.execute(_SCAN_STATE_DDL)
    conn.execute(_REMOVED_FOLDERS_DDL)


#: #1249: az „Eltávolítás a Picasából" SÍRKÖVEI. Az eredetiben a mappa nem
#: törlődik az albumtárból — `]album:removed` tokennel jelölt bejegyzés
#: marad (`0x004b9200`), és a beolvasó ettől nem veszi fel újra. Nálunk a
#: megfelelője ez a tábla: a beolvasás kihagyja a felsorolt útvonalakat
#: (és alfáikat), az újra-hozzáadás pedig feloldja őket.
_REMOVED_FOLDERS_DDL = """
CREATE TABLE IF NOT EXISTS removed_folders (
    path TEXT PRIMARY KEY
)
"""


def add_removed_folder(conn: sqlite3.Connection, path: str | Path) -> None:
    """Sírkő az eltávolított mappára (#1249) — a rescan nem hozza vissza."""
    _ensure_scan_state(conn)
    conn.execute(
        "INSERT OR REPLACE INTO removed_folders (path) VALUES (?)",
        (normalize_path(str(path)),),
    )
    conn.commit()


def clear_removed_folders_under(conn: sqlite3.Connection, path: str | Path) -> None:
    """A sírkövek feloldása az útvonalon ÉS alatta (#1249) — az újra
    felvett mappa (vagy szülője) alatt semmi nem maradhat némán rejtve."""
    _ensure_scan_state(conn)
    torzs = Path(normalize_path(str(path)))
    torlendo = [
        row["path"]
        for row in conn.execute("SELECT path FROM removed_folders")
        if Path(row["path"]) == torzs or Path(row["path"]).is_relative_to(torzs)
    ]
    for item in torlendo:
        conn.execute("DELETE FROM removed_folders WHERE path = ?", (item,))
    conn.commit()


def removed_folder_paths(conn: sqlite3.Connection) -> tuple[str, ...]:
    """A sírkövek listája — a beolvasás kizáró-készletéhez (#1249)."""
    _ensure_scan_state(conn)
    return tuple(
        row["path"]
        for row in conn.execute("SELECT path FROM removed_folders ORDER BY path")
    )


def folder_paths_under(conn: sqlite3.Connection, root: str | Path) -> tuple[str, ...]:
    """A `root` és az alatta lévő mappák INDEXBELI útvonalai (#1538).

    Akkor kell, amikor egy részfa a LEMEZEN már nincs meg, tehát a „mi
    tartozik ide" kérdésre csak az index tud válaszolni — a mappa-
    áthelyezés RÉGI oldala pontosan ilyen. A hívó ezután mappánként
    szinkronizál, így az eltűnt sorok a `sync_folder` saját
    `folder_looks_offline` próbáján át esnek ki: egy ELÉRHETETLEN (nem
    eltűnt) mappa sorai megmaradnak.

    A LIKE-mintát a `_under_root_query` escape-eli, tehát a `%`/`_` a
    mappanévben nem viselkedik jokerként. A sorrend determinisztikus
    (`ORDER BY path`), hogy a naplók és a tesztek stabilak legyenek."""
    root_path = Path(normalize_path(root))
    query, params = _under_root_query("SELECT path", root_path)
    return tuple(
        row["path"] for row in conn.execute(f"{query} ORDER BY path", params)
    )


#: A #1542 útvonal-átírása ezeket a táblákat érinti — MINDEGYIK ABSZOLÚT
#: útvonalat tárol kulcsként, tehát egy áthelyezett részfánál MIND elavul:
#:
#: * `folders` — a mappák sorai (a fotók a `folder_id`-n lógnak, azokhoz
#:   ezért nem kell nyúlni: a részfa átírása egyetlen fotósort sem érint);
#: * `folder_scan_state` — a „változott-e a mappa" pecsétek. Átírás nélkül
#:   a teljes áthelyezett fa elavultnak látszana (fölösleges újraolvasás),
#:   a régi sorok pedig örökre ottragadnának;
#: * `removed_folders` — a #1249 SÍRKÖVEI. Átírás nélkül egy korábban
#:   „Eltávolítás a Picasából"-val kivett almappa az áthelyezés után némán
#:   VISSZAJÖNNE — a felhasználó döntése veszne el;
#: * `photo_hashes` — a #294 dHash-gyorsítótára (FÁJL-útvonalra kulcsolva).
#:   Tisztán származtatott adat, de átírás nélkül az egész gyűjtemény
#:   hash-eit újra kellene számolni, a régi sorok meg szemétként maradnának.
_PATH_TABLES = ("folders", "folder_scan_state", "removed_folders", "photo_hashes")


def _reszfa_feltetel(root: Path) -> tuple[str, tuple[str, str]]:
    """WHERE-feltétel + paraméterek egy `path` oszlop `root` alatti soraira.

    Az `_under_root_query` mintája, de tábla NÉLKÜL: az `UPDATE`-be a
    `FROM` záradék nem fér bele (SQLite 3.33 óta az `UPDATE … FROM` JOIN-t
    jelent, és a `path` oszlop kétértelművé válna). A LIKE-minta itt is
    escape-elt és elválasztóval zárt: a „…/kep" gyökér NEM foghatja meg a
    „…/kepek" sorait."""
    prefix = str(root).rstrip(os.sep) + os.sep
    escaped = prefix.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return (
        "WHERE path = ? OR path LIKE ? ESCAPE '\\'",
        (str(root), escaped + "%"),
    )


def move_folder_tree(
    conn: sqlite3.Connection, old_root: str | Path, new_root: str | Path
) -> int:
    """Egy ÁTHELYEZETT részfa útvonalainak ÁTÍRÁSA az indexben (#1542).

    Akkor kell, amikor MAGA a figyelt gyökér mozdult el: a `_roots` és a
    `WatchedFolders.txt` az új helyre áll, tehát az indexnek is oda kell
    mutatnia — különben a gyökér alá már egyetlen indexsor sem esik, és a
    következő induláskor a `prune_foreign_folders` (#58) az egészet
    kitakarítaná.

    ⚠️ **Ez a függvény SORT NEM TÖRÖL ÉS NEM HOZ LÉTRE** — kizárólag a
    `path` oszlopokat írja át. Ez a jegy adatbiztonsági súlypontja: egy
    áthelyezés nem járhat sorvesztéssel, és a törlés-majd-újraolvasás
    (`remove_root` + rescan) egy megszakadt köznél épp azt tenné.

    Ütközésnél (az ÚJ út alatt már van indexsor) `ValueError`-t dob és
    SEMMIT nem módosít: két, útvonal szerint megkülönböztethetetlen
    részfáról nem tippelünk, melyik a hatályos — a hívó ilyenkor inkább
    nem követi a gyökeret.

    Visszatérési érték: az átírt MAPPA-sorok száma (a naplóhoz és a
    tesztek fogához)."""
    old_path = Path(normalize_path(old_root))
    new_path = Path(normalize_path(new_root))
    if old_path == new_path:
        return 0
    _ensure_scan_state(conn)
    _ensure_photo_hashes(conn)
    utkozes, params = _reszfa_feltetel(new_path)
    sor = conn.execute(
        f"SELECT 1 FROM folders {utkozes} LIMIT 1", params
    ).fetchone()
    if sor is not None:
        raise ValueError(
            f"Az index már tartalmaz sorokat az új út alatt: {new_path} — "
            "az áthelyezett részfa átírása kimarad."
        )
    # a levágandó előtag hossza; az SQLite `substr` 1-alapú, tehát a
    # +1 adja a maradékot (a pontos egyezésnél üres sztringet)
    vagas = len(str(old_path)) + 1
    mozgatott = 0
    try:
        for table in _PATH_TABLES:
            feltetel, params = _reszfa_feltetel(old_path)
            kurzor = conn.execute(
                f"UPDATE {table} SET path = ? || substr(path, ?) {feltetel}",
                (str(new_path), vagas, *params),
            )
            if table == "folders":
                mozgatott = kurzor.rowcount
    except sqlite3.Error:
        conn.rollback()
        raise
    conn.commit()
    logger.info(
        "#1542: az áthelyezett részfa átírva az indexben: %s → %s (%d mappa)",
        old_path,
        new_path,
        mozgatott,
    )
    return mozgatott


def _ensure_photo_hashes(conn: sqlite3.Connection) -> None:
    """A #294 hash-gyorsítótár lusta létrehozása — a `move_folder_tree`
    régi (a tábla bevezetése előtt született) indexen is futhat."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS photo_hashes ("
        " path TEXT PRIMARY KEY,"
        " mtime_ns INTEGER NOT NULL,"
        " size INTEGER NOT NULL,"
        " dhash INTEGER NOT NULL)"
    )


def folder_scan_stamps(
    conn: sqlite3.Connection, paths: tuple[str, ...]
) -> dict[str, tuple[int, int | None]]:
    """A megadott mappák utoljára LÁTOTT pecsétje (mtime_ns, ini_mtime_ns).

    A `folder_scan_state` táblát a szinkron amúgy is vezeti — ez csak
    OLVASSA (#1435), új séma nincs. A hívó (`app/folder_freshness.py`)
    ehhez hasonlítja a lemezen mért pecsétet, és csak eltérésnél kér
    teljes újraolvasást. A még sosem látott mappa egyszerűen kimarad a
    szótárból."""
    if not paths:
        return {}
    _ensure_scan_state(conn)
    placeholders = ",".join("?" for _ in paths)
    return {
        row["path"]: (row["mtime_ns"], row["ini_mtime_ns"])
        for row in conn.execute(
            "SELECT s.path, s.mtime_ns, s.ini_mtime_ns"
            " FROM folder_scan_state s JOIN folders f ON f.path = s.path"
            f" WHERE s.path IN ({placeholders})",
            paths,
        )
    }


def _make_skip(conn: sqlite3.Connection):
    """Kihagyás-predikátum az inkrementális rescanhez (#143).

    Csak olyan mappa hagyható ki, amely (1) az indexben is szerepel,
    (2) mappa- és ini-mtime-ja bitre egyezik a tárolt állapottal, és
    (3) mindkét mtime idősebb a frissesség-védőablaknál."""
    state = {
        row["path"]: (row["mtime_ns"], row["ini_mtime_ns"])
        for row in conn.execute(
            "SELECT s.path, s.mtime_ns, s.ini_mtime_ns"
            " FROM folder_scan_state s JOIN folders f ON f.path = s.path"
        )
    }
    fresh_limit = time.time_ns() - _SKIP_SAFETY_NS

    def skip(path: Path, mtime_ns: int, ini_mtime_ns: int | None) -> bool:
        return (
            state.get(str(path)) == (mtime_ns, ini_mtime_ns)
            and mtime_ns <= fresh_limit
            and (ini_mtime_ns is None or ini_mtime_ns <= fresh_limit)
        )

    return skip


def _store_scan_state(conn: sqlite3.Connection, scan: FolderScan) -> None:
    if not scan.mtime_ns:
        return  # a mappa statja nem sikerült — ne rögzítsünk hamis állapotot
    conn.execute(
        "INSERT INTO folder_scan_state(path, mtime_ns, ini_mtime_ns)"
        " VALUES (?, ?, ?)"
        " ON CONFLICT(path) DO UPDATE SET mtime_ns = excluded.mtime_ns,"
        " ini_mtime_ns = excluded.ini_mtime_ns",
        (str(scan.path), scan.mtime_ns, scan.ini_mtime_ns),
    )


def _sync_folder(conn: sqlite3.Connection, scan: FolderScan) -> int:
    """Egy mappa szinkronja; a visszatérési érték az ÚJ (az indexben eddig
    nem szereplő) fotók száma (#209, a haladás-jelzéshez)."""
    # #459/5: a sikeres scan bizonyítja, hogy a mappa elérhető — az esetleges
    # offline jelölés magától elmúlik (a NAS visszatérése után nincs teendő).
    folder_id = conn.execute(
        "INSERT INTO folders(path, has_ini, offline) VALUES (?, ?, 0) "
        "ON CONFLICT(path) DO UPDATE SET has_ini = excluded.has_ini,"
        " offline = 0 "
        "RETURNING id",
        (str(scan.path), int(scan.has_ini)),
    ).fetchone()[0]
    # Az ini-mezőket is beolvassuk (#139): változatlan fájl + változatlan
    # ini-mezők esetén az UPDATE teljesen kimarad — az SQLite azonos
    # értékeknél is átírná a sort és elsütné az FTS-triggert (delete+insert
    # minden fotóra minden syncnél → WAL-hízás, flash-kopás).
    existing = {
        row["name"]: (
            (row["mtime_ns"], row["size"]),
            (
                row["star"],
                row["hidden"],
                row["caption_ini"],
                row["keywords_ini"],
                row["rotate_steps"],
                row["filters"],
                row["geotag_ini"],
            ),
        )
        for row in conn.execute(
            "SELECT name, mtime_ns, size, star, hidden, caption_ini,"
            " keywords_ini, rotate_steps, filters, geotag_ini"
            " FROM photos WHERE folder_id = ?",
            (folder_id,),
        )
    }
    document = _load_ini(scan)
    new_count = 0
    for media in scan.files:
        section = document.section(media.name) if document else None
        ini_fields = (
            int(section.get("star") == "yes") if section else 0,
            int(section.get("hidden") == "yes") if section else 0,
            section.get("caption") if section else None,
            section.get("keywords") if section else None,
            _rotate_steps(section.get("rotate")) if section else 0,
            section.get("filters") if section else None,
            # #30: a geocímke nyers ini-értéke — a feloldást (ini > EXIF)
            # a lekérdezés-réteg végzi, itt bitre pontosan az tárolódik,
            # ami az ini-ben áll
            section.get("geotag") if section else None,
        )
        current = existing.get(media.name)
        if current is not None and current[0] == (media.mtime_ns, media.size):
            # Változatlan fájl: a (drága) EXIF/IPTC-olvasás kimarad, a
            # fájl-metaadat oszlopok maradnak. UPDATE csak akkor fut, ha
            # az ini-mezők ténylegesen eltérnek (#139) — különben a sor
            # érintetlen, az FTS-trigger sem sül el.
            if current[1] != ini_fields:
                conn.execute(
                    "UPDATE photos SET star = ?, hidden = ?, caption_ini = ?,"
                    " keywords_ini = ?, rotate_steps = ?, filters = ?,"
                    " geotag_ini = ?"
                    " WHERE folder_id = ? AND name = ?",
                    (*ini_fields, folder_id, media.name),
                )
        else:
            if current is None:
                new_count += 1  # #209: eddig nem indexelt fotó
            _upsert_photo(conn, folder_id, scan, media, ini_fields)
    _prune_photos(conn, folder_id, [media.name for media in scan.files])
    _sync_albums(conn, folder_id, document)
    _sync_folder_date(conn, folder_id, document)
    return new_count


def _sync_folder_date(
    conn: sqlite3.Connection, folder_id: int, document: IniDocument | None
) -> None:
    """Mappa-dátum (#320): a `.picasa.ini` `[Picasa]` `date=` kézi
    felülírása elsőbbséget élvez; ennek hiányában az alapértelmezett Picasa-
    viselkedés — automatikusan a legrégebbi felvétel ideje."""
    override = read_folder_date_override(document) if document else None
    if override is not None:
        conn.execute(
            "UPDATE folders SET date = ? WHERE id = ?", (override, folder_id)
        )
        return
    conn.execute(
        "UPDATE folders SET date = ("
        " SELECT MIN(p.taken_at) FROM photos p WHERE p.folder_id = ?"
        ") WHERE id = ?",
        (folder_id, folder_id),
    )


def _upsert_photo(
    conn: sqlite3.Connection,
    folder_id: int,
    scan: FolderScan,
    media: MediaFile,
    ini_fields: tuple,
) -> None:
    meta = (
        read_file_metadata(scan.path / media.name)
        if media.kind == "photo"
        else EMPTY_METADATA
    )
    conn.execute(
        "INSERT INTO photos"
        "(folder_id, name, kind, size, mtime_ns, star, hidden, caption_ini,"
        " keywords_ini, rotate_steps, filters, geotag_ini, taken_at,"
        " orientation, width, height, caption_file, keywords_file,"
        " exif_lat, exif_lon)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(folder_id, name) DO UPDATE SET "
        "kind = excluded.kind, size = excluded.size, "
        "mtime_ns = excluded.mtime_ns, star = excluded.star, "
        "hidden = excluded.hidden, "
        "caption_ini = excluded.caption_ini, "
        "keywords_ini = excluded.keywords_ini, "
        "rotate_steps = excluded.rotate_steps, "
        "filters = excluded.filters, "
        "geotag_ini = excluded.geotag_ini, "
        "taken_at = excluded.taken_at, orientation = excluded.orientation, "
        "width = excluded.width, height = excluded.height, "
        "caption_file = excluded.caption_file, "
        "keywords_file = excluded.keywords_file, "
        "exif_lat = excluded.exif_lat, exif_lon = excluded.exif_lon",
        (
            folder_id,
            media.name,
            media.kind,
            media.size,
            media.mtime_ns,
            *ini_fields,
            meta.taken_at,
            meta.orientation,
            meta.width,
            meta.height,
            meta.caption,
            ",".join(meta.keywords) or None,
            meta.latitude,
            meta.longitude,
        ),
    )


def _load_ini(scan: FolderScan) -> IniDocument | None:
    if not scan.has_ini:
        return None
    try:
        return load_document(scan.path / PICASA_INI_NAME)
    except (OSError, ValueError):
        # Zárolt/olvashatatlan/sérült ini (pl. a futó Picasa fogja): a mappa
        # metaadat nélkül indexelődik, a következő sync majd pótolja.
        return None


def _rotate_steps(value: str | None) -> int:
    if value is None:
        return 0
    match = _ROTATE.match(value)
    return int(match.group(1)) % 4 if match else 0


_PRUNE_TEMP_TABLE = "_prune_photos_names"


def _sync_albums(conn, folder_id: int, document) -> None:
    """A mappa virtuális albumainak és a tagságoknak a szinkronizálása (#9).

    Két külön dolog jön az ini-ből:
    - a `[.album:<token>]` szekciók az album DEFINÍCIÓJÁT adják (név, dátum);
      ugyanaz az album több mappában is definiálva lehet, ezért `upsert` a
      tokenre — az utoljára látott, nem üres név nyer,
    - a képek `albums=` kulcsa a TAGSÁGOT adja; ezt mappánként újraépítjük,
      hogy az ini-ből kivett kép az indexből is kiessen.

    Az ini nélküli mappa csak a saját tagságait törli — a máshol definiált
    albumokat nem bántja.
    """
    photo_ids = {
        row["name"]: row["id"]
        for row in conn.execute(
            "SELECT id, name FROM photos WHERE folder_id = ?", (folder_id,)
        )
    }
    conn.execute(
        "DELETE FROM photo_albums WHERE photo_id IN"
        " (SELECT id FROM photos WHERE folder_id = ?)",
        (folder_id,),
    )
    # a mappa SAJÁT definícióit írjuk újra — így az ini-ből törölt album
    # akkor is kiesik, ha egy másik mappa még hivatkozik rá
    conn.execute("DELETE FROM albums WHERE folder_id = ?", (folder_id,))
    if document is None:
        _prune_albums(conn)
        return

    for album in albums_of(document):
        conn.execute(
            "INSERT INTO albums"
            " (folder_id, token, name, date, description, location)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (
                folder_id,
                album.token,
                album.name,
                album.date,
                album.description,
                album.location,
            ),
        )

    for name, photo_id in photo_ids.items():
        section = document.section(name)
        if section is None:
            continue
        refs = section.get("albums")
        if not refs:
            continue
        for token in parse_album_refs(refs):
            conn.execute(
                "INSERT OR IGNORE INTO photo_albums (photo_id, token)"
                " VALUES (?, ?)",
                (photo_id, token),
            )
    _prune_albums(conn)


def _prune_albums(conn) -> None:
    """A már sehol nem DEFINIÁLT albumok tagságainak kivezetése.

    Az albumot a definíciója tartja életben: ha egyetlen mappa ini-jében sem
    szerepel többé a `[.album:<token>]` szekció, akkor a rá mutató tagságok
    is értelmüket vesztik. A definíciós sorokat maga a mappa-szinkron írja
    újra, itt csak az árván maradt hivatkozásokat takarítjuk.
    """
    conn.execute(
        "DELETE FROM photo_albums WHERE token NOT IN (SELECT token FROM albums)"
    )


def _prune_photos(
    conn: sqlite3.Connection, folder_id: int, names: list[str]
) -> None:
    """A mappából eltűnt fotók (indexbeli sorai) törlése.

    #304: `names` egy nagy (32 766-nál — az SQLite `SQLITE_MAX_VARIABLE_
    NUMBER` alapértéke — több elemű) mappánál nem paraméterezhető közvetlenül
    egy `NOT IN (?, ?, ...)` listaként — az `sqlite3.OperationalError`-ral
    bukna. Ehelyett egy ideiglenes (kapcsolat-lokális) táblába kerülnek a
    látott nevek, és a törlés egy al-SELECT-tel szűr. A temp tábla neve nem
    ütközhet más kapcsolattal (az SQLite temp táblái kapcsolat-lokálisak),
    de a `_sync_folder` ugyanazon a kapcsolaton mappánként újra hívja ezt a
    függvényt — ezért a hívás elején `DROP TABLE IF EXISTS`-szel takarítunk,
    a végén pedig explicit `DROP TABLE`-lel."""
    if not names:
        conn.execute("DELETE FROM photos WHERE folder_id = ?", (folder_id,))
        return
    conn.execute(f"DROP TABLE IF EXISTS temp.{_PRUNE_TEMP_TABLE}")
    conn.execute(f"CREATE TEMP TABLE {_PRUNE_TEMP_TABLE} (name TEXT PRIMARY KEY)")
    conn.executemany(
        f"INSERT INTO {_PRUNE_TEMP_TABLE}(name) VALUES (?)",
        [(name,) for name in names],
    )
    conn.execute(
        "DELETE FROM photos WHERE folder_id = ? AND name NOT IN"
        f" (SELECT name FROM {_PRUNE_TEMP_TABLE})",
        (folder_id,),
    )
    conn.execute(f"DROP TABLE {_PRUNE_TEMP_TABLE}")


def _prune_folders(
    conn: sqlite3.Connection, root: Path, seen_paths: set[str]
) -> None:
    """A gyökér alatti, de a mostani scanben nem látott mappák törlése.

    #143: a gyökér-szűrés SQL-oldalon fut (indexelhető LIKE-prefix), nem
    Pythonban az összes mappán iterálva. Explicit photos-törlés a folders
    előtt, hogy az FTS-triggerek biztosan lefussanak (az FK-cascade nem
    minden konfigurációban futtat triggert).

    #459/5: a nem látott mappa nem feltétlenül eltűnt mappa — lehet, hogy
    csak épp nem elérhető (levált NAS-mount). Az ilyen mappa a fotóival
    EGYÜTT bennmarad az indexben, `offline = 1` jelöléssel; a takarítás
    csak a bizonyítottan eltűnt mappákra fut. Ld. `folder_looks_offline`.
    """
    stale = [
        (row["id"], row["path"])
        for row in conn.execute(*_under_root_query("SELECT id, path", root))
        if row["path"] not in seen_paths
    ]
    for folder_id, path in stale:
        # Óvni csak azt érdemes, amiben van is mit veszíteni: fotó nélküli
        # sor eltávolítása nem jár adatvesztéssel, ott a takarítás mehet.
        if _has_photos(conn, folder_id) and folder_looks_offline(Path(path)):
            _set_folder_offline(conn, folder_id, True)
            logger.warning(
                "A mappa jelenleg nem elérhető, az indexben marad: %s", path
            )
            continue
        conn.execute("DELETE FROM photos WHERE folder_id = ?", (folder_id,))
        conn.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
        conn.execute("DELETE FROM folder_scan_state WHERE path = ?", (path,))


def _under_root_query(select: str, root: Path) -> tuple[str, tuple[str, str]]:
    """SQL + paraméterek a gyökér alatti folders-sorokhoz (#143).

    A LIKE-minta escape-elt (%, _ és \\ a path-ban nem viselkedhet
    joker-ként), és elválasztóval zárt prefixet használ — a „/a/kep" gyökér
    nem foghatja meg a „/a/kepek" mappáit."""
    prefix = str(root).rstrip(os.sep) + os.sep
    escaped = (
        prefix.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    )
    return (
        f"{select} FROM folders WHERE path = ? OR path LIKE ? ESCAPE '\\'",
        (str(root), escaped + "%"),
    )


def _is_under(path: Path, root: Path) -> bool:
    return path == root or path.is_relative_to(root)


def _has_indexed_folders(conn: sqlite3.Connection, root: Path) -> bool:
    """Van-e a gyökér alá eső mappa az indexben (a scan-eredménytől függetlenül)."""
    query, params = _under_root_query("SELECT 1", root)
    return conn.execute(f"{query} LIMIT 1", params).fetchone() is not None


# #141: fehérlista — csak ismert, biztonságos oszlopokra engedjük a célzott
# UPDATE-et (csillag/felirat/forgatás gyors-útja, teljes resync nélkül).
_TARGETED_UPDATE_COLUMNS = {
    "star",
    "hidden",
    "caption_ini",
    "caption_file",
    "keywords_ini",
    "keywords_file",
    "rotate_steps",
}


def update_photo_fields(conn: sqlite3.Connection, photo_id: int, **fields) -> None:
    """Egy fotó indexsorának célzott, egy-soros UPDATE-je (#141).

    A csillag/felirat/forgatás gyors-útja: amikor az új érték már ismert (a
    hívó épp most írta az inibe/IPTC-be), nincs szükség a teljes mappa-
    resyncre (`sync_tree`/`sync_folder`) — egyetlen UPDATE elég, ami az
    FTS-triggert is csak az érintett sorra sütteti el."""
    if not fields:
        return
    unknown = set(fields) - _TARGETED_UPDATE_COLUMNS
    if unknown:
        raise ValueError(f"Nem célzott-frissíthető oszlop(ok): {sorted(unknown)}")
    columns = ", ".join(f"{name} = ?" for name in fields)
    conn.execute(
        f"UPDATE photos SET {columns} WHERE id = ?",
        (*fields.values(), photo_id),
    )
    conn.commit()


def remove_root(conn: sqlite3.Connection, root: str | Path) -> None:
    """Egy gyökér teljes eltávolítása az indexből (Mappakezelő:
    „Eltávolítás a Picasából"). Explicit photos-törlés a folders előtt,
    hogy az FTS-triggerek lefussanak."""
    root_path = Path(normalize_path(root))
    _ensure_scan_state(conn)
    _prune_folders(conn, root_path, set())
    conn.commit()


def prune_foreign_folders(
    conn: sqlite3.Connection, roots: tuple[str | Path, ...]
) -> None:
    """A figyelt gyökerek egyikéhez sem tartozó mappák törlése az indexből.

    Induláskor fut (#58): a korábbi futásokból ottragadt gyökerek (pl. régi
    parancssori argumentum) mappái ne jelenjenek meg a bal hasábban. Üres
    gyökérlistával nem csinál semmit — védekezés, nehogy egy hiányzó
    WatchedFolders.txt csendben kiürítse az egész indexet. Explicit
    photos-törlés a folders előtt, hogy az FTS-triggerek lefussanak."""
    if not roots:
        return
    _ensure_scan_state(conn)
    root_paths = tuple(Path(normalize_path(root)) for root in roots)
    stale = [
        (row["id"], row["path"])
        for row in conn.execute("SELECT id, path FROM folders")
        if not any(_is_under(Path(row["path"]), root) for root in root_paths)
    ]
    for folder_id, path in stale:
        conn.execute("DELETE FROM photos WHERE folder_id = ?", (folder_id,))
        conn.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
        conn.execute("DELETE FROM folder_scan_state WHERE path = ?", (path,))
    conn.commit()
