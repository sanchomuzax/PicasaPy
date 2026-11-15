"""A mentett kép ujjlenyomata: a külső módosítás észleléséhez (#6972).

Az eredeti Picasa a Visszaállítás (Revert) előtt megnézi, hogy a fájl a
mentés óta kívülről módosult-e (`CThumbUI::FileRevert::changed1` /
`changedX`, `0x0053b87e`), és ha igen, külön figyelmeztet.

## Miért kell saját tár

A meglévő mentési metaadatok erre nem használhatók:

* az eredeti-mappa ini-jének `moddate` kulcsa a mentés ELŐTTI fájlidőt őrzi,
  nem a mentés utánit;
* a `backuphash` az írás időpontjából képzett, 16 bites bélyeg, amelyet
  minden ini-írás frissít;
* a képfájl `mtime`-ját minden ini-írás megérinti (#2491), tehát az sem
  mérce.

Ezért a mentés után a kép tartalom-aláírását egy saját JSON-tárba írjuk, a
szerkesztés-napló (`edit_journal`) mintájára: NEM a fotó mappájába, hanem az
adatgyökérbe, így nem szennyezi az eredeti-mappát, és a fájlkezelő
(átnevezés, költöztetés, törlés) kódjához sem nyúl.

## Amit az aláírás szándékosan nem néz

JPEG-nél a metaadat-szegmensek (APP0-APP15, COM) kimaradnak az aláírásból:
a PicasaPy a feliratot és a kulcsszavakat maga írja a fájlba (IPTC, APP13),
és az nem „külső módosítás". A kép adata (táblák, keretek, a letapogatott
bájtok) számít. Ami nem JPEG, annak a teljes bájtsora.

## Konzervatív: nincs adat, nincs figyelmeztetés

Ha egy képhez nincs bejegyzés (a Picasa mentette, a tár törlődött, a
Visszavonás elfelejtette), a vizsgálat `False`-t ad. Hamis riasztás rosszabb,
mint a hiányzó figyelmeztetés: utóbbi az eredetivel is megesik, ha az nem
mentett semmit. A bejegyzés a megőrzött eredeti méretét is tárolja; ha az
eltér, a bejegyzés egy másik, régebbi mentéshez tartozik, és nem számít.
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
from collections.abc import Iterable
from pathlib import Path

from picasapy.edit.edit_journal import naplo_kulcs
from picasapy.edit.save import find_original_backup
from picasapy.ioutil import write_atomic

#: A tár fájlneve az adatgyökérben (az index-SQLite és a napló mellett).
STORE_FILENAME = "saved-fingerprints.json"

#: A tár olvasás-módosítás-írás körét védő zár: a mentés háttérszálon fut,
#: a Visszaállítás/Visszavonás egy másikon.
_LOCK = threading.RLock()

_SOI = b"\xff\xd8"
_SOS = 0xDA
#: önálló jelölők (nincs hosszuk): TEM, RSTn, EOI
_STANDALONE = frozenset({0x01, 0xD9, *range(0xD0, 0xD8)})


def _is_metadata_marker(marker: int) -> bool:
    """APP0-APP15 és COM: itt él az EXIF, az XMP, az IPTC és a felirat."""
    return 0xE0 <= marker <= 0xEF or marker == 0xFE


def _without_jpeg_metadata(data: bytes) -> bytes | None:
    """A JPEG a metaadat-szegmensek nélkül, vagy `None`, ha nem értelmezhető."""
    if data[:2] != _SOI:
        return None
    kimenet = bytearray(_SOI)
    pos, vege = 2, len(data)
    while pos + 2 <= vege:
        if data[pos] != 0xFF:
            return None
        marker = data[pos + 1]
        if marker == 0xFF:  # kitöltő bájt
            pos += 1
            continue
        if marker in _STANDALONE:
            kimenet += data[pos : pos + 2]
            pos += 2
            continue
        if pos + 4 > vege:
            return None
        hossz = int.from_bytes(data[pos + 2 : pos + 4], "big")
        szegmens_vege = pos + 2 + hossz
        if hossz < 2 or szegmens_vege > vege:
            return None
        if not _is_metadata_marker(marker):
            kimenet += data[pos:szegmens_vege]
        pos = szegmens_vege
        if marker == _SOS:
            kimenet += data[pos:]
            return bytes(kimenet)
    return None


def content_signature(data: bytes) -> str:
    """A kép tartalom-aláírása (SHA-256, hexa); JPEG-nél metaadat nélkül."""
    alap = _without_jpeg_metadata(data)
    return hashlib.sha256(data if alap is None else alap).hexdigest()


def _load(store: Path) -> dict[str, dict]:
    try:
        raw = json.loads(Path(store).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(raw, dict):
        return {}
    return {k: v for k, v in raw.items() if isinstance(v, dict)}


def _save(store: Path, entries: dict[str, dict]) -> None:
    payload = json.dumps(entries, ensure_ascii=False, indent=1, sort_keys=True)
    write_atomic(Path(store), payload.encode("utf-8"), make_parents=True)


def _backup_size(image_path: Path) -> int | None:
    backup = find_original_backup(image_path)
    if backup is None:
        return None
    try:
        return backup.stat().st_size
    except OSError:
        return None


def record_saved(store: Path, image_paths: Iterable[Path | str]) -> None:
    """A MOST mentett képek ujjlenyomatának rögzítése (egy olvasás + írás).

    Az, amelyiket nem tudunk beolvasni, kimarad (és a régi bejegyzése
    törlődik): a hiányzó adat nem riaszt, a régi viszont tévedne.
    """
    pontok: dict[str, dict | None] = {}
    for item in image_paths:
        path = Path(item)
        kulcs = naplo_kulcs(path)
        try:
            signature = content_signature(path.read_bytes())
        except OSError:
            logging.getLogger(__name__).warning(
                "a mentett kép ujjlenyomata nem rögzíthető (#6972): %s", path
            )
            pontok[kulcs] = None
            continue
        pontok[kulcs] = {"signature": signature, "backup_size": _backup_size(path)}
    if not pontok:
        return
    with _LOCK:
        entries = _load(store)
        for kulcs, bejegyzes in pontok.items():
            if bejegyzes is None:
                entries.pop(kulcs, None)
            else:
                entries[kulcs] = bejegyzes
        _save(store, entries)


def forget(store: Path, image_paths: Iterable[Path | str]) -> None:
    """A képek bejegyzésének törlése (Visszaállítás, Mentés visszavonása).

    A Mentés visszavonása után a fájl egy KORÁBBI mentés bájtjait viseli,
    amelyek ujjlenyomatát nem őrizzük: nincs adat, tehát nincs riasztás.
    """
    kulcsok = {naplo_kulcs(item) for item in image_paths}
    if not kulcsok:
        return
    with _LOCK:
        entries = _load(store)
        if not kulcsok & entries.keys():
            return
        for kulcs in kulcsok:
            entries.pop(kulcs, None)
        _save(store, entries)


def changed_outside(store: Path, image_path: Path | str) -> bool:
    """Igaz, ha a kép a mentés óta kívülről módosult.

    `False`, ha nincs (érvényes) bejegyzés, a kép hiányzik vagy nem
    olvasható: ilyenkor a Visszaállítás a maga útján hibázik, nem itt.
    """
    path = Path(image_path)
    with _LOCK:
        bejegyzes = _load(store).get(naplo_kulcs(path))
    if not bejegyzes or not bejegyzes.get("signature"):
        return False
    tarolt_meret = bejegyzes.get("backup_size")
    if tarolt_meret is not None and tarolt_meret != _backup_size(path):
        return False
    try:
        ma = content_signature(path.read_bytes())
    except OSError:
        return False
    return ma != bejegyzes["signature"]
