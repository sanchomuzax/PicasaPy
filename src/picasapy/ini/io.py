"""Fájl-I/O: betöltés kódolás-felismeréssel, atomikus mentés backuppal.

Írási szabályok a specből: temp fájl + rename (atomikus), opcionális backup
írás előtt, BOM és kódolás megőrzése a byte-pontos round-triphez.
"""

from __future__ import annotations

import os
import stat
import tempfile
from dataclasses import replace
from pathlib import Path

from .document import IniDocument, parse_document

_BOM = b"\xef\xbb\xbf"


def load_document(path: str | Path) -> IniDocument:
    raw = Path(path).read_bytes()
    bom = raw.startswith(_BOM)
    if bom:
        raw = raw[len(_BOM) :]
    try:
        text, encoding = raw.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        # Régi, nem UTF-8 Picasa-fájl: a latin-1 byte-őrző, így a
        # round-trip visszaírás bitre pontos marad.
        text, encoding = raw.decode("latin-1"), "latin-1"
    return replace(parse_document(text), encoding=encoding, bom=bom)


def save_document(
    document: IniDocument, path: str | Path, *, backup: bool = False
) -> None:
    target = Path(path)
    payload = document.serialize().encode(document.encoding)
    if document.bom:
        payload = _BOM + payload
    if backup and target.exists():
        _write_backup(target)
    _write_atomic(target, payload)


def _write_backup(target: Path) -> None:
    backup_path = target.with_name(target.name + ".bak")
    _write_atomic(backup_path, target.read_bytes())


def _write_atomic(target: Path, payload: bytes) -> None:
    fd, temp_name = tempfile.mkstemp(dir=target.parent, prefix=f"{target.name}.tmp")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        # A mkstemp 0600-at ad; egy meglévő fájl jogait meg kell őrizni,
        # hogy a NAS-on más folyamatok (az eredeti Picasa) is olvashassák.
        if target.exists():
            os.chmod(temp_name, stat.S_IMODE(target.stat().st_mode))
        os.replace(temp_name, target)
    except BaseException:
        os.unlink(temp_name)
        raise
    _fsync_directory(target.parent)


def _fsync_directory(directory: Path) -> None:
    """A rename tartósságához a könyvtárbejegyzést is ki kell írni."""
    dir_fd = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)
