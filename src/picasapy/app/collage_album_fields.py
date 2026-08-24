"""A kollázs FORRÁSALBUMÁT leíró két `.cxf` mező (#1092).

A `.cxf` gyökere három dolgot mond a forrásalbumról: a címét
(`<albumTitle>`), az azonosítóját (`albumUID`) és a dátumát
(`<albumDate>`). A címet a panel régóta kitölti; a másik kettő a
PicasaPy saját kollázsaiból **teljesen hiányzott**, pedig a 12 golden
mintában (`referencia/kollazs-golden/`) mindkettő ott van, mind a 12-ben.

Mindhárom mező forrása UGYANAZ: a képek **közös forrásmappája**. Több
mappából érkező kijelölésnél nincs egy forrásalbum — ilyenkor a cím is
üres marad (`_title_from_sources`), és mi sem találunk ki egyet.

## Az `albumDate` alakja — mérve

`2023. november`: év, pont, szóköz, honos hónapnév. A hónapnév a
**felület** nyelvéből jön, nem a rendszerlokálból — a #1131 mérte ki,
hogy a `QLocale()` alapértelmezése magyar rendszeren angol felülettel
hazudik, a CI „C" lokálján pedig futtatókörnyezet-függővé tenné a
kimenetet.

## Melyik dátum?

A mappa **legrégebbi** képének felvételi ideje — ugyanaz a szabály, amit
az index is használ a mappa-dátumra (`index/sync.py`, `folders.date` =
`MIN(taken_at)`). A KIJELÖLÉS szándékosan nem számít bele: a golden
készlet 11 kollázsa ugyanabból a mappából készült, más-más képekkel, és
mindegyik ugyanazt az `albumDate`-et viseli.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from pathlib import Path

from PySide6.QtCore import QLocale

from picasapy.collage.uids import album_uid_for


def _common_source_folder(sources: Iterable) -> Path | None:
    """A források közös mappája, vagy `None`, ha nem egy van belőle."""
    folders = {Path(source.path).parent for source in sources if source.path}
    if len(folders) != 1:
        return None
    return next(iter(folders))


def _oldest_taken_at(folder: Path, photos: Sequence) -> str:
    """A mappa legrégebbi képének felvételi ideje ISO-alakban, vagy üres.

    A dátum nélküli rekordok kimaradnak: az mtime-ra visszaesni itt
    félrevezető volna — egy másolt fájl mai dátuma az album korát
    hazudná el."""
    dates = [
        str(photo.taken_at)
        for photo in photos
        if getattr(photo, "taken_at", None)
        and Path(str(photo.folder_path)) == folder
    ]
    return min(dates) if dates else ""


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
    sources: Iterable, photos: Sequence, *, language: str
) -> tuple[str, str]:
    """A kollázs forrásalbumának `(albumUID, albumDate)` párja.

    Közös forrásmappa hiányában mindkettő üres. A dátum hiánya nem viszi
    el az azonosítót is: a kettő független."""
    folder = _common_source_folder(sources)
    if folder is None:
        return "", ""
    return album_uid_for(folder), album_date_label(
        _oldest_taken_at(folder, photos), language
    )


__all__ = ["album_date_label", "album_fields_of"]
