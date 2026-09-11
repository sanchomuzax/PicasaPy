"""A mentés-készlet három fájlszűrő-állása (#440).

Az eredeti dialógus három választása:

| állás | mit ment |
|---|---|
| **Minden fájltípus** | amit az index médiának lát (fotó, RAW, videó) |
| **Minden kép (videók nélkül)** | fotó és RAW, videó nélkül |
| **Csak JPEG-ek fényképezőgép-adatokkal** | JPEG, amiben van EXIF `Make`/`Model` |

⚠️ A harmadik állás nem kiterjesztés-kérdés: a fényképezőgép-adat a
fájlban van. Ezért az a szűrő OLVASSA a fájlt — a hívó ezt a költséget a
tervezéskor egyszer fizeti meg.
"""

from __future__ import annotations

from pathlib import Path

from picasapy.index.backup_sets import (
    SZURO_FENYKEPEZOGEP,
    SZURO_KEPEK,
    SZURO_MINDEN,
)
from picasapy.scanner.filetypes import media_kind_of

_JPEG_KITERJESZTESEK = (".jpg", ".jpeg", ".jpe")


def _van_fenykepezogep_adata(utvonal: Path) -> bool:
    """EXIF `Make`/`Model` a fájlban (#440).

    A hibát elnyeljük: egy olvashatatlan fájl NEM dönthet le egy mentést,
    és fényképezőgép-adat nélkülinek számít."""
    if utvonal.suffix.lower() not in _JPEG_KITERJESZTESEK:
        return False
    try:
        from picasapy.metadata.reader import read_exif_details

        reszletek = read_exif_details(utvonal)
    except OSError:
        return False
    return bool(getattr(reszletek, "camera", None))


def szurd_meg(utvonalak, szuro: str) -> tuple[Path, ...]:
    """A szűrőnek megfelelő fájlok, a kapott sorrendben."""
    eredmeny: list[Path] = []
    for nyers in utvonalak:
        utvonal = Path(nyers)
        fajta = media_kind_of(utvonal.name)
        if fajta is None:
            continue
        if szuro == SZURO_MINDEN:
            eredmeny.append(utvonal)
        elif szuro == SZURO_KEPEK:
            if fajta != "video":
                eredmeny.append(utvonal)
        elif szuro == SZURO_FENYKEPEZOGEP:
            if _van_fenykepezogep_adata(utvonal):
                eredmeny.append(utvonal)
        else:
            raise ValueError(f"ismeretlen fájlszűrő: {szuro!r}")
    return tuple(eredmeny)
