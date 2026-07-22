"""Fájl-I/O: betöltés kódolás-felismeréssel, atomikus mentés backuppal.

Írási szabályok a specből: temp fájl + rename (atomikus), opcionális backup
írás előtt, BOM és kódolás megőrzése a byte-pontos round-triphez.
"""

from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path
from typing import Callable

from picasapy.ioutil import write_atomic

from .document import NO_SOURCE_FILE, IniDocument, SourceFingerprint, parse_document

_BOM = b"\xef\xbb\xbf"


class IniSaveError(RuntimeError):
    """A dokumentum egyik támogatott kódolással sem írható ki bájtra.

    #133: régen ez csendben (kezeletlen `UnicodeEncodeError`-ral) elveszett
    mentés volt — helyette a hívó itt explicit hibát kap."""


class IniConflictError(RuntimeError):
    """Az `update_document` a `max_retries` újrapróbálkozás alatt sem tudott
    ütközésmentesen menteni (#137): a fájlt egy párhuzamos író (pl. a futó
    eredeti Picasa) minden egyes betöltés–mentés ablakban módosította.

    A hívó ezt jelzésként kezelheti (pl. újrapróbál később), a lényeg, hogy
    a beavatkozó írás NEM íródik felül csendben (lost update kizárva)."""


def _fingerprint_from_bytes(target: Path, raw: bytes) -> SourceFingerprint:
    """Egy létező fájl ujjlenyomata a már beolvasott bájtokból (nincs második
    olvasás). A hash a NYERS (BOM-ostul) lemezes tartalomból készül."""
    return SourceFingerprint(
        exists=True,
        size=len(raw),
        digest=hashlib.sha256(raw).hexdigest(),
        mtime_ns=target.stat().st_mtime_ns,
    )


def _fingerprint_of(path: str | Path) -> SourceFingerprint:
    """A cél jelenlegi lemezállapotának ujjlenyomata; hiányzó fájlra a
    `NO_SOURCE_FILE` sentinel. Az ütközés-újraellenőrzéshez (mentés előtt)
    frissen olvassa a fájlt."""
    target = Path(path)
    try:
        raw = target.read_bytes()
    except FileNotFoundError:
        return NO_SOURCE_FILE
    return _fingerprint_from_bytes(target, raw)


def load_document(path: str | Path) -> IniDocument:
    target = Path(path)
    raw = target.read_bytes()
    fingerprint = _fingerprint_from_bytes(target, raw)
    bom = raw.startswith(_BOM)
    body = raw[len(_BOM) :] if bom else raw
    try:
        text, encoding = body.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        # Régi, nem UTF-8 Picasa-fájl: a latin-1 byte-őrző, így a
        # round-trip visszaírás bitre pontos marad.
        text, encoding = body.decode("latin-1"), "latin-1"
    return replace(
        parse_document(text),
        encoding=encoding,
        bom=bom,
        source_fingerprint=fingerprint,
    )


def load_or_empty(path: str | Path) -> IniDocument:
    """A dokumentum betöltése, vagy üres dokumentum, ha a fájl nem létezik.

    #151/7: a `load_document(p) if p.exists() else parse_document("")`
    minta közös helpere — a controllerek eddig 6 helyen ismételték.

    #137: a hiányzó fájlhoz a `NO_SOURCE_FILE` ujjlenyomat társul, hogy az
    `update_document` a „még nem létezett" esetet is ütközésként ismerje fel,
    ha időközben egy párhuzamos író létrehozza a fájlt."""
    target = Path(path)
    if not target.exists():
        return replace(parse_document(""), source_fingerprint=NO_SOURCE_FILE)
    return load_document(target)


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


def update_document(
    path: str | Path,
    mutate: Callable[[IniDocument], IniDocument],
    *,
    backup: bool = True,
    max_retries: int = 3,
) -> IniDocument:
    """Ütközésbiztos betöltés → módosítás → atomikus mentés (#137).

    A `.picasa.ini`-t párhuzamosan a futó eredeti Picasa is írhatja ugyanazon
    a NAS-mappán. A sima `load → módosít → save_document` némán felülírná, amit
    a Picasa időközben írt (lost update — pl. egy frissen adott csillag
    elveszne). Ez a helper ezt zárja ki:

    1. betölti a dokumentumot (a `load_or_empty` révén az ujjlenyomatával),
    2. a `mutate` TISZTA függvénnyel előállítja a módosítottat,
    3. mentés ELŐTT újraolvassa a fájl aktuális ujjlenyomatát; ha az eltér a
       betöltéskoritól (egy párhuzamos író közben módosított), eldobja a
       munkát, frissen újratölt, és a `mutate`-et ÚJRAJÁTSSZA az új
       dokumentumon — így a másik író változása ÉS a miénk is megmarad,
    4. ha egyeznek, atomikusan (backuppal) ment.

    A `mutate` KULCS-szintű, immutábilis módosítás legyen (`with_value` /
    `with_removed` / …) és mellékhatásmentes, mert újrajátszásra kerülhet — a
    merge így biztonságos: a friss (más író általi) sorok érintetlenek
    maradnak, csak a mi kulcsaink íródnak felül.

    Returns:
        A ténylegesen kimentett dokumentum (a nyertes betöltésre alkalmazott
        `mutate` eredménye).

    Raises:
        IniConflictError: ha `max_retries` próbálkozás alatt sem sikerült
            beavatkozás nélküli ablakot fogni.
    """
    target = Path(path)
    for _ in range(max_retries + 1):
        document = load_or_empty(target)
        mutated = mutate(document)
        # Mentés előtti újraellenőrzés: változott-e a fájl a betöltés óta?
        # (A tartalom-hash a döntő; az mtime önmagában nem megbízható.)
        if _fingerprint_of(target) == document.source_fingerprint:
            save_document(mutated, target, backup=backup)
            return mutated
        # Ütközés: egy párhuzamos író közbeírt — friss újratöltés + újrajátszás.
    raise IniConflictError(
        f"A(z) {target} tartósan változott egy párhuzamos író miatt; a mentés "
        f"{max_retries + 1} próbálkozás után sem volt ütközésmentes."
    )


def _write_backup(target: Path) -> None:
    backup_path = target.with_name(target.name + ".bak")
    # Közös helper (#129): fsync + jogmegőrzés + atomikus csere.
    write_atomic(backup_path, target.read_bytes())
