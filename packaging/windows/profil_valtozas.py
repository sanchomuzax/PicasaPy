"""Mit írt a program a profilba egy indulás alatt (#6374).

A valódi ablakos első indulás a windowsos csomagmérésen 4,1 s-os Main.qml-
betöltést mutatott, a második 1,3 s-ot, holott a QML-gyorsítótár előre
elkészült. Hogy a program első alkalommal mit hoz még létre és ment el, az
csak a windowsos gépen látszik: ez a lista megnevezi.
"""

from __future__ import annotations

from pathlib import Path


def uj_fajlok(profil: Path, ota: float, korlat: int = 40) -> list[str]:
    """A profil alatt `ota` (epoch mp) után létrejött vagy módosult fájlok,
    mappánként összesítve: `relatív mappa: N fájl, M bájt`."""
    mappak: dict[str, list[int]] = {}
    if not profil.is_dir():
        return []
    for ut in profil.rglob("*"):
        try:
            if not ut.is_file() or ut.stat().st_mtime < ota:
                continue
            meret = ut.stat().st_size
        except OSError:
            continue
        kulcs = ut.parent.relative_to(profil).as_posix() or "."
        osszeg = mappak.setdefault(kulcs, [0, 0])
        osszeg[0] += 1
        osszeg[1] += meret
    sorok = sorted(mappak.items(), key=lambda e: -e[1][1])[:korlat]
    return [f"{mappa}: {db} fájl, {bajt} bájt" for mappa, (db, bajt) in sorok]
