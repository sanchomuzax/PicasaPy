"""#1527: „Mentés másként…" és „Másolat mentése" — a másolatkészítő mag.

A `save.py` a fájlt a HELYÉRE írja vissza (biztonsági másolattal); ez a
modul ennek a testvére: a renderelt képet **új fájlba** teszi, a forráshoz
hozzá sem nyúlva.

## A két parancs különbsége — MÉRVE, nem következtetve

A jegy (#1527) kimondja, hogy ezt nem mérte, és tiltja a nevekből való
következtetést. A mérés (bináris-index `xrefs` + helyi diszasszemblálás,
`referencia/eszkozok/binaris/annot_disasm.py`):

* A parancs-diszpécser `0x005cb990` **ugyanazt** a `0x005e6a20` függvényt
  hívja mindkét menüpontra (`call_count = 2`).
* A függvény egyetlen bájt-paraméterre ágazik:
  `0x005e6b6a  cmp byte ptr [esp+0x14d4], bl` → `je 0x5e6bb1`.

| ág | mit tesz |
|---|---|
| param **== 0** — `Mentés másként…` | szűrőlistát épít (`JPEG Files`/`*.jpg`, és ha a forrás WebP, `WebP Files`/`*.webp`), **fájlválasztót nyit** (`0x0097f1d0`: `"SaveFile"`, `"ytApp::JPEGFilter"`, `"Preferences"`), majd elutasítja, ha a cél a forrás (`IDS_CANT_SAVE_TO_SAME`), és megnézi, létezik-e (`0x00992ed0`, `"Exists"`) |
| param **!= 0** — `Másolat mentése` | `call 0x00993650`, aminek EGYETLEN sztringje **`%s-%03lu`**, majd `jmp 0x5e6f24`: **átugorja** a fájlválasztót és az azonosság-ellenőrzést |

⇒ a másolat neve `kep.jpg` → **`kep-001.jpg`**, ütközésnél `-002`, …
A feliratok is ezt támasztják alá: `Save &As...` **ellipszissel** (párbeszéd
következik), `Save a Cop&y` **anélkül** (azonnali művelet).

Mindkét ág a cél mappájának `.picasa.ini`-jén (`0x005e6f33`) és a KÖZÖS
hibaüzeneten (`CThumbUI::FileSaveCopy:err`) fut át.

## Amit a mérés NEM ad — dokumentált döntés

Hogy a cél `.picasa.ini`-jébe pontosan mely kulcsok kerülnek, a
sztringekből nem derül ki (`0x005aafd0` nem tartalmaz kulcsnevet).
**Döntés (nem mérés):** a másolat a `save_edited`-del azonos könyvelést
kap — `redo=` + `originhash` —, mert a lánc a pixelekbe van égetve;
`filters=`-t odaírni dupla-szerkesztés volna (#297). A FORRÁS fájlja és
ini-bejegyzése érintetlen marad.

**Mi döntené el:** egy valódi Picasa 3.9-cel készített „Másolat mentése"
kimenet mellé exportált `.picasa.ini` (a `MEMORY.md` „Referencia-export a
windowsos Picasából" lapja szerinti kérés).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from picasapy.edit.save import (
    SaveError,
    _compute_originhash,
    _encode_image,
    _section_name,
    _update_ini_document,
)
from picasapy.edit.session import EditSession
from picasapy.ioutil import write_atomic

#: A másolat nevének mintája — MÉRT: a `0x00993650` egyetlen sztringje
#: `"%s-%03lu"` (tő, majd kötőjel és HÁROM jegyű, nullákkal feltöltött
#: sorszám). A kiterjesztés a forrásé marad.
COPY_NAME_PATTERN = "{stem}-{number:03d}{suffix}"

#: Ennyi sorszámot próbálunk végig, mielőtt feladjuk. A minta három jegyű,
#: de a `%03lu` nem VÁGJA a számot — csak feltölti —, ezért a felső korlát
#: nem 999. Ez a szám a végtelen ciklus elleni vészfék, nem formátum-szabály.
_MAX_COPY_NUMBER = 100_000


class FileNameCollisionError(SaveError):
    """A cél nem írható: már létezik, vagy azonos a forrással.

    A felület KÉT hivatalos üzenete tartozik hozzá — a hívó dönti el,
    melyik illik a helyzethez:

    * `CFileSaveThread:filesaveerr2` — „A fájl mentése nem lehetséges.
      Már van ilyen nevű fájl."
    * `IDS_CANT_SAVE_TO_SAME` — „A képet nem lehet kicserélni. Próbálja
      újra másik fájlnévvel."

    Külön kivétel-osztály, mert ez az EGYETLEN ág, ahol a felhasználó
    fájlját néma felülírás fenyegetné (#1527 adatbiztonsági pont).
    """


@dataclass(frozen=True)
class SaveCopyResult:
    """A `save_copy` eredménye."""

    source_path: Path
    target_path: Path
    #: a cél `.picasa.ini`-jébe írt `redo=` érték
    redo_value: str
    originhash: str


def next_copy_path(image_path: str | Path) -> Path:
    """A „Másolat mentése" MÉRT célútvonala: `<tő>-001.<kit>`, szabadig.

    A `%s-%03lu` mintát követi (ld. modul-docstring). Ha a `-001` már
    foglalt, `-002`, és így tovább — a meglévő fájlt SOHA nem javasolja.
    """
    image_path = Path(image_path)
    folder = image_path.parent
    for number in range(1, _MAX_COPY_NUMBER + 1):
        candidate = folder / COPY_NAME_PATTERN.format(
            stem=image_path.stem, number=number, suffix=image_path.suffix
        )
        if not candidate.exists():
            return candidate
    raise FileNameCollisionError(
        f"Nem található szabad másolat-név ehhez: {image_path.name}"
    )


def save_copy(
    image_path: str | Path,
    rendered_image: np.ndarray,
    filters: EditSession,
    *,
    target_path: str | Path | None = None,
    jpeg_quality: int = 95,
) -> SaveCopyResult:
    """A renderelt kép ÚJ fájlba mentése; a forrás érintetlen marad.

    Args:
        image_path: a forráskép útja (a `.picasa.ini` mellette van).
        rendered_image: a szerkesztési lánc beégetésével kapott mátrix,
            OpenCV BGR-ben — a renderelés a hívó dolga, ahogy a
            `save_edited`-nél is.
        filters: a beégetett lánc; szerializált értéke a cél `redo=`-jába
            kerül.
        target_path: `None` esetén a MÉRT `-001` minta adja („Másolat
            mentése"); megadva a felhasználó választotta út („Mentés
            másként…", fájlválasztóból).
        jpeg_quality: JPEG-minőség a cél kiterjesztéséhez.

    Raises:
        FileNameCollisionError: ha a cél már létezik, vagy azonos a
            forrással. **Felülírás soha nincs** — a hívónak kell másik
            nevet kérnie a felhasználótól.
        SaveError: ha a kép nem kódolható a cél kiterjesztésébe
            (`filesaveerr3`, fájlformázási hiba).
        OSError | IniSaveError | IniConflictError: lemezhiba vagy
            ini-ütközés (`filesaveerr-win`). Ilyenkor a MÁR kiírt
            célfájlt eltávolítjuk: fél-kész másolat ne maradjon a
            gyűjteményben, ini-bejegyzés nélkül.
    """
    image_path = Path(image_path)
    target = Path(target_path) if target_path is not None else next_copy_path(image_path)

    # ⚠️ #1527 adatbiztonság: NÉMA FELÜLÍRÁS SOHA. Két külön ok, két külön
    # hivatalos üzenet a felületen — a kivétel ugyanaz, a hívó választja
    # az üzenetet a `target == source` összehasonlításból.
    if target.resolve() == image_path.resolve():
        raise FileNameCollisionError(
            f"A cél azonos a forrással: {image_path.name}"
        )
    if target.exists():
        raise FileNameCollisionError(f"Már van ilyen nevű fájl: {target.name}")

    # A kódolás ELŐBB fut, mint bármilyen írás: fájlformázási hibánál
    # (`filesaveerr3`) így egyetlen bájt sem kerül a lemezre.
    payload = _encode_image(target.suffix, rendered_image, jpeg_quality)

    redo_value = filters.to_value()
    originhash = _compute_originhash(redo_value)

    write_atomic(target, payload, make_parents=True)
    try:
        _update_ini_document(
            target,
            lambda document: document.with_value(
                # #643: a lánc ÁTVITT tartalom (a forrás `filters=`-éből
                # jön), nem most keletkező tag — a round-trip őr ezt a
                # `carried=True` jelzésből tudja.
                _section_name(target),
                "redo",
                redo_value,
                carried=True,
            ).with_value(_section_name(target), "originhash", originhash),
        )
    except BaseException:
        # A cél fájl MÁR kint van, az ini-könyvelés viszont elbukott. A
        # `save_edited` ilyenkor visszaállítja az EREDETI bájtokat; itt
        # nincs mit visszaállítani, tehát a fél-kész másolatot töröljük —
        # különben egy könyveletlen fájl maradna a gyűjteményben, amit a
        # felhasználó a következő indexeléskor valódi képként látna.
        target.unlink(missing_ok=True)
        raise

    return SaveCopyResult(
        source_path=image_path,
        target_path=target,
        redo_value=redo_value,
        originhash=originhash,
    )
