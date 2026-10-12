"""A Picasából átvett (kézzel módosított) fotódátum beírása az indexbe (#4591).

A `photos.taken_at_override` oszlop a kézi dátum helye: a lekérdezések
előnyben részesítik a `taken_at`-tal szemben, és a szinkron is megtartja
(`sync.py`, #4332). Az átvétel ide ír — a `.picasa.ini`-hez és a fájlhoz
nem nyúl. A séma nem változik.

Az írás után az érintett mappák dátumát újraszámoljuk (`sync_folder_date`):
a mappa dátuma a legrégebbi fotó effektív dátuma, tehát az átvett dátum
megváltoztathatja.
"""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Iterable
from pathlib import Path

from picasapy.index.sync import sync_folder_date
from picasapy.ini.io import load_or_empty
from picasapy.ini.names import INI_NAME
from picasapy.paths import path_key

_log = logging.getLogger(__name__)

#: (mappa útvonala, fájlnév, helyi ISO dátum)
AtvettDatum = tuple[str, str, str]


def _mappa_azonosito(
    conn: sqlite3.Connection,
    mappa: str,
    kulcsok: dict[str, tuple[int, str]],
    felepitve: list[bool],
) -> tuple[int, str] | None:
    """A mappa indexbeli (id, tárolt útvonal) párja; előbb pontos egyezés,
    aztán `path_key` alapon (más betűzés / szimbolikus útvonal). A kulcstáblát
    csak az első pontos tévesztés után építjük fel (fájlrendszer-hívások)."""
    sor = conn.execute(
        "SELECT id, path FROM folders WHERE path = ?", (mappa,)
    ).fetchone()
    if sor is not None:
        return sor["id"], sor["path"]
    if not felepitve[0]:
        felepitve[0] = True
        for tarolt in conn.execute("SELECT id, path FROM folders"):
            kulcsok.setdefault(path_key(tarolt["path"]), (tarolt["id"], tarolt["path"]))
    return kulcsok.get(path_key(mappa))


def atvett_datumokat_beir(
    conn: sqlite3.Connection, tetelek: Iterable[AtvettDatum]
) -> int:
    """A dátumokat beírja azoknál az indexelt fotóknál, ahol még NINCS
    `taken_at_override`, és a dátum a metaadat-dátumtól (`taken_at`) is
    eltér — meglévő kézi dátumot soha nem ír felül, a metaadat-dátumos,
    módosítatlan fájlt (pl. PNG) nem érinti (10.3: az 1. FILETIME a
    metaadat-dátum, a 2.-tól kézi módosítás nélkül is eltérhet).

    Az érintett mappák dátumát újraszámolja. Visszaadja a ténylegesen
    beírt sorok számát. Az indexben még nem szereplő fotó kimarad.
    """
    beirt = 0
    erintett: dict[int, str] = {}
    kulcsok: dict[str, tuple[int, str]] = {}
    felepitve = [False]  # a kulcstábla felépült-e (üres index is „felépült")
    for mappa, nev, datum in tetelek:
        azon = _mappa_azonosito(conn, mappa, kulcsok, felepitve)
        if azon is None:
            continue
        folder_id, tarolt_ut = azon
        db = conn.execute(
            "UPDATE photos SET taken_at_override = ? "
            "WHERE folder_id = ? AND name = ? AND taken_at_override IS NULL "
            "AND (taken_at IS NULL OR taken_at <> ?)",
            (datum, folder_id, nev, datum),
        ).rowcount
        if db:
            beirt += db
            erintett[folder_id] = tarolt_ut
    for folder_id, ut in erintett.items():
        try:
            dokumentum = load_or_empty(Path(ut) / INI_NAME)
        except (OSError, ValueError) as hiba:
            # olvashatatlan ini: a mappa dátumát a következő szinkron
            # számolja újra; az átvett fotódátum így is bent marad
            _log.warning(
                "A mappa ini-je nem olvasható, a mappa dátuma nem frissült (%s): %s",
                ut,
                hiba,
            )
            continue
        sync_folder_date(conn, folder_id, dokumentum)
    conn.commit()
    return beirt
