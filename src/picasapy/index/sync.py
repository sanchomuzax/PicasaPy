# ruff: noqa: F401
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
from collections.abc import Callable, Collection
from pathlib import Path
from typing import NamedTuple

from picasapy.index.queries import HIDDEN_INI_PENDING
from picasapy.index.origin import forget_origin_keys_outside
from picasapy.ini import (
    IniDocument,
    ini_source_path,
    is_hidden_folders_category,
    load_document,
    read_folder_category,
    read_folder_date_override,
    set_folder_hidden_in_ini,
)
from picasapy.ini.names import INI_NAME
from picasapy.ini.album_order import places_of_section
from picasapy.ini.albums import albums_of, parse_album_refs
from picasapy.metadata import (
    EMPTY_METADATA,
    EMPTY_VIDEO_METADATA,
    read_file_metadata,
    read_video_metadata,
)
from picasapy.paths import normalize_path
from picasapy.render.flip import FLIP_MASK
from picasapy.scanner import (
    FolderScan,
    HibasBejegyzes,
    MediaFile,
    scan_folder,
    scan_tree,
)


# Régi importútvonalak: a függvények közvetlenül erről a modulról maradnak elérhetők.
from .sync_folders import (
    _PATH_TABLES,
    _csatolasi_hataron_ul,
    _ensure_scan_state,
    _gyoker_baja,
    _gyoker_ures_vagy_olvashatatlan,
    _has_photos,
    _remove_folder,
    _reszfa_feltetel,
    _scandir,
    _set_folder_offline,
    add_removed_folder,
    clear_removed_folders_under,
    folder_looks_offline,
    folder_paths_under,
    move_folder_tree,
    remove_folder_tree,
    removed_folder_paths,
    watched_root_missing,
)
from .sync_state import (
    _ensure_photo_hashes,
    _ensure_similarity_features,
    _filetype_signature,
    _make_skip,
    _store_scan_state,
    folder_scan_stamps,
)
from .sync_photos import (
    _FolderSyncResult,
    _load_ini,
    _prune_albums,
    _prune_photos,
    _rotate_steps,
    _sync_albums,
    _sync_folder,
    _sync_folder_hidden,
    _upsert_photo,
    flip_jelzo,
    sync_folder_date,
)
from .sync_cleanup import (
    _TARGETED_UPDATE_COLUMNS,
    _azonossag,
    _elojeles64,
    _feloldas_gyorstarral,
    _has_indexed_folders,
    _is_under,
    _prune_folders,
    _resolved_protected_roots,
    _under_root_query,
    prune_foreign_folders,
    remove_root,
    update_photo_fields,
)


#: Az `os.stat` MODULSZINTŰ fogantyúja (#1375, #1560) — a teszt EZT cserélje:
#: `monkeypatch.setattr(sync, "_stat", …)`.
#:
#: A `monkeypatch.setattr(sync.os, "stat", …)` alak a GLOBÁLIS `os`-t írja át,
#: és a csere a teszt teljes idejére MINDEN más modulra is hat — a
#: `test_szabalykonyv_szinkron` őre ezért bukik rá. A fogantyú cseréje viszont
#: csak ezt az egy döntést mozdítja.
#:
#: Miért kell egyáltalán cserélhetőnek lennie: a `watched_root_missing`
#: „eltűnt vs. elérhetetlen" elhatárolása azon múlik, MILYEN `OSError` jön —
#: és az `ESTALE`/`ENOTCONN` fajtát fájlrendszerrel nem lehet előállítani, a
#: jogosultság-alapú változat pedig Windowson hatástalan (ott a `chmod` nem
#: korlátoz).
_stat = os.stat

_ROTATE = re.compile(r"^rotate\((\d+)\)$")
#: #2976: a tükrözés maszkja. A `flipped=` ÜRES értéke (és a hiányzó kulcs)
#: egyaránt „nincs tükrözés" — az eredeti a nullát épp üresen írja ki.
_FLIPPED = re.compile(r"^flipped\((\d+)\)$")

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
    " ini_mtime_ns INTEGER,"
    " filetype_signature TEXT)"
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
    enabled_filetypes: Collection[str] | None = None,
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
    filetype_signature = _filetype_signature(enabled_filetypes)
    skip = _make_skip(conn, filetype_signature) if incremental else None
    # #358: az `excluded_names` a #349 NÉV-kizárólista miatt kihagyott
    # mappákat gyűjti — ha ez nem üres, a gyökér scandirje bizonyíthatóan
    # lefutott (a gyökér tehát elérhető), csak minden talált tartalom
    # kizárt nevű mappa alatt van. Ez különbözteti meg a védő-heurisztikát
    # a ténylegesen elérhetetlen gyökértől (ld. lent).
    excluded_names: list[Path] = []
    # #1998: a bejáró eddig NÉMÁN nyelte el az olvasási hibákat — a
    # felhasználó annyit látott, hogy egy mappa vagy egy kép „nincs ott".
    # Elemenként a `walker` naplóz; itt egy összesítő sor is kell, mert a
    # hosszú scan naplójában az egyedi sorok elvesznek.
    hibas_bejegyzesek: list[HibasBejegyzes] = []
    scans = scan_tree(
        root_path,
        exclude=exclude,
        skip=skip,
        excluded_names=excluded_names,
        hibas_bejegyzesek=hibas_bejegyzesek,
        enabled_filetypes=enabled_filetypes,
    )
    if hibas_bejegyzesek:
        mappak = sum(1 for elem in hibas_bejegyzesek if elem.mappa)
        logger.warning(
            "A beolvasás %d elemet nem tudott feldolgozni (%d mappa, %d fájl) "
            "a(z) %s alatt — az elsők: %s",
            len(hibas_bejegyzesek),
            mappak,
            len(hibas_bejegyzesek) - mappak,
            root_path,
            ", ".join(str(elem.path) for elem in hibas_bejegyzesek[:5]),
        )
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
            if progress is not None and progress(str(scan.path), done, len(scans), new_total):
                cancelled = True
                break
            continue
        folder_result = _sync_folder(conn, scan)
        new_total += folder_result.new_count
        if should_stop is not None and should_stop():
            # Az olvasás alatt változhatott a Mappakezelő kizárási
            # generációja. A jelen mappa még nem commitolt írásait eldobjuk,
            # különben egy frissen kizárt ágat visszaírhatna a stale worker.
            conn.rollback()
            cancelled = True
            break
        if incremental and (scan.files or scan.has_ini) and not folder_result.retry:
            _store_scan_state(conn, scan, filetype_signature)
        conn.commit()
        if progress is not None and progress(str(scan.path), done, len(scans), new_total):
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
    incremental: bool = False,
    enabled_filetypes: Collection[str] | None = None,
) -> None:
    """Egyetlen mappa nem-rekurzív szinkronja (watcher-ág, #143).

    #1674: `incremental=True` esetén a VÁLTOZATLAN mappa fájljait meg sem
    statoljuk — a #139 kihagyás-predikátumát (`_make_skip`) használjuk, azt
    a gépezetet, amit eddig csak a rekurzív rescan kapott meg. A feltétel
    szigorú: a mappa- ÉS az ini-mtime bitre egyezzen a tárolt állapottal, és
    mindkettő legyen idősebb a frissesség-védőablaknál — egy épp íródó
    mappa így nem ragadhat be.

    Az alapértelmezés SZÁNDÉKOSAN `False`: a watcher jelzésére a mappa épp
    azért jön, mert valami történt vele. Az indulási önjavító ágak
    (#1565/#1075) viszont változatlan mappákat olvasnak újra, és ott a
    kihagyás a nyereség.

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
    # #2483: az indulási önjavító ág a gyökeret és a mappát AZONOS értékkel
    # adja át (`sync_folder(conn, mappa, mappa)`), a feloldás viszont
    # mélységnyi `lstat`-ot jelent útvonalanként. Ugyanaz a nyers szöveg
    # ugyanarra az útra vezet — a kihagyás tehát a végeredményt nem
    # változtatja, csak a felesleges rendszerhívást takarítja meg (a #1706
    # `_resolved_protected_roots` érvelése, egy hívásra szűkítve).
    folder_path = root_path if str(folder) == str(root) else Path(normalize_path(folder))
    if not folder_path.is_relative_to(root_path):
        raise ValueError(f"A mappa nem a figyelt gyökér alatt van: {folder_path} ∉ {root_path}")
    _ensure_scan_state(conn)
    # #1249: a sírkövek itt is kizárnak (a watcher-ág is ide fut)
    #
    # #2483: a sírkövek útvonala MÁR kanonikus — az `add_removed_folder`
    # `normalize_path`-szal ír, az áthelyezés-migráció (`_PATH_TABLES`) is
    # kanonikus alakot tesz vissza. Az újrafeloldásuk tehát tiszta
    # veszteség, és a szorzó rossz: hívásonként (tehát exportcélonként)
    # futott le MINDEN sírkőre. MÉRVE: 20 sírkő × 10 exportcél = +800
    # `lstat` egyetlen induláson.
    exclude_paths = tuple(Path(normalize_path(item)) for item in exclude) + tuple(
        Path(item) for item in removed_folder_paths(conn)
    )
    excluded = any(folder_path == item or item in folder_path.parents for item in exclude_paths)
    filetype_signature = _filetype_signature(enabled_filetypes)
    skip = _make_skip(conn, filetype_signature) if incremental else None
    # #2483: a `folder_path` EBBEN a függvényben lett feloldva — a
    # kizárólista ne oldja fel még egyszer (útvonal-komponensenként egy
    # `lstat`)
    scan = (
        None
        if excluded
        else scan_folder(
            folder_path,
            skip=skip,
            mar_feloldva=True,
            enabled_filetypes=enabled_filetypes,
        )
    )
    gyoker_baja = "" if excluded or scan is not None else _gyoker_baja(root_path)
    if gyoker_baja:
        # #1560: a takarítás bizonyítéka a GYÖKÉR. Ha az nem tudja
        # bizonyítani, hogy a tároló ott van, alatta SEMMILYEN sort nem
        # veszünk ki — ld. a `_gyoker_baja` docstringjét. A hibázás ára
        # aszimmetrikus: egy elavult sor átmeneti kényelmetlenség, a
        # kiürült index viszont a felhasználó teljes nyilvántartása.
        row = conn.execute("SELECT id FROM folders WHERE path = ?", (str(folder_path),)).fetchone()
        if row is not None:
            # a felhasználó ne néma üres rácsot lásson: a meglévő #459/5
            # jelölés (halvány, dőlt sor + súgószöveg + tájékoztató sáv)
            # kimondja, hogy a mappa most nem érhető el. A jelölés
            # visszafordítható: az első sikeres scan törli (`_sync_folder`).
            _set_folder_offline(conn, row["id"], True)
        logger.warning(
            "#1560: a figyelt gyökér (%s) %s — a(z) %s mappa indexsorait NEM takarítjuk.",
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
        row = (
            None
            if excluded
            else conn.execute(
                "SELECT id FROM folders WHERE path = ?", (str(folder_path),)
            ).fetchone()
        )
        if row is not None and _has_photos(conn, row["id"]) and folder_looks_offline(folder_path):
            _set_folder_offline(conn, row["id"], True)
            logger.warning(
                "A mappa jelenleg nem elérhető, az indexben marad: %s",
                folder_path,
            )
        else:
            _remove_folder(conn, folder_path)
    elif scan.skipped:
        # #1674: változatlan mappa — az indexbeli állapot érvényes. Sem
        # fotósort, sem scan-állapotot nem írunk: nincs mit frissíteni, és
        # a felesleges írás a `folder_scan_state` mtime-ját is elmozdítaná.
        conn.commit()
        return
    else:
        folder_result = _sync_folder(conn, scan)
        if (scan.files or scan.has_ini) and not folder_result.retry:
            _store_scan_state(conn, scan, filetype_signature)
    conn.commit()
