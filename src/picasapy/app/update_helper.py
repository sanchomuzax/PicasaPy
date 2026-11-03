"""Az önfrissítő telepítési környezetének és segédindításának műveletei."""

from __future__ import annotations

import logging
import os
from pathlib import Path
import tempfile

KILEPESI_HATARIDO_MP = 20.0


def installation_kind(
    *,
    frozen: bool | None = None,
    platform: str | None = None,
    executable: str | None = None,
    package_path: str | Path | None = None,
) -> str:
    """A csomagfajtát futásidőben azonosítja: `windows`, `deb` vagy `pip`."""
    import sys

    frozen = bool(getattr(sys, "frozen", False)) if frozen is None else frozen
    platform = os.name if platform is None else platform
    executable = sys.executable if executable is None else executable
    if frozen and platform == "nt":
        return "windows"
    executable_path = Path(executable).resolve()
    installed_module = Path(package_path or __file__).resolve().as_posix()
    if platform != "nt" and (
        "/usr/lib/python3/dist-packages/" in installed_module
        or ("/usr/lib/python3." in installed_module and "/dist-packages/" in installed_module)
        or "/usr/lib/python3/dist-packages" in executable_path.as_posix()
        or Path("/usr/share/doc/picasapy").is_dir()
    ):
        return "deb"
    return "pip"


def mappa_irhato(folder: Path) -> bool:
    """Írhat-e a felhasználó a mappába — kipróbálva, nem az ACL-ből találgatva.

    A telepítési mappa cseréje a SZÜLŐ mappába ír (átnevezés). A felhasználói
    telepítésnél (`%LOCALAPPDATA%\\Programs`) ez UAC nélkül megy; csak a
    `Program Files` alá telepített program kér rendszergazdai jogot."""
    try:
        fd, proba = tempfile.mkstemp(prefix=".picasapy-irasproba-", dir=folder)
    except OSError:
        return False
    os.close(fd)
    try:
        os.unlink(proba)
    except OSError:
        pass
    return True


def kenyszeritett_kilepes_ha_beragad(
    hatarido_mp: float,
    *,
    azonnali_kilepes,
    logger: logging.Logger,
) -> None:
    """Határidővel lezárja a folyamatot, ha a rendes kilépés beragad."""
    import threading

    def _kilepes() -> None:
        logger.warning("A lezárás %.0f s alatt nem fejeződött be; kilépés a frissítéshez", hatarido_mp)
        logging.shutdown()
        azonnali_kilepes(0)

    idozito = threading.Timer(hatarido_mp, _kilepes)
    idozito.daemon = True
    idozito.start()


def inditsd_a_segedet(args: list[str], *, emelt: bool, platform: str) -> bool:
    """A frissítő segéd indítása; UAC-ot csak akkor kér, ha `emelt` (#6340)."""
    import subprocess

    if platform != "win32":
        subprocess.Popen(args, close_fds=True)
        return True
    import ctypes

    params = subprocess.list2cmdline(args[1:])
    result = ctypes.windll.shell32.ShellExecuteW(
        None, "runas" if emelt else "open", str(args[0]), params, None, 0
    )
    if result <= 32:
        _UTOLSO_HIBA["szoveg"] = f"ShellExecute {result}"
        return False
    _UTOLSO_HIBA["szoveg"] = ""
    return True


#: #6458: az utolsó sikertelen segédindítás oka, a hibaüzenetbe
_UTOLSO_HIBA = {"szoveg": ""}


def utolso_inditasi_hiba() -> str:
    """Az utolsó sikertelen frissítősegéd-indítás oka (pl. „ShellExecute 5”)."""
    return _UTOLSO_HIBA["szoveg"] or "ismeretlen ok"


def update_command(kind: str) -> str:
    if kind == "deb":
        return "sudo apt update && sudo apt install --only-upgrade picasapy"
    return "python -m pip install --upgrade picasapy"
