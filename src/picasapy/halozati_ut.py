"""Hálózati útvonal elérhetősége: időkorláttal és gyorsítótárral (#6344, #6349, #7048).

## Miért

A tulajdonos gépén a felület 41 s-ig épült fel, futás közben pedig 11–38 s-os
fagyások jöttek; a fő szál-figyelő szerint (#6349) mindegyik egy `stat()` volt
a fő szálon: a navigáció exportcéljain (`existing_exported_folders`) és egy
`.picasa.ini` keresésén (`ini_source_path`). Az indexben `\\\\NAS\\megosztás\\…`
alakú exportmappák vannak; ha a NAS nem érhető el, a Windows MINDEN ilyen
hívásnál kivárja a hálózati időkorlátot (20–40 s).

## Hogyan

Az ellenőrzés a megosztás GYÖKERÉRE megy (`\\\\szerver\\megosztás\\`), egy
háttérszálon, `IDOKORLAT_S` határidővel. Ha addig nem válaszol, a gyökér
elérhetetlennek számít — `ELERHETETLEN_TTL_S` ideig minden további kérdés
azonnal választ kap. Ez UGYANAZ a kimenet, amit a hívó eddig is kapott
(`is_file()`/`is_dir()` hamis), csak nem 20–40 s, hanem legfeljebb fél
másodperc múlva, és utána egy percig semennyi.

Nem hálózati útvonalra (helyi lemez) a válasz azonnali igen, lemezművelet
nélkül. Linuxon a hálózati mountpontot a helyi `/proc/self/mounts` táblából
azonosítjuk, aztán ugyanilyen időkorlátos háttérpróba ellenőrzi.
"""

from __future__ import annotations

import ntpath
import os
import posixpath
import re
import sys
import threading
import time
from pathlib import Path, PureWindowsPath

#: ennyit vár a fő szál egy ismeretlen állapotú megosztás válaszára
IDOKORLAT_S = 0.5
#: ennyi ideig hisszük el, hogy egy megosztás elérhetetlen / elérhető
ELERHETETLEN_TTL_S = 60.0
ELERHETO_TTL_S = 300.0

#: a gyökér létezésének lekérdezése — modulszintű fogantyú a tesztnek (#1375)
_letezik = os.path.isdir
_ora = time.monotonic

_zar = threading.Lock()
#: gyökér → (elérhető-e, meddig érvényes)
_allapot: dict[str, tuple[bool, float]] = {}
#: gyökér → a folyamatban lévő próba vége
_folyamatban: dict[str, threading.Event] = {}
_mount_cache_lock = threading.Lock()
_mount_cache_until = 0.0
_mount_cache: tuple[tuple[str, str], ...] = ()

_NETWORK_FILESYSTEMS = {
    "9p",
    "afs",
    "ceph",
    "cifs",
    "davfs",
    "glusterfs",
    "nfs",
    "nfs4",
    "smb3",
    "sshfs",
    "fuse.gvfsd-fuse",
    "fuse.sshfs",
    "fuse.rclone",
    "fuse.s3fs",
    "fuse.goofys",
    "fuse.davfs",
}


def _platform() -> str:
    """A platform cserélhető fogantyúja (#1217)."""
    return sys.platform


def _mount_records() -> tuple[tuple[str, str], ...]:
    """A Linux mount-tábla (csatolási pont, fájlrendszertípus) gyorsítótárral.

    A `/proc/self/mounts` olvasása helyi procfs-művelet; nem kérdez le
    csatolt fájlrendszert. A 100 ms-os gyorsítótár az útvonal-normalizálásnál
    kerüli az ismételt feldolgozást, de gyorsan észleli az új GVFS mountot is.
    """
    global _mount_cache_until, _mount_cache
    now = time.monotonic()
    with _mount_cache_lock:
        if now < _mount_cache_until:
            return _mount_cache

    records = []
    try:
        with open("/proc/self/mounts", encoding="utf-8") as mounts:
            for line in mounts:
                fields = line.split()
                if len(fields) < 3:
                    continue
                mountpoint = re.sub(
                    r"\\([0-7]{3})",
                    lambda match: chr(int(match.group(1), 8)),
                    fields[1],
                )
                records.append((posixpath.normpath(mountpoint), fields[2].casefold()))
    except OSError:
        records = []

    with _mount_cache_lock:
        _mount_cache = tuple(
            sorted(records, key=lambda item: len(item[0]), reverse=True)
        )
        _mount_cache_until = time.monotonic() + 0.1
        return _mount_cache


def _query_dos_device(drive: str) -> str | None:
    """A meghajtóbetű DOS-eszközcélja hálózati lekérdezés nélkül."""
    try:
        import ctypes

        buffer = ctypes.create_unicode_buffer(4096)
        if ctypes.windll.kernel32.QueryDosDeviceW(drive, buffer, len(buffer)):
            return buffer.value
    except (AttributeError, OSError):
        return None
    return None


def _mapped_drive_is_network(drive: str) -> bool:
    target = (_query_dos_device(drive.upper()) or "").casefold()
    return target.startswith(
        (
            "\\device\\mup\\",
            "\\device\\lanmanredirector\\",
            "\\device\\webdavredirector\\",
            "\\device\\rdbss\\",
        )
    )


def fajlrendszer_gyoker(
    path: str | Path, *, platform: str | None = None
) -> str | None:
    """A hálózati út gyökere: UNC/meghajtóbetű vagy Linuxos mountpont.

    Linuxon a csatolási pontot kizárólag a helyi `/proc/self/mounts` táblából
    azonosítja, ezért a felismerés maga nem ér hozzá a hálózati fájlrendszerhez.
    A POSIX `//` útvonalat nem tekinti UNC-nek.
    """
    szoveg = str(path)
    futasi_platform = _platform() if platform is None else platform
    unc = halozati_gyoker(szoveg)
    # Régi tesztek és hívók Windowst UNC-t Linuxon is szimulálnak `\\`-sel;
    # a POSIX `//` viszont csak Windowson jelent UNC-t.
    if unc is not None and (
        futasi_platform.startswith("win") or szoveg.startswith("\\\\")
    ):
        return unc

    if futasi_platform.startswith("win"):
        drive, _tail = ntpath.splitdrive(szoveg)
        if len(drive) == 2 and drive[1] == ":" and _mapped_drive_is_network(drive):
            return drive.upper() + "\\"
        return None

    if futasi_platform.startswith("linux"):
        absolute = posixpath.normpath(posixpath.abspath(szoveg))
        for mountpoint, fstype in _mount_records():
            if fstype not in _NETWORK_FILESYSTEMS:
                continue
            prefix = mountpoint.rstrip("/")
            if absolute == mountpoint or absolute.startswith(prefix + "/"):
                return mountpoint
    return None


def is_network_path(path: str | Path, *, platform: str | None = None) -> bool:
    """Igaz, ha az út hálózati megosztásra vagy Linuxos hálózati mountra esik."""
    return fajlrendszer_gyoker(path, platform=platform) is not None


def halozati_gyoker(path: str | Path) -> str | None:
    """A UNC-útvonal megosztás-gyökere (`\\\\szerver\\megosztás\\`), kisbetűsen;
    nem hálózati útvonalra `None`."""
    szoveg = str(path)
    if not szoveg.startswith(("\\\\", "//")):
        return None
    horgony = PureWindowsPath(szoveg).anchor
    if not horgony or horgony.strip("\\/") == "":
        return None
    return horgony.lower()


def elerheto(path: str | Path, *, idokorlat_s: float | None = None) -> bool:
    """Elérhető-e az útvonal megosztása. Nem hálózati útvonalra mindig igaz.

    Legfeljebb `idokorlat_s` másodpercig blokkol (alapból `IDOKORLAT_S`),
    utána a választ a gyorsítótárból adja."""
    gyoker = fajlrendszer_gyoker(path)
    if gyoker is None:
        return True
    most = _ora()
    with _zar:
        tarolt = _allapot.get(gyoker)
        if tarolt is not None and most < tarolt[1]:
            return tarolt[0]
        esemeny = _folyamatban.get(gyoker)
        if esemeny is None:
            esemeny = threading.Event()
            _folyamatban[gyoker] = esemeny
            threading.Thread(
                target=_probald,
                args=(gyoker, esemeny),
                name="picasapy-halozati-ut",
                daemon=True,
            ).start()
    esemeny.wait(IDOKORLAT_S if idokorlat_s is None else idokorlat_s)
    with _zar:
        tarolt = _allapot.get(gyoker)
        if tarolt is not None and esemeny.is_set():
            return tarolt[0]
        # a határidőn túl: elérhetetlennek számít, amíg a próba be nem fejeződik
        _allapot[gyoker] = (False, _ora() + ELERHETETLEN_TTL_S)
        return False


def _probald(gyoker: str, esemeny: threading.Event) -> None:
    try:
        ok = bool(_letezik(gyoker))
    except OSError:
        ok = False
    with _zar:
        _allapot[gyoker] = (
            ok,
            _ora() + (ELERHETO_TTL_S if ok else ELERHETETLEN_TTL_S),
        )
        _folyamatban.pop(gyoker, None)
    esemeny.set()


def _alaphelyzet() -> None:
    """Csak teszteknek: a gyorsítótár ürítése."""
    global _mount_cache_until, _mount_cache
    with _zar:
        _allapot.clear()
        _folyamatban.clear()
    with _mount_cache_lock:
        _mount_cache = ()
        _mount_cache_until = 0.0
