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
from pathlib import Path

from picasapy.scanner.walker import PICASA_INI_NAME

# (mappa mtime_ns, ini mtime_ns vagy None, ha nincs ini)
FolderStamp = tuple[int, int | None]


def directory_stamp(folder: str | Path) -> FolderStamp | None:
    """A mappa olcsó változás-pecsétje, vagy None, ha a mappa nem érhető el.

    KÖLTSÉG: pontosan két fájlrendszer-művelet (a mappa statja és az
    ini statja) — a hívó ezzel a kettővel dönti el, kell-e a drága
    teljes újraolvasás. A pecsét alakja szándékosan azonos a
    `folder_scan_state` tárolt párosával (mtime_ns, ini_mtime_ns).
    """
    folder_path = Path(folder)
    try:
        folder_mtime = os.stat(folder_path).st_mtime_ns
    except OSError:
        return None  # eltűnt, lecsatolt vagy elérhetetlen mappa
    try:
        ini_mtime = os.stat(folder_path / PICASA_INI_NAME).st_mtime_ns
    except OSError:
        ini_mtime = None  # nincs (még) ini — érvényes állapot, nem hiba
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
    return tuple(
        folder
        for folder in candidates
        # a sorrend szándékos: az ismeretlen mappánál a pecsét két
        # műveletét meg sem fizetjük, úgyis szinkronra megy
        if folder not in stored or directory_stamp(folder) != stored[folder]
    )


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
