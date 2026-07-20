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


class IniSaveError(RuntimeError):
    """A dokumentum egyik támogatott kódolással sem írható ki bájtra.

    #133: régen ez csendben (kezeletlen `UnicodeEncodeError`-ral) elveszett
    mentés volt — helyette a hívó itt explicit hibát kap."""


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
    text = document.serialize()
    try:
        payload = text.encode(document.encoding)
    except UnicodeEncodeError as exc:
        if document.encoding == "utf-8":
            # UTF-8 gyakorlatilag minden érvényes str-t kódol; ha mégsem
            # sikerül, ez valódi, nem a legacy-kódolásból eredő hiba —
            # nem nyeljük el csendben (#133).
            raise IniSaveError(
                f"A .picasa.ini nem menthető ({document.encoding}): {exc}"
            ) from exc
        # Régi (latin-1/CP125x) fájlba nem illeszkedő (pl. ékezetes magyar)
        # szöveg került: dokumentált szabály szerint a mentés UTF-8-ra vált
        # — a fájl ezután olvasható marad, csak a kódolása módosul. Amíg a
        # tartalom a legacy kódolással is kifejezhető lett volna, nem
        # térünk el tőle (kevesebb felesleges byte-eltérés a régi Picasa
        # felé), ezért ez csak a hibaágban történik meg.
        document = replace(document, encoding="utf-8")
        try:
            payload = text.encode("utf-8")
        except UnicodeEncodeError as utf8_exc:  # pragma: no cover — gyakorlatilag elérhetetlen
            raise IniSaveError(
                f"A .picasa.ini nem menthető UTF-8-ként sem: {utf8_exc}"
            ) from utf8_exc
    if document.bom:
        payload = _BOM + payload
    if backup and target.exists():
        _write_backup(target)
    write_atomic(target, payload)


def _write_backup(target: Path) -> None:
    backup_path = target.with_name(target.name + ".bak")
    # Közös helper (#129): fsync + jogmegőrzés + atomikus csere.
    write_atomic(backup_path, target.read_bytes())
