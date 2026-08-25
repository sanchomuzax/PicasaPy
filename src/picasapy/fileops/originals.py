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
hibaosztálya (#1003, #1207, #1213). A tanács attól függ, KIÉ az útban lévő
fájl: ha egy másik, ÉLŐ kép eredetije, a törlését tanácsolni pont azt a kárt
okozná, amit ez a modul megelőzni hivatott (`_occupied_message`).

## A megnyugtatás feltételes

Ha a visszagörgetés IS elbukik, a „minden a helyén maradt" mondat HAMIS
lenne, és a következménye nem kozmetikai: a `find_original_backup` a kép
mellett ilyenkor nem talál eredetit, az `edit/save.py` pedig
`existing_backup is None` mellett a MÁR SZERKESZTETT bájtokat írja be új
„eredetiként". A megnyugtatott felhasználó egyetlen mentéssel véglegesen
elveszítené az érintetlen változatot — ezért a `_stranded_warning` ilyenkor
azt mondja meg, mit NE tegyen (`_reassurance` csak üres `stranded` mellett
szólalhat meg).

A hibaüzenetek a KÖTEGELT úton is kimennek: a felületen az áthelyezés mindig
a `movePhotos`-t hívja, ezért a `FileOpsController` a `batchFinished`-del az
első bukás okát is átadja (#1430).
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
        # `isdecimal()`, nem `isdigit()`: az utóbbi átengedi a `²`-t és
        # társait, amiken az `int()` `ValueError`-t dob — az a felhasználó
        # felé olvashatatlan angol hibaüzenetként bukna ki.
        if not middle.isdecimal():
            continue
        if (photo.parent / name).exists():
            continue  # egy önálló kép eredetije, nem a mi pillanatképünk
        # A sorszám SZÖVEGÉT is visszaadjuk, nem csak a számértékét: a
        # célnévben szó szerint megtartjuk (ld. `plan_original_moves`).
        yield int(middle), middle, path


def originals_slot_free(folder: str | Path, name: str) -> bool:
    """Szabad-e a `name` fájlnév helye a `folder` ÖSSZES eredeti-mappájában.

    „Szabad" az, ahol sem a megőrzött eredeti, sem EGYETLEN sorszámozott
    pillanatkép helye nincs elfoglalva — a kettő együtt költözik, tehát a
    kettő közül bármelyik ütközése megbuktatná a műveletet.

    A kötegelt áthelyezés ütközés-feloldása (`fileops/batch.py`) ezzel kerüli
    el, hogy egy korábbi költöztetés árván maradt fájlja miatt válasszon
    olyan pótnevet, amivel a művelet aztán elbukna.

    Szándékosan óvatos: ha a mappában van a névhez illő pillanatkép-hely, a
    nevet akkor is foglaltnak mondjuk, ha a költöző képnek éppen nincs
    pillanatképe. A tévedés iránya így egy másik pótnév — nem egy bukott
    művelet."""
    folder = Path(folder)
    photo = folder / name
    for dir_name in _originals_dir_names():
        directory = folder / dir_name
        if not directory.is_dir():
            continue
        if (directory / name).exists():
            return False
        if next(_snapshot_numbers(directory, photo), None) is not None:
            return False
    return True


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
        for _, sorszam, snapshot in sorted(
            _snapshot_numbers(source_dir, source_photo)
        ):
            # A sorszám SZÖVEGÉT visszük át, nem a számértékét: `a.01.jpg`
            # így `b.01.jpg` lesz, nem `b.1.jpg`. Az átszámozás összeejtené
            # az `a.1.jpg`-t és az `a.01.jpg`-t ugyanarra a célnévre, és a
            # `shutil.move` POSIX-on NÉMÁN felülírja a másikat.
            new_name = f"{target_photo.stem}.{sorszam}{target_photo.suffix}"
            moves.append(OriginalMove(snapshot, target_dir / new_name))
    return tuple(moves)


def _reject_unsafe_targets(moves: Sequence[OriginalMove]) -> None:
    """A terv ellenőrzése MIELŐTT bármi elmozdulna: felülírni sosem írunk
    felül, se meglévő fájlt, se a saját tervünk másik elemét.

    Raises:
        FileExistsError: emberi nyelvű üzenettel arról, MI van útban.
    """
    latott: dict[Path, OriginalMove] = {}
    for move in moves:
        elozo = latott.get(move.target)
        if elozo is not None:
            # A `plan_original_moves` a sorszámot szó szerint viszi át, ezért
            # ez ma nem fordulhat elő. Az őr mégis marad: ha valaha
            # visszakerülne az átszámozás, ez a sor állítja meg — nem a
            # felhasználó adatvesztése.
            raise FileExistsError(
                f"A képhez két megőrzött változat is ugyanarra a névre "
                f"költözne ({elozo.source.name} és {move.source.name} → "
                f"{move.target.name}), így az egyik felülírná a másikat. "
                f"Semmi nem változott: a kép és a megőrzött változatai is a "
                f"régi helyükön maradtak."
            )
        latott[move.target] = move
        if move.target.exists():
            raise FileExistsError(_occupied_message(move))


def _occupied_message(move: OriginalMove) -> str:
    """Az „útban van egy fájl" üzenet — a tanács attól függ, KIÉ az a fájl.

    Az eredeti-mappában lévő fájl lehet egy MÁSIK, élő kép saját megőrzött
    eredetije (a `<név>.<N>` névminta kétértelműsége miatt ez valódi eset).
    Annak a törlését tanácsolni pont azt a kárt okozná, amit ez a modul
    megelőzni hivatott — ezért előbb megnézzük, van-e a képmappában ilyen
    nevű, élő kép."""
    kep_mappa = move.target.parent.parent
    gazda = kep_mappa / move.target.name
    fej = (
        f"A képhez megőrzött eredeti változatot nem lehet a helyére tenni, mert "
        f"ott "
        f"már van egy azonos nevű fájl: {move.target}. Semmi nem változott: "
        f"a kép és a megőrzött változatai is a régi helyükön maradtak. "
    )
    if gazda.exists():
        return fej + (
            f"Ez a fájl a(z) {gazda.name} nevű képhez tartozik, annak az "
            f"eredeti változata — NE törölje, mert azzal annak a képnek a "
            f"visszaútját semmisítené meg. Adjon inkább a képnek másik "
            f"nevet, vagy válasszon másik célmappát."
        )
    return fej + (
        f"Ez valószínűleg egy korábbi költöztetés árván maradt fájlja: nincs "
        f"a(z) {kep_mappa} mappában {move.target.name} nevű kép, amihez "
        f"tartozhatna. Ha nincs rá szüksége, törölje vagy nevezze át a(z) "
        f"„{move.target.parent.name}” mappában, és próbálja újra."
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
    _reject_unsafe_targets(moves)

    done: list[OriginalMove] = []
    for move in moves:
        try:
            move.target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(move.source), str(move.target))
        except OSError as error:
            stranded = undo_original_moves(tuple(done))
            # A célmappa itt akkor is takarítandó, ha a `done` ÜRES (mindjárt
            # az első kísérőnél buktunk): a `mkdir` már lefutott, és egy üres,
            # a legacy esetben LÁTHATÓ `Originals/` maradna a felhasználó
            # célmappájában — miközben az üzenet azt mondja, semmi nem
            # változott.
            _remove_if_empty(move.target.parent)
            raise type(error)(
                f"A képhez megőrzött eredeti változatot nem sikerült átvinni ide: "
                f"{move.target} ({error})."
                f"{_stranded_warning(stranded) or _reassurance()}"
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
        # mappaként tűnne fel a felhasználó fájlkezelőjében.
        _remove_if_empty(move.target.parent)
    return tuple(stranded)


def _remove_if_empty(directory: Path) -> None:
    """Üres eredeti-mappa eltakarítása. Az `rmdir` csak ÜRES könyvtárat
    töröl, tehát semmit nem vihet magával."""
    try:
        directory.rmdir()
    except OSError:
        pass


def _reassurance() -> str:
    """A megnyugtató zárómondat — KIZÁRÓLAG akkor mondható ki, ha minden
    megőrzött változat a kép mellett maradt."""
    return (
        " A kép nem mozdult el, és a megőrzött változatai is a helyükön "
        "vannak: a „Vissza az eredetihez” továbbra is működik."
    )


def _stranded_warning(stranded: Sequence[OriginalMove]) -> str:
    """A figyelmeztetés, ha a visszatétel IS elbukott. Üres sztring, ha
    minden visszakerült.

    Itt a megnyugtatás HAZUGSÁG lenne, és a kár nem kozmetikai: a
    `find_original_backup` a kép mellett ilyenkor nem talál eredetit, az
    `edit/save.py` pedig `existing_backup is None` mellett a MÁR
    SZERKESZTETT bájtokat írja be új „eredetiként". A megnyugtatott
    felhasználó egyetlen mentéssel véglegesen elveszítené az érintetlen
    változatot — ezért a legfontosabb mondanivaló az, hogy MIT NE tegyen."""
    if not stranded:
        return ""
    helyek = ", ".join(str(move.target) for move in stranded)
    honnan = ", ".join(str(move.source) for move in stranded)
    return (
        f" FIGYELEM: a kép megőrzött változatát nem sikerült a helyére "
        f"visszatenni, itt maradt: {helyek}. Amíg nincs a kép mellett, a "
        f"„Vissza az eredetihez” nem talál semmit, és ha ÚJRA MENTI a képet, "
        f"a program a mostani, szerkesztett állapotot fogja eredetinek "
        f"tekinteni — az érintetlen változat véglegesen elveszne. Ne mentse "
        f"újra a képet, amíg ezt a fájlt kézzel vissza nem másolta ide: "
        f"{honnan}."
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
        warning = _stranded_warning(stranded)
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
