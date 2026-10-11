"""A Tulajdonságok-panel #4579-es sorainak szövegei (spec
`picasa-metaadat-tulajdonsagok.md` 17.): Fájl dátuma és Személycímkék.

Tiszta segédek a `formatting.exif_entries`-nek; a CCD-szélesség, a Rekesz és
a JPEG minőség szövege a `crt_g_format` / `metadata.jpeg_quality` dolga.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from PySide6.QtCore import QDateTime, QLocale

from picasapy.ini import contacts_of, load_existing, parse_faces

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
    stamp = QDateTime.fromString(photo_date(photo), "yyyy-MM-ddTHH:mm:ss")
    if not stamp.isValid():
        stamp = QDateTime.fromString(photo_date(photo), "yyyy-MM-ddTHH:mm:ss.zzzzzz")
    if not stamp.isValid():
        return None
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


def person_tags_text(photo, xmp_people: tuple[str, ...]) -> str | None:
    """A „Személycímkék": a kép megnevezett arcai (`.picasa.ini` `faces=` +
    `[Contacts2]`); ha nincs, a fájl XMP-régióinak nevei. Azonos név N-szer:
    „Név (N)"; több név vesszővel (a Kulcsszavak-sor mintája)."""
    nevek = ini_person_names(photo) or xmp_people
    if not nevek:
        return None
    szamlalo = Counter(nevek)
    return ", ".join(
        nev if szamlalo[nev] == 1 else f"{nev} ({szamlalo[nev]})"
        for nev in dict.fromkeys(nevek)
    )


def ini_person_names(photo) -> tuple[str, ...]:
    """A kép nevesített arcainak nevei az ini-ből, az arclista sorrendjében;
    a meg nem nevezett (üres nevű) arc kimarad. Olvasási hibára ()."""
    try:
        document = load_existing(Path(photo.folder_path) / _INI_NEV)
        section = document.section(photo.name)
        raw = section.get("faces") if section is not None else None
        if not raw:
            return ()
        arcok = parse_faces(raw)
        nevek = {
            contact.person_id.casefold(): contact.name
            for contact in contacts_of(document)
        }
    except (OSError, ValueError):
        return ()
    return tuple(
        nev
        for arc in arcok
        if arc.is_identified
        and (nev := nevek.get(arc.contact_id.casefold(), "").strip())
    )
