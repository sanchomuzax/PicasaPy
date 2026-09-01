"""Nem-destruktív mentés / Visszaállítás (#21) — a Picasa "Mentés" viselkedése.

A UX 3. alapelve („Észrevétlen eredeti-megőrzés", `docs/specs/ux-principles.md`):
a felhasználó sosem lát verziókáoszt, és nincs kötelező export-lépés. Mentéskor:

1. Az EREDETI (a mentés pillanatában a lemezen lévő, még "szűz" — a jelen
   mentés által még nem érintett) fájl bájtjai ELSŐ alkalommal átkerülnek a
   kép melletti rejtett `.picasaoriginals/` almappába. Ha ott már van egy
   korábbi mentésből (a képet már egyszer elmentettük), NEM írjuk felül: az
   ELSŐ eredeti a szent példány — ez garantálja, hogy több egymást követő
   mentés se veszítse el a "valódi" eredetit.
2. A renderelt (a szerkesztési lánc beleégetésével kapott — a RENDERELÉS a
   HÍVÓ feladata, ez a modul csak a perzisztenciát végzi) kép az EREDETI
   fájl HELYÉRE kerül: a felhasználó a fájlkezelőben ugyanazt a fájlnevet
   látja, csak a tartalma frissült.
3. A `.picasa.ini`-ben a `redo=` kulcs kapja meg a MOST elmentett
   szerkesztési láncot (a `filters=`-szel azonos szintaxisban — a spec
   táblázata szerint: "`redo=crop64=1,...;` — visszavonási (redo) verem,
   megőrzendő!"), a `filters=` kulcsot pedig TÖRÖLJÜK: a lánc már be van
   égetve a pixelekbe, ha `filters=` bent maradna, a következő megnyitáskor
   a renderelő KÉTSZER alkalmazná (dupla-szerkesztés hiba). Az `originhash`
   frissül (ld. lent); a `backuphash` és minden más, nem ismert kulcs
   ÉRINTETLEN marad — kizárólag a round-trip réteg (`update_document`/
   `with_value`/`with_removed`) útján írunk, ahogy a spec 2., 4. írási
   szabálya előírja.

Ha a 3. lépés elbukik (ütközés a párhuzamosan futó Picasával, tele lemez,
zárolt ini), a 2. lépést VISSZAVONJUK: a képfájl visszakapja a mentés
előtti bájtjait (#297). Enélkül a kép a beégetett szerkesztést tartalmazná,
miközben a `filters=` bent maradt az ini-ben — a következő megnyitáskor a
renderelő MÁSODSZOR is ráfuttatná a láncot. Ugyanez a védelem a `revert`-nél
fordított irányban: ott a kulcsok törlésének bukásakor a szerkesztett kép
íródik vissza.

## `originhash` — dokumentált, józan döntés (2026-07-23, #21)

A specifikáció (`docs/specs/picasa-ini-format.md`, `[<fájlnév.ext>]` tábla)
az `originhash`-t „szerkesztési verem integritás-hash"-ként írja le, KONKRÉT
ALGORITMUS NÉLKÜL — ez nem publikus, a valódi Picasa binárisából nem lett
visszafejtve (ld. `docs/research-plan.md` nyitott kérdései). PicasaPy-döntés:
az `originhash` a MOST mentett `redo=` érték SHA-256 hexdigestje
(`sha256(redo_érték UTF-8 bájtjai)`) — azaz magának a megőrzött szerkesztési
veremnek az integritását fedezi, ami a legszorosabban megfelel a
specifikáció szövegének ("szerkesztési verem integritás-hash").

**FONTOS:** ezt a felhasználónak egy valódi Picasa 3.x által írt
`.picasa.ini`-mintán ellenőriznie kell (pl. Wine alatt lefuttatott mentés
összevetésével) — ha eltérés derül ki a tényleges Picasa-algoritmustól, az
egyetlen érintett függvény a `_compute_originhash`.

## Két mappanév: `.picasaoriginals` és `Originals` (#1425)

A Picasa a szerkesztés előtti eredetit **két, időben elváló néven** tárolta
(`docs/specs/picasa-ini-format.md`, „Az eredeti képek mentése — KÉT
elnevezés, verzióváltással"; 181 valós mappa, *megerősített*):

| mappanév | darab a korpuszban | évek |
|---|---:|---|
| `Originals` (látható) | 127 | 2005–2009 |
| `.picasaoriginals` (rejtett) | 54 | 2009–2016 |

A #371 kutatása kizárta, hogy a retus/vörösszem régió-adata bárhol
tárolódna: a javítás a mentett képbe van beleégetve, tehát a Visszaállítás
EGYETLEN útja a megőrzött eredeti fájl. A régi név ismerete nélkül a
tulajdonos 127 mappányi eredetijéhez nem tudnánk visszatérni, ezért az
`ORIGINALS_DIR_NAMES` sorrendjében **mindkettőt** megnézzük.

**SAJÁT FUNKCIÓ (#1425):** ütközéskor — ha ugyanahhoz a képhez MINDKÉT
mappában van példány — a régi, `Originals` nyer. Ez **nem mérés**: arra,
hogy az eredeti Picasa mit tesz ilyenkor, nincs bizonyítékunk (a korpusz
csak `.picasa.ini`-szövegeket tartalmaz, és `Originals/` alatt egyetlen ini
sincs — az a név rajta van a Picasa saját kizárási listáján, ezért oda
sosem írt). A döntés két megfontoláson áll:

1. **Időrend.** A két név nem keveredik: az `Originals`-beli példány
   szükségképpen a korábbi, tehát közelebb van az érintetlen eredetihez.
   A `.picasaoriginals`-beli ilyenkor a 2005–2009 közötti szerkesztéseket
   MÁR beégetve tartalmazza.
2. **A hiba iránya.** Az újabbat választva a felhasználó egy részlegesen
   visszaállított képet kapna, **némán** — pont az, amit a Visszaállítás
   ígérete kizár. A régebbit választva „minden változás elvész", ami a
   művelet kimondott szerződése.

Ugyanez a szabály védi a mentést is: ha bármelyik mappában MÁR van
megőrzött eredeti, a `save_edited` **nem tesz mellé másodikat** — különben
az első PicasaPy-mentés egy `Originals`-os mappában a már szerkesztett
bájtokat írná a `.picasaoriginals`-ba, és (ha valaha megfordulna a
sorrend) a valódi eredeti elérhetetlenné válna.

**A sorszámozott pillanatképek (`undo_save`) KIZÁRÓLAG a
`.picasaoriginals`-ban élnek.** Ezek a MI mentéseink melléktermékei, és a
`undo_save` a felhasznált pillanatképet TÖRLI — a látható, Picasa-korabeli
`Originals` mappában fájlt törölni nem szabad.

## `.picasaoriginals` accent-path-tolerancia

A MEMORY.md #190-es tanulsága szerint a `cv2.imwrite`/`cv2.imread`
Windowson ékezetes útvonalon NÉMÁN nem ír/olvas. Ez a modul ezért SOHA nem
hív `cv2.imwrite`-ot vagy `cv2.imread`-et: az eredeti biztonsági mentés
nyers `Path.read_bytes`/`write_atomic` bájt-másolás (nincs újrakódolás,
bitre pontos), a renderelt kép írása pedig `cv2.imencode` (memóriapuffer,
NEM fájlútvonal-paraméteres) + `write_atomic` — pontosan az
`export/exporter.py`-ban már bevált mintát követve.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from picasapy import cv as cv2
import numpy as np

from picasapy.edit.session import EditSession
from picasapy.ini import (
    FilterWriteError,
    IniConflictError,
    IniSaveError,
    load_document,
    update_document,
)
from picasapy.scanner import PICASA_INI_NAME
from picasapy.ioutil import write_atomic

#: A rejtett almappa neve, ahová az ÚJ mentéseink érintetlen eredetije kerül
#: (spec + UX #3). Írni MINDIG ide írunk.
ORIGINALS_DIR_NAME = ".picasaoriginals"

#: A 2009 ELŐTTI Picasa-verziók LÁTHATÓ mappaneve ugyanerre a célra (#1425).
#: Csak OLVASSUK — a tulajdonos gyűjteményében élesben előfordul.
LEGACY_ORIGINALS_DIR_NAME = "Originals"

#: A megőrzött eredeti KERESÉSI SORRENDJE — az első találat nyer.
#: A régi, `Originals` áll elöl; az indoklás a modul „Két mappanév”
#: szakaszában.
ORIGINALS_DIR_NAMES = (LEGACY_ORIGINALS_DIR_NAME, ORIGINALS_DIR_NAME)

# A mentéskor/visszaállításkor érintett ini-kulcsok — a redo verem és a
# hozzá tartozó integritás-hash a szerkesztési lánc állapotát tükrözi; a
# `filters=` a pixelekbe égetés után törlendő (ld. modul docstring).
_FILTERS_KEY = "filters"
_REDO_KEY = "redo"
_ORIGINHASH_KEY = "originhash"
_EDIT_BOOKKEEPING_KEYS = (_FILTERS_KEY, _REDO_KEY, _ORIGINHASH_KEY)

_INI_FILENAME = ".picasa.ini"

# Az ini-könyvelés kezelt hibái (#297): a fájlrendszeré (`OSError`: tele
# lemez, zárolt fájl), a kódolásé (`IniSaveError`) és a párhuzamosan futó
# eredeti Picasa tartós ütközése (`IniConflictError`).
#
# #643: a round-trip őr visszautasítása (`FilterWriteError`) itt NEM csak
# üzenet-kérdés, hanem ADATVÉDELEM. Ha a `redo=`/`filters=` átforgatása
# elbukik, a képfájl ekkor MÁR a beégetett szerkesztést tartalmazza, az
# ini viszont a régi állapotot — a következő megnyitáskor a lánc másodszor
# is lefutna (dupla-szerkesztés, #297). Enélkül a kivétel a `_restore_
# image_or_raise` MELLETT szökött volna ki, visszaállítás nélkül.
_INI_WRITE_ERRORS = (OSError, IniSaveError, IniConflictError, FilterWriteError)

# JPEG-nél a mentés-minőség alapértéke magas (a felhasználó explicit
# "Mentés" szándékát tükrözi — a nem-destruktív elv ELLENÉRE ez a pillanat
# fizikailag lecseréli a fájlt, tehát a minőségvesztés minimalizálandó).
_DEFAULT_JPEG_QUALITY = 95


class SaveError(RuntimeError):
    """Mentés vagy visszaállítás nem hajtható végre.

    Pl. a renderelt kép nem kódolható a cél formátumba, vagy a
    `.picasaoriginals`-ban nincs elérhető eredeti a Visszaállításhoz.
    """


@dataclass(frozen=True)
class SaveResult:
    """A `save_edited` eredménye: mely fájlok/ini-kulcsok íródtak.

    Attributes:
        image_path: A (felülírt) kép útja.
        original_backup_path: A `.picasaoriginals`-beli eredeti útja.
        backup_created_now: True, ha ELSŐ mentés volt (most jött létre az
            eredeti-mentés); False, ha egy korábbi mentésből származó
            eredeti már megvolt (és ezért nem íródott felül).
        redo_value: A `.picasa.ini`-be írt `redo=` érték.
        originhash: A `.picasa.ini`-be írt `originhash` érték.
    """

    image_path: Path
    original_backup_path: Path
    backup_created_now: bool
    redo_value: str
    originhash: str


@dataclass(frozen=True)
class RevertResult:
    """A `revert` eredménye: honnan állt vissza a kép, mely kulcsok törlődtek."""

    image_path: Path
    restored_from: Path
    removed_keys: tuple[str, ...]


def save_edited(
    image_path: str | Path,
    rendered_image: np.ndarray,
    filters: EditSession,
    *,
    jpeg_quality: int = _DEFAULT_JPEG_QUALITY,
) -> SaveResult:
    """A nem-destruktív "Mentés": a renderelt kép az eredeti helyére kerül.

    Args:
        image_path: A kép jelenlegi, fizikai elérési útja a mappában (a
            `.picasa.ini` mellette, a szülőkönyvtárban van).
        rendered_image: A szerkesztési lánc beleégetésével kapott
            képmátrix, OpenCV BGR-konvencióban (ahogy a render/export
            modulok is használják) — a RENDERELÉS a hívó feladata, ez a
            függvény csak a perzisztenciát és az ini-könyvelést végzi.
        filters: A MOST mentett szerkesztési lánc (`EditSession`); ennek
            szerializált értéke kerül a `redo=` kulcsba.
        jpeg_quality: JPEG-minőség (csak `.jpg`/`.jpeg` célútnál számít).

    Returns:
        `SaveResult` a végrehajtott lépések adataival.

    Raises:
        SaveError: ha a renderelt kép nem kódolható a cél kiterjesztésbe,
            vagy ha az ini-hiba utáni képfájl-visszaállítás sem sikerült
            (#297 — ekkor a kép és az ini nyilvántartása eltér).
        OSError | IniSaveError | IniConflictError: ha az ini-könyvelés nem
            sikerült. A képfájl ilyenkor VISSZAÁLL a mentés előtti
            állapotra, hogy ne maradjon dupla-szerkesztés (#297).
    """
    image_path = Path(image_path)
    # #1425: a „szent" eredeti bármelyik ismert mappanév alatt ott lehet —
    # ha van, azt tekintjük megőrzöttnek, és nem teszünk mellé másodikat.
    existing_backup = find_original_backup(image_path)
    backup_path = existing_backup or _backup_path_for(image_path)

    # A (b) lépés ELŐTTI bájtok — ezekre kell visszaállni, ha a (c) elbukik
    # (#297). Első mentésnél ez maga az eredeti (ugyanaz, ami a
    # `.picasaoriginals`-ba kerül), ismételt mentésnél a KORÁBBI mentés
    # renderelt tartalma.
    bytes_before_write = image_path.read_bytes()

    # (a) Az eredeti megőrzése — KIZÁRÓLAG ha még nincs korábbi mentésből
    # (sem a mai, sem a 2009 előtti nevű mappában).
    backup_created_now = existing_backup is None
    if backup_created_now:
        write_atomic(backup_path, bytes_before_write, make_parents=True)

    # (a2) #444: MENTÉSENKÉNTI, sorszámozott pillanatkép a mentés ELŐTTI
    # bájtokról — ez teszi visszavonhatóvá az utolsó mentést a szerkesztések
    # elvesztése nélkül (`undo_save`). A „szent" eredeti (fent) ettől
    # függetlenül megmarad a Visszaállításhoz.
    snapshots = _existing_snapshots(image_path)
    next_number = (snapshots[-1][0] + 1) if snapshots else 1
    write_atomic(
        _snapshot_path(image_path, next_number), bytes_before_write, make_parents=True
    )

    # (b) A renderelt kép az eredeti HELYÉRE.
    payload = _encode_image(image_path.suffix, rendered_image, jpeg_quality)
    write_atomic(image_path, payload)

    # (c) `.picasa.ini`: redo/originhash frissítése, filters törlése.
    redo_value = filters.to_value()
    originhash = _compute_originhash(redo_value)
    try:
        _update_ini_document(
            image_path,
            lambda document: (
                document.with_removed(_section_name(image_path), _FILTERS_KEY)
                # #643: a `filters=` lánc ÁTFORGATÁSA a `redo=`-ba — átvitt
                # tartalom, nem most keletkező tag (ld. `ini.filter_guard`).
                .with_value(
                    _section_name(image_path), _REDO_KEY, redo_value, carried=True
                )
                .with_value(_section_name(image_path), _ORIGINHASH_KEY, originhash)
            ),
        )
    except _INI_WRITE_ERRORS as error:
        # #297: a kép ekkor már a beégetett szerkesztést tartalmazza, de a
        # `filters=` bent maradt az ini-ben — a következő megnyitáskor a
        # renderelő MÁSODSZOR is ráfuttatná a láncot (dupla-szerkesztés).
        # A két állapot csak úgy marad összhangban, ha a képet visszaállítjuk.
        _restore_image_or_raise(image_path, bytes_before_write, backup_path, error)
        raise

    return SaveResult(
        image_path=image_path,
        original_backup_path=backup_path,
        backup_created_now=backup_created_now,
        redo_value=redo_value,
        originhash=originhash,
    )


@dataclass(frozen=True)
class UndoSaveResult:
    """Az `undo_save` eredménye (#444)."""

    image_path: Path
    restored_from: Path
    #: a visszaadott szerkesztési lánc (a `redo=`-ból a `filters=`-be)
    restored_filters: str


def undo_save(image_path: str | Path) -> UndoSaveResult:
    """„Utolsó mentés visszavonása" — a SZERKESZTÉSEK MEGMARADNAK (#444).

    Ez a Picasa négy mentés-műveletéből a köztes fokozat, és élesen KÜLÖNBÖZIK
    a `revert`-től:

    * `revert` — a kép visszaáll a „szent" eredetire, és a szerkesztési
      könyvelés is törlődik: *„This cannot be undone and all changes will be
      lost."*
    * `undo_save` — csak az UTOLSÓ lemezre írást vonja vissza: a kép a mentés
      előtti bájtjait kapja vissza, a mentéskor `redo=`-ba tett lánc pedig
      visszakerül `filters=`-be. Az eredeti szavakkal: *„To undo the last
      save and keep edits click 'Undo Save'."*

    A mentés előtti bájtok a mentésenként készülő, sorszámozott
    pillanatképből jönnek (`_snapshot_path`); a felhasznált pillanatkép a
    művelet végén törlődik, így többszöri hívás lépésenként halad visszafelé.

    Raises:
        SaveError: ha nincs visszavonható mentés (nincs pillanatkép).
    """
    image_path = Path(image_path)
    snapshots = _existing_snapshots(image_path)
    if not snapshots:
        raise SaveError(
            f"Nincs visszavonható mentés: {image_path.name} "
            f"({ORIGINALS_DIR_NAME} üres vagy hiányzik)"
        )
    number, snapshot = snapshots[-1]
    del number

    section = _section_name(image_path)
    document = load_document(image_path.parent / PICASA_INI_NAME)
    stored = document.section(section)
    restored_filters = (stored.get(_REDO_KEY) or "") if stored else ""

    bytes_before = image_path.read_bytes()
    write_atomic(image_path, snapshot.read_bytes())
    try:
        _update_ini_document(
            image_path,
            lambda doc: (
                # #643: a `redo=`-ból VISSZAforgatott lánc — átvitt tartalom.
                doc.with_value(section, _FILTERS_KEY, restored_filters, carried=True)
                if restored_filters
                else doc.with_removed(section, _FILTERS_KEY)
            )
            .with_removed(section, _REDO_KEY)
            .with_removed(section, _ORIGINHASH_KEY),
        )
    except _INI_WRITE_ERRORS as error:
        # #297 mintája: ha a könyvelés elbukik, a képfájl is álljon vissza —
        # különben a kép a mentés ELŐTTI állapotban lenne, de az ini a
        # mentés utánit hinné (a lánc kétszer futna a következő nyitáskor).
        _restore_image_or_raise(image_path, bytes_before, snapshot, error)
        raise

    snapshot.unlink(missing_ok=True)
    return UndoSaveResult(
        image_path=image_path,
        restored_from=snapshot,
        restored_filters=restored_filters,
    )


def revert(image_path: str | Path) -> RevertResult:
    """A "Visszaállítás": a megőrzött eredeti visszamásolása.

    Az eredetit MINDKÉT ismert mappanév alatt keresi (`.picasaoriginals` és
    a 2009 előtti `Originals` — ld. a modul „Két mappanév" szakaszát), és a
    `RevertResult.restored_from` megmondja, melyikből dolgozott (#1425).

    A korábbi szerkesztés-könyvelést (`filters=`, `redo=`, `originhash`) az
    ini-ből törli — a fájl a szerkesztés ELŐTTI állapotba kerül vissza,
    a nem-technikai felhasználó elvárása szerint: "vissza az eredetihez".
    Minden más ini-kulcs (csillag, felirat, arcok, albumok, `backuphash`,
    ismeretlen mezők) érintetlen marad.

    Args:
        image_path: A kép jelenlegi, fizikai elérési útja a mappában.

    Returns:
        `RevertResult` a visszaállítás adataival.

    Raises:
        SaveError: ha egyik ismert mappában sincs megőrzött eredeti — az
            üzenet a felhasználónak szól, és megnevezi mindkét mappát
            (`_missing_original_message`).
    """
    image_path = Path(image_path)
    backup_path = find_original_backup(image_path)
    if backup_path is None:
        raise SaveError(_missing_original_message(image_path))

    # A visszaállítás ELŐTTI (szerkesztett) bájtok — ezekre kell visszaállni,
    # ha az ini-kulcsok törlése elbukik (#297, fordított irányú rés). Ha a
    # képfájl közben eltűnt, nincs mire visszaállni: ilyenkor a `revert`
    # pótolja a fájlt, és hiba esetén ott is hagyja.
    edited_bytes = image_path.read_bytes() if image_path.exists() else None

    original_bytes = backup_path.read_bytes()
    write_atomic(image_path, original_bytes)

    section = _section_name(image_path)

    def _mutate(document):
        for key in _EDIT_BOOKKEEPING_KEYS:
            document = document.with_removed(section, key)
        return document

    try:
        _update_ini_document(image_path, _mutate)
    except _INI_WRITE_ERRORS as error:
        # A kép már az eredeti, de az ini szerint még szerkesztett — a
        # következő megnyitáskor a `redo=`/`filters=` alapján hamis állapot
        # látszana. Visszaírjuk a szerkesztett képet, és továbbdobjuk a hibát.
        if edited_bytes is not None:
            _restore_image_or_raise(image_path, edited_bytes, backup_path, error)
        raise

    return RevertResult(
        image_path=image_path,
        restored_from=backup_path,
        removed_keys=_EDIT_BOOKKEEPING_KEYS,
    )


def _restore_image_or_raise(
    image_path: Path, payload: bytes, backup_path: Path, error: Exception
) -> None:
    """A képfájl visszaállítása a művelet előtti bájtokra (#297).

    Ha maga a visszaállítás is elbukik, `SaveError`-t emel: a felhasználónak
    magyarul, cselekvésre fordíthatóan meg kell tudnia, hogy a kép fizikailag
    elmentődött, a `.picasa.ini` nyilvántartása viszont nem követte — így
    tudja, hogy a kép a következő megnyitáskor kétszer szerkesztettnek
    látszhat, és hol keresse az eredetit."""
    try:
        write_atomic(image_path, payload)
    except OSError as restore_error:
        raise SaveError(
            f"A kép elmentődött ({image_path}), de a .picasa.ini "
            f"nyilvántartása nem frissült ({error}), és a kép mentés előtti "
            f"állapotát sem sikerült visszaállítani ({restore_error}). A kép "
            f"a következő megnyitáskor kétszer szerkesztettnek látszhat; az "
            f"érintetlen eredeti itt található: {backup_path} "
            f"(a(z) {ORIGINALS_DIR_NAME} mappában)."
        ) from error


def find_original_backup(image_path: str | Path) -> Path | None:
    """A képhez megőrzött eredeti — MINDKÉT mappanevet megnézve (#1425).

    Az `ORIGINALS_DIR_NAMES` sorrendjében keres (régi `Originals` előbb, ld.
    a modul „Két mappanév" szakaszát), és az első meglévő fájl útját adja
    vissza. Ha egyik mappában sincs példány, `None`.

    Csak a KÉT ismert nevet nézi meg, kis-nagybetű pontosan, és nem listázza
    ki a mappát: képenként így legfeljebb két `stat()` — a #1146 tanulsága
    szerint a tulajdonos gyűjteménye hálózati megosztáson él, ahol minden
    fölösleges könyvtárlistázás egy hálózati kör.
    """
    image_path = Path(image_path)
    for dir_name in ORIGINALS_DIR_NAMES:
        candidate = image_path.parent / dir_name / image_path.name
        if candidate.is_file():
            return candidate
    return None


def _missing_original_message(image_path: Path) -> str:
    """A „nincs megőrzött eredeti" ÉRTHETŐ üzenete (#1425).

    A néma elutasítás a projekt visszatérő hibaosztálya (#1003, #1207,
    #1213): a felhasználónak — aki nem programozó — meg kell tudnia, MIT
    kerestünk, HOL, és mikor működik egyáltalán a Visszaállítás. Belső
    függvénynevek nem szivároghatnak ki ide.
    """
    mappak = " és ".join(f"„{name}”" for name in ORIGINALS_DIR_NAMES)
    return (
        f"Ehhez a képhez nincs megőrzött eredeti: {image_path.name}. "
        f"A kép melletti {mappak} nevű almappák egyikében sem találtuk meg "
        f"a mentés előtti változatát. A Visszaállítás csak olyan képnél "
        f"működik, amelyről készült ilyen másolat — a PicasaPy és a Picasa "
        f"is az első mentéskor készíti el. "
        f"(Keresett hely: {image_path.parent})"
    )


def _backup_path_for(image_path: Path) -> Path:
    """Ahová egy ÚJ eredeti-mentés kerül: mindig a `.picasaoriginals`.

    A régi, `Originals` mappát csak OLVASSUK (ld. `find_original_backup`) —
    a Picasa-korabeli, látható mappába nem írunk.
    """
    return image_path.parent / ORIGINALS_DIR_NAME / image_path.name


def _snapshot_path(image_path: Path, number: int) -> Path:
    """A `<név>.<N><kiterjesztés>` alakú, MENTÉSENKÉNTI pillanatkép útja.

    #444: a Picasa binárisában a `.picasaoriginals` névmintája `%s.%d.jpg`
    (`.mov`, `.wmv`) — vagyis a „szent" eredeti MELLETT mentésenként külön,
    SORSZÁMOZOTT másolat is készül. Ez teszi lehetővé az „Utolsó mentés
    visszavonása" parancsot (`undo_save`): az utolsó mentés visszavonható
    úgy, hogy a SZERKESZTÉSEK MEGMARADNAK.
    """
    directory = image_path.parent / ORIGINALS_DIR_NAME
    return directory / f"{image_path.stem}.{number}{image_path.suffix}"


def _existing_snapshots(image_path: Path) -> list[tuple[int, Path]]:
    """A meglévő sorszámozott pillanatképek `(N, útvonal)` párjai, növekvő
    sorrendben. Hibás (nem szám) sorszámú fájlt figyelmen kívül hagy."""
    directory = image_path.parent / ORIGINALS_DIR_NAME
    if not directory.is_dir():
        return []
    found: list[tuple[int, Path]] = []
    for path in directory.glob(f"{image_path.stem}.*{image_path.suffix}"):
        middle = path.name[len(image_path.stem) + 1 : -len(image_path.suffix)]
        if middle.isdigit():
            found.append((int(middle), path))
    return sorted(found)


def _section_name(image_path: Path) -> str:
    """A `.picasa.ini`-beli szekciónév: a fájl neve, a spec `[<fájlnév.ext>]`
    szabálya szerint (ld. `picasa-ini-format.md`)."""
    return image_path.name


def _update_ini_document(image_path: Path, mutate) -> None:
    """Ütközésbiztos, atomikus, backup-olt ini-frissítés (#137-minta).

    Kizárólag a round-trip réteget (`update_document`) hívja — soha nem ír
    közvetlenül fájlba —, hogy az ismeretlen kulcsok/szekciók bitre pontosan
    megmaradjanak (spec 2. írási szabálya)."""
    ini_path = image_path.parent / _INI_FILENAME
    update_document(ini_path, mutate, backup=True)


def _compute_originhash(redo_value: str) -> str:
    """A szerkesztési verem (`redo=`) integritás-hash-e.

    Ld. a modul docstring "originhash" szakaszát a döntés indoklásához — a
    spec az algoritmust nem rögzíti, ez egy dokumentált, ellenőrzendő
    józan döntés."""
    return hashlib.sha256(redo_value.encode("utf-8")).hexdigest()


def _encode_image(suffix: str, image: np.ndarray, jpeg_quality: int) -> bytes:
    """A renderelt képmátrix kódolása a cél kiterjesztésének megfelelő
    formátumba — `cv2.imencode`-dal (memóriapuffer, nem fájlútvonal),
    accent-path-biztosan (MEMORY.md #190)."""
    ext = suffix.lower() or ".jpg"
    params: list[int] = []
    if ext in (".jpg", ".jpeg"):
        params = [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality]
    # #1527: az OpenCV NEM mindig `ok=False`-szal jelez. Ismeretlen
    # kiterjesztésnél `cv2.error`-t DOB („could not find encoder for the
    # specified extension"), ami eddig NYERSEN szökött ki a mentésből — a
    # `save_controller._SAVE_ERRORS` sem fogta, mert a `cv2.error` nem
    # `OSError`/`ValueError`. Ez a hivatalos „fájlformázási hiba" ága
    # (`CFileSaveThread:filesaveerr3`), tehát ide `SaveError` való.
    try:
        ok, encoded = cv2.imencode(ext, image, params)
    except cv2.error as hiba:
        raise SaveError(f"A renderelt kép nem kódolható ide: {ext!r}") from hiba
    if not ok:
        raise SaveError(f"A renderelt kép nem kódolható ide: {ext!r}")
    return encoded.tobytes()
