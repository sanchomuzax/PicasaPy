"""Fájl-I/O: betöltés kódolás-felismeréssel, atomikus mentés backuppal.

Írási szabályok a specből: temp fájl + rename (atomikus), opcionális backup
írás előtt, BOM és kódolás megőrzése a byte-pontos round-triphez.

#1320: a párhuzamosan futó eredeti Picasát MAGA AZ INI KIÍRÁSA értesíti —
a Picasa a mappa `.picasa.ini`-jének írási idejét tárolja
(`albumdata_inisync`), és ha a lemezen lévő fájl újabb, újraolvassa. Ehhez
tehát ezen a ponton nincs külön teendő.

#643 / #2491: a `photo_touch` modul emellett megérinti a változott fotók
MTIME-ját is, és ez 2026-09-06 óta **alapértelmezésben BE van kapcsolva**
(`PICASAPY_TOUCH_PHOTO_MTIME=0` kapcsolja ki). A tulajdonos mérése szerint
enélkül a FUTÓ Picasa nem veszi észre a szerkesztésünket, ezzel viszont
azonnal frissül — az ini saját dátuma csak a későbbi, hideg beolvasást
dönti el. Az indoklás a `photo_touch` fejlécében és a
`docs/decisions/photo-mtime-erintes.md` ADR-ben él.
"""

from __future__ import annotations

import hashlib
import os
import threading
from contextlib import contextmanager
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable, Iterator

from picasapy.ioutil import write_atomic

from .document import NO_SOURCE_FILE, IniDocument, SourceFingerprint, parse_document
from .photo_touch import notify_picasa_after_ini_write

_BOM = b"\xef\xbb\xbf"

#: A HELYBEN írás fájlmegnyitó fogantyúja (`save_document(in_place=True)`).
#: #1375 tanulsága szerint MODULSZINTŰ, hogy a teszt EZT cserélhesse — a
#: `builtins.open` cseréje a folyamat összes fájlmegnyitására hatna.
_open = open


@dataclass(slots=True)
class _PathLockEntry:
    """Egy normalizált ini-útvonal reentrant lockja és aktív használói."""

    lock: Any
    users: int = 0


_path_lock_registry_guard = threading.Lock()
_path_lock_registry: dict[str, _PathLockEntry] = {}


@contextmanager
def _ini_path_lock(path: str | Path) -> Iterator[None]:
    """Ugyanazon normalizált útvonal írásait szerializálja a folyamaton belül.

    A registry lock csak a lockobjektum kiválasztásakor van fogva; a fájl-I/O
    alatt kizárólag az adott útvonal saját reentrant lockja tart.
    """
    key = os.path.normcase(str(Path(path).resolve()))
    with _path_lock_registry_guard:
        entry = _path_lock_registry.get(key)
        if entry is None:
            entry = _PathLockEntry(threading.RLock())
            _path_lock_registry[key] = entry
        entry.users += 1

    try:
        with entry.lock:
            yield
    finally:
        # A várakozó szálak is users-ként szerepelnek, ezért az utolsó kilépő
        # után biztonságosan eltávolítható az útvonalhoz tartozó lock.
        with _path_lock_registry_guard:
            entry.users -= 1
            if entry.users == 0 and _path_lock_registry.get(key) is entry:
                del _path_lock_registry[key]


class IniSaveError(RuntimeError):
    """A dokumentum egyik támogatott kódolással sem írható ki bájtra.

    #133: régen ez csendben (kezeletlen `UnicodeEncodeError`-ral) elveszett
    mentés volt — helyette a hívó itt explicit hibát kap."""


class IniConflictError(RuntimeError):
    """Minden próbálkozás során észlelt fájlváltozás miatt a mentés elmaradt.

    Az `update_document` a betöltés és az előzetes ujjlenyomat-ellenőrzés
    között látott változásra újrapróbál. Ez nem zárja ki a külső írást az
    utolsó ellenőrzés és az atomikus csere közötti rövid ablakban.
    """


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


def _ini_source_path(path: str | Path) -> Path:
    """A mentés kiinduló fájlja: modern ini, korai Picasa ini, vagy a cél.

    A kimeneti útvonal ettől nem változik: a `Picasa.ini` csak akkor olvasási
    forrás, ha a kért `.picasa.ini` még nem létezik.
    """
    target = Path(path)
    if target.exists():
        return target
    if target.name == ".picasa.ini":
        legacy = target.with_name("Picasa.ini")
        if legacy.exists():
            return legacy
    return target


def load_or_empty(path: str | Path) -> IniDocument:
    """A dokumentum betöltése, vagy üres dokumentum, ha nincs ini-fájl.

    #151/7: a `load_document(p) if p.exists() else parse_document("")`
    minta közös helpere — a controllerek eddig 6 helyen ismételték.

    Ha a kért `.picasa.ini` hiányzik, a korai Picasa `Picasa.ini` fájl a
    mentés kiinduló dokumentuma. A mentés célja ettől továbbra is a kért út.

    #137: ha egyik ini-fájl sincs meg, a `NO_SOURCE_FILE` ujjlenyomat segít,
    hogy az `update_document` észrevegye, ha egy párhuzamos író közben
    létrehozza a célfájlt. Legacy fallbacknél a betöltött dokumentum az
    olvasási forrás ujjlenyomatát tartja meg."""
    source = _ini_source_path(path)
    if not source.exists():
        return replace(parse_document(""), source_fingerprint=NO_SOURCE_FILE)
    return load_document(source)


def save_document(
    document: IniDocument,
    path: str | Path,
    *,
    backup: bool = False,
    in_place: bool = False,
) -> None:
    """A dokumentum kiírása bájtra pontosan (kódolás + BOM megőrzésével).

    Args:
        backup: mentés előtti másolat a célfájlról.
        in_place: HELYBEN írás (`r+b` + csonkolás) az atomikus temp+rename
            helyett. ⚠️ Csak ott, ahol a fájl AZONOSSÁGA számít: windowson a
            `.picasa.ini`-t a Picasa **rejtettként** hozza létre, és a
            rename utáni új fájl már nem rejtett — a felhasználó
            Intézőjében láthatóvá válna, a `CREATE_ALWAYS`-es megnyitás
            pedig `Permission denied`-del bukna (#1097). Cserébe ez az út
            NEM atomikus: megszakadó írás után csonka fájl maradhat, ezért
            a szerkesztés-mentés útvonalai maradnak az atomikuson.
    """
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
    with _ini_path_lock(target):
        if backup and target.exists():
            _write_backup(target)
        if in_place:
            _write_in_place(target, payload)
            return
        write_atomic(target, payload)


def _write_in_place(target: Path, payload: bytes) -> None:
    """Írás a MEGLÉVŐ fájlba, a fájl azonosságát (attribútumait) megtartva.

    Létező fájlt `r+b`-vel nyitunk (`OPEN_EXISTING`) — a csonkoló `w` mód
    windowson egy rejtett fájlon `ERROR_ACCESS_DENIED`-del bukna (#1097).
    A `truncate()` kötelező: nélküle a rövidebb új tartalom után a régi
    bájtok a fájl végén maradnának."""
    if target.exists():
        with _open(target, "r+b") as fajl:
            fajl.write(payload)
            fajl.truncate()
        return
    target.write_bytes(payload)


def update_document(
    path: str | Path,
    mutate: Callable[[IniDocument], IniDocument],
    *,
    backup: bool = True,
    max_retries: int = 3,
) -> IniDocument:
    """Best-effort konkurenciakezelésű betöltés → módosítás → mentés (#137).

    Az azonos normalizált útvonalra hívott PicasaPy `update_document` műveletek
    folyamaton belül, útvonalankénti reentrant lockkal sorosak. Külön ini-
    útvonalak egymástól függetlenül írhatók.

    A külső Picasa / más folyamat írásait nem tudjuk lockolni. Ha az
    ujjlenyomat eltér a betöltés és az előzetes ellenőrzés között, a helper
    frissen újratölt és újrajátssza a `mutate`-et. A sikeres ellenőrzés és az
    atomikus fájlcsere között viszont egy külső írás elveszhet: hagyományos
    fájlrendszeri API-val ez a két művelet nem valódi compare-and-swap.

    A működés lépései:

    1. megszerzi az adott normalizált útvonal lockját,
    2. betölti a dokumentumot (a `load_or_empty` révén az ujjlenyomatával),
    3. a `mutate` TISZTA függvénnyel előállítja a módosítottat,
    4. mentés ELŐTT újraolvassa a fájl aktuális ujjlenyomatát; eltéréskor
       frissen újratölt és a `mutate`-et újrajátssza,
    5. egyező ujjlenyomatnál atomikusan (backuppal) ment.

    A `mutate` KULCS-szintű, immutábilis módosítás legyen (`with_value` /
    `with_removed` / …) és mellékhatásmentes, mert újrajátszásra kerülhet. Az
    ellenőrzés előtt észlelt külső sorok így a friss dokumentumban megmaradnak.

    Returns:
        A ténylegesen kimentett dokumentum (a nyertes betöltésre alkalmazott
        `mutate` eredménye).

    Raises:
        IniConflictError: ha minden próbálkozásnál eltérést észlel a betöltés
            és az előzetes ujjlenyomat-ellenőrzés között.
    """
    target = Path(path)
    with _ini_path_lock(target):
        for _ in range(max_retries + 1):
            source = _ini_source_path(target)
            document = load_or_empty(target)
            mutated = mutate(document)
            # Mentés előtti újraellenőrzés: változott-e a fájl a betöltés óta?
            # (A tartalom-hash a döntő; az mtime önmagában nem megbízható.)
            if (
                _ini_source_path(target) == source
                and _fingerprint_of(source) == document.source_fingerprint
            ):
                save_document(mutated, target, backup=backup)
                # #643: a Picasa a fotó rekordjának érvényességét a KÉPFÁJLHOZ
                # méri (`moddate`/`onlinechecksum`), ezért a puszta ini-írás nem
                # teszi elavulttá — a változott szakaszok képfájljának mtime-ját
                # is meg kell érinteni. Sosem dob: az érintés kudarca (írásvédett
                # kép, hálózati megosztás) nem boríthatja a kész mentést.
                notify_picasa_after_ini_write(target, document, mutated)
                return mutated
            # Az ellenőrzésig észlelt változás: friss újratöltés + újrajátszás.
    raise IniConflictError(
        f"A(z) {target} a betöltés és az ujjlenyomat-ellenőrzés között "
        f"{max_retries + 1} próbálkozás mindegyikében megváltozott."
    )


def _write_backup(target: Path) -> None:
    backup_path = target.with_name(target.name + ".bak")
    # Közös helper (#129): fsync + jogmegőrzés + atomikus csere.
    write_atomic(backup_path, target.read_bytes())
