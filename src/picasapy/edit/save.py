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

import cv2
import numpy as np

from picasapy.edit.session import EditSession
from picasapy.ini import IniConflictError, IniSaveError, update_document
from picasapy.ioutil import write_atomic

#: A rejtett almappa neve, ahová az érintetlen eredeti kerül (spec + UX #3).
ORIGINALS_DIR_NAME = ".picasaoriginals"

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
_INI_WRITE_ERRORS = (OSError, IniSaveError, IniConflictError)

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
    backup_path = _backup_path_for(image_path)

    # A (b) lépés ELŐTTI bájtok — ezekre kell visszaállni, ha a (c) elbukik
    # (#297). Első mentésnél ez maga az eredeti (ugyanaz, ami a
    # `.picasaoriginals`-ba kerül), ismételt mentésnél a KORÁBBI mentés
    # renderelt tartalma.
    bytes_before_write = image_path.read_bytes()

    # (a) Az eredeti megőrzése — KIZÁRÓLAG ha még nincs korábbi mentésből.
    backup_created_now = not backup_path.exists()
    if backup_created_now:
        write_atomic(backup_path, bytes_before_write, make_parents=True)

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
                .with_value(_section_name(image_path), _REDO_KEY, redo_value)
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


def revert(image_path: str | Path) -> RevertResult:
    """A "Visszaállítás": az eredeti visszamásolása a `.picasaoriginals`-ból.

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
        SaveError: ha a `.picasaoriginals`-ban nincs mentett eredeti (a kép
            még sosem lett `save_edited`-del elmentve).
    """
    image_path = Path(image_path)
    backup_path = _backup_path_for(image_path)
    if not backup_path.exists():
        raise SaveError(
            f"Nincs elérhető eredeti-mentés ehhez a képhez: {image_path} "
            f"(hiányzik: {backup_path}) — a Visszaállítás csak korábban "
            f"elmentett (save_edited-en átment) képnél lehetséges."
        )

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


def _backup_path_for(image_path: Path) -> Path:
    """A kép `.picasaoriginals`-beli, várt biztonsági-mentés útja."""
    return image_path.parent / ORIGINALS_DIR_NAME / image_path.name


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
    ok, encoded = cv2.imencode(ext, image, params)
    if not ok:
        raise SaveError(f"A renderelt kép nem kódolható ide: {ext!r}")
    return encoded.tobytes()
