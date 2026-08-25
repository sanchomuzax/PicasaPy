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
nem-atomikus direkt-írás végső fallbackként (képfájlnál elfogadható),
párhuzamos írók versenyének tűrése (thumbnail-cache).
"""

from __future__ import annotations

import contextlib
import os
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
    - fallback_direct: ha a zár nem enged fel, nem-atomikus közvetlen írás
      a célfájlba (képfájlnál elfogadható; ini-nél tilos).
    - ignore_replace_race: ha a csere hibája után a cél már létezik (egy
      párhuzamos író nyert), a hiba lenyelhető.
    """
    target = Path(target)
    if make_parents:
        target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(
        dir=target.parent, prefix=f"{target.name}.", suffix=suffix
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
            payload,
            lock_retries=lock_retries,
            lock_retry_delay=lock_retry_delay,
            fallback_direct=fallback_direct,
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
    payload: bytes,
    *,
    lock_retries: int,
    lock_retry_delay: float,
    fallback_direct: bool,
    ignore_replace_race: bool,
) -> None:
    """`os.replace` a paraméterezett hibautakkal (retry, fallback, verseny)."""
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
            if not fallback_direct:
                raise
            break
        except OSError:
            if ignore_replace_race and target.exists():
                # A cél közben (egy párhuzamos írótól) létrejött — a
                # vesztes fél dolga kész, a temp fájlt eltakarítjuk.
                _remove_quietly(temp_name)
                return
            raise
    # Végső fallback: a zár nem engedett fel → nem-atomikus közvetlen írás.
    target.write_bytes(payload)
    _remove_quietly(temp_name)


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
