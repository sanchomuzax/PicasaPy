"""#643 / #1320 — a KÉPFÁJL módosítási idejének megérintése az ini-írás után.

SAJÁT FUNKCIÓ (#1320): ez a modul egy olyan utat valósít meg, ami az eredeti
Picasában NEM létezik — a képfájl `mtime`-jának megérintése nem része a
Picasa frissesség-vizsgálatának (az az ini saját dátumát nézi). Ezért
alapértelmezésben KI van kapcsolva, és opt-in kísérleti kapcsolóként marad
meg (lista: docs/decisions/vedett-sajat-funkciok.md).

## Amit MA tudunk: az újraolvasás kulcsa az INI SAJÁT dátuma

Az eredeti Picasa mappánként eltárolja a `.picasa.ini` **utolsó írási
idejét** (`db3/albumdata_inisync.pmp`, FILETIME), és a következő
beolvasáskor ehhez méri a lemezen lévő fájlt: ha az ini újabb, a mappát
újraolvassa — **`flags = 3` értékkel, ami a szerkesztéseket (`filters`,
`crop`, `rotate`, …) is magában foglalja**. A mérés a felhasználó valódi
adatbázisán 787 mappából 783-ra bitre egyezett (99,5%); a négy eltérésből
három olyan mappa, ahol épp az ini az újabb, azaz újraolvasásra vár.

⇒ **A helyes lépés egyszerűen az, hogy írjuk a `.picasa.ini`-t.** A fájl
írási ideje ettől magától megváltozik, ami a mechanizmus teljes kiváltása.
Ezt az `io.update_document` amúgy is megteszi minden mentésnél; nincs
szükség hozzá külön lépésre.

Részletek: `docs/specs/picasa-ini-format.md` → „MEGFEJTVE: az újraolvasás
kulcsa az INI FÁJL saját dátuma", és `docs/specs/pmp-database.md` →
„Az `albumdata_inisync` oszlop".

## Amit ez a modul csinál, és MIÉRT NEM alapértelmezés

Ez a modul egy MÁSIK, **feltételezett** utat valósít meg: az ini-írás után
megérinti a változott szakaszokhoz tartozó **képfájlok** `mtime`-ját
(`os.utime`, a tartalom változtatása nélkül). A gondolatmenet az volt, hogy
egy már indexelt fotó rekordja csak akkor avul el, ha maga a képfájl
frissül.

**A feltevés Picasa-oldalon soha nem lett megmérve, és két mérés szól
ellene** (`docs/specs/picasa-ini-format.md` → „Az mtime-megkerülés
mérlege"):

1. mind a **három** `CompareFileTime`-hívási hely rendezés-komparátor,
   egyik sem frissesség-vizsgálat;
2. a könyvtárbejáró rekordja **nem tárol** módosítási időt (a hibakereső
   CSV oszlopai: `Name, Creation Time, Access Time, Size, Type, Dirty,
   Valid`), a `GetFileAttributesExW` egyetlen hívója pedig csak méretet
   vizsgál.

*(Amit viszont NEM cáfoltunk: az eredeti IGENIS figyel változás-értesítést,
`FindFirstChangeNotification` a `0x007062b9`-nél, szűrő `0x17`, benne a
`LAST_WRITE` bittel, rekurzívan — ez `docs/specs/picasa-mappakezelo.md`
16.5-ben megerősített. Az értesítés léte azonban nem mond semmit arról,
hogy a fotó `mtime`-ja számít-e; a frissességet az ini dátuma dönti el.)*

## A döntés: az alapértelmezés KI (#1320)

Egy éles, családi fotógyűjtemény időbélyegeinek átírása
**visszafordíthatatlan** mellékhatás (fájlkezelős rendezés, `rsync`
méret+mtime alapú mentés, „régóta nem használt" takarítók). Ezt az árat
csak **mért** haszonért szabad megfizetni — a haszon pedig ma nem mért, sőt
a mechanizmus ismeretében szükségtelen.

A modul mégis MEGMARAD, kifejezetten bekapcsolhatóan
(`PICASAPY_TOUCH_PHOTO_MTIME=1`), mert a „segít-e mégis?" kérdést egyedül a
felhasználó párhuzamos windowsos próbája döntheti el — ehhez kell egy
kapcsoló, amivel a kísérlet elvégezhető. Ha a próba pozitív, az
alapértelmezés visszafordítható; ha negatív, a modul törölhető.

A vonatkozó ADR: `docs/decisions/photo-mtime-erintes.md`.

## A többi, változatlanul érvényes döntés

**1. A képfájl TARTALMA nem változhat.** Kizárólag `os.utime` fut le; a
fájlt meg sem nyitjuk. A bájtjai, jogosultságai, tulajdonosa és mérete
érintetlen marad.

**2. Az `atime` megőrzendő.** Az `os.utime` egyszerre állítja a két
időbélyeget, ezért az `atime`-ot előbb kiolvassuk (`os.stat`) és
változatlanul visszaírjuk — enélkül az érintés „olvasottnak" jelölné a
fájlt az `atime`-ra építő eszközök felé.

**3. A kapcsoló KÖRNYEZETI VÁLTOZÓ, nem beállítás-ablak.** Ez a réteg a
Qt-tól FÜGGETLEN (az `ini` csomag szándékosan nem importál PySide6-ot),
tehát a `QSettings` itt architektúra-törés nélkül nem elérhető; ráadásul ez
most egy kísérleti kapcsoló, nem felhasználónak szánt beállítás.

**4. Ha fut, LÁTSZANIA kell.** Bekapcsolt állapotban a modul naplózza, hány
képfájl időbélyegét írta át — az éles archívum módosítása nem lehet néma.
"""


from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from collections.abc import Iterable, Mapping

from .document import IniDocument

_log = logging.getLogger(__name__)

#: A BEKAPCSOLÓ környezeti változó. Hiányában KI (#1320 döntése).
TOUCH_ENV_VAR = "PICASAPY_TOUCH_PHOTO_MTIME"

#: „Igaz" értékek — a `PICASAPY_*` kapcsolók szokásos, elnéző olvasata.
#: Bármi más (üres érték, elgépelés) a BIZTONSÁGOS irányba dől: nem érintünk.
_TRUE_VALUES = frozenset({"1", "true", "yes", "on", "igen", "be"})

#: Óraeltérés-tartalék: ha a képfájl mtime-ja a JÖVŐBEN van (NAS és gép
#: órája eltér, ami a felhasználó pontos helyzete), a „most" beállítása
#: VISSZAfelé mozdítaná az időbélyeget. A cél viszont az, hogy a fájl
#: biztosan újabbnak látsszon a Picasa rekordjánál, ezért ilyenkor a
#: jelenlegi értéknél egy másodperccel későbbre lépünk. Egy másodperc
#: azért, mert durvább felbontású fájlrendszereken (FAT, ext3) egy
#: mikromásodperces lépés lekerekedne ugyanarra az értékre.
_SKEW_BUMP_NS = 1_000_000_000


def is_touch_enabled(environ: Mapping[str, str] | None = None) -> bool:
    """Be van-e kapcsolva a képfájl-érintés (alapértelmezésben NEM).

    A #1320 óta ez opt-in: a képfájl `mtime`-jának átírása nem része az
    eredeti Picasa mechanizmusának, ezért csak kifejezett kérésre fut.

    Args:
        environ: A vizsgálandó környezet; alapértelmezésben `os.environ`
            (a paraméter a tesztelhetőséget szolgálja).

    Returns:
        True, ha a `PICASAPY_TOUCH_PHOTO_MTIME` értéke kifejezetten „igaz".
    """
    env = os.environ if environ is None else environ
    raw = env.get(TOUCH_ENV_VAR)
    if raw is None:
        return False
    return raw.strip().casefold() in _TRUE_VALUES


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

    Kikapcsolt állapotban (ez az alapértelmezés) azonnal üressel tér vissza,
    tehát a képfájlokat `stat`-tal sem érinti.

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
    if touched:
        # #1320: az éles archívum időbélyegeinek átírása nem lehet néma —
        # a hatásnak látszania kell, hogy a felhasználó tudjon róla.
        _log.info(
            "%d képfájl módosítási idejét írtuk át a(z) %s mappában, mert a "
            "%s=1 kapcsoló be van kapcsolva (#1320). A fájlok tartalma "
            "változatlan.",
            len(touched),
            folder,
            TOUCH_ENV_VAR,
        )
    return tuple(touched)


def notify_picasa_after_ini_write(
    ini_path: Path, before: IniDocument, after: IniDocument
) -> tuple[Path, ...]:
    """Az ini-írás utáni értesítő lépés — az `update_document` közös pontja.

    Összeköti a két felét: kiszámolja, mely fotók rekordja változott, és
    azok képfájljának mtime-ját frissíti. Ez az EGYETLEN hely, ahonnan az
    érintés indul, hogy minden ini-író (szerkesztő, csillag, felirat,
    arcok, kulcsszavak, csoportos effekt, mentés) egyformán viselkedjen.

    **Alapértelmezésben nem csinál semmit** (#1320): a Picasa újraolvasását
    maga az ini kiírása váltja ki, a képfájl megérintése nem része a
    mechanizmusnak. Csak `PICASAPY_TOUCH_PHOTO_MTIME=1` mellett fut le.

    Args:
        ini_path: A most kiírt `.picasa.ini` útja.
        before: A módosítás előtti dokumentum.
        after: A kiírt dokumentum.

    Returns:
        A megérintett képfájlok útjai (üres, ha ki van kapcsolva — ez az
        alapértelmezés).
    """
    if not is_touch_enabled():
        return ()
    changed = changed_photo_sections(before, after)
    if not changed:
        return ()
    return touch_photos(ini_path, changed)
