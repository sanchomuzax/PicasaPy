"""Fotó másolása másik mappába — a .picasa.ini szekció is átmásolódik (#23).

A `move_photo`-val (#15) ellentétben a FORRÁS érintetlen marad — ez az
Import forrásból (#23) nem-destruktív alapértelmezése (kártyáról/forrás-
mappából a könyvtárba). Ütközésnél (már van azonos nevű fájl a célban) a
névfeloldás az export-mag (`picasapy.export.exporter._unique_target`)
mintáját követi: `név-1.jpg`, `név-2.jpg`, ... — sosem ír felül meglévő
fájlt csendben.
"""

from __future__ import annotations

import shutil
from dataclasses import replace
from pathlib import Path

from picasapy.ini import Section, load_document, parse_document, save_document
from picasapy.scanner import PICASA_INI_NAME


def copy_photo(path: Path, dest_folder: Path) -> Path:
    """A `path` fájl MÁSOLÁSA a `dest_folder` mappába (a forrás megmarad).

    Args:
        path: A másolandó fájl elérési útja.
        dest_folder: A célmappa (léteznie kell, könyvtárnak kell lennie).

    Returns:
        Az új (ütközés esetén automatikusan átnevezett) elérési út.

    Raises:
        FileNotFoundError: Ha `path` vagy `dest_folder` nem létezik.
        NotADirectoryError: Ha `dest_folder` nem könyvtár.
    """
    path = Path(path)
    dest_folder = Path(dest_folder)
    if not path.exists():
        raise FileNotFoundError(f"A fájl nem létezik: {path}")
    if not dest_folder.exists():
        raise FileNotFoundError(f"A célmappa nem létezik: {dest_folder}")
    if not dest_folder.is_dir():
        raise NotADirectoryError(f"A cél nem könyvtár: {dest_folder}")

    target = _unique_target(dest_folder, path.stem, path.suffix)
    shutil.copy2(str(path), str(target))  # copy2: mtime is átkerül (WYSIWYG dátum)

    source_ini = path.parent / PICASA_INI_NAME
    source_doc = load_document(source_ini) if source_ini.exists() else None
    source_section = (
        source_doc.section(path.name) if source_doc is not None else None
    )
    if source_section is not None:
        _copy_ini_section(source_section, target, dest_folder)

    return target


def _copy_ini_section(source_section: Section, target: Path, dest_folder: Path) -> None:
    """A forrás ini-szekció átmásolása a cél mappa `.picasa.ini`-jébe.

    A tartalom (star/caption/rotate/filters/… és minden ismeretlen sor)
    bitre pontosan megmarad; ha az ütközés-feloldás miatt a célfájl neve
    eltér a forrásétól, a szekció fejléce is a cél nevét kapja. Ha a
    célban (más forrásból) már foglalt a célnév szekciója, csendben
    kimarad — adatvesztés helyett inkább a másolt kép marad ini-adat
    nélkül (a fájl maga ekkor is átkerül)."""
    dest_ini = dest_folder / PICASA_INI_NAME
    dest_doc = load_document(dest_ini) if dest_ini.exists() else parse_document("")
    if dest_doc.section(target.name) is not None:
        return
    section_to_write = source_section
    if target.name != source_section.name:
        section_to_write = replace(
            source_section,
            name=target.name,
            header=replace(source_section.header, text=f"[{target.name}]"),
        )
    save_document(dest_doc.with_section(section_to_write), dest_ini, backup=True)


def _unique_target(dest_folder: Path, stem: str, suffix: str) -> Path:
    """Ütközésmentes célnév: `név.jpg`, `név-1.jpg`, `név-2.jpg`, ... — az
    export-mag azonos nevű helperének (`export/exporter.py`) mintája."""
    candidate = dest_folder / f"{stem}{suffix}"
    counter = 1
    while candidate.exists():
        candidate = dest_folder / f"{stem}-{counter}{suffix}"
        counter += 1
    return candidate
