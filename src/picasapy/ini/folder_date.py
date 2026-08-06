"""Mappa-dátum kézi felülírása a `.picasa.ini` `[Picasa]` szekciójában (#320).

**PicasaPy-kiterjesztés** — a hivatalos Picasa-formátumban ez a kulcs nem
dokumentált (ld. `docs/specs/picasa-ini-format.md`, `[Picasa]` táblázat: a
Buchinger-visszafejtés és az exe string-tábla sem sorol fel mappa-szintű
`date` kulcsot, csak az albumoknál — `[.album:token]` — van `date=ISO8601`
mező). A PicasaPy a mappákra ugyanezt a kulcsot és formátumot használja; ha
valódi Picasa-ini-ben él (elő)forduló mappa-dátum kulcs kerül elő, a specet
frissíteni kell.

Alapból a mappa dátuma a legrégebbi kép felvételi ideje (`index/sync.py`,
`_sync_folder`); ez a modul a felhasználó KÉZI felülírását olvassa/írja —
ha jelen van, a szinkron ezt veszi át a számított érték helyett.
"""

from __future__ import annotations

import re

from .document import IniDocument

_FOLDER_DATE_KEY = "date"
_FOLDER_SECTION = "Picasa"

# ISO 8601 dátum (év-hónap-nap), órarész nélkül — a mappa-szintű dátum-
# felülírásnak nincs értelme óra/perc pontossággal.
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def is_valid_folder_date(date_iso: str) -> bool:
    """Érvényes-e a `date_iso` ISO 8601 (év-hónap-nap) alakban — a hívó
    (controller-slot, QML-dialógus) ezzel véd a hibás formátum ellen."""
    return bool(_ISO_DATE.match(date_iso.strip()))


def read_folder_date_override(document: IniDocument) -> str | None:
    """A `[Picasa]` szekció kézi `date=` felülírása, ha érvényes ISO-dátum.

    Érvénytelen (nem ISO-formátumú) vagy hiányzó kulcsnál `None` — a hívó
    ilyenkor a számított (legrégebbi kép) dátumra esik vissza."""
    section = document.section(_FOLDER_SECTION)
    if section is None:
        return None
    value = section.get(_FOLDER_DATE_KEY)
    if value is None or not _ISO_DATE.match(value.strip()):
        return None
    return value.strip()


def with_folder_date_override(document: IniDocument, date_iso: str) -> IniDocument:
    """Új dokumentum a mappa-dátum felülírásával (`[Picasa]` `date=`)."""
    return document.with_value(_FOLDER_SECTION, _FOLDER_DATE_KEY, date_iso)


def without_folder_date_override(document: IniDocument) -> IniDocument:
    """Új dokumentum a kézi felülírás nélkül — a mappa a legrégebbi kép
    dátumára áll vissza a következő szinkronnál."""
    return document.with_removed(_FOLDER_SECTION, _FOLDER_DATE_KEY)
