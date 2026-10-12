"""A Tulajdonságok-panel #4579-es sorainak szövegei (spec
`picasa-metaadat-tulajdonsagok.md` 17.): Fájl dátuma és Személycímkék.

Tiszta segédek a `formatting.exif_entries`-nek; a CCD-szélesség, a Rekesz és
a JPEG minőség szövege a `crt_g_format` / `metadata.jpeg_quality` dolga.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from datetime import datetime

from PySide6.QtCore import QDate, QDateTime, QLocale, QTime

from picasapy.ini import load_existing, parse_faces

from .contact_names import contact_names_by_id
from .photo_sort import photo_date

_INI_NEV = ".picasa.ini"
_PERC_RESZ = re.compile(r"m+")


def file_date_text(photo, locale: QLocale) -> str | None:
    """A „Fájl dátuma": a kép indexbeli 1. időbélyege (`photo_date`), a
    hívó területi beállításával: rövid dátum + másodperces idő, éjfélkor
    csak a dátum (`VarBstrFromDate` szerződése). Elérhetetlen fájlnál None
    (az eredetinél a `GetFileAttributesEx` sikere a feltétel)."""
    if not (Path(photo.folder_path) / photo.name).is_file():
        return None
    if not photo.taken_at and not photo.sort_mtime_ns:
        return None  # a 0 ns „nincs adat", nem 1970
    try:
        # a `photo_date` ISO-ja törtmásodpercet is hordozhat (fájlidő)
        idopont = datetime.fromisoformat(photo_date(photo)).replace(microsecond=0)
    except (OSError, ValueError, OverflowError):
        return None
    stamp = QDateTime(
        QDate(idopont.year, idopont.month, idopont.day),
        QTime(idopont.hour, idopont.minute, idopont.second),
    )
    datum = locale.toString(stamp.date(), QLocale.FormatType.ShortFormat)
    ido = stamp.time()
    if ido.hour() == 0 and ido.minute() == 0 and ido.second() == 0:
        return datum
    return f"{datum} {locale.toString(ido, _masodperces_formatum(locale))}"


def _masodperces_formatum(locale: QLocale) -> str:
    """A területi rövid időformátum másodperccel bővítve (`HH:mm` ->
    `HH:mm:ss`, `h:mm AP` -> `h:mm:ss AP`)."""
    alap = locale.timeFormat(QLocale.FormatType.ShortFormat)
    if "s" in alap.replace("'", ""):
        return alap
    return _PERC_RESZ.sub(lambda talalat: talalat.group(0) + ":ss", alap, count=1)


def person_tags_text(
    photo, xmp_people: tuple[str, ...], contacts_xml=None
) -> str | None:
    """A „Személycímkék": a kép megnevezett arcai (`.picasa.ini` `faces=` +
    `[Contacts2]`); ha nincs, a fájl XMP-régióinak nevei. Azonos név N-szer:
    „Név (N)"; több név vesszővel (a Kulcsszavak-sor mintája)."""
    nevek = ini_person_names(photo, contacts_xml) or xmp_people
    if not nevek:
        return None
    szamlalo = Counter(nevek)
    return ", ".join(
        nev if szamlalo[nev] == 1 else f"{nev} ({szamlalo[nev]})"
        for nev in dict.fromkeys(nevek)
    )


def ini_person_names(photo, contacts_xml=None) -> tuple[str, ...]:
    """A kép nevesített arcainak nevei az ini-ből, az arclista sorrendjében;
    a meg nem nevezett (üres nevű) arc kimarad. A nevet a központi
    `contacts_xml` és a mappa `[Contacts2]`-je adja (`contact_names`).
    Olvasási hibára ()."""
    try:
        document = load_existing(Path(photo.folder_path) / _INI_NEV)
        section = document.section(photo.name)
        raw = section.get("faces") if section is not None else None
        if not raw:
            return ()
        arcok = parse_faces(raw)
        nevek = contact_names_by_id(document, contacts_xml)
    except (OSError, ValueError):
        return ()
    return tuple(
        nev
        for arc in arcok
        if arc.is_identified
        and (nev := nevek.get(arc.contact_id.casefold(), "").strip())
    )
