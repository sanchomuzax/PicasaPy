"""Képkocka mentése a videóból — a Picasa `capture_frame` parancsa (#1838).

Az eredeti videó-vezérlősávján a `capture_frame` a **Rögzített
videoklipek** mappába írt egy **JPEG**-et. A név felépítése kimérve
(`0x00591fa6`–`0x0059203c`, spec: `picasa-menu-parancsok-viselkedes.md`
64. tétel):

1. a honosított mappanév (a mappa a webkamera-pillanatképpel KÖZÖS —
   `app/project_folder_names.py`, `CAPTURED_VIDEOS`);
2. ha a mappa nincs meg, létrejön (az eredeti a `.picasa.ini`-t is
   megírja hozzá);
3. az alapnév, majd a **`.jpg`** kiterjesztés;
4. egyediesítés a **`%s-%03lu`** mintával, `0x1000` = **4096**-ig.

Az új célmappa `[Picasa] P2category=Projects (internal)` jelölést kap az
`ini/` API-n keresztül; létező mappánál az ini érintetlen. A JPEG explicit
85-ös minőséggel készül (`0x55`).

⚠️ Ez MÁS minta, mint a kollázsé és a mozgófilmé (`%s%lu` →
`nev1.jpg`): itt a sorszám **kötőjeles és háromjegyű**, és a
kiterjesztés leválasztva kerül vissza a végére. Aki az
`app/movie_output.output_path()`-ot emelné át ide, rossz nevet adna.

⛔ **Amit NEM tudunk:** mi az eredeti alapneve (`[obj+0x68]`) — a mezőt a
hívó tölti, literál nincs rá (a spec „BLOKKOLT"-ként tartja). Nálunk a
videó saját fájlneve az alap; ez a legkevésbé meglepő választás, és a
mappán belül önmagában is megmondja, melyik klipből való.

A modul TISZTA: a bemenetét nem mutálja, és a lemezre csak a
`mentsd_a_kepkockat` ír.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

#: A képkocka kiterjesztése — mérve (`0x00c80a50`).
KEPKOCKA_KITERJESZTES = ".jpg"

#: A videóból mentett JPEG minősége — mérve (`0x00592033`–`0x00592067`).
KEPKOCKA_JPEG_MINOSEG = 85

#: A natív egyediesítő `0x1000`-ig emeli a számlálót (`0x00993a1a`).
MAX_SORSZAM = 4096

#: Ha a videó neve nem ad használható alapnevet.
TARTALEK_ALAPNEV = "frame"

#: Fájlnévben nem használható karakterek (a windowsos készlet a szűkebb).
_TILTOTT = set('<>:"/\\|?*')


def kepkocka_alapneve(video_utvonal: str | Path) -> str:
    """A képkocka alapneve a videó fájlnevéből, kiterjesztés nélkül.

    A tiltott karakterek kiesnek; üres eredménynél a `TARTALEK_ALAPNEV`."""
    torzs = Path(str(video_utvonal)).stem
    tisztitott = "".join(karakter for karakter in torzs if karakter not in _TILTOTT)
    tisztitott = tisztitott.strip()
    return tisztitott or TARTALEK_ALAPNEV


def egyedi_utvonal(mappa: str | Path, alapnev: str) -> Path:
    """Ütközésmentes célfájl: `<alapnév>.jpg`, majd `<alapnév>-001.jpg`…

    A sorszám a NÉV végére kerül, a kiterjesztés mögé SOHA. A számláló a
    natív határig (`MAX_SORSZAM`) megy; fölötte `ValueError` — néma
    felülírás helyett hiba, mert a felülírt képkocka visszaállíthatatlan.
    """
    mappa = Path(mappa)
    jelolt = mappa / f"{alapnev}{KEPKOCKA_KITERJESZTES}"
    if not jelolt.exists():
        return jelolt
    for sorszam in range(1, MAX_SORSZAM + 1):
        jelolt = mappa / f"{alapnev}-{sorszam:03d}{KEPKOCKA_KITERJESZTES}"
        if not jelolt.exists():
            return jelolt
    raise ValueError(
        f"A(z) {mappa} mappában nincs szabad képkocka-név "
        f"(a sorszám elérte a {MAX_SORSZAM} határt)."
    )


def mentsd_a_kepkockat(
    kep: np.ndarray, mappa: str | Path, alapnev: str
) -> Path:
    """Egy RGB képkocka kiírása JPEG-ként, ütközésmentes néven.

    A mappa létrejön, ha nincs. A bemenet a projekt render-konvenciója
    szerint **RGB** `uint8` (H, W, 3); a lemezre írás BGR-t vár, ezért a
    csatornasorrend itt fordul meg — ez a hely, ahol a kettő találkozik.
    """
    from picasapy.lazy_cv2 import cv2

    if kep.ndim != 3 or kep.shape[2] != 3:
        raise ValueError(f"RGB (H, W, 3) képkocka kell, ez {kep.shape} alakú.")
    mappa = Path(mappa)
    try:
        mappa.mkdir(parents=True)
    except FileExistsError:
        if not mappa.is_dir():
            raise
    else:
        from picasapy.ini import (
            INI_NAME,
            PROJECTS_CATEGORY,
            update_document,
            with_folder_category,
        )

        update_document(
            mappa / INI_NAME,
            lambda document: with_folder_category(document, PROJECTS_CATEGORY),
        )
    cel = egyedi_utvonal(mappa, alapnev)
    # ⚠️ #65/#190/#1991: fájlútvonalas `cv2.imwrite` ékezetes néven Windowson
    # NÉMÁN elbukik — és a célmappa neve épp ékezetes („Rögzített
    # videoklipek"). Ezért kódolunk memóriába, és a Path ír.
    sikeres, puffer = cv2.imencode(
        KEPKOCKA_KITERJESZTES,
        kep[..., ::-1],
        [cv2.IMWRITE_JPEG_QUALITY, KEPKOCKA_JPEG_MINOSEG],
    )
    if not sikeres:
        raise OSError(f"A képkocka kódolása nem sikerült: {cel}")
    cel.write_bytes(puffer.tobytes())
    return cel


__all__ = [
    "KEPKOCKA_KITERJESZTES",
    "KEPKOCKA_JPEG_MINOSEG",
    "MAX_SORSZAM",
    "TARTALEK_ALAPNEV",
    "egyedi_utvonal",
    "kepkocka_alapneve",
    "mentsd_a_kepkockat",
]
