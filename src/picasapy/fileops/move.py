"""Fotó áthelyezése másik mappába — a .picasa.ini szekció átvándorol (#15).

A forrás szekció (star/caption/rotate/filters/… és minden ismeretlen sor)
bitre pontosan átkerül a cél mappa `.picasa.ini`-jébe.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from picasapy.ini import load_document, parse_document, save_document
from picasapy.scanner import PICASA_INI_NAME


def move_photo(path: Path, dest_folder: Path) -> Path:
    """A `path` fájl áthelyezése a `dest_folder` mappába.

    Args:
        path: Az áthelyezendő fájl jelenlegi elérési útja.
        dest_folder: A célmappa (léteznie kell, könyvtárnak kell lennie).

    Returns:
        Az új elérési út.

    Raises:
        FileNotFoundError: Ha `path` vagy `dest_folder` nem létezik.
        NotADirectoryError: Ha `dest_folder` nem könyvtár.
        FileExistsError: Ha a célmappában már van azonos nevű fájl vagy
            ini-szekció — nem írjuk felül csendben.
    """
    path = Path(path)
    dest_folder = Path(dest_folder)
    if not path.exists():
        raise FileNotFoundError(f"A fájl nem létezik: {path}")
    if not dest_folder.exists():
        raise FileNotFoundError(f"A célmappa nem létezik: {dest_folder}")
    if not dest_folder.is_dir():
        raise NotADirectoryError(f"A cél nem könyvtár: {dest_folder}")
    target = dest_folder / path.name
    if target.exists():
        raise FileExistsError(f"A célfájl már létezik: {target}")

    source_ini = path.parent / PICASA_INI_NAME
    dest_ini = dest_folder / PICASA_INI_NAME
    source_doc = load_document(source_ini) if source_ini.exists() else None
    source_section = source_doc.section(path.name) if source_doc is not None else None

    dest_doc = None
    if source_section is not None:
        dest_doc = load_document(dest_ini) if dest_ini.exists() else parse_document("")
        if dest_doc.section(path.name) is not None:
            raise FileExistsError(
                f"A célmappa ini-jében már van ilyen nevű szekció: {path.name}"
            )

    shutil.move(str(path), str(target))

    if source_section is not None:
        save_document(dest_doc.with_section(source_section), dest_ini, backup=True)
        save_document(source_doc.without_section(path.name), source_ini, backup=True)

    return target
