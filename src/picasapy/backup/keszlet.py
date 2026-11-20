"""A készlet módosítása a `.picasa.ini`-beli bélyegek követésével (#7292).

Az `index.backup_sets.keszlet_modositasa` csak az SQLite-sort írja. Az
eredeti Picasa a készlet átnevezésekor a képek `.picasa.ini`-jében is
átnevezi a készlet társkulcsát (`0x00473fd5`, `0x0047402f`): a kulcs NEVE
hordozza a készletet, így átnevezés nélkül minden kép "soha nem mentettnek"
látszana az új néven.

Ugyanazzal az aláírással áll, mint az index függvénye, hogy a hívók (a
mentésvezérlő) változtatás nélkül ezt használhassák.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from picasapy.index.backup_sets import (
    elmentett_allapot,
    keszletek,
)
from picasapy.index.backup_sets import keszlet_modositasa as _modositd_az_indexben

from .belyeg import nevezd_at_a_belyegeket


def keszlet_modositasa(
    conn: sqlite3.Connection,
    keszlet_id: int,
    *,
    nev: str | None = None,
    cel: str | None = None,
    szuro: str | None = None,
    tipus: str | None = None,
) -> None:
    """Az „Edit Set” művelete: az index mellett az ini-kulcsokat is átnevezi.

    Az ini-átnevezés csak az index sikeres módosítása UTÁN fut (egy foglalt
    név hibája így nem hagy félig átnevezett kulcsokat), és csak a készlet
    által már mentett mappákra."""
    regi = next((k for k in keszletek(conn) if k.id == int(keszlet_id)), None)
    _modositd_az_indexben(
        conn, keszlet_id, nev=nev, cel=cel, szuro=szuro, tipus=tipus
    )
    if regi is None or not nev or nev == regi.nev:
        return
    forrasok = [Path(forras) for forras in elmentett_allapot(conn, int(keszlet_id))]
    nevezd_at_a_belyegeket(forrasok, regi.nev, nev)
