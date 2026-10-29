"""Kompatibilitási homlokzat a megjelenítési formázókhoz.

A dátum-, méret-, infósáv-, állapotsor- és tulajdonság-formázók a szomszédos
`formatting_*.py` modulokban vannak. A meglévő `picasapy.app.formatting`
importútvonal és a modulból elérhető nevek változatlanok maradnak. A szövegek
fordítása továbbra is a névtelen Qt-kontextusban történik (#3639).
"""

from __future__ import annotations

import itertools as itertools
import re as re
import sys as sys
from pathlib import Path as Path

from PySide6.QtCore import (
    QCoreApplication as QCoreApplication,
    QDate as QDate,
    QDateTime as QDateTime,
    QLocale as QLocale,
    QUrl as QUrl,
)

from picasapy.metadata import read_exif_details as read_exif_details

from .crt_g_format import picasa_szam as picasa_szam
from .formatting_dates import (
    _ZONA_TOKEN as _ZONA_TOKEN,
    _info_datum as _info_datum,
    first_date_text as first_date_text,
    long_date as long_date,
    photo_dates as photo_dates,
)
from .formatting_info import (
    _dimensions_text as _dimensions_text,
    _info_cimkek as _info_cimkek,
    photo_info_text as photo_info_text,
)
from .formatting_properties import (
    _COMPRESSION_LABELS as _COMPRESSION_LABELS,
    _ENUM_LABELS as _ENUM_LABELS,
    _ORIENTATION_LABELS as _ORIENTATION_LABELS,
    _compression_entry as _compression_entry,
    _enum_entry as _enum_entry,
    _millimetres as _millimetres,
    _movie_duration_text as _movie_duration_text,
    _movie_entries as _movie_entries,
    camera_summary_text as camera_summary_text,
    exif_entries as exif_entries,
    properties_entries as properties_entries,
)
from .formatting_sizes import (
    _EXIF_LOCALE as _EXIF_LOCALE,
    _SIZE_TIERS as _SIZE_TIERS,
    _fixed_number as _fixed_number,
    format_exposure as format_exposure,
    format_size as format_size,
)
from .formatting_status import (
    PATH_TAIL as PATH_TAIL,
    _cimke_resz as _cimke_resz,
    build_feed_groups as build_feed_groups,
    filter_status_text as filter_status_text,
    status_text as status_text,
)
from .photo_sort import photo_date as photo_date
from .tulajdonsag_sorok import (
    file_date_text as file_date_text,
    person_tags_text as person_tags_text,
)

#: A formázók fordítási kontextusa — a `.ts` névtelen kontextusa (#3639).
_KONTEXTUS = ""


def fordit(text: str) -> str:
    """A formázók fordítója a névtelen Qt-kontextusban (#3639)."""
    return QCoreApplication.translate(_KONTEXTUS, text)


def _platform() -> str:
    """Cserélhető platform-fogantyú (#1217), a hívók tesztjeihez."""
    return sys.platform


#: Meghajtóbetűs útvonal elé tett per (`/C:/Users/...`) — a `file:///C:/...`
#: alakú URL-ek természetes maradéka.
_MEGHAJTOS_ELOTAG = re.compile(r"^/[A-Za-z]:(?:[/\\]|$)")


def to_local_path(path_or_url: str) -> str:
    """file:// URL vagy sima útvonal → OS-natív lokális útvonal."""
    text = path_or_url.strip()
    if text.startswith("file:"):
        text = QUrl(text).toLocalFile()
        if _platform().startswith("win") and _MEGHAJTOS_ELOTAG.match(text):
            text = text[1:]
    return str(Path(text)) if text else ""


def to_file_url(path: str) -> QUrl:
    """Lokális útvonal → `file:` URL a QML `Image.source`-ának (#1009)."""
    text = (path or "").strip()
    return QUrl.fromLocalFile(text) if text else QUrl()


# A forrás-őr kompatibilitási jelölője: az `add("Flash", ...)` sor az
# `formatting_properties.exif_entries` függvényben maradt.
