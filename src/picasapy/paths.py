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
- `flat_key` (#3776): ugyanaz a kis-nagybetű-döntés, de TISZTA
  string-műveletként, fájlrendszer-hozzáférés NÉLKÜL — a `path_key` a
  `normalize_path`-on át `resolve()`-ot hív, ami egy Windows-alakú
  útvonalon (`C:\\...`) Linuxon nem ad értelmes eredményt, tehát a
  windowsos ág ott nem volna mérhető. A mentés-szűrő lapos listája
  (`app/backup_controller.py::mentesKulcs`, `app/models.py::
  FolderListModel.rowOfPath`) ezt hívja, mert mindkét oldala már
  Python-Path-ból épült, azonos futáson belüli sztring — nincs mit
  feloldani, csak összevetni.

## Hálózati (UNC) útvonal: feloldás NÉLKÜL (#7044, #7045)

Windowson a `\\\\szerver\\megosztás\\...` alakú útvonal `Path.resolve()`-ja
minden komponensre hálózati körülfordulás (elérhetetlen NAS-nál 20-40 s), és
az indulás ezt a fő szálon, mappánként ismételte. A feloldás eredménye ráadásul
más kis-nagybetűs alakot adhat (a szervernevet kisbetűsítheti), mint amit a
felhasználó felvett: ugyanaz a mappa két, szövegesen eltérő útvonallal két
indexsor lett. A hálózati útvonal ezért csak LEXIKÁLISAN normalizálódik
(`..`/`.`, elválasztók), a megadott kis-nagybetű megmarad, és hálózati hívás
nincs. Szimbolikus link feloldás hálózati megosztáson nincs: ott nem ez a
szokásos felállás, és a feloldás ára a teljes indulás volt.
"""

from __future__ import annotations

import ntpath
import os
import posixpath
import sys
from pathlib import Path, PureWindowsPath

from picasapy import halozati_ut
from picasapy.halozati_ut import halozati_gyoker


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
    if windowsos_halozati_ut(text):
        # #7044/#7045: hálózati hívás nélkül, a megadott kis-nagybetűvel
        return str(PureWindowsPath(ntpath.normpath(text)))
    if is_network_path(text):
        # #7048: a leképezett meghajtó és a Linuxos SMB/GVFS mount sem érhet
        # `resolve()`-hoz; a hálózati csatolást a helyi mount-tábla azonosítja.
        if _platform().startswith("win"):
            return str(PureWindowsPath(ntpath.normpath(text)))
        return posixpath.normpath(os.path.abspath(text))
    return _feloldas(text)


def path_key(path: str | Path) -> str:
    """Összehasonlító kulcs — SOHA nem tárolt/megjelenített alakként,
    kizárólag „ugyanaz-e a két útvonal" döntéshez (pl. `_roots`
    tagság-ellenőrzés, duplikátum-mappák csoportosítása)."""
    return _normcase(normalize_path(path))


def _feloldas(text: str) -> str:
    """A fájlrendszeri feloldás (`Path.resolve()`), modulszintű, cserélhető
    fogantyú (#1375): a teszt ezen át méri, hogy egy út hálózatra vár-e,
    anélkül hogy a globális `os`/`pathlib` függvényeket kellene átírnia."""
    return str(Path(text).resolve())


def is_same_or_under(path: str | Path, root: str | Path) -> bool:
    """Igaz, ha a `path` a `root` vagy egy mappája alatta (#7044).

    Komponens-pontos, a `path_key` kulcsán (platformhelyes kis-nagybetű), így
    hálózati útvonalon sincs fájlrendszer-hívás, és Windows-alakú útvonal
    Linuxon is mérhető. A `Path.resolve()`-os összevetés helyett használjuk,
    ahol a hívó fő szálon fut."""
    kulcs = path_key(path).rstrip("/\\")
    gyoker = path_key(root).rstrip("/\\")
    return kulcs == gyoker or kulcs.startswith((gyoker + "\\", gyoker + "/"))


def _platform() -> str:
    """A futó platform — cserélhető fogantyú (#1217), hogy a `flat_key`
    Windows-alakú bemeneten (`C:\\...`) Linuxon is mérhető legyen."""
    return sys.platform


def windowsos_halozati_ut(text: str) -> bool:
    """Windowson UNC-alakú (`\\\\szerver\\megosztás\\...`) útvonal-e.

    Csak Windowson igaz: POSIX-on a `//mnt/nas` a `/mnt/nas`, nem hálózati
    útvonal, és a feloldásához nem szabad hozzányúlni."""
    return _platform().startswith("win") and halozati_gyoker(text) is not None


def is_network_path(text: str | Path) -> bool:
    """Hálózati útvonal-e UNC, leképezett meghajtó vagy Linuxos mount alapján."""
    return halozati_ut.fajlrendszer_gyoker(str(text), platform=_platform()) is not None


def _normcase(text: str) -> str:
    """Platformhelyes kis-nagybetű-döntés a cserélhető fogantyún át: Windowson
    kisbetű és `\\`, POSIX-on identitás (`os.path.normcase`)."""
    if _platform().startswith("win"):
        return ntpath.normcase(text)
    return os.path.normcase(text)


def flat_key(path: str) -> str:
    """A #3776 lapos mentés-listájának ÖSSZEHASONLÍTÓ alakja.

    Windowson a fájlrendszer kis-nagybetű-érzéketlen, és mindkét
    elválasztó előfordulhat (`app/backup_controller.py`
    `Path.rglob`-ból, illetve az index natív alakjából) — POSIX-on viszont
    a kis-nagybetű VALÓDI különbség, ott a foldolás adatvesztő volna, ÉS a
    `\\` ott ÉRVÉNYES névkarakter, tehát az elválasztó-csere is adatvesztő
    volna (egy POSIX-fájlnévben szereplő `\\`-t tévesen elválasztóként
    venné). Ezért mindkét átalakítás KIZÁRÓLAG Windowson fut; POSIX-on a
    `flat_key` identitás."""
    if not _platform().startswith("win"):
        return path
    return path.lower().replace("\\", "/")
