"""IPTC-felirat és -kulcsszavak írása JPEG-be, minden más bájt megőrzésével.

Picasa-viselkedés (spec, írási szabály #3): JPEG-nél a caption az IPTC
Caption/Abstract (2:120), a címkék a Keywords (2:25) mezőbe kerülnek. A
művelet szegmens-szintű: csak az APP13 (Photoshop 3.0 / 8BIM) blokk épül
újra — a képadat, az EXIF és az IPTC nem kezelt mezői bájtra pontosan
megmaradnak. A szöveg UTF-8-ként íródik az 1:90-es karakterkészlet-
jelölővel (digiKam/Lightroom-kompatibilis); a jelölő addig marad, amíg
bármely adatmező van a rekordban. Üres érték = a mező (és ha kiürül, az
egész APP13) eltávolítása — így a fel-le művelet bitre pontos round-trip.
"""

from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path

_RETRY_DELAY = 0.05
_RETRY_COUNT = 5

_SOI = b"\xff\xd8"
_SOS = 0xDA
_APP13 = 0xED
_APP_RANGE = range(0xE0, 0xF0)
_PHOTOSHOP = b"Photoshop 3.0\x00"
_8BIM = b"8BIM"
_IPTC_RESOURCE = 0x0404
_CHARSET_KEY = (1, 90)
_KEYWORDS_KEY = (2, 25)
_CAPTION_KEY = (2, 120)
_UTF8_MARKER = b"\x1b%G"
_MAX_CAPTION_BYTES = 2000  # IPTC 2:120 szabvány-korlát
_MAX_KEYWORD_BYTES = 64  # IPTC 2:25 szabvány-korlát


def write_iptc_caption(path: str | Path, caption: str) -> bool:
    """True, ha sikerült; False, ha a fájl nem (ép) JPEG."""
    values = (
        [_utf8_truncated(caption, _MAX_CAPTION_BYTES)] if caption else []
    )
    return _write_datasets(path, _CAPTION_KEY, values)


def write_iptc_keywords(path: str | Path, keywords: tuple[str, ...]) -> bool:
    """A teljes kulcsszó-lista cseréje (2:25, kulcsszavanként egy adatmező).

    True, ha sikerült; False, ha a fájl nem (ép) JPEG. Üres lista = az
    összes Keywords-mező eltávolítása."""
    values = [
        _utf8_truncated(keyword, _MAX_KEYWORD_BYTES)
        for keyword in keywords
        if keyword
    ]
    return _write_datasets(path, _KEYWORDS_KEY, values)


def _utf8_truncated(text: str, limit: int) -> bytes:
    """UTF-8 bájtok a limitre vágva, karakterhatáron (nincs csonka szekvencia)."""
    encoded = text.encode("utf-8")
    if len(encoded) <= limit:
        return encoded
    return encoded[:limit].decode("utf-8", errors="ignore").encode("utf-8")


def _write_datasets(
    path: str | Path, key: tuple[int, int], values: list[bytes]
) -> bool:
    target = Path(path)
    try:
        data = target.read_bytes()
        rebuilt = _rebuild_jpeg(data, key, values)
    except (OSError, ValueError):
        return False
    if rebuilt is None:
        return False
    _write_atomic(target, rebuilt)
    return True


def _rebuild_jpeg(
    data: bytes, key: tuple[int, int], values: list[bytes]
) -> bytes | None:
    if not data.startswith(_SOI):
        return None
    segments, sos_offset = _parse_header_segments(data)
    if sos_offset is None:
        return None

    app13_index = None
    resources: list[tuple[int, bytes, bytes]] = []
    for index, (marker, start, end) in enumerate(segments):
        if marker == _APP13 and data[start + 4 : start + 4 + len(_PHOTOSHOP)] == _PHOTOSHOP:
            app13_index = index
            resources = _parse_resources(data[start + 4 + len(_PHOTOSHOP) : end])
            break

    resources = _with_datasets(resources, key, values)
    new_app13 = _serialize_app13(resources)

    parts = [data[:2]]
    inserted = False
    for index, (marker, start, end) in enumerate(segments):
        if index == app13_index:
            if new_app13:
                parts.append(new_app13)
            inserted = True
            continue
        if (
            not inserted
            and app13_index is None
            and new_app13
            and marker not in _APP_RANGE
        ):
            # nincs meglévő APP13: az APP-blokkok után szúrjuk be
            parts.append(new_app13)
            inserted = True
        parts.append(data[start:end])
    if not inserted and new_app13:
        parts.append(new_app13)
    parts.append(data[sos_offset:])
    return b"".join(parts)


def _parse_header_segments(data: bytes):
    """(marker, kezdet, vég) hármasok a SOI után, a SOS-ig."""
    segments = []
    pos = 2
    while pos + 4 <= len(data):
        if data[pos] != 0xFF:
            return segments, None
        marker = data[pos + 1]
        if marker == 0xFF:  # kitöltő bájt
            pos += 1
            continue
        if marker == _SOS:
            return segments, pos
        length = int.from_bytes(data[pos + 2 : pos + 4], "big")
        if length < 2 or pos + 2 + length > len(data):
            return segments, None
        segments.append((marker, pos, pos + 2 + length))
        pos += 2 + length
    return segments, None


def _parse_resources(blob: bytes) -> list[tuple[int, bytes, bytes]]:
    """8BIM erőforrások: (azonosító, név-bájtok, adat)."""
    resources = []
    pos = 0
    while pos + 12 <= len(blob):
        if blob[pos : pos + 4] != _8BIM:
            break
        resource_id = int.from_bytes(blob[pos + 4 : pos + 6], "big")
        name_length = blob[pos + 6]
        name_end = pos + 7 + name_length
        if (name_length + 1) % 2:
            name_end += 1  # párosra igazítás
        name_bytes = blob[pos + 6 : name_end]
        size = int.from_bytes(blob[name_end : name_end + 4], "big")
        data_start = name_end + 4
        resources.append((resource_id, name_bytes, blob[data_start : data_start + size]))
        pos = data_start + size + (size % 2)
    return resources


def _with_datasets(
    resources: list[tuple[int, bytes, bytes]],
    key: tuple[int, int],
    values: list[bytes],
) -> list[tuple[int, bytes, bytes]]:
    """A `key` adatmezőinek cseréje `values`-ra a 8BIM-erőforrások közt.

    Az 1:90-es karakterkészlet-jelölő addig marad az elején, amíg bármely
    adatmező van a rekordban (a másik kezelt mező — pl. a felirat a
    kulcsszó-írásnál — nem veszítheti el az UTF-8-jelölőjét)."""
    datasets = []
    for resource_id, _name, payload in resources:
        if resource_id == _IPTC_RESOURCE:
            datasets = _parse_datasets(payload)
            break
    kept = [d for d in datasets if d[:2] not in (_CHARSET_KEY, key)]
    kept.extend((*key, value) for value in values)
    if kept:
        kept = [(*_CHARSET_KEY, _UTF8_MARKER), *kept]
    new_payload = b"".join(
        b"\x1c" + bytes((record, dataset)) + len(value).to_bytes(2, "big") + value
        for record, dataset, value in kept
    )
    others = [r for r in resources if r[0] != _IPTC_RESOURCE]
    if new_payload:
        others.append((_IPTC_RESOURCE, b"\x00\x00", new_payload))
    return others


def _parse_datasets(payload: bytes) -> list[tuple[int, int, bytes]]:
    datasets = []
    pos = 0
    while pos + 5 <= len(payload):
        if payload[pos] != 0x1C:
            break
        record, dataset = payload[pos + 1], payload[pos + 2]
        length = int.from_bytes(payload[pos + 3 : pos + 5], "big")
        if length > 32767:
            break  # kiterjesztett hosszú mezőt nem kezelünk
        datasets.append((record, dataset, payload[pos + 5 : pos + 5 + length]))
        pos += 5 + length
    return datasets


def _serialize_app13(resources: list[tuple[int, bytes, bytes]]) -> bytes:
    if not resources:
        return b""
    body = b""
    for resource_id, name_bytes, payload in resources:
        block = (
            _8BIM
            + resource_id.to_bytes(2, "big")
            + (name_bytes or b"\x00\x00")
            + len(payload).to_bytes(4, "big")
            + payload
        )
        if len(payload) % 2:
            block += b"\x00"
        body += block
    payload = _PHOTOSHOP + body
    return b"\xff" + bytes((_APP13,)) + (len(payload) + 2).to_bytes(2, "big") + payload


def _write_atomic(target: Path, payload: bytes) -> None:
    """Atomikus csere; Windowson a nyitott célfájl (pl. a néző épp tölti)
    zárolja a rename-et → rövid retry, végső esetben közvetlen írás
    (képfájlnál ez elfogadható fallback)."""
    fd, temp_name = tempfile.mkstemp(dir=target.parent, suffix=".jpgtmp")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
        for attempt in range(_RETRY_COUNT):
            try:
                os.replace(temp_name, target)
                return
            except PermissionError:
                time.sleep(_RETRY_DELAY * (attempt + 1))
        target.write_bytes(payload)
        os.unlink(temp_name)
    except BaseException:
        os.unlink(temp_name)
        raise
