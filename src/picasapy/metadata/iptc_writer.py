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

from pathlib import Path

from picasapy.ioutil import write_atomic

_RETRY_DELAY = 0.05
_RETRY_COUNT = 4  # újrapróbálkozások száma az első csere-kísérlet után

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
# Egy APP13 szegmens teljes hossza max 65535 (2 bájt hossz + payload);
# a payload elejét a "Photoshop 3.0\0" azonosító foglalja.
_MAX_SEGMENT_BODY = 65535 - 2 - len(_PHOTOSHOP)


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
    # Közös helper (#129): fsync a csere előtt (crash-nél sem csonkulhat az
    # eredeti fotó) + a fájl jogainak megőrzése (NAS-on más kliens is
    # olvassa). Windowson a nyitott célfájl (pl. a néző épp tölti) zárolja
    # a rename-et → rövid retry, végső esetben közvetlen írás (képfájlnál
    # ez elfogadható fallback).
    write_atomic(
        target,
        rebuilt,
        lock_retries=_RETRY_COUNT,
        lock_retry_delay=_RETRY_DELAY,
        fallback_direct=True,
        suffix=".jpgtmp",
    )
    return True


def _rebuild_jpeg(
    data: bytes, key: tuple[int, int], values: list[bytes]
) -> bytes | None:
    if not data.startswith(_SOI):
        return None
    segments, sos_offset = _parse_header_segments(data)
    if sos_offset is None:
        return None

    # A Photoshop-erőforrások 64 KB felett TÖBB APP13 szegmensre oszlanak
    # (egy erőforrás akár szegmenshatáron át is folytatódhat), ezért az
    # összes Photoshop-azonosítós APP13 payloadját összefűzve parsoljuk,
    # és az elsőnek a helyére írjuk vissza az újraépített (szükség esetén
    # ismét feldarabolt) egészet. A nem-Photoshop APP13 érintetlen marad.
    photoshop_indices: set[int] = set()
    payloads: list[bytes] = []
    for index, (marker, start, end) in enumerate(segments):
        if marker == _APP13 and data[start + 4 : start + 4 + len(_PHOTOSHOP)] == _PHOTOSHOP:
            photoshop_indices.add(index)
            payloads.append(data[start + 4 + len(_PHOTOSHOP) : end])
    first_photoshop = min(photoshop_indices) if photoshop_indices else None
    resources, resource_tail = _parse_resources(b"".join(payloads))

    resources = _with_datasets(resources, key, values)
    new_app13 = _serialize_app13(resources, resource_tail)

    parts = [data[:2]]
    inserted = False
    for index, (marker, start, end) in enumerate(segments):
        if index in photoshop_indices:
            if index == first_photoshop and new_app13:
                parts.append(new_app13)
            inserted = True
            continue
        if (
            not inserted
            and first_photoshop is None
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


def _parse_resources(blob: bytes) -> tuple[list[tuple[int, bytes, bytes]], bytes]:
    """8BIM erőforrások: ((azonosító, név-bájtok, adat) lista, nyers maradék).

    A nem értett részt (ismeretlen szignatúra, csonka blokk) nyers bájtként
    adjuk vissza, hogy a round-trip elv szerint változatlanul visszaírható
    legyen."""
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
        if name_end + 4 > len(blob):
            break  # csonka fejléc → nyers maradékként őrizzük
        name_bytes = blob[pos + 6 : name_end]
        size = int.from_bytes(blob[name_end : name_end + 4], "big")
        data_start = name_end + 4
        if data_start + size > len(blob):
            break  # csonka adat → nyers maradékként őrizzük
        resources.append((resource_id, name_bytes, blob[data_start : data_start + size]))
        pos = data_start + size + (size % 2)
    return resources, blob[pos:]


def _with_datasets(
    resources: list[tuple[int, bytes, bytes]],
    key: tuple[int, int],
    values: list[bytes],
) -> list[tuple[int, bytes, bytes]]:
    """A `key` adatmezőinek cseréje `values`-ra a 8BIM-erőforrások közt.

    Az 1:90-es karakterkészlet-jelölő addig marad az elején, amíg bármely
    adatmező van a rekordban (a másik kezelt mező — pl. a felirat a
    kulcsszó-írásnál — nem veszítheti el az UTF-8-jelölőjét)."""
    datasets: list[tuple[int, int, bytes, bytes]] = []
    dataset_tail = b""
    iptc_name = b"\x00\x00"
    for resource_id, name, payload in resources:
        if resource_id == _IPTC_RESOURCE:
            datasets, dataset_tail = _parse_datasets(payload)
            iptc_name = name or b"\x00\x00"
            break
    # A nem kezelt adatmezők NYERS bájtjai őrződnek meg (kiterjesztett
    # hosszú mezők is), a nem parseolható maradék (dataset_tail) pedig
    # változatlanul a rekord végére kerül — round-trip elv.
    kept = [d for d in datasets if (d[0], d[1]) not in (_CHARSET_KEY, key)]
    added = [_encode_dataset(*key, value) for value in values]
    parts: list[bytes] = []
    if kept or added:
        parts.append(_encode_dataset(*_CHARSET_KEY, _UTF8_MARKER))
        parts.extend(raw for _record, _dataset, _value, raw in kept)
        parts.extend(added)
    parts.append(dataset_tail)
    new_payload = b"".join(parts)

    # Az IPTC-erőforrás a helyén (nevével együtt) épül újra; ha kiürült,
    # kimarad. A többi erőforrás sorrendje változatlan.
    rebuilt: list[tuple[int, bytes, bytes]] = []
    replaced = False
    for resource in resources:
        if resource[0] == _IPTC_RESOURCE:
            if new_payload and not replaced:
                rebuilt.append((_IPTC_RESOURCE, iptc_name, new_payload))
                replaced = True
            continue
        rebuilt.append(resource)
    if new_payload and not replaced:
        rebuilt.append((_IPTC_RESOURCE, iptc_name, new_payload))
    return rebuilt


def _encode_dataset(record: int, dataset: int, value: bytes) -> bytes:
    """Szabványos (nem kiterjesztett) IPTC-adatmező kódolása."""
    return b"\x1c" + bytes((record, dataset)) + len(value).to_bytes(2, "big") + value


def _parse_datasets(payload: bytes) -> tuple[list[tuple[int, int, bytes, bytes]], bytes]:
    """IPTC-adatmezők: ((rekord, mező, érték, nyers bájtok) lista, maradék).

    A kiterjesztett hosszú (32767 bájt feletti) mezőt is beparsoljuk, hogy
    az utána álló mezők ne vesszenek el; a nyers bájtok megőrzésével a
    visszaírás bitre pontos. A nem érthető maradék nyersen jön vissza."""
    datasets = []
    pos = 0
    while pos + 5 <= len(payload):
        if payload[pos] != 0x1C:
            break
        record, dataset = payload[pos + 1], payload[pos + 2]
        length = int.from_bytes(payload[pos + 3 : pos + 5], "big")
        data_start = pos + 5
        if length & 0x8000:
            # Kiterjesztett hossz: az alsó 15 bit a következő hosszmező
            # bájtszáma, maga a hossz abban áll.
            size_length = length & 0x7FFF
            data_start = pos + 5 + size_length
            if size_length == 0 or data_start > len(payload):
                break
            length = int.from_bytes(payload[pos + 5 : data_start], "big")
        end = data_start + length
        if end > len(payload):
            break  # csonka mező → nyers maradékként őrizzük
        datasets.append((record, dataset, payload[data_start:end], payload[pos:end]))
        pos = end
    return datasets, payload[pos:]


def _serialize_app13(
    resources: list[tuple[int, bytes, bytes]], resource_tail: bytes = b""
) -> bytes:
    """APP13 szegmens(ek) építése; 64 KB felett több szegmensre darabolva."""
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
    body += resource_tail
    segments = b""
    for offset in range(0, len(body), _MAX_SEGMENT_BODY):
        payload = _PHOTOSHOP + body[offset : offset + _MAX_SEGMENT_BODY]
        segments += (
            b"\xff"
            + bytes((_APP13,))
            + (len(payload) + 2).to_bytes(2, "big")
            + payload
        )
    return segments
