"""A frissítősegéd eredményjelzője: a program a következő induláskor kiírja (#6458).

A segéd a régi változatot indítja vissza, ha a csere nem sikerült; eddig erről
a felhasználó semmit nem tudott meg. A jelzőt a segéd írja, a program az
induláskor egyszer olvassa ki, majd törli.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from .update_folyamatok import foglalt_hiba

logger = logging.getLogger(__name__)

FAJL_FOGLALT = "fajl-foglalt"
ONELLENORZES = "onellenorzes"
EGYEB = "egyeb"
_ISMERT = frozenset({FAJL_FOGLALT, ONELLENORZES, EGYEB})


def jelzo_utvonal() -> Path:
    from .platform_storage import default_storage_paths
    from .update_swap_helper import _platform

    return default_storage_paths(_platform()).data / "frissites-eredmeny.json"


def ok_kod(hiba: BaseException) -> str:
    return FAJL_FOGLALT if foglalt_hiba(hiba) else EGYEB


def ird(jelzo: Path, *, siker: bool, ok: str) -> None:
    try:
        jelzo.parent.mkdir(parents=True, exist_ok=True)
        jelzo.write_text(json.dumps({"siker": siker, "ok": ok}), encoding="utf-8")
    except OSError:
        logger.warning("A frissítés eredményjelzője nem írható (#6458)")


def olvasd_es_torold(jelzo: Path) -> str:
    """Az előző frissítés kudarcának okkódja; siker vagy hiányzó jelző esetén üres."""
    try:
        nyers = jelzo.read_text(encoding="utf-8")
    except OSError:
        return ""
    try:
        jelzo.unlink()
    except OSError:
        pass
    try:
        adat = json.loads(nyers)
    except ValueError:
        return EGYEB
    if not isinstance(adat, dict) or adat.get("siker") is True:
        return ""
    ok = adat.get("ok")
    return ok if ok in _ISMERT else EGYEB
