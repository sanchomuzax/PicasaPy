"""A frissítősegéd eredményjelzője: a program a következő induláskor kiírja (#6458).

A segéd a régi változatot indítja vissza, ha a csere nem sikerült; eddig erről
a felhasználó semmit nem tudott meg. A jelzőt a segéd írja, a program az
induláskor egyszer olvassa ki, majd törli.

#6471: a program már a segéd indításakor „vár” állapotba teszi a jelzőt a várt
verzióval. Ha a segéd el sem jut a végéig, ez marad meg; ha sikert jelez, de
mégis a régi verzió indul, az is kiderül.
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
#: #6471: a segéd elindult, de nem írt eredményt (el sem jutott a végéig)
NEM_FUTOTT = "nem-futott"
#: #6471: a segéd sikert jelzett, mégsem a várt verzió indult el
VERZIO = "verzio"
_ISMERT = frozenset({FAJL_FOGLALT, ONELLENORZES, EGYEB, NEM_FUTOTT, VERZIO})


def jelzo_utvonal() -> Path:
    from .platform_storage import default_storage_paths
    from .update_swap_helper import _platform

    return default_storage_paths(_platform()).data / "frissites-eredmeny.json"


def ok_kod(hiba: BaseException) -> str:
    return FAJL_FOGLALT if foglalt_hiba(hiba) else EGYEB


def ird(jelzo: Path, *, siker: bool, ok: str) -> None:
    """A segéd eredménye; a program által beírt várt verzió megmarad (#6471)."""
    _ment(jelzo, {"siker": siker, "ok": ok, "vart": _vart_verzio(jelzo)})


def ird_varakozik(jelzo: Path, vart: str) -> None:
    """A segéd indításakor: a frissítés vár, a várt verzióval (#6471)."""
    _ment(jelzo, {"siker": False, "ok": NEM_FUTOTT, "vart": vart})


def torold(jelzo: Path) -> None:
    try:
        jelzo.unlink()
    except OSError:
        pass


def _ment(jelzo: Path, adat: dict) -> None:
    try:
        jelzo.parent.mkdir(parents=True, exist_ok=True)
        jelzo.write_text(json.dumps(adat), encoding="utf-8")
    except OSError:
        logger.warning("A frissítés eredményjelzője nem írható (#6458)")


def _vart_verzio(jelzo: Path) -> str:
    try:
        adat = json.loads(jelzo.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    vart = adat.get("vart") if isinstance(adat, dict) else ""
    return vart if isinstance(vart, str) else ""


def olvasd_es_torold(jelzo: Path, jelenlegi_verzio: str = "") -> str:
    """Az előző frissítés kudarcának okkódja; siker vagy hiányzó jelző esetén üres.

    #6471: sikeres jelzésnél is kudarc (`VERZIO`), ha a várt verzió ismert,
    és nem az fut."""
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
    if not isinstance(adat, dict):
        return EGYEB
    if adat.get("siker") is True:
        vart = adat.get("vart") or ""
        if vart and jelenlegi_verzio and vart != jelenlegi_verzio:
            return VERZIO
        return ""
    ok = adat.get("ok")
    return ok if ok in _ISMERT else EGYEB
