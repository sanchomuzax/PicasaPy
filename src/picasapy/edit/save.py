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
from picasapy.ini import update_document
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
        SaveError: ha a renderelt kép nem kódolható a cél kiterjesztésbe.
        OSError: alacsony szintű fájlrendszer-hiba (pl. tele lemez) —
            a hívók felől ez is jelzésértékű, nem nyeljük el csendben.
    """
    image_path = Path(image_path)
    backup_path = _backup_path_for(image_path)

    # (a) Az eredeti megőrzése — KIZÁRÓLAG ha még nincs korábbi mentésből.
    backup_created_now = not backup_path.exists()
    if backup_created_now:
        original_bytes = image_path.read_bytes()
        write_atomic(backup_path, original_bytes, make_parents=True)

    # (b) A renderelt kép az eredeti HELYÉRE.
    payload = _encode_image(image_path.suffix, rendered_image, jpeg_quality)
    write_atomic(image_path, payload)

    # (c) `.picasa.ini`: redo/originhash frissítése, filters törlése.
    redo_value = filters.to_value()
    originhash = _compute_originhash(redo_value)
    _update_ini_document(
        image_path,
        lambda document: (
            document.with_removed(_section_name(image_path), _FILTERS_KEY)
            .with_value(_section_name(image_path), _REDO_KEY, redo_value)
            .with_value(_section_name(image_path), _ORIGINHASH_KEY, originhash)
        ),
    )

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

    original_bytes = backup_path.read_bytes()
    write_atomic(image_path, original_bytes)

    section = _section_name(image_path)

    def _mutate(document):
        for key in _EDIT_BOOKKEEPING_KEYS:
            document = document.with_removed(section, key)
        return document

    _update_ini_document(image_path, _mutate)

    return RevertResult(
        image_path=image_path,
        restored_from=backup_path,
        removed_keys=_EDIT_BOOKKEEPING_KEYS,
    )


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
