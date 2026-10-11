"""A „Rejtett mappák" jelszó-lenyomatának átvétele a db3-ból (#4597).

Az eredeti Picasa a jelszó 32 jegyű hex MD5 lenyomatát a db3 `catdata`
táblájának `info` oszlopába írja, a `Hidden Folders` gyűjtemény sorába
(`docs/specs/picasa-menu-parancsok-viselkedes.md` 32.3.1: `0x005ebc52`).
A `.pmp` fájlnév a `<tábla>_<oszlop>.pmp` konvencióból következik
(`catdata_name.pmp`, `catdata_info.pmp`) — az `info` fájl mintán NEM látott
(jelszót sosem állítottak be a mintagazdánál), ezért a hiányzó vagy sérült
fájl csendben „nincs jelszó".
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from picasapy.ini import HIDDEN_FOLDERS_CATEGORY
from picasapy.pmpimport.pmp_column import PmpFormatError, read_pmp_column

logger = logging.getLogger(__name__)

_NAME_FILE = "catdata_name.pmp"
_INFO_FILE = "catdata_info.pmp"
_MD5_HEX = re.compile(r"[0-9a-fA-F]{32}")


def read_hidden_password_hash(db3_dir: Path) -> str | None:
    """A db3-ban tárolt rejtett-jelszó lenyomata (kisbetűs hex MD5), vagy
    `None`, ha nincs / nem olvasható / nem 32 jegyű hex.

    A gyűjteménynév-keresés az eredetivel egyezően csak az ASCII betűkre
    kis-nagybetű-tűrő (`0x00453970`)."""
    nevek_ut = Path(db3_dir) / _NAME_FILE
    info_ut = Path(db3_dir) / _INFO_FILE
    try:
        nevek = read_pmp_column(nevek_ut).values
        info = read_pmp_column(info_ut).values
    except (OSError, PmpFormatError) as hiba:
        logger.debug("Nincs átvehető rejtett-jelszó (%s): %s", db3_dir, hiba)
        return None
    cel = HIDDEN_FOLDERS_CATEGORY.casefold()
    for index, nev in enumerate(nevek):
        if not isinstance(nev, str) or nev.strip().casefold() != cel:
            continue
        if index >= len(info) or not isinstance(info[index], str):
            return None
        ertek = info[index].strip()
        return ertek.lower() if _MD5_HEX.fullmatch(ertek) else None
    return None
