"""A megőrzött eredeti a képpel EGYÜTT költözik (#1430).

A #371 kutatása kizárta, hogy a Picasa a szerkesztést a képfájlon kívül
bárhol tárolná: a retus és a vörösszem-javítás a JPEG-be van beleégetve.
A „Vissza az eredetihez” EGYETLEN útja tehát a kép mellé mentett, érintetlen
másolat. Ha az elszakad a képtől — mert a képet átneveztük vagy másik
mappába vittük —, a szerkesztés visszafordíthatatlanná válik, és a régi
helyen árván marad egy fájl, amiről már senki nem tudja, kihez tartozik.
Ez a modul a `rename_photo` és a `move_photo` kísérőfájl-logikája.

## Mi költözik

1. A **megőrzött eredeti**: `<mappa>/<originals-mappa>/<fájlnév>`.
2. A **sorszámozott pillanatképek**: `<név>.<N><kiterjesztés>` — mentésenként
   egy, ezek teszik lehetővé az „Utolsó mentés visszavonása” parancsot
   (`edit/save.py`, #444).

Mindkettőt MINDKÉT ismert mappanév alatt keressük (`.picasaoriginals` és a
2009 előtti, látható `Originals` — ld. `edit/save.py` „Két mappanév”,
#1425). A pillanatképeket a spec szerint csak a `.picasaoriginals` tárolja,
de a keresés itt szándékosan szimmetrikus: egy ott mégis fellelhető
pillanatkép elhagyása ugyanolyan visszafordíthatatlan veszteség lenne.

## A mappanév a költözéskor NEM változik

Egy `Originals`-ból induló eredeti a célmappában is `Originals` alá kerül,
nem a `.picasaoriginals`-ba. Két oka van:

* Az `ORIGINALS_DIR_NAMES` sorrendje jelentést hordoz (a régi példány nyer,
  mert az van közelebb az érintetlen eredetihez, #1425). A mappanév
  átírásával ez az információ elveszne.
* Ha a képhez MINDKÉT mappában van példány, az egy célmappába terelés
  ütközést okozna — a kettő közül az egyiket el kellene dobni.

A `.picasaoriginals`-t továbbra is csak a mentés hozza létre újonnan; itt
azért készül el a célmappában, mert egy MÁR MEGLÉVŐ eredetinek kell hely.

## Sorrend és visszagörgetés

Előbb a kísérőfájlok költöznek, és csak utána maga a kép. Így ha a kísérő
költöztetése bukik, a kép el sem indul: a felhasználó felől nézve nem
történt semmi, és a Visszaállítás a régi helyen működik tovább. Ha a KÉP
mozgatása bukik el (verseny egy párhuzamos íróval, tele lemez), az
`originals_follow` visszagörgeti a már elmozdított kísérőket.

Felülírni sosem írunk felül: ha a célhelyen már van azonos nevű fájl (pl.
egy korábbi költözés árvája), a művelet EL SEM INDUL, és a hiba üzenete
megmondja, mi van útban — a néma elutasítás a projekt visszatérő
hibaosztálya (#1003, #1207, #1213).
"""

from __future__ import annotations

import shutil
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class OriginalMove:
    """Egy kísérőfájl (megőrzött eredeti vagy pillanatkép) tervezett útja.

    Attributes:
        source: A kísérőfájl jelenlegi helye.
        target: Ahová a kép költözésével kerülnie kell.
    """

    source: Path
    target: Path


def _originals_dir_names() -> tuple[str, ...]:
    """A megőrzött eredeti ismert mappanevei, a keresési sorrendjükben.

    Késleltetett import: a nevek az `edit.save`-ben élnek (ott az
    igazságforrásuk), az a modul viszont az OpenCV-t is behúzza — ezen a
    gépen mérve 1,8 másodperc, szemben a `fileops` 0,2 másodpercével. A
    `fileops`-ot fájlműveletekhez importáló hívók (és a tesztek) ne
    fizessenek érte. Ugyanezt a mintát követi a `save_controller` is."""
    from picasapy.edit.save import ORIGINALS_DIR_NAMES

    return ORIGINALS_DIR_NAMES


def _snapshot_numbers(directory: Path, photo: Path) -> Iterator[tuple[int, Path]]:
    """A `photo`-hoz tartozó sorszámozott pillanatképek a `directory`-ban.

    A `<név>.<N><kiterjesztés>` névminta (#444) sajnos KÉTÉRTELMŰ: az `a.jpg`
    kép `a.2.jpg` pillanatképe pontosan úgy néz ki, mint egy `a.2.jpg` nevű
    ÖNÁLLÓ kép megőrzött eredetije. Ezért ha a képmappában létezik ilyen nevű
    fájl, a példányt békén hagyjuk — inkább maradjon a helyén, mint hogy egy
    másik kép visszaútját rángassuk el.

    A mappát `iterdir()`-rel járjuk be, nem `glob()`-bal: a fájlnévben lévő
    `[`, `*` vagy `?` a mintában joker lenne, és némán rossz találatokat
    adna.

    A könyvtárlistázás hálózati megosztáson drága (#1146), ezért a
    `find_original_backup` szándékosan kerüli. Itt viszont vállaljuk: a
    pillanatképek száma és sorszáma előre nem ismert, és a költöztetés
    ritka, a felhasználó által kezdeményezett művelet — nem megjelenítési
    útvonal."""
    stem, suffix = photo.stem, photo.suffix
    prefix = f"{stem}."
    for path in directory.iterdir():
        name = path.name
        if not name.startswith(prefix) or not name.endswith(suffix):
            continue
        middle = (
            name[len(prefix) : len(name) - len(suffix)] if suffix else name[len(prefix) :]
        )
        if not middle.isdigit():
            continue
        if (photo.parent / name).exists():
            continue  # egy önálló kép eredetije, nem a mi pillanatképünk
        yield int(middle), path


def originals_slot_free(folder: str | Path, name: str) -> bool:
    """Szabad-e a `name` fájlnév helye a `folder` ÖSSZES eredeti-mappájában.

    A kötegelt áthelyezés ütközés-feloldása (`fileops/batch.py`) ezzel kerüli
    el, hogy egy korábbi költöztetés árván maradt eredetije miatt válasszon
    olyan pótnevet, amivel a művelet aztán elbukna."""
    folder = Path(folder)
    return not any(
        (folder / dir_name / name).exists() for dir_name in _originals_dir_names()
    )


def plan_original_moves(
    source_photo: str | Path, target_photo: str | Path
) -> tuple[OriginalMove, ...]:
    """A kép költözéséhez tartozó kísérőfájl-mozgatások — végrehajtás nélkül.

    Args:
        source_photo: A kép jelenlegi, teljes elérési útja.
        target_photo: A kép leendő, teljes elérési útja (átnevezésnél
            ugyanaz a mappa, mozgatásnál a célmappa).

    Returns:
        A mozgatandó párok; üres, ha a képhez nincs megőrzött eredeti.
    """
    source_photo = Path(source_photo)
    target_photo = Path(target_photo)
    moves: list[OriginalMove] = []
    for dir_name in _originals_dir_names():
        source_dir = source_photo.parent / dir_name
        if not source_dir.is_dir():
            continue
        target_dir = target_photo.parent / dir_name
        backup = source_dir / source_photo.name
        if backup.is_file():
            moves.append(OriginalMove(backup, target_dir / target_photo.name))
        for number, snapshot in sorted(_snapshot_numbers(source_dir, source_photo)):
            new_name = f"{target_photo.stem}.{number}{target_photo.suffix}"
            moves.append(OriginalMove(snapshot, target_dir / new_name))
    return tuple(moves)


def _reject_occupied_targets(moves: Sequence[OriginalMove]) -> None:
    """Ha bármelyik célhely foglalt, a művelet el sem indul.

    Raises:
        FileExistsError: emberi nyelvű üzenettel arról, MI van útban —
            felülírni nem írunk felül, az a másik kép visszaútja lenne.
    """
    for move in moves:
        if not move.target.exists():
            continue
        raise FileExistsError(
            f"A képhez megőrzött eredetit nem lehet átvinni, mert a helyén "
            f"már van egy azonos nevű fájl: {move.target}. Ez valószínűleg "
            f"egy korábbi költöztetés árván maradt fájlja. Semmi nem "
            f"változott: a kép és az eredetije is a régi helyén maradt. "
            f"Ha az útban lévő fájlra nincs szüksége, előbb törölje vagy "
            f"nevezze át a(z) „{move.target.parent.name}” mappában, "
            f"és próbálja újra."
        )


def move_preserved_originals(
    source_photo: str | Path, target_photo: str | Path
) -> tuple[OriginalMove, ...]:
    """A megőrzött eredeti (és a pillanatképek) átköltöztetése.

    A képet MAGÁT nem mozgatja — azt a hívó (`rename_photo`, `move_photo`)
    teszi, közvetlenül utána.

    Args:
        source_photo: A kép jelenlegi, teljes elérési útja.
        target_photo: A kép leendő, teljes elérési útja.

    Returns:
        A ténylegesen végrehajtott mozgatások (a visszagörgetéshez).

    Raises:
        FileExistsError: ha valamelyik célhely foglalt — ilyenkor semmi nem
            mozdult el.
        OSError: ha a másolás/mozgatás fájlrendszer-hibába futott. A már
            elmozdított kísérőket ilyenkor visszatesszük, és a hiba üzenete
            megmondja, hol keresse a felhasználó a fájljait.
    """
    moves = plan_original_moves(source_photo, target_photo)
    if not moves:
        return ()
    _reject_occupied_targets(moves)

    done: list[OriginalMove] = []
    for move in moves:
        try:
            move.target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(move.source), str(move.target))
        except OSError as error:
            stranded = undo_original_moves(tuple(done))
            raise type(error)(
                f"A képhez megőrzött eredetit nem sikerült átvinni ide: "
                f"{move.target} ({error}). A kép nem mozdult el, a "
                f"„Vissza az eredetihez” a régi helyén továbbra is működik."
                f"{_rollback_warning(stranded)}"
            ) from error
        done.append(move)
    return tuple(done)


def undo_original_moves(
    moves: Sequence[OriginalMove],
) -> tuple[OriginalMove, ...]:
    """A már elmozdított kísérőfájlok visszatétele a helyükre.

    Legjobb szándék szerint dolgozik: egy fájl bukása nem akadályozza a
    többi visszatételét.

    Returns:
        Azok a mozgatások, amelyeket NEM sikerült visszacsinálni — a hívó
        ezeket nevezi meg a hibaüzenetében.
    """
    stranded: list[OriginalMove] = []
    for move in reversed(list(moves)):
        try:
            move.source.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(move.target), str(move.source))
        except OSError:
            stranded.append(move)
            continue
        # A célmappában közben létrehozott eredeti-mappa ne maradjon ott
        # üresen — a látható `Originals` egy üres, magyarázat nélküli
        # mappaként tűnne fel a felhasználó fájlkezelőjében. Az `rmdir`
        # csak ÜRES könyvtárat töröl, tehát semmit nem vihet magával.
        try:
            move.target.parent.rmdir()
        except OSError:
            pass
    return tuple(stranded)


def _rollback_warning(stranded: Sequence[OriginalMove]) -> str:
    """Kiegészítő mondat, ha a visszatétel sem sikerült.

    Üres sztring, ha minden visszakerült — ilyenkor a felhasználót nem kell
    olyasmivel terhelni, amit nem kell megoldania."""
    if not stranded:
        return ""
    helyek = ", ".join(str(move.target) for move in stranded)
    return (
        f" Figyelem: a kép megőrzött eredetijét nem sikerült a régi helyére "
        f"visszatenni, itt maradt: {helyek}. A fájl megvan, csak máshol — "
        f"kézzel visszamásolható."
    )


@contextmanager
def originals_follow(
    source_photo: str | Path, target_photo: str | Path
) -> Iterator[None]:
    """A kép mozgatását a megőrzött eredeti költöztetésébe csomagolja.

    Előbb a kísérőfájlok költöznek, majd lefut a blokk (a kép tényleges
    átnevezése/mozgatása). Ha a blokk fájlrendszer-hibával bukik, a kísérőket
    visszagörgetjük, hogy a kép a régi nevén/helyén se veszítse el a
    visszaútját.

    Használat::

        with originals_follow(path, target):
            path.rename(target)
    """
    moved = move_preserved_originals(source_photo, target_photo)
    try:
        yield
    except OSError as error:
        stranded = undo_original_moves(moved)
        warning = _rollback_warning(stranded)
        if warning:
            # A típus megőrzése kötelező: a hívók (FileOpsController,
            # PhotoOpsController) kivételosztály szerint szűrnek, egy új
            # osztály némán kicsúszna a szűrőjükön.
            raise type(error)(f"{error}{warning}") from error
        raise


__all__ = [
    "OriginalMove",
    "move_preserved_originals",
    "originals_follow",
    "originals_slot_free",
    "plan_original_moves",
    "undo_original_moves",
]
