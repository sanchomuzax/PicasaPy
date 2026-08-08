"""Egységes mappa-útvonal normalizálás (#507).

## A hiba

Ugyanaz a valódi mappa TÖBB, karakterláncként eltérő alakban is érkezhet:
záró perjellel/anélkül, `file://` URL-ként, `..`/`.` szegmenssel, szimbolikus
linken át, vagy (Windowson) eltérő kis-nagybetűzéssel. A figyelt gyökerek
listája (`library_controller._roots`) és az index (`folders.path`) korábban
NYERS szövegösszehasonlítással döntötte el, hogy „ugyanaz-e" két útvonal —
ez a két eltérő alaknál hamis negatívot adott, és a mappa duplikátumként
jelent meg (bal hasáb, azonos névvel és képszámmal).

## A megoldás — EGYETLEN hely

Ezt a modult hívja MINDEN kódút, amely egy mappa-útvonal AZONOSSÁGÁRÓL dönt:
a figyelt gyökerek kezelése (`app/library_controller.py`) ÉS az index
gyökér-normalizálása (`index/sync.py`). Két függvény, két célra:

- `normalize_path`: a TÁROLÁSRA/MEGJELENÍTÉSRE szánt kanonikus alak
  (abszolút, `..`/`.` feloldva, szimbolikus link feloldva, amennyire a
  fájlrendszer engedi) — a kis-nagybetűzést NEM változtatja, hogy a
  „mappa helye" a valódi (OS-adta) alakot mutassa.
- `path_key`: ÖSSZEHASONLÍTÁSRA/dedup-kulcsnak való — a `normalize_path`
  eredményén platformhelyes kis-nagybetű-kezelést végez
  (`os.path.normcase`): Windowson kisbetűre foldol (ott a fájlrendszer is
  kis-nagybetűre nem érzékeny), POSIX-on IDENTITÁS — Linuxon/macOS-en két
  eltérő nagybetűzésű mappa két KÜLÖNBÖZŐ, valódi mappa lehet, a foldolás
  ott adatvesztő összemosás volna.
"""

from __future__ import annotations

import os
from pathlib import Path


def normalize_path(path: str | Path) -> str:
    """Kanonikus, tárolásra/megjelenítésre alkalmas alak.

    Üres bemenetre üres sztringet ad (a hívók ezt „nincs útvonal"-ként
    kezelik, ld. `library_controller.addWatchedFolder`). Nemlétező
    útvonalnál a `Path.resolve()` a fel NEM oldható maradék szegmenseket
    (a legmélyebb létező előtag felett) változatlanul hagyja — ez csak a
    `..`/`.` feloldást és az abszolúttá tételt biztosítja számukra,
    szimbolikus link feloldást nem (nincs mit feloldani egy nemlétező
    célon)."""
    text = str(path).strip()
    if not text:
        return ""
    return str(Path(text).resolve())


def path_key(path: str | Path) -> str:
    """Összehasonlító kulcs — SOHA nem tárolt/megjelenített alakként,
    kizárólag „ugyanaz-e a két útvonal" döntéshez (pl. `_roots`
    tagság-ellenőrzés, duplikátum-mappák csoportosítása)."""
    return os.path.normcase(normalize_path(path))
