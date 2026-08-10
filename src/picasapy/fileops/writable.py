"""Mappa-írhatóság ellenőrzése szerkesztés-mentés ELŐTT (#459, jegy 1.
pontja).

Az eredeti Picasa a szerkesztés mentésekor felajánlotta a kiutat:
*"This file is read only. In order to edit this file, Picasa needs to
copy the file's folder. Would you like to make a copy now?"* — a mi
elsődleges cél itt a FELISMERÉS és a látható jelzés (a tényleges
mappa-másolás a jegy szerint külön, nagyobb munka, ld. `edit_controller.py`
docstringje a hívási helyen).

Az ellenőrzés Windows-kompatibilis módon (CLAUDE.md (h) szabály): NEM
`os.access(..., os.W_OK)`-t használunk könyvtárra (az Windowson nem
megbízható), hanem egy valódi próba-fájl írását/törlését — ez minden
platformon ugyanazt a végeredményt adja, amit a tényleges mentés is
tapasztalna."""

from __future__ import annotations

import tempfile
from pathlib import Path


def is_folder_writable(folder: Path) -> bool:
    """`True`, ha `folder`-be ténylegesen írható (próba-fájl létrehozása és
    törlése). Nem létező mappánál `False` — nincs hova írni."""
    if not folder.is_dir():
        return False
    try:
        with tempfile.NamedTemporaryFile(dir=folder, prefix=".picasapy-wtest-"):
            pass
    except OSError:
        return False
    return True
