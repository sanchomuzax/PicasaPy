"""A megőrzött eredetik és a pillanatképek NEVEINEK keresése.

A `picasapy.fileops.originals` szétbontott része: a mappanevek, a
pillanatkép-minta szerinti keresés, a foglaltság-vizsgálat és a kép
kísérőfájljainak felsorolása. A tervezés (`originals_plan`) és a
mozgatás/másolás ezekre épül, fordítva nem.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from picasapy.fileops.originals_cache import _entry_names


def _originals_dir_names() -> tuple[str, ...]:
    """A megőrzött eredeti ismert mappanevei, a keresési sorrendjükben.

    Késleltetett import: a nevek az `edit.save`-ben élnek (ott az
    igazságforrásuk), az a modul viszont az OpenCV-t is behúzza - ezen a
    gépen mérve 1,8 másodperc, szemben a `fileops` 0,2 másodpercével. A
    `fileops`-ot fájlműveletekhez importáló hívók (és a tesztek) ne
    fizessenek érte. Ugyanezt a mintát követi a `save_controller` is."""
    from picasapy.edit.save import ORIGINALS_DIR_NAMES

    return ORIGINALS_DIR_NAMES


def _snapshot_dir_name() -> str:
    """A MI pillanatképeink alkönyvtárának neve (#2512), ugyanazzal a
    késleltetett importtal, mint az `_originals_dir_names`."""
    from picasapy.edit.save import SNAPSHOT_DIR_NAME

    return SNAPSHOT_DIR_NAME


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
    fájl, a példányt békén hagyjuk - inkább maradjon a helyén, mint hogy egy
    másik kép visszaútját rángassuk el.

    A mappát LISTÁZZUK, nem `glob()`-bal keresünk: a fájlnévben lévő `[`,
    `*` vagy `?` a mintában joker lenne, és némán rossz találatokat adna.

    A könyvtárlistázás hálózati megosztáson drága (#1146), ezért a
    `find_original_backup` szándékosan kerüli. Itt viszont vállaljuk: a
    pillanatképek száma és sorszáma előre nem ismert, és a költöztetés
    ritka, a felhasználó által kezdeményezett művelet - nem megjelenítési
    útvonal. A KÖTEGELT úton a `listing_cache()` mappánként egyetlen
    listázásra fogja össze (#1452). A #2512 óta ez eredeti-mappánként KÉT
    listázás (az alkönyvtár is), de ugyanabban a hatókörben, ugyanazzal a
    gyorstárral - és ugyanazokon a ritka, felhasználó által kezdeményezett
    útvonalakon.

    **#2512: két hely.** Az ÚJ pillanatképek a `directory` alatti
    `.picasapy-snapshots` alkönyvtárba kerülnek, ahol a névminta NEM
    kétértelmű - oda rajtunk kívül senki nem ír, tehát ott a gazda-szűrés
    nem alkalmazandó. Ha ott is szűrnénk, egy véletlenül azonos nevű
    önálló kép puszta létezése elnémítaná a SAJÁT visszavonásunkat, és a
    kép mozgatásakor hátrahagyná a saját pillanatképeinket.

    Args:
        directory: az eredeti-mappa (`.picasaoriginals` vagy `Originals`) -
            az alkönyvtárat ez a függvény nézi meg magától.
        photo: a kép a SAJÁT mappájában (a gazda-szűréshez kell).

    Yields:
        `(sorszám, a sorszám SZÖVEGE, útvonal)` hármasok, rendezetlenül.
    """
    # Az ÚJ hely: kétértelműség nincs, gazda-szűrés sem kell.
    yield from _snapshot_candidates(directory / _snapshot_dir_name(), photo)
    # A RÉGI, a „szent" eredetivel KÖZÖS hely: itt áll a #1449 szabálya.
    for szam, szoveg, path in _snapshot_candidates(directory, photo):
        if (photo.parent / path.name).exists():
            continue  # egy önálló kép eredetije, nem a mi pillanatképünk
        yield szam, szoveg, path


def _placement_candidates(
    directory: Path, photo: Path
) -> Iterator[tuple[int, str, Path]]:
    """A pillanatkép-nevekre illő fájlok MINDKÉT helyen, gazda-szűrés nélkül.

    Az `originals_slot_free` „el tudom-e HELYEZNI ide?" ágának halmaza (ld.
    ott): a foglaltság kérdésénél a gazdás példány is foglal, mert a
    `_reject_unsafe_targets` fizikailag létező fájlra dob.
    """
    yield from _snapshot_candidates(directory / _snapshot_dir_name(), photo)
    yield from _snapshot_candidates(directory, photo)


def _snapshot_candidates(
    directory: Path, photo: Path
) -> Iterator[tuple[int, str, Path]]:
    """A `<név>.<N><kiterjesztés>` NÉVMINTÁRA illő fájlok - gazda-szűrés nélkül.

    A névminta kétértelmű: egy találat lehet a mi pillanatképünk, de lehet
    egy azonos nevű, ÖNÁLLÓ kép megőrzött eredetije is.

    Ez a függvény EGYETLEN könyvtárat néz meg; hogy melyik kettőt (az ÚJ
    `.picasapy-snapshots` alkönyvtárat és a régi, közös helyet), azt a két
    hívója rakja össze - `snapshot_numbers` és `_placement_candidates`
    (#2512).

    A kétértelműség csak a RÉGI, közös helyen áll fenn, és a két fogyasztó
    ott különbözőképp szűr rá:

    * a `snapshot_numbers` (amivel dolgozunk: mozgatjuk, töröljük,
      visszaállítjuk) a gazdás találatot KIHAGYJA - idegen kép visszaútját
      nem rángatjuk el (#1449);
    * a `_placement_candidates`, azaz az `originals_slot_free` „el tudom-e
      HELYEZNI ide?" ága (ami csak azt kérdezi, SZABAD-E a hely) a gazdás
      találatot is foglaltnak mondja - ott ugyanis fizikailag áll egy
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
        # társait, amiken az `int()` `ValueError`-t dob - az a felhasználó
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
    példány - csak nem dönthető el, kié (#1449 átnézés, 3. lelet). Az
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
    ugyanaz - ezt mondja ki a `moving_companions` (#2510):

    * `True` (alapértelmezés) - „el tudom-e HELYEZNI ide a kép kísérőit?".
      Ilyenkor a `_snapshot_candidates` halmaza számít: minden névre illő
      fájl foglal, még az is, amelyiknek a képmappában GAZDÁJA van. Az
      utóbbi kihagyása azt jelentené, hogy „szabadnak" mondunk egy helyet,
      amire a `_reject_unsafe_targets` aztán `FileExistsError`-t dob - a
      másolás elbukott ahelyett, hogy a `_unique_target` másik nevet
      választott volna (#1450 átnézés, 4. lelet). A tévedés iránya így egy
      másik pótnév, nem egy bukott művelet.

    * `False` - „ÖRÖKÖLNE-E a képem itt idegen adatot?". A kísérő nélküli
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
            _placement_candidates(directory, photo)
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
