"""Az önfrissítés után megmaradt telepítőfájlok helyreállítása."""

from __future__ import annotations

import logging
from pathlib import Path
import shutil
import sys
import threading

logger = logging.getLogger(__name__)
_ELTAVOLITO_KITERJESZTESEK = frozenset({".exe", ".dat", ".msg"})
_thread = threading.Thread


def _eltavolito_fajlok(mappa: Path) -> list[Path]:
    """Az Inno Setup eltávolító fájljait adja vissza a mappa gyökeréből."""
    if not mappa.is_dir():
        return []
    return sorted(
        fajl
        for fajl in mappa.iterdir()
        if fajl.is_file()
        and fajl.name.casefold().startswith("unins")
        and fajl.suffix.casefold() in _ELTAVOLITO_KITERJESZTESEK
    )


def _masold_at_a_hianyzo_eltavolitokat(elod: Path, telepites: Path) -> None:
    """Átmásolja azokat az eltávolító fájlokat, amelyek még hiányoznak."""
    for forras in _eltavolito_fajlok(elod):
        cel = telepites / forras.name
        if cel.exists() or cel.is_symlink():
            continue
        shutil.copy2(forras, cel)


def mentsd_at_az_eltavolitot(elod: Path, telepites: Path) -> None:
    """A régi mappa eltávolító fájljait a telepítésbe menti, ha ott hiányoznak.

    A segéd hívja a régi mappa törlése ELŐTT; ha a telepítési mappa nem
    létezik, nincs hová menteni."""
    if Path(telepites).is_dir():
        _masold_at_a_hianyzo_eltavolitokat(Path(elod), Path(telepites))


def finalize_successful_update(install_dir: Path) -> None:
    """A sikeresen ellenőrzött új telepítés után törli az előző mappát."""
    install_dir = Path(install_dir)
    previous_dir = install_dir.with_name(f"{install_dir.name}.previous")
    _masold_at_a_hianyzo_eltavolitokat(previous_dir, install_dir)
    shutil.rmtree(previous_dir, ignore_errors=True)


def cleanup_previous_installation(install_dir: Path) -> None:
    """Eltávolítót állít helyre induláskor, ha a régi mappában maradt."""
    install_dir = Path(install_dir)
    previous_dir = install_dir.with_name(f"{install_dir.name}.previous")
    if not _eltavolito_fajlok(previous_dir):
        return
    _masold_at_a_hianyzo_eltavolitokat(previous_dir, install_dir)
    shutil.rmtree(previous_dir, ignore_errors=True)


def _platform() -> str:
    """Platformfogantyú az induláskori takarításhoz."""
    return sys.platform


def _frozen() -> bool:
    """Igaz, ha csomagolt futásban indul a program."""
    return bool(getattr(sys, "frozen", False))


def _executable_path() -> Path:
    """A futó program végrehajtható fájlját adja vissza."""
    return Path(sys.executable)


def start_startup_cleanup() -> None:
    """Csomagolt Windows-futásnál háttérszálon helyreállítja az eltávolítót."""
    if _platform() != "win32" or not _frozen():
        return

    try:
        install_dir = _executable_path().resolve().parent

        def takarits() -> None:
            try:
                cleanup_previous_installation(install_dir)
            except Exception:
                logger.exception("Az induláskori eltávolító-takarítás nem sikerült")

        szal = _thread(
            target=takarits,
            name="picasapy-update-cleanup",
            daemon=True,
        )
        szal.start()
    except Exception:
        logger.exception("Az induláskori eltávolító-takarító szál nem indult el")
