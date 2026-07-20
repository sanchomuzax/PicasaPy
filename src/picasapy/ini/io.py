"""Fájl-I/O: betöltés kódolás-felismeréssel, atomikus mentés backuppal.

Írási szabályok a specből: temp fájl + rename (atomikus), opcionális backup
írás előtt, BOM és kódolás megőrzése a byte-pontos round-triphez.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from picasapy.ioutil import write_atomic

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
    write_atomic(target, payload)


def _write_backup(target: Path) -> None:
    backup_path = target.with_name(target.name + ".bak")
    # Közös helper (#129): fsync + jogmegőrzés + atomikus csere.
    write_atomic(backup_path, target.read_bytes())
