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


def qmlc_nevek(profil: Path, ota: float, qml_gyoker: Path, korlat: int = 20) -> list[str]:
    """Az indulás alatt írt `.qmlc` fájlok forrásneve (#6426).

    A Qt a gyorsítótár-fájlt a perjeles helyi útvonal SHA-1-éről nevezi el;
    a `qml_gyoker` alatti `.qml` fájlok hash-éből visszakereshető, melyik
    forrást fordította futás közben. Ami nem található, a hash-ével szerepel."""
    from hashlib import sha1

    if not profil.is_dir():
        return []
    irtak = []
    for ut in profil.rglob("*.qmlc"):
        try:
            if ut.stat().st_mtime >= ota:
                irtak.append(ut.stem)
        except OSError:
            continue
    if not irtak:
        return []
    terkep = {}
    if qml_gyoker.is_dir():
        for forras in qml_gyoker.rglob("*.qml"):
            terkep[sha1(forras.resolve().as_posix().encode("utf-8")).hexdigest()] = forras
    nevek = []
    for kulcs in sorted(irtak):
        forras = terkep.get(kulcs)
        nevek.append(forras.relative_to(qml_gyoker).as_posix() if forras else kulcs)
    return nevek[:korlat]
