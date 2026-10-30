"""Az importforrás-vezérlő fájlműveleti segédei."""

from __future__ import annotations

from pathlib import Path

from picasapy.fileops import companions_of
from picasapy.fileops.original_ini import remove_original_ini_sections
from picasapy.ini import (
    has_ini_source,
    load_or_empty,
    update_document,
    with_backuphash,
)
from picasapy.ini.names import INI_NAME


def _size_of(path: Path) -> int:
    """A fájl mérete bájtban; olvashatatlan fájlnál 0 — a sebesség-becslés
    sosem akaszthatja meg az importot."""
    try:
        return path.stat().st_size
    except OSError:
        return 0

def _mark_imported_ini(
    target: Path, rotation: int, starred: bool
) -> None:
    """A forgatás/csillag beírása a MÁSOLAT `.picasa.ini`-jébe (#441).

    Nem-destruktív, ahogy a rács forgatása is: `rotate=rotate(n)` és
    `star=yes`. A kártyán lévő eredetihez NEM nyúlunk — a „Leave card
    alone" ág épp azt várja el, hogy a forrás érintetlen maradjon.
    """
    if not rotation and not starred:
        return

    def _mutate(document):
        result = document
        if rotation:
            result = result.with_value(target.name, "rotate", f"rotate({rotation})")
            result = with_backuphash(result, target.name)
        if starred:
            result = result.with_value(target.name, "star", "yes")
        return result

    update_document(target.parent / INI_NAME, _mutate, backup=True)

def _remove_source_file(path: Path) -> None:
    """Egy forrásfájl eltávolítása (#441 "After Copying:" törléssel járó két
    állapota): a fájl törlése, majd — ha volt — az ini-szekció eltávolítása
    a forrás `.picasa.ini`-jéből. A cél a saját (ütközés esetén átnevezett)
    másolatát már megkapta a `copy_photo`-tól, mielőtt ez lefut.

    #1450/#1451: a megőrzött eredeti és a pillanatképek is mennek. Ez az út
    (`copy_photo` + forrástörlés) TÉNYLEGES mozgatás, tehát ha a kísérők itt
    maradnának, a forrásmappában árván gyűlnének, és a következő, azonos
    nevű kép egy IDEGEN fénykép eredetijét örökölné. A célban a példányuk
    már ott van (`copy_photo`), tehát a visszaút nem vész el."""
    kiserok = companions_of(path)
    path.unlink(missing_ok=True)
    for kisero in kiserok:
        kisero.unlink(missing_ok=True)
    if kiserok:
        try:
            remove_original_ini_sections(kiserok)
        except Exception:  # noqa: BLE001 — az ini-réteg többféle hibát dob
            pass
        for directory in {kisero.parent for kisero in kiserok}:
            try:
                directory.rmdir()  # csak ÜRES mappát töröl
            except OSError:
                pass
    source_ini = path.parent / INI_NAME
    if not has_ini_source(source_ini):
        return
    try:
        document = load_or_empty(source_ini)
    except (OSError, ValueError):
        return
    if document.section(path.name) is not None:
        update_document(
            source_ini,
            lambda current: current.without_section(path.name),
            backup=True,
        )
