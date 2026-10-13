"""A videó (nem-JPEG) fájl Picasában módosított dátumának átvétele (#4591).

Az eredeti Picasa a dátum kézi módosításakor a nem-JPEG fájlnál (a videókat
is ide értve) nem ír EXIF-et, hanem a `thumbindex.db` rekordjának 1.
FILETIME-ját állítja át (`docs/specs/pmp-database.md` 15.1). Módosítatlan
videónál a két FILETIME bitre egyenlő (15.2), tehát az eltérés a kézi
módosítás nyoma — ilyenkor az 1. FILETIME a kép dátuma.

A 2-es típus (JPEG) kimarad: ott az eredeti az EXIF-et írja át, és azt a
PicasaPy maga olvassa.

A FILETIME a Picasában HELYI időből képződik (`TzSpecificLocalTimeToSystemTime`
`NULL` zónával), ezért a visszaalakítás a helyi zónával értelmes (15.6).
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from picasapy.pmpimport.importer import PhotoRecord

#: a `thumbindex` rekord típusa, amelyiknél az eredeti EXIF-et ír (JPEG)
JPEG_TIPUS = 2

_log = logging.getLogger(__name__)

_FILETIME_EPOCH = datetime(1601, 1, 1, tzinfo=UTC)


def filetime_helyi_iso(filetime: int) -> str:
    """FILETIME (100 ns, 1601-01-01, UTC) → helyi idő, ISO `yyyy-MM-ddTHH:mm:ss`.

    Ugyanazt az alakot adja, amit a `photos.taken_at` tárol.
    """
    utc = _FILETIME_EPOCH + timedelta(microseconds=filetime // 10)
    return utc.astimezone().replace(tzinfo=None).isoformat(timespec="seconds")


def atveendo_datum(rekord: PhotoRecord) -> str | None:
    """A rekord átveendő (módosított) dátuma, vagy `None`.

    `None`, ha JPEG a típus, ha a két FILETIME egyenlő, vagy ha az 1.
    FILETIME nem értelmezhető (0, illetve a datetime tartományán kívül).
    """
    if rekord.entry_kind == JPEG_TIPUS:
        return None
    if rekord.creation_filetime == rekord.modified_filetime:
        return None
    if rekord.creation_filetime <= 0:
        return None
    try:
        return filetime_helyi_iso(rekord.creation_filetime)
    except (OverflowError, OSError, ValueError) as hiba:
        # a helyi időre alakítás a platform időzóna-adatán múlik (OSError)
        _log.warning(
            "A videódátum nem alakítható helyi időre (%s, FILETIME=%s): %s",
            rekord.local_path,
            rekord.creation_filetime,
            hiba,
        )
        return None


__all__ = ["JPEG_TIPUS", "atveendo_datum", "filetime_helyi_iso"]
