"""A kollázs automatikus mentése és helyreállítása (#431).

A Picasa a kollázs szerkesztése közben külön szálon (`CAutosaveCollageThread`)
folyamatosan írt egy **`autosave.cxf`** piszkozatot, és a következő indításkor
felajánlotta a visszaállítást (`collage::recoveredautosave` / `lastautosave`
üzenetek). Forrás: `docs/specs/picasa-create-features.md` 1.5; a 4. fejezet 3.
pontja külön kiemeli, hogy „a felhasználó munkája sosem veszett el".

A piszkozat tartalma ugyanaz a `.cxf`, amit a `picasapy.collage.cxf` ír és
olvas — ez a modul csak a **piszkozat életciklusát** adja hozzá: hova kerül,
hogyan lehet biztonságosan felülírni, és mikor kell eldobni.

## Miért atomi az írás

A piszkozatot azért írjuk, hogy egy összeomlás ne vigye el a munkát. Ha a
mentés maga nem atomi, akkor pont az összeomlás pillanatában keletkezik egy
féllig kiírt `autosave.cxf` — és a helyreállítás azt találná meg a jó
piszkozat helyett. Ezért **ideiglenes fájlba írunk** (`autosave.cxf.tmp` — a
Picasa is `.cxf.tmp`-t használt mentéskor, ld. spec 1.5), és csak a teljes,
sikeres kiírás után mozgatjuk a helyére egyetlen `os.replace` hívással. Ha
bármi elszáll közben, a **korábbi piszkozat érintetlen marad**.

## Miért nem dob kivételt az olvasás

A helyreállítás egy összeomlás UTÁN fut, tehát pont akkor, amikor a fájl
sérült vagy csonk lehet. Ilyenkor a helyes válasz az, hogy „nincs
visszaállítható piszkozat" — nem az, hogy az alkalmazás indulás közben
elszáll. Ezért az olvasó függvények soha nem dobnak: hiba esetén `None`,
illetve `False` a válasz.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from picasapy.collage.cxf import CxfProject, dumps, loads
from picasapy.collage.win_paths import decode_cxf_path

logger = logging.getLogger(__name__)

#: a piszkozat fájlneve — a Picasáéval szó szerint egyezik (spec 1.5)
AUTOSAVE_NAME = "autosave.cxf"

#: az átmeneti fájl neve írás közben (a Picasa `.cxf.tmp`-je)
_TEMP_NAME = AUTOSAVE_NAME + ".tmp"


def autosave_path(directory: Path | str) -> Path:
    """A piszkozat teljes útvonala a megadott kollázs-mappában."""
    return Path(directory) / AUTOSAVE_NAME


def write_autosave(directory: Path | str, project: CxfProject) -> Path:
    """A piszkozat **atomi** kiírása; a végleges útvonalat adja vissza.

    Előbb az `autosave.cxf.tmp`-be írunk, és csak a hiánytalan kiírás után
    mozgatjuk a helyére. Ha az írás vagy a mozgatás elszáll, az átmeneti
    fájlt eltakarítjuk, a korábbi piszkozat pedig **változatlan marad** — a
    hívó a kivételből értesül a hibáról.
    """
    mappa = Path(directory)
    mappa.mkdir(parents=True, exist_ok=True)
    ideiglenes = mappa / _TEMP_NAME
    vegleges = mappa / AUTOSAVE_NAME

    try:
        ideiglenes.write_bytes(dumps(project))
        os.replace(ideiglenes, vegleges)
    except OSError:
        # a félkész átmeneti fájl nem maradhat ott: a következő mentés
        # megbízhatóságát rontaná, és a felhasználó mappájában is szemét
        try:
            ideiglenes.unlink(missing_ok=True)
        except OSError:  # pragma: no cover - a takarítás hibája nem elsődleges
            logger.warning("A kollázs-piszkozat átmeneti fájlja nem törölhető: %s", ideiglenes)
        raise

    return vegleges


def read_autosave(directory: Path | str) -> CxfProject | None:
    """A piszkozat beolvasása, vagy `None`, ha nincs / nem értelmezhető.

    Soha nem dob kivételt: összeomlás után a fájl csonk is lehet, és ilyenkor
    a „nincs mit visszaállítani" a helyes válasz.
    """
    utvonal = autosave_path(directory)
    try:
        adat = utvonal.read_bytes()
    except OSError:
        return None

    try:
        return loads(adat)
    except (ValueError, TypeError) as hiba:
        logger.info("A kollázs-piszkozat sérült, nem állítható vissza (%s): %s", utvonal, hiba)
        return None


def has_recoverable_draft(directory: Path | str) -> bool:
    """Van-e ÉP, visszaállítható piszkozat a mappában.

    Szándékosan a tényleges beolvasással válaszol, nem a fájl létezésével: a
    felhasználónak felajánlani egy sérült piszkozatot rosszabb, mint nem
    felajánlani semmit.

    ⚠️ #1064: a beolvashatóság nem elég — **legalább egy képnek lennie is
    kell**. Az eredeti erre külön üzenetet tart fenn
    (`CollageUI::AllImagesMissing`, spec 9.3): „A kollázs nem szerkeszthető,
    mert a benne hivatkozott képek egyike sem található." Ha nem
    szerkeszthető, felajánlani sincs értelme — a felhasználó rábólintana, és
    csupa helykitöltő csempéből álló lapot kapna.

    A határ **legalább egy**, nem „mind": a részleges visszaállítás értékes,
    a hiányzók helykitöltőként jelennek meg (spec 9.4), a többi munka pedig
    megmarad.

    A piszkozatot ez a függvény SOHA nem törli. Ha a képek visszakerülnek a
    helyükre (visszacsatolt meghajtó, visszaállított mappa), a piszkozat
    magától újra érvényessé válik.
    """
    projekt = read_autosave(directory)
    if projekt is None:
        return False
    return any(_letezik(node.src) for node in projekt.nodes)


def _letezik(forras: str) -> bool:
    """Létezik-e a csomópont képe. Hibára `False` — egy elérhetetlen hálózati
    útvonal nem dobhat kivételt egy indulási ellenőrzésben."""
    if not forras:
        return False
    try:
        # #1096: a `.cxf` KÓDOLT útvonalat tárol (`$My Pictures\…`) — nyersen
        # vizsgálva SOHA nem létezne, és a felajánlás némán elmaradna.
        return Path(decode_cxf_path(forras)).is_file()
    except OSError:  # pragma: no cover - platformfüggő, ritka
        return False


def discard_autosave(directory: Path | str) -> bool:
    """A piszkozat eldobása; `True`, ha tényleg volt mit törölni.

    Akkor hívandó, ha a kollázs mentése sikerült (a piszkozat betöltötte a
    szerepét), vagy ha a felhasználó nemet mondott a visszaállításra. Sérült
    piszkozatot is eltakarít, és ismételhető — a második hívás `False`.
    """
    utvonal = autosave_path(directory)
    try:
        utvonal.unlink()
    except FileNotFoundError:
        return False
    except OSError as hiba:
        logger.warning("A kollázs-piszkozat nem törölhető (%s): %s", utvonal, hiba)
        return False
    return True


__all__ = [
    "AUTOSAVE_NAME",
    "autosave_path",
    "discard_autosave",
    "has_recoverable_draft",
    "read_autosave",
    "write_autosave",
]
