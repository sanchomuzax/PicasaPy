"""#643 — a KÉPFÁJL módosítási idejének megérintése az ini-írás után.

## A probléma, amit ez old (a jegy kutatói szála, LEZÁRVA)

A futó eredeti Picasa nem a `.picasa.ini`-t, hanem a saját `db3`
adatbázisát tekinti igazságforrásnak, és a fotó rekordjának ÉRVÉNYESSÉGÉT
a **képfájlhoz** méri (`moddate`, `onlinechecksum` — az ini ↔ adatbázis
szinkron `0x00467ca0`-nál). Ebből három, méréssel megerősített
következmény adódik:

1. A `.picasa.ini` írása kivált ugyan operációs rendszer szintű értesítést
   (`FindFirstChangeNotificationW`, a szűrőben benne a `LAST_WRITE` bit,
   rekurzívan) — de egy **már indexelt** fotót nem tesz elavulttá.
2. Ezért a Picasa **újraindítás után sem** olvassa be a `filters=`-ünket:
   az adatbázis-gyorsítótárból dolgozik.
3. Sőt: amikor a Picasa legközelebb maga ír a fotóhoz, a szakaszt EGÉSZBEN
   írja ki a `db3`-ból — a mi láncunk némán elveszik.

A spec (`docs/specs/picasa-ini-format.md`, „A beolvasás életciklusa") ebből
egyetlen ismert, mérhető megkerülési utat vezet le: **ha a külső író a
képfájl módosítási idejét is megérinti, a fotó bekerülhet az
újrafeldolgozandók közé — és akkor az ini-t is beolvassa.**

Ez a modul pontosan ezt teszi, és semmi mást.

## A négy kimondott döntés

**1. A képfájl TARTALMA nem változhat.** Kizárólag `os.utime` fut le; a
fájlt meg sem nyitjuk. Ez éles családi fotógyűjteményen dolgozik — egy
újrakódolás vagy akár egy „ártalmatlan" bájtmódosítás visszafordíthatatlan
minőségvesztés lenne. A fájl bájtjai, jogosultságai, tulajdonosa és mérete
érintetlen marad.

**2. Az `atime` megőrzendő.** Az `os.utime` egyszerre állítja a két
időbélyeget, ezért az `atime`-ot előbb kiolvassuk (`os.stat`) és
változatlanul visszaírjuk. Enélkül egy szerkesztés „olvasottnak" jelölné a
fájlt olyan eszközök felé (archiválók, „régóta nem használt" takarítók),
amelyek az `atime`-ra építenek.

**3. Kikapcsolható — KÖRNYEZETI VÁLTOZÓVAL, nem beállítás-ablakkal.** Van,
akinél a mtime rendezési (fájlkezelő) vagy biztonsági mentési (rsync
méret+mtime összehasonlítás) szempontból számít, ezért a kikapcsolás
lehetősége kötelező. A környezeti változó mellett szól, hogy (a) ez a
réteg a Qt-tól FÜGGETLEN — az `ini` csomag szándékosan nem importál
PySide6-ot, tehát a `QSettings` itt nem elérhető architektúra-törés
nélkül; (b) egy felületi kapcsoló a `Main.qml`-t és a beállítás-ablakot is
érintené, ami ebben a körben tiltott terület; (c) a viselkedés a
felhasználó 99%-ának láthatatlan, a maradéknak pedig egyszeri, tartós
döntés — nem futásidőben kapcsolgatandó opció.

**4. Az alapértelmezés BE.** Ez a projekt 1. döntése (kétirányú
`.picasa.ini`-kompatibilitás): érintés nélkül a PicasaPy-ban végzett
szerkesztés a párhuzamosan futó Picasában **soha** nem jelenik meg — pont
ez a #643-as hibajelentés. A mtime-változás ára ehhez képest kicsi és
visszafordítható; aki mégsem kéri, egy környezeti változóval kikapcsolja.

## Amit ez a modul NEM ígér

Azt, hogy a valódi, windowsos Picasa emiatt tényleg újraindexeli a fotót,
**Linuxon nem lehet mérni**. A megkerülési út a visszafejtésből levezetett,
a jegy által kért kísérlet — a megerősítése a felhasználó párhuzamos
windowsos próbája. A kód a saját oldalát garantálja: az érintés megtörténik,
a tartalom nem változik.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Iterable

from .document import IniDocument

_log = logging.getLogger(__name__)

#: A kikapcsoló környezeti változó. Hiányában BE (ld. a modul 4. döntését).
TOUCH_ENV_VAR = "PICASAPY_TOUCH_PHOTO_MTIME"

#: „Hamis" értékek — a `PICASAPY_*` kapcsolók szokásos, elnéző olvasata.
_FALSE_VALUES = frozenset({"0", "false", "no", "off", "nem", "ki"})

#: Óraeltérés-tartalék: ha a képfájl mtime-ja a JÖVŐBEN van (NAS és gép
#: órája eltér, ami a felhasználó pontos helyzete), a „most" beállítása
#: VISSZAfelé mozdítaná az időbélyeget. A cél viszont az, hogy a fájl
#: biztosan újabbnak látsszon a Picasa rekordjánál, ezért ilyenkor a
#: jelenlegi értéknél egy másodperccel későbbre lépünk. Egy másodperc
#: azért, mert durvább felbontású fájlrendszereken (FAT, ext3) egy
#: mikromásodperces lépés lekerekedne ugyanarra az értékre.
_SKEW_BUMP_NS = 1_000_000_000


def is_touch_enabled(environ: dict[str, str] | None = None) -> bool:
    """Be van-e kapcsolva a képfájl-érintés (alapértelmezésben igen).

    Args:
        environ: A vizsgálandó környezet; alapértelmezésben `os.environ`
            (a paraméter a tesztelhetőséget szolgálja).

    Returns:
        True, ha a `PICASAPY_TOUCH_PHOTO_MTIME` hiányzik vagy nem „hamis".
    """
    env = os.environ if environ is None else environ
    raw = env.get(TOUCH_ENV_VAR)
    if raw is None:
        return True
    return raw.strip().casefold() not in _FALSE_VALUES


def changed_photo_sections(before: IniDocument, after: IniDocument) -> tuple[str, ...]:
    """Mely FOTÓ-szakaszok kulcsai változtak a két dokumentum között.

    Tiszta függvény, nem nyúl a lemezhez. A speciális szakaszokat
    (`[Picasa]`, `[Contacts2]`, `[.album:…]`) kihagyja: azok nem egy
    képfájlhoz tartoznak, tehát nincs mit megérinteni miattuk.

    A TÖRÖLT szakaszok is változásnak számítanak (pl. a `revert` az összes
    szerkesztés-kulcsot leszedi, és a szakasz üresen kiesik) — a fotó
    rekordja ugyanúgy elavult a Picasa felé.

    Args:
        before: A módosítás előtti (lemezről betöltött) dokumentum.
        after: A `mutate` által előállított, kimentett dokumentum.

    Returns:
        A változott szakasznevek, a dokumentumbeli sorrendben, ismétlés nélkül.
    """
    before_items = {s.name: s.items() for s in before.sections if not s.is_special}
    after_items = {s.name: s.items() for s in after.sections if not s.is_special}
    changed: list[str] = []
    for name, items in after_items.items():
        if before_items.get(name) != items:
            changed.append(name)
    changed.extend(name for name in before_items if name not in after_items)
    return tuple(changed)


def touch_photo(image_path: Path) -> bool:
    """Egyetlen képfájl mtime-jának frissítése, az atime megőrzésével.

    A fájlt NEM nyitja meg és NEM írja — csak az időbélyegeit állítja
    (`os.utime`), tehát a tartalom bájtra azonos marad.

    Hibatűrő: ha a fájl időközben eltűnt, írásvédett, vagy a hálózati
    megosztás nem engedi az `utime`-ot, azt **naplózza és továbbenged** — a
    felhasználó elmentett szerkesztése fontosabb, mint a Picasa értesítése.

    Args:
        image_path: A megérintendő képfájl útja.

    Returns:
        True, ha az érintés sikerült.
    """
    try:
        stat = image_path.stat()
        new_mtime_ns = max(time.time_ns(), stat.st_mtime_ns + _SKEW_BUMP_NS)
        os.utime(image_path, ns=(stat.st_atime_ns, new_mtime_ns))
    except OSError as error:
        _log.warning(
            "A(z) %s módosítási ideje nem frissíthető (%s) — a mentés ettől "
            "érvényes marad, csak a párhuzamosan futó Picasa nem fogja "
            "észrevenni a változást (#643).",
            image_path,
            error,
        )
        return False
    return True


def touch_photos(ini_path: Path, section_names: Iterable[str]) -> tuple[Path, ...]:
    """A megadott szakaszokhoz tartozó, LÉTEZŐ képfájlok megérintése.

    A szakasznév a spec szerint a fájlnév (`[<fájlnév.ext>]`), az ini pedig
    a képek melletti mappában él — a kettőből adódik az útvonal. Ami nem
    létező fájlra mutat (törölt/áthelyezett kép, vagy egy fel nem ismert
    speciális szakasz), azt csendben kihagyjuk: az nem hiba.

    Args:
        ini_path: A most kiírt `.picasa.ini` útja.
        section_names: A megérintendő fotók szakasznevei.

    Returns:
        A ténylegesen megérintett képfájlok útjai.
    """
    if not is_touch_enabled():
        return ()
    folder = ini_path.parent
    touched: list[Path] = []
    for name in section_names:
        candidate = folder / name
        # Védelem a szakasznévbe csempészett útvonal ellen: csak közvetlenül
        # az ini melletti fájlt érintjük meg, alkönyvtárat/`..`-t soha.
        if candidate.parent != folder:
            continue
        if not candidate.is_file():
            continue
        if touch_photo(candidate):
            touched.append(candidate)
    return tuple(touched)


def notify_picasa_after_ini_write(
    ini_path: Path, before: IniDocument, after: IniDocument
) -> tuple[Path, ...]:
    """Az ini-írás utáni értesítő lépés — az `update_document` közös pontja.

    Összeköti a két felét: kiszámolja, mely fotók rekordja változott, és
    azok képfájljának mtime-ját frissíti. Ez az EGYETLEN hely, ahonnan az
    érintés indul, hogy minden ini-író (szerkesztő, csillag, felirat,
    arcok, kulcsszavak, csoportos effekt, mentés) automatikusan részesüljön
    belőle, és ne kelljen hívónként emlékezni rá.

    Args:
        ini_path: A most kiírt `.picasa.ini` útja.
        before: A módosítás előtti dokumentum.
        after: A kiírt dokumentum.

    Returns:
        A megérintett képfájlok útjai (üres, ha ki van kapcsolva).
    """
    if not is_touch_enabled():
        return ()
    changed = changed_photo_sections(before, after)
    if not changed:
        return ()
    return touch_photos(ini_path, changed)
