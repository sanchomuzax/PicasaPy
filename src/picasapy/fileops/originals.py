"""A megőrzött eredeti a képpel EGYÜTT költözik (#1430).

A #371 kutatása kizárta, hogy a Picasa a szerkesztést a képfájlon kívül
bárhol tárolná: a retus és a vörösszem-javítás a JPEG-be van beleégetve.
A „Vissza az eredetihez” EGYETLEN útja tehát a kép mellé mentett, érintetlen
másolat. Ha az elszakad a képtől — mert a képet átneveztük vagy másik
mappába vittük —, a szerkesztés visszafordíthatatlanná válik, és a régi
helyen árván marad egy fájl, amiről már senki nem tudja, kihez tartozik.
Ez a modul a kísérőfájl-logika: a `rename_photo` és a `move_photo`
mozgatása (#1430), a `copy_photo` másolása (#1450), valamint a törlés
leltára (`companions_of`, #1451). Az ini-szekcióik a testvérmodulban
költöznek (`original_ini.py`, #1448).

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

## Ütközés: a kötegelt úton FELOLDJUK, egyébként MEGMAGYARÁZZUK

Felülírni sosem írunk felül: ha a célhelyen már van azonos nevű fájl (pl.
egy korábbi költözés árvája), a művelet EL SEM INDUL, és a hiba üzenete
megmondja, mi van útban — a néma elutasítás a projekt visszatérő
hibaosztálya (#1003, #1207, #1213). A tanács attól függ, KIÉ az útban lévő
fájl: ha egy másik, ÉLŐ kép eredetije, a törlését tanácsolni pont azt a kárt
okozná, amit ez a modul megelőzni hivatott (`_occupied_message`).

A KÖTEGELT áthelyezés (`fileops/batch.py`) viszont ide el sem jut, és ez
TUDATOS döntés (#1448 2. átnézés, 1. lelet): ott a felhasználó a művelet
indításakor KIMONDOTTAN az „átnevezés" házirendet választotta, ezért a
foglalt eredeti-hely nem megállítja a képet, hanem pótnevet ad neki
(`originals_slot_free` → `batch._free_name`). A hibaüzenet tanácsa — „adjon
inkább a képnek másik nevet" — épp az, amit a pótnév automatikusan megtesz,
és közben a célban álló idegen fájlhoz nem nyúlunk: a másik kép eredetije
és a mi pillanatképünk is a saját, ütközésmentes nevén marad. A magyarázó
üzenet így az F2-es átnevezésé, a másolásé és az egyfájlos mozgatásé marad
— azoké az utaké, ahol nincs mit feloldani, mert a nevet a felhasználó adta
meg.

Mindez arra a képre vonatkozik, amelyiknek VAN megőrzött eredetije: kísérő
nélkül nincs mit elhelyezni, ott a kötegelt út csak az ÖRÖKBEFOGADÁS ellen
őriz (`originals_slot_free(..., moving_companions=False)`, #2510) — a
foglaltnak látszó, de valójában gazdás pillanatkép-hely miatt korábban
fölösleges ütközés-párbeszéd és néma átnevezés lett belőle.

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
első bukás okát is átadja (#1430). Amit a pótnév nem old fel
(fájlrendszer-hiba, verseny egy párhuzamos íróval), annak az oka így a
kötegelt úton is eljut a felhasználóig.
"""

from __future__ import annotations

import os
import shutil
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # a futásidejű import késleltetett (ld. `_move_ini_sections`)
    from picasapy.fileops.original_ini import IniSectionCopy, IniSectionMove

#: A `shutil.move` MODULSZINTŰ fogantyúja (#1375) — a teszt EZT cserélje.
#:
#: A `"picasapy.fileops.originals.shutil.move"` sztringes rögzítés a GLOBÁLIS
#: `shutil`-t írja át, tehát a „bukjon el a mozgatás" szimuláció a teszt
#: minden más mozgatását is elrontja — a takarítást is.
_move = shutil.move

#: A `shutil.copy2` MODULSZINTŰ fogantyúja (#1450) — ugyanaz a gondolat.
#:
#: `copy2`, nem `copy`: a megőrzött eredeti mtime-ja a WYSIWYG dátum
#: forrása, és a Picasa a rekord érvényességét is a `moddate`-hez méri.
_copy = shutil.copy2

#: A kísérő-mappák neveinek gyorstára EGY kötegelt művelet idejére (#1452).
#:
#: `None`, amíg senki nem nyitott `listing_cache()` hatókört — ilyenkor
#: minden olvasás friss listázás, pontosan úgy, mint korábban. A
#: `ContextVar` (és nem modulszintű dict) azért kell, mert a felület a
#: kötegelt műveleteket munkaszálon is futtathatja: minden szál SAJÁT,
#: üres kontextussal indul, tehát nem örökli meg egy másik szál félkész
#: gyorstárát.
_LISTINGS: ContextVar[dict[str, list[str]] | None] = ContextVar(
    "picasapy_originals_listings", default=None
)


@contextmanager
def listing_cache() -> Iterator[None]:
    """A kísérő-mappákat MAPPÁNKÉNT EGYSZER listázza a hatókörön belül (#1452).

    Mit old meg: a kötegelt áthelyezés képenként KÉT teljes
    könyvtárlistázást végzett — egyet a célmappa eredeti-mappáira
    (`originals_slot_free`), egyet a forráséira (`plan_original_moves`).
    500 képnél ez 999 listázás volt. A gyűjtemény NAS-on van, mért
    napló-korláttal (#1146), ahol egy listázás drága.

    Hogyan marad PONTOS: a gyorstár nem „elévül", hanem KÖNYVELT. Ez a
    modul minden saját mozgatását/másolását/törlését azonnal átvezeti a
    tárolt névlistán (`_moved`, `_copied`, `_discarded`,
    `_remove_if_empty`), tehát a hatókörön belül a listák együtt mozognak
    a lemezzel. Amit a modul NEM ír — a `.picasa.ini` és a `.bak` párja —,
    az a keresésben sem vesz részt: a pillanatkép-minta a kép
    törzsnevével kezdődik (`<név>.<N><kiterjesztés>`), a foglaltság-
    vizsgálat pedig a konkrét névre `exists()`-tel kérdez, nem a listából.

    Egy PÁRHUZAMOS író (a futó Picasa) közbeírását a hatókörön belül nem
    látjuk — de a művelet enélkül is versenyzik vele, és a tényleges
    ütközést a `_reject_unsafe_targets` közvetlenül a mozgatás előtt
    ellenőrzi, friss `exists()`-tel.

    A hatókört a kötegelt út nyitja (`fileops/batch.py`); az egyfájlos
    utak nélküle futnak, ott nincs mit megtakarítani.
    """
    token = _LISTINGS.set({})
    try:
        yield
    finally:
        _LISTINGS.reset(token)


def _read_names(directory: Path) -> list[str]:
    """A könyvtár bejegyzéseinek NEVE; üres lista, ha nem olvasható.

    `os.scandir`, nem `iterdir()`: ugyanaz a rendszerhívás, de nem
    gyártunk `Path`-t minden bejegyzéshez — a 250 000 fájlos gyűjteményben
    ez a kötegelt úton mérhető."""
    try:
        with os.scandir(directory) as entries:
            return [entry.name for entry in entries]
    except OSError:
        return []


def _entry_names(directory: Path) -> tuple[str, ...]:
    """A könyvtár bejegyzés-nevei, a `listing_cache()` hatókörén belül
    mappánként EGYETLEN listázásból (#1452)."""
    cache = _LISTINGS.get()
    if cache is None:
        return tuple(_read_names(directory))
    key = str(directory)
    names = cache.get(key)
    if names is None:
        names = _read_names(directory)
        cache[key] = names
    return tuple(names)


def _cache_added(directory: Path, name: str) -> None:
    """Új név a mappában — a gyorstár együtt mozog a lemezzel."""
    cache = _LISTINGS.get()
    if cache is None:
        return
    names = cache.get(str(directory))
    if names is not None and name not in names:
        names.append(name)


def _cache_removed(directory: Path, name: str) -> None:
    """Eltűnt név a mappában."""
    cache = _LISTINGS.get()
    if cache is None:
        return
    names = cache.get(str(directory))
    if names is not None and name in names:
        names.remove(name)


def _cache_unknown(directory: Path) -> None:
    """A mappa tartalma bizonytalanná vált (félbemaradt írás) — a következő
    kérdésre ismét listázzunk. Az elfelejtés SOSEM ad rossz választ, csak
    egy listázásba kerül."""
    cache = _LISTINGS.get()
    if cache is not None:
        cache.pop(str(directory), None)


def _moved(source: Path, target: Path) -> None:
    """A kísérőfájl mozgatása + a gyorstár könyvelése (#1452)."""
    try:
        _move(str(source), str(target))
    except BaseException:
        # Nem tudjuk, meddig jutott — a két mappa tartalma bizonytalan.
        _cache_unknown(source.parent)
        _cache_unknown(target.parent)
        raise
    _cache_removed(source.parent, source.name)
    _cache_added(target.parent, target.name)


def _copied(source: Path, target: Path) -> None:
    """A kísérőfájl másolása + a gyorstár könyvelése (#1452)."""
    try:
        _copy(str(source), str(target))
    except BaseException:
        _cache_unknown(target.parent)
        raise
    _cache_added(target.parent, target.name)


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


def snapshot_numbers(
    directory: Path, photo: Path
) -> Iterator[tuple[int, str, Path]]:
    """A `photo`-hoz tartozó sorszámozott pillanatképek a `directory`-ban.

    Ez a KÖZÖS keresési szabály (#1449): az `edit/save.py` is ezt hívja, hogy
    a kettő ne csússzon szét. Ott korábban `glob()` volt, joker-szennyezéssel
    és az idegen-eredeti védelem nélkül; az „Utolsó mentés visszavonása" így
    egy `IMG[1].jpg` nevű képnél némán rossz fájlt talált, sőt egy MÁSIK kép
    megőrzött eredetijét is törölhette.

    A `<név>.<N><kiterjesztés>` névminta (#444) sajnos KÉTÉRTELMŰ: az `a.jpg`
    kép `a.2.jpg` pillanatképe pontosan úgy néz ki, mint egy `a.2.jpg` nevű
    ÖNÁLLÓ kép megőrzött eredetije. Ezért ha a képmappában létezik ilyen nevű
    fájl, a példányt békén hagyjuk — inkább maradjon a helyén, mint hogy egy
    másik kép visszaútját rángassuk el.

    A mappát LISTÁZZUK, nem `glob()`-bal keresünk: a fájlnévben lévő `[`,
    `*` vagy `?` a mintában joker lenne, és némán rossz találatokat adna.

    A könyvtárlistázás hálózati megosztáson drága (#1146), ezért a
    `find_original_backup` szándékosan kerüli. Itt viszont vállaljuk: a
    pillanatképek száma és sorszáma előre nem ismert, és a költöztetés
    ritka, a felhasználó által kezdeményezett művelet — nem megjelenítési
    útvonal. A KÖTEGELT úton a `listing_cache()` mappánként egyetlen
    listázásra fogja össze (#1452).

    Yields:
        `(sorszám, a sorszám SZÖVEGE, útvonal)` hármasok, rendezetlenül.
    """
    for szam, szoveg, path in _snapshot_candidates(directory, photo):
        if (photo.parent / path.name).exists():
            continue  # egy önálló kép eredetije, nem a mi pillanatképünk
        yield szam, szoveg, path


def _snapshot_candidates(
    directory: Path, photo: Path
) -> Iterator[tuple[int, str, Path]]:
    """A `<név>.<N><kiterjesztés>` NÉVMINTÁRA illő fájlok — gazda-szűrés nélkül.

    A névminta kétértelmű: egy találat lehet a mi pillanatképünk, de lehet
    egy azonos nevű, ÖNÁLLÓ kép megőrzött eredetije is. A két fogyasztó
    ezért különbözőképp szűr rá:

    * a `snapshot_numbers` (amivel dolgozunk: mozgatjuk, töröljük,
      visszaállítjuk) a gazdás találatot KIHAGYJA — idegen kép visszaútját
      nem rángatjuk el (#1449);
    * az `originals_slot_free` (ami csak azt kérdezi, SZABAD-E a hely) a
      gazdás találatot is foglaltnak mondja — ott ugyanis fizikailag áll egy
      fájl, amire a `_reject_unsafe_targets` dobna (#1450 átnézés, 4. lelet).

    Yields:
        `(sorszám, a sorszám SZÖVEGE, útvonal)` hármasok, rendezetlenül. A
        sorszám SZÖVEGE is kell, nem csak a számértéke: a célnévben szó
        szerint megtartjuk (ld. `plan_original_moves`).
    """
    stem, suffix = photo.stem, photo.suffix
    prefix = f"{stem}."
    for name in _entry_names(directory):
        if not name.startswith(prefix) or not name.endswith(suffix):
            continue
        path = directory / name
        middle = (
            name[len(prefix) : len(name) - len(suffix)] if suffix else name[len(prefix) :]
        )
        # `isdecimal()`, nem `isdigit()`: az utóbbi átengedi a `²`-t és
        # társait, amiken az `int()` `ValueError`-t dob — az a felhasználó
        # felé olvashatatlan angol hibaüzenetként bukna ki.
        if not middle.isdecimal():
            continue
        yield int(middle), middle, path


def ambiguous_snapshot_names(directory: Path, photo: Path) -> tuple[str, ...]:
    """A `photo` pillanatkép-nevein álló, de GAZDÁS példányok nevei.

    Ezeket a `snapshot_numbers` szándékosan kihagyja (#1449): a
    `<név>.<N><kiterjesztés>` alak egy önálló kép megőrzött eredetije is
    lehet, és az `undo_save` a felhasznált pillanatképet TÖRLI.

    Az óvatosság ára viszont KIMONDANDÓ: az `undo_save` ilyenkor „nincs
    visszavonható mentés"-t jelentett, holott a mappában áll a képhez illő
    példány — csak nem dönthető el, kié (#1449 átnézés, 3. lelet). Az
    üzenet ebből a listából nevezi meg, MI a kétértelmű.

    Returns:
        A fájlnevek, ábécésorrendben; üres, ha nincs ilyen.
    """
    return tuple(
        sorted(
            path.name
            for _, _, path in _snapshot_candidates(directory, photo)
            if (photo.parent / path.name).exists()
        )
    )


def originals_slot_free(
    folder: str | Path, name: str, *, moving_companions: bool = True
) -> bool:
    """Szabad-e a `name` fájlnév helye a `folder` ÖSSZES eredeti-mappájában.

    „Szabad" az, ahol sem a megőrzött eredeti, sem EGYETLEN sorszámozott
    pillanatkép helye nincs elfoglalva.

    A hívók KÉT KÜLÖNBÖZŐ kérdést tesznek fel ezzel, és a válasz nem
    ugyanaz — ezt mondja ki a `moving_companions` (#2510):

    * `True` (alapértelmezés) — „el tudom-e HELYEZNI ide a kép kísérőit?".
      Ilyenkor a `_snapshot_candidates` halmaza számít: minden névre illő
      fájl foglal, még az is, amelyiknek a képmappában GAZDÁJA van. Az
      utóbbi kihagyása azt jelentené, hogy „szabadnak" mondunk egy helyet,
      amire a `_reject_unsafe_targets` aztán `FileExistsError`-t dob — a
      másolás elbukott ahelyett, hogy a `_unique_target` másik nevet
      választott volna (#1450 átnézés, 4. lelet). A tévedés iránya így egy
      másik pótnév, nem egy bukott művelet.

    * `False` — „ÖRÖKÖLNE-E a képem itt idegen adatot?". A kísérő nélküli
      kép nem helyez el semmit, tehát a placement-ütközés nem érdekli; az
      viszont igen, hogy a célnéven áll-e olyan fájl, amit a
      `find_original_backup` (vagy a pillanatkép-kereső) MÁR AZ Ő
      eredetijének látna. A gazdás példány itt nem számít: annak a
      `snapshot_numbers` szerint van gazdája, tehát a mi képünk nem
      örökölné (#1449).

    A kettő közti különbség NEM elméleti. A kötegelt áthelyezés a bővebb
    halmazt kérdezte kísérő nélküli képnél is, és ezért fölösleges
    ütközést jelentett, majd némán átnevezett (#2510 reprodukció). A
    szűkebb halmaz elhagyása viszont adatvesztés lenne: a kép NÉMÁN
    ÖRÖKBE FOGADNÁ az ott heverő árva eredetit, és a „Vissza az
    eredetihez" egy vadidegen kép bájtjait tenné a helyére.
    """
    folder = Path(folder)
    photo = folder / name
    for dir_name in _originals_dir_names():
        directory = folder / dir_name
        if not directory.is_dir():
            continue
        if (directory / name).exists():
            return False
        jeloltek = (
            _snapshot_candidates(directory, photo)
            if moving_companions
            else snapshot_numbers(directory, photo)
        )
        if next(iter(jeloltek), None) is not None:
            return False
    return True


def companions_of(photo: str | Path) -> tuple[Path, ...]:
    """A képhez tartozó ÖSSZES kísérőfájl: a megőrzött eredeti és a
    sorszámozott pillanatképek, mindkét ismert mappanév alatt.

    A törlés (#1451) és a forrástörléssel járó import (#1450) használja: ami
    a képpel költözik, annak a képpel EGYÜTT is kell tűnnie. Ha ott marad,
    láthatatlanul gyűlik (teljes méretű JPEG-ek egy rejtett mappában), és a
    következő, azonos nevű kép **egy idegen kép eredetijét örökli**.

    Returns:
        A létező kísérőfájlok, keresési sorrendben; üres, ha nincs egy sem.
    """
    photo = Path(photo)
    found: list[Path] = []
    for dir_name in _originals_dir_names():
        directory = photo.parent / dir_name
        if not directory.is_dir():
            continue
        backup = directory / photo.name
        if backup.is_file():
            found.append(backup)
        for _, _, snapshot in sorted(snapshot_numbers(directory, photo)):
            found.append(snapshot)
    return tuple(found)


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
            snapshot_numbers(source_dir, source_photo)
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
    nevű, élő kép.

    MELYIK ÚTON hangzik el: az F2-es átnevezésén, a másolásén és az
    egyfájlos mozgatásén — ahol a nevet a felhasználó adta meg, tehát ő is
    tudja megváltoztatni. A kötegelt áthelyezés az „átnevezés" házirenddel
    pótnevet keres helyette (ld. a modul docstringjét); ott ez az üzenet
    csak akkor szólal meg, ha a hely a pótnév-keresés ÓTA lett foglalt."""
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
    return _move_preserved_originals(source_photo, target_photo)[0]


def _move_preserved_originals(
    source_photo: str | Path, target_photo: str | Path
) -> tuple[tuple[OriginalMove, ...], tuple["IniSectionMove", ...]]:
    """A `move_preserved_originals` MAGJA — a megtett ini-lépéseket is adja.

    A visszagörgetés (`originals_follow`) ezekből dolgozik, és KIZÁRÓLAG
    ezekből: a fájlállapotból következtető őr a soha-nem-is-volt szekciót
    „elmentnek" hitte, és a cél inijéből rántott át egy azonos nevű, ÁRVA
    szekciót (#1448 átnézés, 1. lelet).

    Returns:
        `(megtett fájlmozgatások, megtett ini-szekció-költözések)`.
    """
    moves = plan_original_moves(source_photo, target_photo)
    if not moves:
        return (), ()
    _reject_unsafe_targets(moves)

    done: list[OriginalMove] = []
    for move in moves:
        try:
            move.target.parent.mkdir(parents=True, exist_ok=True)
            _moved(move.source, move.target)
        except OSError as error:
            # Az ini-fázis el sem indult, tehát nincs szekció-lépés, amit
            # vissza kellene venni.
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

    # #1448: a fájlok után a `.picasa.ini` szekcióik is átköltöznek. Azért
    # UTÓLAG, mert így az ini-írás a már véglegesített fájlállapotot
    # könyveli; ha viszont ELBUKIK, mindent visszagörgetünk — egy fél
    # költözés (fájl az új helyen, szekció a régiben) pont az a néma
    # eltérés, amit ez a jegy megszüntet.
    from picasapy.fileops.original_ini import IniSectionsFailed

    try:
        ini_done = _move_ini_sections(done)
    except Exception as error:  # noqa: BLE001 — az ini-réteg többféle hibát dob
        # A MÁR átvitt szekciókat a kivétel hozza magával — a fájlállapotból
        # kikövetkeztetni őket NEM lehet (#1448 átnézés, 1. lelet).
        ini_stranded = _undo_ini_sections(
            error.done if isinstance(error, IniSectionsFailed) else ()
        )
        stranded = undo_original_moves(tuple(done))
        raise OSError(
            f"A képhez megőrzött eredeti beállításait nem sikerült átvinni "
            f"({error})."
            f"{_stranded_warning(stranded)}"
            f"{_ini_stranded_warning(ini_stranded)}"
            f"{_reassurance() if not stranded and not ini_stranded else ''}"
        ) from error
    return tuple(done), ini_done


def _move_ini_sections(
    moves: Sequence[OriginalMove],
) -> tuple["IniSectionMove", ...]:
    """A kísérőfájlok ini-szekcióinak átvitele (#1448).

    Késleltetett import: a `original_ini` az `ini/` csomagot húzza be, amire
    a puszta fájlmozgatás nem szorul rá.

    Returns:
        A ténylegesen megtett szekció-költözések — a visszagörgetés
        EGYETLEN forrása. Korábban ez az érték a padlóra esett, és a
        visszagörgetés a fájlállapotból következtetett; ld. az
        `_undo_ini_sections` docstringjét.
    """
    from picasapy.fileops.original_ini import move_original_ini_sections

    return move_original_ini_sections(
        tuple((move.source, move.target) for move in moves)
    )


def _undo_ini_sections(
    moves: Sequence["IniSectionMove"],
) -> tuple["IniSectionMove", ...]:
    """A MEGTETT ini-szekció-költözések visszavitele (#1448).

    Kizárólag a `_move_ini_sections` által visszaadott listából dolgozik.
    A korábbi változat a fájlállapotból következtetett („ha a szekció már
    nincs a forrásban, akkor elment"), ami a gyakori esetet — hogy soha nem
    is volt ott szekció — átengedte, és a CÉL inijéből rántott át egy
    azonos nevű, ÁRVA szekciót a forrásba (#1448 átnézés, 1. lelet).

    Legjobb szándék szerint dolgozik: a visszatétel bukása nem akadályozhatja
    meg a FÁJLOK visszagörgetését — az a fontosabb, azon múlik a kép
    visszaútja.

    Returns:
        Amit NEM sikerült visszatenni. Ez az érték korábban a padlóra esett,
        és a felhasználó a „minden a helyén maradt" mondatot kapta, miközben
        a beállításai a célmappában ragadtak (#1448 2. átnézés, 3. lelet).
    """
    if not moves:
        return ()
    from picasapy.fileops.original_ini import undo_original_ini_sections

    return undo_original_ini_sections(tuple(moves))


def copy_preserved_originals(
    source_photo: str | Path, target_photo: str | Path
) -> tuple[OriginalMove, ...]:
    """A megőrzött eredeti (és a pillanatképek) MÁSOLÁSA a kép mellé (#1450).

    A `move_preserved_originals` nem-destruktív párja: a forrás mindenestül
    a helyén marad. A `copy_photo` hívja, közvetlenül a képfájl másolása
    után.

    Miért kell: enélkül a másolt kép az új helyen nem tudott visszaállni —
    a „Vissza az eredetihez" nem talált semmit, a szerkesztés a példányon
    véglegesnek látszott. Az „After copying: delete" import-módban ez
    ténylegesen adatvesztés volt, mert ott a forrás is törlődik.

    Args:
        source_photo: A másolandó kép jelenlegi útja.
        target_photo: A MÁR ELKÉSZÜLT másolat útja (az ütközés-feloldás
            utáni, végleges néven — a kísérők ezt a nevet veszik fel).

    Returns:
        A ténylegesen elkészült másolatok.

    Raises:
        FileExistsError: ha valamelyik célhely foglalt — ilyenkor semmi nem
            készült el.
        OSError: fájlrendszer-hiba esetén. A már elkészült másolatokat
            eltakarítjuk, hogy ne maradjon fél eredményű célmappa.
    """
    moves = plan_original_moves(source_photo, target_photo)
    if not moves:
        return ()
    _reject_unsafe_targets(moves)

    done: list[OriginalMove] = []
    for move in moves:
        try:
            move.target.parent.mkdir(parents=True, exist_ok=True)
            _copied(move.source, move.target)
        except OSError as error:
            _discard_copies(done)
            _remove_if_empty(move.target.parent)
            raise type(error)(
                f"A képhez megőrzött eredeti változatot nem sikerült ide "
                f"másolni: {move.target} ({error}). A forrás kép és a "
                f"megőrzött változatai érintetlenek."
            ) from error
        done.append(move)

    from picasapy.fileops.original_ini import (
        IniSectionsFailed,
        undo_copied_ini_sections,
    )

    try:
        _copy_ini_sections(done)
    except Exception as error:  # noqa: BLE001 — az ini-réteg többféle hibát dob
        # A `_discard_copies` csak a FÁJLOKAT törli. A már kiírt szekciókat
        # külön kell visszavenni, különben FRISSEN ÜLTETETT árvák maradnak a
        # cél inijében, amiket a következő, azonos nevű eredeti örökölne
        # (#1450 átnézés, 5. lelet).
        if isinstance(error, IniSectionsFailed):
            undo_copied_ini_sections(error.done)
        _discard_copies(done)
        raise OSError(
            f"A képhez megőrzött eredeti beállításait nem sikerült átmásolni "
            f"({error}). A forrás kép és a megőrzött változatai érintetlenek."
        ) from error
    return tuple(done)


def _discard_copies(moves: Sequence[OriginalMove]) -> None:
    """A félbemaradt másolás eltakarítása — csak a MOST készült példányokat
    törli, a forráshoz nem nyúl."""
    for move in reversed(list(moves)):
        try:
            move.target.unlink(missing_ok=True)
        except OSError:
            _cache_unknown(move.target.parent)
            continue
        _cache_removed(move.target.parent, move.target.name)
        _remove_if_empty(move.target.parent)


def _copy_ini_sections(
    moves: Sequence[OriginalMove],
) -> tuple["IniSectionCopy", ...]:
    """A kísérőfájlok ini-szekcióinak MÁSOLÁSA (#1450) — a forrás marad.

    Returns:
        A kiírt szekciók, a visszavételükhöz szükséges előzménnyel együtt.
    """
    from picasapy.fileops.original_ini import copy_original_ini_sections

    return copy_original_ini_sections(
        tuple((move.source, move.target) for move in moves)
    )


def undo_original_moves(
    moves: Sequence[OriginalMove],
) -> tuple[OriginalMove, ...]:
    """A már elmozdított kísérőfájlok visszatétele a helyükre.

    KIZÁRÓLAG a fájlokkal foglalkozik. Az ini-szekciók visszavitele nem
    következtethető ki a fájlok listájából (#1448 átnézés, 1. lelet), ezért
    azt a hívó végzi, a `_move_ini_sections` visszaadott listájából — a
    fájlok visszagörgetése ELŐTT, mert utána a célmappa már nem létezik.

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
            _moved(move.target, move.source)
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
    töröl, tehát semmit nem vihet magával.

    A CSAK `.picasa.ini`-t tartalmazó mappát SZÁNDÉKOSAN nem takarítja el
    (#2511): innen nem látszik, hogy azt az ini-t mi hoztuk-e létre, vagy a
    felhasználóé (esetleg a párhuzamosan futó Picasáé) volt már a művelet
    előtt. A törléshez szükséges tudás egy réteggel feljebb van, és ott is
    marad: a `original_ini._remove_if_contentless` KIZÁRÓLAG azt az ini-t
    törli, amelyik a művelet előtt nem létezett (`target_ini_existed`) és
    üresre is fogyott — a `.bak` párjával együtt. Mivel a hívási sorrend
    mindenhol „előbb az ini-fázis visszavétele, utána a fájloké"
    (`originals_follow`, `_move_preserved_originals`, `_discard_copies`
    előtt az `undo_copied_ini_sections`), mire ide érünk, az általunk
    gyártott ini már nincs ott, és a mappa valóban üres.

    Ami marad, az a felhasználó adata: azt a `_ini_stranded_warning`
    mondja ki, nem törli."""
    try:
        directory.rmdir()
    except OSError:
        return
    # A mappa megszűnt: a róla tárolt lista már semmit nem jelent. Nem
    # „üresre" javítjuk, hanem ELFELEJTJÜK — az elfelejtés sosem ad rossz
    # választ, legfeljebb egy listázásba kerül, és nem kell hozzá
    # feltevés arról, mi volt még bent (a `.picasa.ini` például nem a mi
    # könyvelésünk).
    _cache_unknown(directory)


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


def _ini_stranded_warning(stranded: Sequence["IniSectionMove"]) -> str:
    """A figyelmeztetés, ha a MEGŐRZÖTT EREDETI BEÁLLÍTÁSAIT nem sikerült
    visszatenni a régi helyükre. Üres sztring, ha minden visszakerült.

    A fájlokénál enyhébb kár, de ki kell mondani: a beállítások (`filters`,
    `crop`, `rotate`, `moddate`) a célmappa inijében ragadtak, ahol egy
    későbbi, azonos nevű eredeti örökölné őket — és a párhuzamosan futó
    windowsos Picasa is onnan olvasná. A megnyugtató mondat ilyenkor
    HAZUGSÁG lenne (#1448 2. átnézés, 3. lelet)."""
    if not stranded:
        return ""
    helyek = ", ".join(
        f"{move.target_ini} [{move.target_name}]" for move in stranded
    )
    return (
        f" FIGYELEM: a megőrzött eredeti beállításait nem sikerült a régi "
        f"helyükre visszatenni, itt maradtak: {helyek}. A képhez tartozó "
        f"fájlok a helyükön vannak, de ezt a bejegyzést érdemes kézzel "
        f"eltávolítani, mert egy későbbi, azonos nevű megőrzött eredeti "
        f"örökölné a beállításait."
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
    moved, ini_moved = _move_preserved_originals(source_photo, target_photo)
    try:
        yield
    except OSError as error:
        # Előbb a szekciók, csak utána a fájlok: fordítva a szekció-
        # visszavitel egy már megszűnt célmappa inijéből olvasna.
        ini_stranded = _undo_ini_sections(ini_moved)
        stranded = undo_original_moves(moved)
        warning = _stranded_warning(stranded) + _ini_stranded_warning(ini_stranded)
        if warning:
            # A típus megőrzése kötelező: a hívók (FileOpsController,
            # PhotoOpsController) kivételosztály szerint szűrnek, egy új
            # osztály némán kicsúszna a szűrőjükön.
            raise type(error)(f"{error}{warning}") from error
        raise


__all__ = [
    "OriginalMove",
    "ambiguous_snapshot_names",
    "companions_of",
    "copy_preserved_originals",
    "listing_cache",
    "move_preserved_originals",
    "originals_follow",
    "originals_slot_free",
    "plan_original_moves",
    "snapshot_numbers",
    "undo_original_moves",
]
