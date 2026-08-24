"""A kollázs KÖZÖS FORRÁSMAPPÁJA — egyetlen szabály, egy helyen (#1092).

A `.cxf` három mezője beszél a forrásalbumról — a címe (`<albumTitle>`),
az azonosítója (`albumUID`) és a dátuma (`<albumDate>`) —, és mind a
háromnak UGYANAZ a forrása: a kollázsba került képek közös mappája.

A szabály elsőre két helyen, két megvalósításban élt (a cím a
vezérlőben, a másik kettő az album-mezőknél). Két másolat egy ilyen
szabályból garantáltan elválik: elég egy `resolve()` az egyik oldalon,
és a cím már mást mond, mint az azonosító.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path


def common_source_folder(sources: Iterable) -> Path | None:
    """A képek közös forrásmappája, vagy `None`, ha nem egy van belőle.

    Több mappából érkező kijelölésnél NINCS forrásalbum. Kitalált,
    „Nyaralás + 2 másik mappa" jellegű nevet — és a hozzá tartozó
    azonosítót — nem gyártunk."""
    folders = {Path(source.path).parent for source in sources if source.path}
    if len(folders) != 1:
        return None
    return next(iter(folders))


def common_source_folder_name(sources: Iterable) -> str:
    """A közös forrásmappa NEVE (ebből lesz a kimeneti fájl neve, 9.1)."""
    folder = common_source_folder(sources)
    return "" if folder is None else folder.name


__all__ = ["common_source_folder", "common_source_folder_name"]
