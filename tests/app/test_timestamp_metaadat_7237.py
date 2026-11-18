"""A dátummódosítás a JPEG EXIF, XMP és IPTC dátumait együtt frissíti (#7237)."""

from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime

import piexif

from picasapy.app.timestamp_controller import _write_exif_datetime_original
from support.jpeg_factory import make_jpeg


_XMP_ID = b"http://ns.adobe.com/xap/1.0/\x00"
_PHOTOSHOP_ID = b"Photoshop 3.0\x00"
_IPTC_DATASET = 0x0404
_IPTC_MD5 = 0x0425
_EXIF_NS = "http://ns.adobe.com/exif/1.0/"
_RDF_NS = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
_DC_NS = "http://purl.org/dc/elements/1.1/"
_DATE = datetime(2024, 6, 7, 8, 9, 10)


def _app_segment(marker: int, payload: bytes) -> bytes:
    length = len(payload) + 2
    return b"\xff" + bytes((marker,)) + length.to_bytes(2, "big") + payload


def _dataset(record: int, tag: int, value: bytes) -> bytes:
    return b"\x1c" + bytes((record, tag)) + len(value).to_bytes(2, "big") + value


def _resource(resource_id: int, value: bytes) -> bytes:
    block = b"8BIM" + resource_id.to_bytes(2, "big") + b"\x00\x00"
    block += len(value).to_bytes(4, "big") + value
    return block + (b"\x00" if len(value) % 2 else b"")


def _photoshop_segment(datasets: bytes) -> bytes:
    iptc = _resource(_IPTC_DATASET, datasets)
    return _app_segment(0xED, _PHOTOSHOP_ID + iptc)


def _segments(path) -> list[tuple[int, bytes]]:
    data = path.read_bytes()
    segments = []
    pos = 2
    while pos + 4 <= len(data):
        assert data[pos] == 0xFF
        marker = data[pos + 1]
        if marker == 0xDA:
            break
        length = int.from_bytes(data[pos + 2 : pos + 4], "big")
        end = pos + length + 2
        segments.append((marker, data[pos:end]))
        pos = end
    return segments


def _xmp(path) -> bytes:
    return next(
        segment[4 + len(_XMP_ID) :]
        for marker, segment in _segments(path)
        if marker == 0xE1 and segment[4:].startswith(_XMP_ID)
    )


def _xmp_root(packet: bytes) -> ET.Element:
    start = packet.find(b"<x:xmpmeta")
    end = packet.find(b"</x:xmpmeta>", start)
    assert start >= 0 and end >= 0
    return ET.fromstring(packet[start : end + len(b"</x:xmpmeta>")])


def _photoshop_resources(path) -> dict[int, bytes]:
    resources = {}
    for marker, segment in _segments(path):
        if marker != 0xED or not segment[4:].startswith(_PHOTOSHOP_ID):
            continue
        blob = segment[4 + len(_PHOTOSHOP_ID) :]
        pos = 0
        while pos + 12 <= len(blob) and blob[pos : pos + 4] == b"8BIM":
            resource_id = int.from_bytes(blob[pos + 4 : pos + 6], "big")
            name_length = blob[pos + 6]
            name_end = pos + 7 + name_length
            if (name_length + 1) % 2:
                name_end += 1
            size = int.from_bytes(blob[name_end : name_end + 4], "big")
            value_start = name_end + 4
            resources[resource_id] = blob[value_start : value_start + size]
            pos = value_start + size + (size % 2)
    return resources


def _datasets(payload: bytes) -> dict[tuple[int, int], list[tuple[bytes, bytes]]]:
    out: dict[tuple[int, int], list[tuple[bytes, bytes]]] = {}
    pos = 0
    while pos + 5 <= len(payload) and payload[pos] == 0x1C:
        record, tag = payload[pos + 1], payload[pos + 2]
        size = int.from_bytes(payload[pos + 3 : pos + 5], "big")
        end = pos + 5 + size
        raw = payload[pos:end]
        out.setdefault((record, tag), []).append((payload[pos + 5 : end], raw))
        pos = end
    assert pos == len(payload)
    return out


def _target_xmp_datetime() -> str:
    return _DATE.astimezone().isoformat(timespec="seconds")


def _insert_after_soi(path, *segments: bytes) -> None:
    raw = path.read_bytes()
    path.write_bytes(raw[:2] + b"".join(segments) + raw[2:])


def test_metaadat_nelkuli_jpeg_mindharom_datumot_es_sorrendet_kap(tmp_path):
    path = make_jpeg(tmp_path / "uj.jpg")

    _write_exif_datetime_original(path, _DATE)

    exif = piexif.load(str(path))
    assert exif["Exif"][piexif.ExifIFD.DateTimeOriginal] == b"2024:06:07 08:09:10"
    assert exif["Exif"][piexif.ExifIFD.ExifVersion] == b"0220"
    assert piexif.ImageIFD.DateTime not in exif["0th"]
    assert piexif.ImageIFD.Software not in exif["0th"]
    assert piexif.ExifIFD.DateTimeDigitized not in exif["Exif"]

    packet = _xmp(path)
    assert len(packet) == 509
    xmp_root = _xmp_root(packet)
    description = xmp_root.find(f".//{{{_RDF_NS}}}Description")
    assert description is not None
    assert description.attrib[f"{{{_EXIF_NS}}}DateTimeOriginal"] == _target_xmp_datetime()

    resources = _photoshop_resources(path)
    datasets = _datasets(resources[_IPTC_DATASET])
    assert datasets[(1, 90)][0][0] == b"\x1b%G"
    assert datasets[(2, 55)][0][0] == b"20240607"
    assert datasets[(2, 60)][0][0] == _DATE.astimezone().strftime("%H%M%S%z").encode("ascii")
    assert resources[_IPTC_MD5] == hashlib.md5(resources[_IPTC_DATASET]).digest()

    markers = [marker for marker, _segment in _segments(path)]
    assert markers[:4] == [0xE0, 0xE1, 0xE1, 0xED]
    assert _segments(path)[1][1][4:].startswith(b"Exif\x00\x00")
    assert _segments(path)[2][1][4:].startswith(_XMP_ID)
    assert _segments(path)[3][1][4:].startswith(_PHOTOSHOP_ID)


def test_meglevo_xmp_es_iptc_mas_mezoit_megorizve_frissul(tmp_path):
    path = make_jpeg(
        tmp_path / "meglevo.jpg",
        taken_at="2020:01:02 03:04:05",
        datetime_0th="2020:01:02 03:04:05",
    )
    exif = piexif.load(str(path))
    exif["Exif"][piexif.ExifIFD.ExifVersion] = b"0231"
    exif["Exif"][piexif.ExifIFD.DateTimeDigitized] = b"2020:01:02 03:04:05"
    piexif.insert(piexif.dump(exif), str(path))

    old_xmp = (
        b'<x:xmpmeta xmlns:x="adobe:ns:meta/">'
        b'<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
        b'<rdf:Description rdf:about="" '
        b'xmlns:exif="http://ns.adobe.com/exif/1.0/" '
        b'xmlns:dc="http://purl.org/dc/elements/1.1/" '
        b'exif:DateTimeOriginal="2001-02-03T04:05:06+00:00" '
        b'dc:format="image/jpeg"><dc:title><rdf:Alt><rdf:li '
        b'xml:lang="x-default">megtartand'
        + "ó cím".encode("utf-8")
        + b"</rdf:li></rdf:Alt>"
        b'</dc:title></rdf:Description></rdf:RDF></x:xmpmeta>'
    )
    old_iptc = (
        _dataset(1, 90, b"\x1b%G")
        + _dataset(2, 25, "régi címke".encode("utf-8"))
        + _dataset(2, 55, b"20010203")
        + _dataset(2, 60, b"040506+0000")
        + _dataset(2, 120, "régi képaláírás".encode("utf-8"))
    )
    _insert_after_soi(
        path,
        _app_segment(
            0xE1,
            _XMP_ID
            + b'<?xpacket begin="\xef\xbb\xbf" id="W5M0MpCehiHzreSzNTczkc9d"?>'
            + old_xmp
            + b'<?xpacket end="w"?>',
        ),
        _photoshop_segment(old_iptc),
    )
    before_datasets = _datasets(old_iptc)
    before_others = {
        key: values
        for key, values in before_datasets.items()
        if key not in {(1, 90), (2, 55), (2, 60)}
    }

    _write_exif_datetime_original(path, _DATE)

    updated_exif = piexif.load(str(path))
    assert updated_exif["Exif"][piexif.ExifIFD.ExifVersion] == b"0231"
    assert updated_exif["0th"][piexif.ImageIFD.DateTime] == b"2020:01:02 03:04:05"
    assert piexif.ImageIFD.Software not in updated_exif["0th"]
    assert updated_exif["Exif"][piexif.ExifIFD.DateTimeDigitized] == b"2020:01:02 03:04:05"
    updated_xmp = _xmp_root(_xmp(path))
    description = updated_xmp.find(f".//{{{_RDF_NS}}}Description")
    assert description is not None
    assert description.attrib[f"{{{_EXIF_NS}}}DateTimeOriginal"] == _target_xmp_datetime()
    assert description.attrib[f"{{{_DC_NS}}}format"] == "image/jpeg"
    assert updated_xmp.findtext(f".//{{{_DC_NS}}}title/{{{_RDF_NS}}}Alt/{{{_RDF_NS}}}li") == (
        "megtartandó cím"
    )

    resources = _photoshop_resources(path)
    updated_datasets = _datasets(resources[_IPTC_DATASET])
    assert {key: values for key, values in updated_datasets.items() if key not in {(1, 90), (2, 55), (2, 60)}} == before_others
    assert updated_datasets[(1, 90)][0][0] == b"\x1b%G"
    assert updated_datasets[(2, 55)][0][0] == b"20240607"
    assert updated_datasets[(2, 60)][0][0] == _DATE.astimezone().strftime("%H%M%S%z").encode("ascii")
    assert resources[_IPTC_MD5] == hashlib.md5(resources[_IPTC_DATASET]).digest()
