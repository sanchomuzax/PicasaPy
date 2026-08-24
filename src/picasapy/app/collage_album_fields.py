"""A kollázs FORRÁSALBUMÁT leíró két `.cxf` mező (#1092).

A `.cxf` gyökere három dolgot mond a forrásalbumról: a címét
(`<albumTitle>`), az azonosítóját (`albumUID`) és a dátumát
(`<albumDate>`). A címet a panel régóta kitölti; a másik kettő a
PicasaPy saját kollázsaiból **teljesen hiányzott**, pedig a 12 golden
mintában (`referencia/kollazs-golden/`) mindkettő ott van, mind a 12-ben.

Mindhárom mező forrása UGYANAZ: a képek **közös forrásmappája**
(`collage_sources.common_source_folder`). Több mappából érkező
kijelölésnél nincs egy forrásalbum — ilyenkor a cím is üres marad, és mi
sem találunk ki egyet.

## Az `albumDate` alakja — mérve

`2023. november`: év, pont, szóköz, honos hónapnév. A hónapnév a
**felület** nyelvéből jön, nem a rendszerlokálból — a #1131 mérte ki,
hogy a `QLocale()` alapértelmezése magyar rendszeren angol felülettel
hazudik, a CI „C" lokálján pedig futtatókörnyezet-függővé tenné a
kimenetet.

⚠️ Csak a MAGYAR alak van kimérve (12/12 golden minta). Hogy az angol
Picasa `November 2023`-at ír-e, nem tudjuk — mi minden nyelven a mért
`{év}. {hónap}` szerkezetet írjuk. A kérdés a #1390-en áll, a tulajdonos
windowsos próbájára várva.

## Melyik dátum? — az INDEXBŐL, nem a látott képekből

A mappa dátuma az index `folders.date` oszlopa. Ez a mező **már
tartalmazza a helyes szabályt** (`index/sync.py` `_sync_folder_date`):
a `.picasa.ini` `[Picasa] date=` **kézi felülírása elsőbbséget élvez**,
és csak annak hiányában jön a legrégebbi felvétel ideje
(`MIN(taken_at)`).

⚠️ **Miért nem a betöltött fotólistából számolunk** (az első nekifutás
ezt tette, és hibás volt): a rács tartalmát a főablak SZŰRI — rejtett
képek, bezárt gyűjtemények, keresés, csillag-szűrő. Ugyanabból a
mappából két kollázs így két KÜLÖNBÖZŐ `albumDate`-et kapott volna,
pontosan azt az invariánst megsértve, amiért a modul készült: a 12
golden minta 11 kollázsa ugyanabból a mappából, más-más képekkel
készült, és mindegyik UGYANAZT az `albumDate`-et viseli.

⚠️ **Nem indexelt mappára üres marad.** Ilyenkor az utolsó esély a
mappa `.picasa.ini`-jének kézi dátum-felülírása; ha az sincs, a mező
kimarad a fájlból. A mappát végigolvasni EXIF-ért itt nem szabad: a
felület a mentés útjában áll, és egy hálózati mappa bejárása
másodperceket vinne el.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from pathlib import Path

from PySide6.QtCore import QLocale

from picasapy.collage.uids import album_uid_for

from .collage_sources import common_source_folder

logger = logging.getLogger(__name__)


def folder_date_iso(db_path, folder: Path | str) -> str:
    """A mappa dátuma ISO-alakban az INDEXBŐL, vagy üres szöveg.

    Egyetlen `SELECT`, és a válasz a nézettől független. A hiba NYELT: egy
    index-gond nem akadályozhatja meg a kollázs megnyitását — a dátum
    hiánya csak annyit jelent, hogy a mező kimarad a `.cxf`-ből.

    Ha a mappa nincs az indexben, a mappa `.picasa.ini`-jének kézi
    dátum-felülírása (#320) az utolsó esély; ez ugyanaz az érték, amit az
    index is elsőbbséggel venne."""
    if db_path:
        try:
            from picasapy.index import open_index

            with open_index(db_path) as conn:
                row = conn.execute(
                    "SELECT date FROM folders WHERE path = ?", (str(folder),)
                ).fetchone()
            if row is not None and row["date"]:
                return str(row["date"])
        except Exception:  # noqa: BLE001 - az index baja nem viheti el a lapot
            logger.warning(
                "A forrásmappa dátuma nem olvasható az indexből: %s",
                folder,
                exc_info=True,
            )
    return _ini_date_override(folder)


def _ini_date_override(folder: Path | str) -> str:
    """A mappa `.picasa.ini`-jének kézi `[Picasa] date=` felülírása (#320)."""
    try:
        from picasapy.ini import load_or_empty, read_folder_date_override

        return read_folder_date_override(load_or_empty(Path(folder) / ".picasa.ini")) or ""
    except Exception:  # noqa: BLE001 - olvashatatlan ini sem viheti el a lapot
        return ""


def album_date_label(date_iso: str, language: str) -> str:
    """ISO-dátumból a mért `<albumDate>` felirat: `2023. november`.

    Értelmezhetetlen vagy hiányzó dátumra üres szöveg — ilyenkor a mező
    egyszerűen kimarad a fájlból. Kitalálni egy dátumot rosszabb volna a
    hiánynál: a felhasználó azt hinné, tudunk valamit az albumról."""
    text = str(date_iso or "").strip()
    if len(text) < 7 or text[4] != "-":
        return ""
    try:
        year = int(text[:4])
        month = int(text[5:7])
    except ValueError:
        return ""
    if not 1 <= month <= 12 or year < 1:
        return ""
    month_name = QLocale(language).standaloneMonthName(
        month, QLocale.FormatType.LongFormat
    )
    if not month_name:
        return ""
    return f"{year}. {month_name}"


def album_fields_of(
    sources: Iterable, *, db_path=None, language: str
) -> tuple[str, str]:
    """A kollázs forrásalbumának `(albumUID, albumDate)` párja.

    Közös forrásmappa hiányában mindkettő üres. A dátum hiánya nem viszi
    el az azonosítót sem: a kettő független forrásból jön."""
    folder = common_source_folder(sources)
    if folder is None:
        return "", ""
    return album_uid_for(folder), album_date_label(
        folder_date_iso(db_path, folder), language
    )


__all__ = ["album_date_label", "album_fields_of", "folder_date_iso"]
