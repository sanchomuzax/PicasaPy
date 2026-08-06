"""Az adatbázis+cache egyesített gyökerének felülbírálása (#368).

Alapból az XDG-alapértelmezés érvényes (`application.py` `_data_dir`/
`_cache_dir`-je): index-SQLite a `$XDG_DATA_HOME/picasapy`, thumbnail-
cache a `$XDG_CACHE_HOME/picasapy/thumbs` alatt.

A "Move Database" dialógus (`MoveDatabaseDialog.qml`) sikeres áthelyezés
után egyetlen szöveges fájlba írja az ÚJ, EGYESÍTETT adatgyökeret — ez a
Picasa "Move on next restart" viselkedésének felel meg: a FUTÓ példány
útvonalai menet közben nem változnak, csak a KÖVETKEZŐ indítás olvassa az
új helyet. A fájl formátuma szándékosan a lehető legegyszerűbb (egyetlen
sor, a mappa abszolút útvonala) — nincs benne semmi, amit nem ért a
felhasználó, ha kézzel belenéz."""

from __future__ import annotations

from pathlib import Path

_OVERRIDE_FILENAME = "data-location.txt"


def override_file(config_dir: Path) -> Path:
    """Az útvonal-felülbírálást tartalmazó fájl helye — nem feltétlenül
    létezik (ekkor az XDG-alapértelmezés marad érvényben)."""
    return Path(config_dir) / _OVERRIDE_FILENAME


def read_data_root(config_dir: Path) -> Path | None:
    """A felülbírált, egyesített adatgyökér, ha van érvényes bejegyzés;
    egyébként `None` — ekkor a hívó az XDG-alapértelmezésre esik vissza."""
    path = override_file(config_dir)
    try:
        text = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return Path(text) if text else None


def write_data_root(config_dir: Path, new_root: Path) -> None:
    """Az új, egyesített adatgyökér elmentése — a KÖVETKEZŐ indítástól
    érvényes (a jelenleg futó példányt nem érinti)."""
    config_dir = Path(config_dir)
    config_dir.mkdir(parents=True, exist_ok=True)
    override_file(config_dir).write_text(str(Path(new_root)), encoding="utf-8")


def clear_data_root(config_dir: Path) -> None:
    """A felülbírálás törlése — a következő indulástól újra az
    XDG-alapértelmezés lesz érvényben (pl. a "Default" gomb + tényleges
    visszaköltöztetés után)."""
    override_file(config_dir).unlink(missing_ok=True)
