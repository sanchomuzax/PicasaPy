"""Az exporthoz tartozó Picasa-metaadatok mentése."""

from __future__ import annotations

from pathlib import Path

from picasapy.ini import IniConflictError, IniSaveError, update_document
from picasapy.scanner import PICASA_INI_NAME

from .export_models import ExportItem


def _write_ini_metadata(
    target_dir: Path, parok: tuple[tuple[ExportItem, Path], ...]
) -> None:
    """A `caption`/`keywords` átvitele a célmappa `.picasa.ini`-jébe (#1166).

    Egyetlen `update_document` hívással, a köteg végén: az előzetes
    ujjlenyomat-ellenőrzésig észlelt Picasa-változás újratöltést és újrajátszást
    kap (#295). A sikeres ellenőrzés és fájlcsere közti külső írás elveszhet;
    nem nyitjuk-zárjuk fájlonként. Adat nélküli kötegnél nem keletkezik ini.

    A szekció fejléce a CÉLFÁJL neve (sorszámozásnál `001-a.jpg`),
    különben az adatnak nem lenne gazdája."""
    ujak = {
        cel.name: {
            kulcs: ertek
            for kulcs, ertek in (("caption", item.caption), ("keywords", item.keywords))
            if ertek
        }
        for item, cel in parok
    }
    ujak = {nev: mezok for nev, mezok in ujak.items() if mezok}
    if not ujak:
        return
    ini_path = target_dir / PICASA_INI_NAME

    def modosit(document):
        for nev, mezok in ujak.items():
            for kulcs, ertek in mezok.items():
                # a `with_value` a hiányzó szekciót maga hozza létre, és ez
                # a `.picasa.ini` minden kulcsírásának közös kapuja (#643)
                document = document.with_value(nev, kulcs, ertek)
        return document

    try:
        update_document(ini_path, modosit)
    except (OSError, IniSaveError, IniConflictError):
        # Az ini-írás hibája NEM hiúsíthatja meg a kész exportot: a képek
        # a helyükön vannak, csak a felirat/címke marad el.
        pass

