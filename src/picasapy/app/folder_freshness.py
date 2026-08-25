"""Olcsó frissesség-ellenőrzés a rácson LÁTSZÓ mappákra (#1435).

## Miért kell

A rács feedje (#64) egyszerre TÖBB mappát mutat, a célzott újraolvasás
(#1275) viszont csak a KIVÁLASZTOTT mappát nézi. Hálózati megosztáson az
inotify-esemény elmarad (ld. `scanner/watcher.py`), a periodikus teljes
rescan pedig kihagyja a változatlan mappa-mtime-ú mappákat — így a
feedben látszó TÖBBI mappa új és törölt képei csak az ötperces körben
(vagy sehogy) jelentek meg.

## Miért nem elég egyszerűen mindent újraolvasni

Mérés (a jegy körében, 20 fájlos mappa): egyetlen `sync_folder` egy
VÁLTOZATLAN mappán is ~2 fájlrendszer-műveletbe kerül fájlonként
(1 `scandir` + fájlonkénti `lstat`). A tulajdonos gyűjteménye 40 000+
képes NAS-on van, mért 200 napló/mp korláttal — a látszó mappák sűrű
teljes újraolvasása valódi kárt okozna.

## A két fázis

1. **pecsét** (`directory_stamp`) — mappánként PONTOSAN két művelet: a
   mappa és a `.picasa.ini` statja. Ez elárulja, hogy keletkezett vagy
   eltűnt-e fájl (a mappa mtime-ja lép), illetve változott-e az ini.
2. **szinkron** — csak az eltérő pecsétű mappa kap teljes `sync_folder`-t.

A pecsét összehasonlítási alapja a `folder_scan_state` tábla, amit a
szinkron amúgy is vezet (`index/sync.py::_store_scan_state`) — nincs új
séma, nincs új nyilvántartás.

⚠️ **Amit a pecsét NEM lát:** a helyben átírt fájlt (azonos név, más
tartalom) — ilyenkor a mappa mtime-ja nem változik. Ez LEMÉRT tény, nem
feltevés. Ezt az esetet továbbra is a kiválasztott mappa körönkénti
teljes újraolvasása fedi le; a feed többi mappájára nyitott marad
(ld. a jegy zárójelentését).
"""

from __future__ import annotations

import os
from picasapy.paths import normalize_path
from pathlib import Path

from picasapy.scanner.walker import PICASA_INI_LEGACY_NAME, PICASA_INI_NAME

# (mappa mtime_ns, ini mtime_ns vagy None, ha nincs ini)
FolderStamp = tuple[int, int | None]

#: Az ini-fájl nevei ELSŐBBSÉGI SORRENDBEN.
#:
#: ⚠️ Bitre a `scanner/walker.py::_ini_mtime` sorrendjét kell követnie —
#: a tárolt pecsétet AZ készíti, ezt pedig ahhoz hasonlítjuk. Ha a kettő
#: eltér, az érintett mappa pecsétje SOHA nem egyezik, tehát minden
#: körben megkapja a drága teljes újraolvasást, és sosem konvergál.
#: (A régi Picasa-verziók a `Picasa.ini` nevet írták — a tulajdonos
#: NAS-mappáit a windowsos Picasa 3 is írja, ez tehát élő eset.)
_INI_NAMES = (PICASA_INI_NAME, PICASA_INI_LEGACY_NAME)


def directory_stamp(folder: str | Path) -> FolderStamp | None:
    """A mappa olcsó változás-pecsétje, vagy None, ha a mappa nem érhető el.

    KÖLTSÉG: a szokásos esetben (van `.picasa.ini`) pontosan KÉT
    fájlrendszer-művelet, a felső korlát HÁROM — akkor, ha az első
    ini-név hiányzik, tehát a másodikat is meg kell néznünk (csak régi
    `Picasa.ini`, vagy egyáltalán nincs ini).

    A harmadik művelet ára tudatosan vállalt: enélkül a régi nevű ini-t
    tartalmazó mappa pecsétje SOHA nem egyezne a tárolttal, tehát minden
    körben a sokkal drágább teljes újraolvasást kapná (ld. `_INI_NAMES`).

    A pecsét alakja szándékosan azonos a `folder_scan_state` tárolt
    párosával (mtime_ns, ini_mtime_ns).
    """
    folder_path = Path(folder)
    try:
        folder_mtime = os.stat(folder_path).st_mtime_ns
    except OSError:
        return None  # eltűnt, lecsatolt vagy elérhetetlen mappa
    ini_mtime = None  # nincs ini — érvényes állapot, nem hiba
    for name in _INI_NAMES:
        try:
            ini_mtime = os.stat(folder_path / name).st_mtime_ns
            break
        except OSError:
            continue
    return (folder_mtime, ini_mtime)


def stale_folders(
    candidates: tuple[str, ...],
    stored: dict[str, FolderStamp | None],
) -> tuple[str, ...]:
    """A `candidates` közül azok, amelyek lemezen MÁSKÉNT néznek ki, mint
    amit az index utoljára látott (`stored`).

    Elavultnak számít a mappa akkor is, ha nincs róla tárolt pecsét (még
    sosem láttuk) vagy ha eltűnt a lemezről — az utóbbinál a sor
    takarítása a szinkron dolga, tehát oda kell adni neki.
    """
    # ⚠️ A `stored` kulcsai az INDEXBŐL jönnek, ahol a `normalize_path`
    # kanonikus alakja szerepel; a `candidates` viszont a feedből, nyers
    # alakban. Windowson a kettő elválhat (elválasztó-karakter, kis/nagybetű),
    # és akkor MINDEN mappa ismeretlennek látszana → körönként teljes
    # újraolvasás, épp az a NAS-terhelés, amit a jegy el akar kerülni.
    # A CI windows-lába pontosan ezen bukott el (#1435).
    kanoni = {normalize_path(kulcs): ertek for kulcs, ertek in stored.items()}
    talalat = []
    for folder in candidates:
        kulcs = normalize_path(folder)
        # a sorrend szándékos: az ismeretlen mappánál a pecsét két
        # műveletét meg sem fizetjük, úgyis szinkronra megy
        if kulcs not in kanoni or directory_stamp(folder) != kanoni[kulcs]:
            talalat.append(folder)
    return tuple(talalat)


def next_sweep_batch(
    folders: tuple[str, ...], cursor: int, budget: int
) -> tuple[tuple[str, ...], int]:
    """Körbeforgó, KORLÁTOZOTT adag a `folders`-ből, és a következő kurzor.

    A keret teszi a költséget függetlenné a könyvtár méretétől: akárhány
    mappa látszik, körönként legfeljebb `budget` pecsét készül. Egy adagon
    belül nincs ismétlődés (kevés mappánál a nagy keret sem kérdez
    kétszer), és a kurzor körbefordul, tehát idővel minden mappa sorra
    kerül.
    """
    if not folders:
        return (), 0
    if budget <= 0:
        return (), cursor
    count = min(budget, len(folders))
    start = cursor % len(folders)
    batch = tuple(folders[(start + i) % len(folders)] for i in range(count))
    return batch, (start + count) % len(folders)
