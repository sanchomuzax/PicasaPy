"""A kép törlésekor a megőrzött eredeti is megy vele (#1451).

A `trash.py` a FÁJLOK szintjén dolgozik (freedesktop.org Trash-spec) — nem
tud arról, hogy egy képhez a `.picasaoriginals/` (vagy `Originals/`) alatt
kísérőfájlok tartoznak. Emiatt a lomtárba tett vagy véglegesen törölt képnél
a megőrzött eredeti a helyén maradt.

Két következménye volt:

1. **Láthatatlanul gyűlt.** Az eredetik teljes méretű JPEG-ek; a rejtett
   mappa a felhasználó fájlkezelőjében nem tűnik fel, a hely viszont fogy.
2. **Idegen eredetit örökölt a következő kép.** Ha a törölt kép helyére
   később azonos nevű ÚJ kép került, a „Vissza az eredetihez" egy teljesen
   MÁS fénykép változatát adta vissza. Ez nem kozmetikai hiba: a felhasználó
   képe helyett idegen tartalom írja felül a sajátját.

## Mi hova megy

* **Lomtár:** a kép és minden kísérője KÜLÖN lomtár-bejegyzést kap, a saját,
  helyes eredeti útjával. A freedesktop-lomtárban nincs csoportosítás, tehát
  a párban való visszaállítás csak úgy megy, ha a felhasználó mindkettőt
  visszaállítja — de árva fájl nem marad, és idegen eredetit sem örököl
  senki. Ha a KÉP lomtárazása bukik, a már elvitt kísérőket visszatesszük;
  ha a visszatétel IS bukik, azt a hibaüzenet kimondja — néma fél törlés
  nincs. **Windowson fordított a sorrend**: ott a rendszer Lomtárából
  programból nem lehet visszatenni (`uses_system_trash`), ezért a kísérők a
  kép SIKERES lomtárazása után mennek.
* **Végleges törlés:** előbb a kép (a felhasználó kimondott szándéka), utána
  a kísérők. Fordított sorrendben egy bukás úgy semmisítené meg a
  visszaútját, hogy a szerkesztett kép ott marad — az a rosszabb irány.

## Az ini-könyvelés is megy

A kísérők `.picasa.ini` szekciói is törlődnek (`ini/` API-n át, sávhatár).
Enélkül a következő, azonos nevű eredeti örökölné a beállításaikat —
ugyanaz a hibaosztály fájl helyett kulcs szinten. A lomtárból visszahozott
eredeti FÁJL tehát visszajön, a (származtatott, ritkán használt) ini-sorai
nem: ez tudatos csere az öröklés kizárásáért.
"""

from __future__ import annotations

import shutil
from collections.abc import Sequence
from pathlib import Path

from picasapy.fileops.original_ini import remove_original_ini_sections
from picasapy.fileops.originals import companions_of
from picasapy.fileops.trash import (
    delete_permanently,
    delete_to_trash,
    uses_system_trash,
)

#: A `shutil.move` MODULSZINTŰ fogantyúja — a teszt EZT cserélje (#1375).
_move = shutil.move


def delete_photo_to_trash(path: str | Path, *, trash_dir: Path | None = None) -> Path:
    """A kép a lomtárba — a megőrzött eredetijével és a pillanatképeivel.

    Args:
        path: A törlendő kép elérési útja.
        trash_dir: Teszteléshez felülírható lomtár-gyökér.

    Returns:
        A KÉP új elérési útja a lomtárban (a kísérőké nem érdekli a hívót).

    Raises:
        FileNotFoundError: ha a kép nem létezik.
        TrashUnavailableError: ha nincs elérhető lomtár.
        OSError: fájlrendszer-hiba esetén; a már elvitt kísérőket ilyenkor
            visszatesszük a helyükre. Ha a VISSZATÉTEL is bukik, a hiba
            üzenete megmondja, hol keresse a felhasználó a fájljait — némán
            fél törlés nem mehet ki (#1451 átnézés, 2. lelet).
    """
    path = Path(path)
    companions = companions_of(path)

    if uses_system_trash(trash_dir):
        return _rendszer_lomtaraba(path, companions, trash_dir)

    elvittek: list[tuple[Path, Path]] = []
    try:
        for companion in companions:
            elvittek.append(
                (companion, delete_to_trash(companion, trash_dir=trash_dir))
            )
        eredmeny = delete_to_trash(path, trash_dir=trash_dir)
    except OSError as error:
        maradtak = _visszatesz(elvittek)
        if maradtak:
            # A típus megőrzése kötelező: a hívók kivételosztály szerint
            # szűrnek (`TrashUnavailableError` vs. sima `OSError`).
            raise type(error)(
                f"{error}{_lomtarban_maradt_uzenet(maradtak)}"
            ) from error
        raise

    _konyveles_torlese(companions)
    _ures_mappak_takaritasa(companions)
    return eredmeny


def _rendszer_lomtaraba(
    path: Path, companions: Sequence[Path], trash_dir: Path | None
) -> Path:
    """A windowsos ág: a KÉP megy előbb, a kísérők utána (#1451, 2. lelet).

    A `delete_to_trash` a `SHFileOperationW`-ágon a BEMENETI utat adja
    vissza — a rendszer Lomtárán belüli helyet nem ismerjük meg. A
    `_visszatesz` ott `_move(path, path)`-t hívna, azaz a visszatétel
    ELVILEG lehetetlen. Emiatt a linuxos sorrend (kísérők előbb) itt
    vállalhatatlan: a kép bukása után a megőrzött eredeti véglegesen a
    Lomtárban ragadna, miközben a kép a helyén marad — pont a néma fél
    törlés.

    Fordítva a rossz kimenet enyhébb és KIMONDOTT: ha a kép már elment és
    egy kísérő nem, azt a `delete_photo_permanently` mintájára megnevezzük.
    """
    eredmeny = delete_to_trash(path, trash_dir=trash_dir)

    maradtak: list[Path] = []
    for companion in companions:
        try:
            delete_to_trash(companion, trash_dir=trash_dir)
        except OSError:
            maradtak.append(companion)

    _konyveles_torlese(tuple(c for c in companions if c not in maradtak))
    _ures_mappak_takaritasa(companions)

    if maradtak:
        raise OSError(_ott_maradt_uzenet(maradtak))
    return eredmeny


def delete_photo_permanently(path: str | Path) -> None:
    """A kép VÉGLEGES törlése — a megőrzött eredetijével együtt.

    A kép megy előbb: az a felhasználó kimondott szándéka. Ha utána egy
    kísérő törlése bukik, a hiba KIMEGY (néma árva fájl nincs), de a kép már
    törölve van — a hibaüzenet ezt ki is mondja.

    Raises:
        FileNotFoundError: ha a kép nem létezik.
        OSError: ha valamelyik kísérőfájl nem törölhető.
    """
    path = Path(path)
    companions = companions_of(path)
    delete_permanently(path)

    maradtak: list[Path] = []
    for companion in companions:
        try:
            delete_permanently(companion)
        except OSError:
            maradtak.append(companion)

    _konyveles_torlese(tuple(c for c in companions if c not in maradtak))
    _ures_mappak_takaritasa(companions)

    if maradtak:
        raise OSError(_ott_maradt_uzenet(maradtak))


def _visszatesz(
    elvittek: Sequence[tuple[Path, Path]],
) -> tuple[tuple[Path, Path], ...]:
    """A lomtárba már elvitt kísérők visszahelyezése — legjobb szándék
    szerint. A `.trashinfo` párját is takarítjuk, hogy ne maradjon
    visszaállítási bejegyzés fájl nélkül.

    Returns:
        Amit NEM sikerült visszatenni — `(eredeti hely, lomtárbeli hely)`
        párok. Korábban ez az érték nem létezett, és a hibát is elnyelte a
        `continue`: a felhasználó azt látta, hogy a képe a helyén van,
        közben a megőrzött eredetije a lomtárban ült, és a „Vissza az
        eredetihez" némán elromlott (#1451 átnézés, 2. lelet).
    """
    maradtak: list[tuple[Path, Path]] = []
    for eredeti, lomtarban in reversed(list(elvittek)):
        try:
            eredeti.parent.mkdir(parents=True, exist_ok=True)
            _move(str(lomtarban), str(eredeti))
        except OSError:
            maradtak.append((eredeti, lomtarban))
            continue
        info = lomtarban.parent.parent / "info" / f"{lomtarban.name}.trashinfo"
        try:
            info.unlink(missing_ok=True)
        except OSError:
            pass
    return tuple(maradtak)


def _lomtarban_maradt_uzenet(maradtak: Sequence[tuple[Path, Path]]) -> str:
    """A figyelmeztetés, ha a lomtárból való visszatétel IS elbukott.

    Itt a hallgatás a legdrágább kimenet: a kép a helyén marad, a
    `find_original_backup` viszont nem talál mellette eredetit, és az
    `edit/save.py` a következő mentéskor a MÁR SZERKESZTETT bájtokat írja
    be új „eredetiként" — az érintetlen változat véglegesen elveszne.
    Ezért a legfontosabb mondanivaló az, hogy MIT NE tegyen."""
    hol = ", ".join(str(lomtarban) for _, lomtarban in maradtak)
    honnan = ", ".join(str(eredeti) for eredeti, _ in maradtak)
    return (
        f" FIGYELEM: a kép nem került a lomtárba, a hozzá tartozó megőrzött "
        f"változatot viszont már nem sikerült onnan visszahozni. A lomtárban "
        f"maradt: {hol}. Amíg nincs a kép mellett, a „Vissza az eredetihez” "
        f"nem talál semmit, és ha ÚJRA MENTI a képet, a program a mostani, "
        f"szerkesztett állapotot fogja eredetinek tekinteni — az érintetlen "
        f"változat véglegesen elveszne. Ne mentse újra a képet, amíg ezt a "
        f"fájlt a lomtárból vissza nem állította ide: {honnan}."
    )


def _ott_maradt_uzenet(maradtak: Sequence[Path]) -> str:
    """A kép már elment, a kísérője nem — a felhasználónak szóló üzenet."""
    helyek = ", ".join(str(p) for p in maradtak)
    return (
        f"A kép törlődött, de a hozzá tartozó megőrzött változatot nem "
        f"sikerült eltávolítani: {helyek}. Amíg ott van, helyet foglal, "
        f"és ha ugyanezen a néven új kép kerül a mappába, a "
        f"visszaállítás egy IDEGEN fénykép változatát adná vissza — "
        f"érdemes kézzel törölni."
    )


def _konyveles_torlese(companions: Sequence[Path]) -> None:
    """A kísérők ini-szekcióinak eltávolítása. Sosem dob: a fájlok már
    elmentek, egy ini-hiba nem teheti visszavonhatatlanul félbehagyottá a
    törlést — a maradó szekció legrosszabb esetben az eddigi állapot."""
    try:
        remove_original_ini_sections(companions)
    except Exception:  # noqa: BLE001 — az ini-réteg többféle hibát dob
        pass


def _ures_mappak_takaritasa(companions: Sequence[Path]) -> None:
    """Üresre fogyott eredeti-mappa eltakarítása.

    Az `rmdir` csak ÜRES könyvtárat töröl, tehát semmit nem vihet magával:
    ha maradt benne másik kép eredetije vagy a `.picasa.ini`, marad a mappa
    is."""
    for directory in {companion.parent for companion in companions}:
        try:
            directory.rmdir()
        except OSError:
            continue


__all__ = ["delete_photo_permanently", "delete_photo_to_trash"]
