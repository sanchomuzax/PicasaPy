"""Közös atomikus fájlírás (#129): temp fájl + fsync + jogmegőrzés + csere.

Minden fájlt cserélő írás (`.picasa.ini`, IPTC-s JPEG, thumbnail-cache,
export) ezen az egy helperen fut, hogy két garancia egységes legyen:

1. **Tartósság** — a temp fájl tartalma `fsync`-kel lemezre kerül, MIELŐTT
   az `os.replace` a cél helyére teszi; áramszünet/crash esetén sem
   maradhat csonka célfájl. POSIX-on a könyvtárbejegyzés is fsync-elődik.
2. **Jogmegőrzés** — a `mkstemp` 0600-as temp fájlja megkapja a meglévő
   célfájl jogait, így NAS-on a többi kliens (az eredeti Picasa is)
   olvashatja tovább a fájlt.

A viselkedés hívónként paraméterezhető: retry zárolt célfájlra (Windows),
a párhuzamos írók versenyének tűrése (thumbnail-cache). A korábbi direkt-
írási fallback paramétere megmaradt kompatibilitásra, de a csonkulásveszély
miatt már nem végez helyben írást.
"""

from __future__ import annotations

import contextlib
import ctypes
import hashlib
import os
import socket
import stat
import sys
import tempfile
import time
from pathlib import Path

#: Az atomikus írás standard lépéseinek MODULSZINTŰ fogantyúi (#1375) — a
#: teszt EZEKET cserélje: `monkeypatch.setattr(ioutil, "_replace", …)`.
#:
#: A `monkeypatch.setattr(ioutil.os, "replace", …)` alak nem a modult
#: módosítja: az `ioutil.os` MAGA a globális `os` modul. Az `os.replace`-t
#: pedig épp ez a modul adja az egész programnak — ha a hibaút szimulációja
#: globálisan hat, a teszt saját takarítása és minden párhuzamosan futó
#: mentés is ráfut a hamis kivételre.
_replace = os.replace
_fsync = os.fsync
_fdopen = os.fdopen
_mkstemp = tempfile.mkstemp
_ATOMIC_TEMP_MARKER = ".picasapy-atomic-"
_ATOMIC_TEMP_HOST = hashlib.sha256(socket.gethostname().encode("utf-8")).hexdigest()[:12]


def write_atomic(
    target: str | Path,
    payload: bytes,
    *,
    durable: bool = True,
    preserve_mode: bool = True,
    make_parents: bool = False,
    lock_retries: int = 0,
    lock_retry_delay: float = 0.05,
    fallback_direct: bool = False,
    ignore_replace_race: bool = False,
    suffix: str = ".tmp",
) -> None:
    """`payload` atomikus írása a `target` helyére temp fájl + csere úton.

    Paraméterek:
    - durable: fsync a temp fájlra (és POSIX-on a könyvtárra) a csere körül.
      Csak újragenerálható tartalomnál (cache) kapcsolható ki.
    - preserve_mode: meglévő célfájl jogainak átvétele a temp fájlra.
    - make_parents: hiányzó szülőkönyvtárak létrehozása.
    - lock_retries: ennyi ÚJRApróbálkozás `PermissionError`-ra (Windowson a
      nyitott célfájl zárolja a cserét), növekvő várakozással.
    - fallback_direct: a régi hívásokkal való kompatibilitás miatt elfogadott,
      de a közvetlen írás adatvesztési kockázata miatt figyelmen kívül hagyott.
    - ignore_replace_race: ha a csere hibája után a cél már létezik (egy
      párhuzamos író nyert), a hiba lenyelhető.
    """
    target = Path(target)
    if make_parents:
        target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = _mkstemp(
        dir=target.parent,
        prefix=f"{_ATOMIC_TEMP_MARKER}{_ATOMIC_TEMP_HOST}-{os.getpid()}-",
        suffix=suffix,
    )
    try:
        try:
            handle = _fdopen(fd, "wb")
        except BaseException:
            # Az os.fdopen nem vette át a mkstemp nyers fd-jét → nekünk kell
            # lezárni, különben Windowson a nyitott fd megakadályozza a temp
            # fájl törlését (a takarítás csendben elbukna, a .tmp ottragadna).
            os.close(fd)
            raise
        with handle:
            handle.write(payload)
            if durable:
                handle.flush()
                _fsync(handle.fileno())
        if preserve_mode and target.exists():
            os.chmod(temp_name, stat.S_IMODE(target.stat().st_mode))
        _replace_temp(
            temp_name,
            target,
            lock_retries=lock_retries,
            lock_retry_delay=lock_retry_delay,
            ignore_replace_race=ignore_replace_race,
        )
    except BaseException:
        _remove_quietly(temp_name)
        raise
    if durable:
        _fsync_directory(target.parent)


def _replace_temp(
    temp_name: str,
    target: Path,
    *,
    lock_retries: int,
    lock_retry_delay: float,
    ignore_replace_race: bool,
) -> None:
    """`os.replace` paraméterezett hibautakkal (retry, versenytűrés)."""
    for attempt in range(lock_retries + 1):
        try:
            _replace(temp_name, target)
            return
        except PermissionError:
            # Windowson a sharing violation is PermissionError, ezért a
            # verseny-tűrés erre az ágra is vonatkozik (a retry után).
            if attempt < lock_retries:
                time.sleep(lock_retry_delay * (attempt + 1))
                continue
            if ignore_replace_race and target.exists():
                _remove_quietly(temp_name)
                return
            # A `fallback_direct` kérés kompatibilitási okból megmarad a
            # nyilvános hívási alakban, de zárolt célra sem írunk rá közvetlenül:
            # megszakadáskor vagy ENOSPC esetén csonka eredeti maradna.
            raise
        except OSError:
            if ignore_replace_race and target.exists():
                # A cél közben (egy párhuzamos írótól) létrejött — a
                # vesztes fél dolga kész, a temp fájlt eltakarítjuk.
                _remove_quietly(temp_name)
                return
            raise


def cleanup_orphaned_atomic_temps(directory: Path, entries) -> int:
    """Eltávolítja a megszakadt atomikus írások tempfájljait a bejárt mappából.

    A mappabejáró átadja az amúgy is beolvasott DirEntry-listát, ezért ez nem
    indít új fájlrendszer-bejárást. A saját gépről származó fájlt csak akkor
    töröljük, ha a névben jelölt folyamat már nem fut; másik gép tempfájlját
    csak 24 óránál régebben takarítjuk, hogy NAS-on se töröljünk élő írást.
    """
    directory = Path(directory)
    removed = 0
    now = time.time()
    for entry in entries:
        name = entry.name
        if not name.startswith(_ATOMIC_TEMP_MARKER):
            continue
        try:
            _, _, host, pid_text, _random = name.split("-", 4)
            pid = int(pid_text)
            info = entry.stat(follow_symlinks=False)
        except (OSError, ValueError):
            continue
        if not stat.S_ISREG(info.st_mode):
            continue
        local_process_alive = host == _ATOMIC_TEMP_HOST and _process_is_alive(pid)
        if local_process_alive or (
            host != _ATOMIC_TEMP_HOST and now - info.st_mtime < 24 * 60 * 60
        ):
            continue
        try:
            (directory / name).unlink()
        except OSError:
            continue
        removed += 1
    return removed


def _process_is_alive(pid: int) -> bool:
    """A tempnevet létrehozó folyamat él-e ezen a gépen?"""
    if pid <= 0:
        return False
    if _platform() == "win32":
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        open_process = kernel32.OpenProcess
        open_process.argtypes = (ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32)
        open_process.restype = ctypes.c_void_p
        handle = open_process(0x00100000, 0, pid)  # SYNCHRONIZE
        if not handle:
            # ERROR_ACCESS_DENIED azt jelenti, hogy létezik, csak nem kérdezhető.
            return ctypes.get_last_error() == 5
        try:
            wait = kernel32.WaitForSingleObject
            wait.argtypes = (ctypes.c_void_p, ctypes.c_uint32)
            wait.restype = ctypes.c_uint32
            return wait(handle, 0) == 0x00000102  # WAIT_TIMEOUT = még fut
        finally:
            close = kernel32.CloseHandle
            close.argtypes = (ctypes.c_void_p,)
            close.restype = ctypes.c_int
            close(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _remove_quietly(temp_name: str) -> None:
    # A takarítás best-effort: sosem takarhatja el az eredeti hibát, és egy
    # ottragadt zár (Windows) sem buktathatja meg a hívást — a temp fájl
    # legrosszabb esetben ottmarad, de kivételt innen nem engedünk ki.
    with contextlib.suppress(OSError):
        os.unlink(temp_name)


def _platform() -> str:
    """A futó platform — külön függvény, hogy a teszt helyettesíthesse (#1217)."""
    return sys.platform


def _fsync_directory(directory: Path) -> None:
    """A rename tartósságához a könyvtárbejegyzést is ki kell írni.

    Csak POSIX-on lehetséges (Windowson könyvtár nem nyitható fd-ként;
    ott az os.replace enélkül is atomikus).

    ⚠️ #1217: az ág korábban közvetlenül `os.name != "posix"`-ot nézett.
    Ugyanaz a döntés, más szótárral — de fogantyú nélkül, így a windowsos
    ágat a linuxos teszt nem tudta kimondani (és fordítva). A CPython
    `os.name`-je `"posix"` vagy `"nt"`, tehát a „nem POSIX" pontosan a
    windowsos esetet jelentette; a feltétel most ezt mondja ki."""
    if _platform().startswith("win"):
        return
    dir_fd = os.open(directory, os.O_RDONLY)
    try:
        _fsync(dir_fd)
    finally:
        os.close(dir_fd)
