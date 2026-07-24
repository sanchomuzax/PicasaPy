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

from picasapy.ini import Section, load_or_empty, update_document
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
    source_section = (
        load_or_empty(source_ini).section(path.name) if source_ini.exists() else None
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
    nélkül (a fájl maga ekkor is átkerül).

    Az írás az ütközésbiztos `update_document`-en megy (#295): a párhuzamosan
    futó eredeti Picasa közbeírása nem veszhet el."""
    dest_ini = dest_folder / PICASA_INI_NAME
    if load_or_empty(dest_ini).section(target.name) is not None:
        return
    section_to_write = source_section
    if target.name != source_section.name:
        section_to_write = replace(
            source_section,
            name=target.name,
            header=replace(source_section.header, text=f"[{target.name}]"),
        )

    def _mutate(document):
        if document.section(target.name) is not None:
            # Az újrajátszás friss dokumentumában időközben elfoglalt a név:
            # ugyanaz a döntés, mint az előellenőrzésnél — nem írjuk felül.
            return document
        return document.with_section(section_to_write)

    update_document(dest_ini, _mutate, backup=True)


def _unique_target(dest_folder: Path, stem: str, suffix: str) -> Path:
    """Ütközésmentes célnév: `név.jpg`, `név-1.jpg`, `név-2.jpg`, ... — az
    export-mag azonos nevű helperének (`export/exporter.py`) mintája."""
    candidate = dest_folder / f"{stem}{suffix}"
    counter = 1
    while candidate.exists():
        candidate = dest_folder / f"{stem}-{counter}{suffix}"
        counter += 1
    return candidate
