"""Az index-szinkron felelősségi része; a régi API a sync.py-n át él."""

from __future__ import annotations

import logging
import os
import sqlite3
import stat as stat_module
from pathlib import Path


from .sync_compat import legacy

logger = logging.getLogger("picasapy.index.sync")


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
    if _gyoker_ures_vagy_olvashatatlan(root_path):
        return "jelenleg nem elérhető (üres vagy olvashatatlan)"
    return ""


def _gyoker_ures_vagy_olvashatatlan(root_path: Path) -> bool:
    """A GYÖKÉR-szintű próba: üres VAGY olvashatatlan → visszatartunk.

    ⚠️ #1909: itt szándékosan TÁGABB a szabály, mint a mappa-szintű
    `folder_looks_offline`-nál, és ez nem következetlenség, hanem a két
    kérdés különbsége:

    * a GYÖKÉR üressége már önmagában gyanús — a #1560 mérése szerint épp
      így néz ki a lecsatolt NAS (a csatolási pont üres könyvtárként ott
      marad), és a tévedés ára a TELJES index kiürülése volt (9,2 s alatt
      3 mappa / 3 fotó → 0 / 0);
    * egy MAPPA üressége viszont a leggyakoribb esetben azt jelenti, hogy
      a felhasználó kiürítette — erről állított valótlant a felület
      („jelenleg nem elérhető … lecsatolt meghajtó"), miközben a mappa
      olvasható volt.

    A gyökér-szintű visszatartás így továbbra is fedi a lecsatolt NAS
    egész fáját (az almappák sorai megmaradnak), a mappa-szintű döntés
    pedig nem hazudik a kiürített mappáról.
    """
    try:
        with _scandir(root_path) as it:
            return next(iter(it), None) is None
    except FileNotFoundError:
        return False
    except NotADirectoryError:
        return False
    except OSError:
        return True


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
        stat = legacy("_stat")(root)
    except (FileNotFoundError, NotADirectoryError):
        return True  # a horgony tényleg nincs meg
    except OSError:
        # elérhetetlen (levált mount, ESTALE, jogosultság): NEM eltűnt —
        # innen a #459/5 ága viszi tovább
        return False
    return not stat_module.S_ISDIR(stat.st_mode)


#: #1217/#1375: MODULSZINTŰ fogantyúk. A teszt ezeket cseréli, nem a
#: globális `os.stat`/`os.scandir`-t — a globális átírás minden más
#: modulra átszivárog, amíg a teszt fut.
_stat = os.stat
_scandir = os.scandir


def folder_looks_offline(folder_path: Path) -> bool:
    """Igaz, ha a mappa jelenleg NEM ELÉRHETŐNEK látszik (#459/5).

    A #132 gyökér-szintű védelmének mappa-szintű párja. A megkülönböztetés
    szándékosan szűk, hogy a „a felhasználó kiürítette a mappát" eset NE
    minősüljön offline-nak:

    - a `scandir` hibára fut (ESTALE/EIO/EACCES/ENOTCONN — levált mount,
      megszűnt hálózati megosztás, elvett jog) → offline;
    - a mappa létezik és hibátlanul olvasható, de ÜRES → **csak akkor**
      offline, ha CSATOLÁSI HATÁR van rajta (ld. lentebb);
    - a mappa nem létezik, vagy létezik és van benne bármi (csak épp
      média nincs) → NEM offline, a takarítás futhat.

    ## #1909: a „kiürített" és az „elérhetetlen" szétválasztása

    Korábban **minden** üres mappa offline-nak számított, arra a feltevésre
    építve, hogy „a kiürített fotómappában rendszerint ott marad legalább a
    `.picasa.ini`". **Ez a feltevés élesben megdőlt:** a tulajdonos
    kiürített egy mappát, semmi nem maradt benne, és a program azt
    állította róla, hogy *„jelenleg nem elérhető (például lecsatolt
    meghajtó vagy hálózati megosztás)"* — miközben a meghajtó megvolt és a
    mappa olvasható volt. A felület VALÓTLANT állított, és a sor bent
    ragadt.

    A megkülönböztetés ezért nem egy véletlen maradék-fájlon múlik többé,
    hanem azon, hogy **van-e csatolási határ a mappán**: az `st_dev`
    eltér-e a SZÜLŐ mappáétól. Egy ÉLŐ, de üres csatolási pont továbbra is
    offline (ez a levált NAS jellemző képe); egy közönséges, a szülővel
    azonos eszközön ülő üres mappa viszont egyszerűen üres.

    ⚠️ **A maradék kockázat kimondva:** ha egy BEÁGYAZOTT mount csatolódik
    le teljesen, a csatolási pont közönséges üres könyvtárként marad ott
    (`st_dev` = a szülőé), tehát ez a próba „egyszerűen üresnek" látja. Ezt
    a `sync_folder` elé tett GYÖKÉR-szintű védelem fogja (`_gyoker_baja`,
    #1560/#132): a figyelt gyökér elérhetetlensége önmagában megállítja a
    takarítást, és a gyakori eset — a figyelt gyökér MAGA a NAS-útvonal —
    ezzel le van fedve. A beágyazott, külön csatolt almappa esete NINCS
    lefedve; a rekord-id-k ott a következő sikeres scannel újraépülnek.
    """
    try:
        with _scandir(folder_path) as it:
            if next(iter(it), None) is not None:
                return False  # van benne valami — biztosan elérhető
    except FileNotFoundError:
        return False  # ténylegesen eltűnt mappa — nem offline, takarítható
    except NotADirectoryError:
        return False
    except OSError:
        return True  # elérhetetlen (levált mount, jogosultság, I/O hiba)
    return _csatolasi_hataron_ul(folder_path)


def _csatolasi_hataron_ul(folder_path: Path) -> bool:
    """Igaz, ha a mappa MÁS eszközön ül, mint a szülője (#1909).

    Ez az élő csatolási pont jele. Ha a szülő nem olvasható, óvatosak
    vagyunk és igazat adunk: olyankor nem tudjuk kizárni a leválást."""
    try:
        sajat = legacy("_stat")(folder_path).st_dev
        szulo = legacy("_stat")(folder_path.parent).st_dev
    except OSError:
        return True
    return sajat != szulo


def _has_photos(conn: sqlite3.Connection, folder_id: int) -> bool:
    return (
        conn.execute("SELECT 1 FROM photos WHERE folder_id = ? LIMIT 1", (folder_id,)).fetchone()
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
    row = conn.execute("SELECT id FROM folders WHERE path = ?", (str(folder_path),)).fetchone()
    if row is not None:
        conn.execute("DELETE FROM photos WHERE folder_id = ?", (row["id"],))
        conn.execute("DELETE FROM folders WHERE id = ?", (row["id"],))
    conn.execute("DELETE FROM folder_scan_state WHERE path = ?", (str(folder_path),))


def _ensure_scan_state(conn: sqlite3.Connection) -> None:
    """A scan-állapot cache-tábla lusta létrehozása (ld. _SCAN_STATE_DDL)."""
    conn.execute(legacy("_SCAN_STATE_DDL"))
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(folder_scan_state)")}
    if "filetype_signature" not in columns:
        conn.execute("ALTER TABLE folder_scan_state ADD COLUMN filetype_signature TEXT")
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
        (legacy("normalize_path")(str(path)),),
    )
    conn.commit()


def clear_removed_folders_under(conn: sqlite3.Connection, path: str | Path) -> None:
    """A sírkövek feloldása az útvonalon ÉS alatta (#1249) — az újra
    felvett mappa (vagy szülője) alatt semmi nem maradhat némán rejtve."""
    _ensure_scan_state(conn)
    torzs = Path(legacy("normalize_path")(str(path)))
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
        row["path"] for row in conn.execute("SELECT path FROM removed_folders ORDER BY path")
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
    root_path = Path(legacy("normalize_path")(root))
    query, params = legacy("_under_root_query")("SELECT path", root_path)
    return tuple(row["path"] for row in conn.execute(f"{query} ORDER BY path", params))


def remove_folder_tree(conn: sqlite3.Connection, root: str | Path) -> int:
    """Egy eltűnt mappafa törlése kizárólag az indexből (#5177).

    Nem ellenőrzi és nem járja be a lemezt. A jelzett út alatti indexsorokat
    Path-alapon szűri, így Windows alatt az útvonal-komponensek és a
    kis-nagybetű eltérése sem okoz téves előtag-egyezést. A fotókat a
    mappasorok előtt törli, hogy a keresőindex-triggerek lefussanak.

    A visszatérési érték a törölt mappasorok száma.
    """
    root_path = Path(legacy("normalize_path")(root))
    candidates = folder_paths_under(conn, root_path)
    paths = tuple(
        path
        for path in candidates
        if Path(path) == root_path or Path(path).is_relative_to(root_path)
    )
    if not paths:
        return 0

    removed = 0
    for path in paths:
        row = conn.execute("SELECT id FROM folders WHERE path = ?", (path,)).fetchone()
        if row is None:
            continue
        conn.execute("DELETE FROM photos WHERE folder_id = ?", (row["id"],))
        conn.execute("DELETE FROM folders WHERE id = ?", (row["id"],))
        conn.execute("DELETE FROM folder_scan_state WHERE path = ?", (path,))
        removed += 1
    conn.commit()
    return removed


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
#: * `photo_similarity` — a #5744 három Picasa-jellemzőjének cache-e.
#:   Tisztán származtatott adat, de átírás nélkül az egész gyűjtemény
#:   hash-eit újra kellene számolni, a régi sorok meg szemétként maradnának.
_PATH_TABLES = (
    "folders",
    "folder_scan_state",
    "removed_folders",
    "photo_hashes",
    "photo_similarity",
)


def _reszfa_feltetel(root: Path) -> tuple[str, tuple[str, int, str]]:
    """Pontos kis-/nagybetűs WHERE-feltétel a ``root`` alatti sorokra.

    Az `_under_root_query` mintája, de tábla NÉLKÜL: az `UPDATE`-be a
    `FROM` záradék nem fér bele (SQLite 3.33 óta az `UPDATE … FROM` JOIN-t
    jelent, és a `path` oszlop kétértelművé válna). A `LIKE` helyett a
    `substr` + BINARY összehasonlítás pontos útvonal-egyezést és elválasztóval
    zárt részfa-prefixet ad. Így a `Foo` részfa nem fogja meg a különálló
    `foo` testvért, és a célütközés-ellenőrzés sem látja saját régi sorait.
    """
    root_text = str(root)
    prefix = root_text.rstrip(os.sep) + os.sep
    return (
        "WHERE (path = ? COLLATE BINARY OR substr(path, 1, ?) = ? COLLATE BINARY)",
        (root_text, len(prefix), prefix),
    )


def move_folder_tree(conn: sqlite3.Connection, old_root: str | Path, new_root: str | Path) -> int:
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

    # A rename may already have moved the directory before this index update.
    # Resolve the parent, but preserve each supplied leaf spelling: on a
    # case-insensitive filesystem the stale old path can resolve to the new
    # entry and erase the very case-only change this function must record.
    def moved_path(path: str | Path) -> str:
        entry = Path(path)
        return str(Path(legacy("normalize_path")(entry.parent)) / entry.name)

    old_text = moved_path(old_root)
    new_text = moved_path(new_root)
    # Path equality is case-insensitive on Windows; preserve spelling here so
    # a case-only rename updates every indexed path.
    if old_text == new_text:
        return 0
    old_path = Path(old_text)
    new_path = Path(new_text)
    _ensure_scan_state(conn)
    legacy("_ensure_photo_hashes")(conn)
    legacy("_ensure_similarity_features")(conn)
    utkozes, params = _reszfa_feltetel(new_path)
    sor = conn.execute(f"SELECT 1 FROM folders {utkozes} LIMIT 1", params).fetchone()
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
