"""A dátummódosítás XMP- és IPTC-mezői JPEG-szegmensekben (#7237)."""

from __future__ import annotations

import io
import re
import xml.etree.ElementTree as ET
from datetime import datetime

from picasapy.metadata.iptc_writer import _replace_timestamp_iptc_segments

_EXIF_ID = b"Exif\x00\x00"
_XMP_ID = b"http://ns.adobe.com/xap/1.0/\x00"
_PHOTOSHOP_ID = b"Photoshop 3.0\x00"
_XPACKET_START = '<?xpacket begin="\ufeff" id="W5M0MpCehiHzreSzNTczkc9d"?>\n'
_XPACKET_END = '<?xpacket end="w"?>'
_XMP_PACKET_SIZE = 509
_NS_EXIF = "http://ns.adobe.com/exif/1.0/"
_NS_RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"


def update_timestamp_app_metadata(
    segments: list[tuple[int, bytes]], target: datetime
) -> list[tuple[int, bytes]]:
    """XMP/IPTC dátumfrissítés, majd az előírt JPEG-fejlécsorrend."""
    target_local = target.astimezone()
    iso_datetime = target_local.isoformat(timespec="seconds")
    xmp_indices = [
        index
        for index, (marker, segment) in enumerate(segments)
        if marker == 0xE1 and segment[4:].startswith(_XMP_ID)
    ]
    if xmp_indices:
        index = xmp_indices[0]
        segments[index] = (0xE1, _updated_xmp_segment(segments[index][1], iso_datetime))
    else:
        segments.append((0xE1, _new_xmp_segment(iso_datetime)))

    segments = _replace_timestamp_iptc_segments(
        segments,
        target_local.strftime("%Y%m%d").encode("ascii"),
        target_local.strftime("%H%M%S%z").encode("ascii"),
    )
    return [segment for _index, segment in sorted(
        enumerate(segments), key=lambda item: (_segment_priority(item[1]), item[0])
    )]


def _segment_priority(segment: tuple[int, bytes]) -> int:
    marker, raw = segment
    if marker == 0xE0 and raw[4:].startswith(b"JFIF\x00"):
        return 0
    if marker == 0xE1 and raw[4:].startswith(_EXIF_ID):
        return 1
    if marker == 0xE1 and raw[4:].startswith(_XMP_ID):
        return 2
    if marker == 0xED and raw[4:].startswith(_PHOTOSHOP_ID):
        return 3
    return 4


def _updated_xmp_segment(segment: bytes, iso_datetime: str) -> bytes:
    prefix_length = 4 + len(_XMP_ID)
    packet = segment[prefix_length:]
    root_match = re.search(rb"<((?:[A-Za-z_][\w.-]*:)?)xmpmeta(?=[\s>])", packet)
    if root_match is None:
        return segment
    root_name = root_match.group(1) + b"xmpmeta"
    root_end = packet.find(b"</" + root_name + b">", root_match.end())
    if root_end < 0:
        return segment
    xml_end = root_end + len(root_name) + 3
    xml = packet[root_match.start() : xml_end]
    try:
        for _event, (prefix, uri) in ET.iterparse(
            io.BytesIO(xml), events=("start-ns",)
        ):
            if prefix and not re.fullmatch(r"ns\d+", prefix):
                ET.register_namespace(prefix, uri)
        root = ET.fromstring(xml)
    except (ET.ParseError, ValueError):
        return segment

    key = f"{{{_NS_EXIF}}}DateTimeOriginal"
    descriptions = list(root.iter(f"{{{_NS_RDF}}}Description"))
    found = False
    for description in descriptions:
        if key in description.attrib:
            description.set(key, iso_datetime)
            found = True
    for element in root.iter(key):
        element.text = iso_datetime
        found = True
    if not found:
        if not descriptions:
            rdf = root.find(f".//{{{_NS_RDF}}}RDF")
            if rdf is None:
                rdf = ET.SubElement(root, f"{{{_NS_RDF}}}RDF")
            description = ET.SubElement(rdf, f"{{{_NS_RDF}}}Description")
            description.set(f"{{{_NS_RDF}}}about", "")
        else:
            description = descriptions[0]
        description.set(key, iso_datetime)

    updated_packet = packet[: root_match.start()] + ET.tostring(root, encoding="utf-8") + packet[xml_end:]
    return _app1(_XMP_ID, updated_packet) if _app1_fits(_XMP_ID, updated_packet) else segment


def _new_xmp_segment(iso_datetime: str) -> bytes:
    xml = (
        '<x:xmpmeta xmlns:x="adobe:ns:meta/">\n'
        ' <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n'
        '  <rdf:Description rdf:about=""\n'
        '    xmlns:exif="http://ns.adobe.com/exif/1.0/"\n'
        f'    exif:DateTimeOriginal="{iso_datetime}"/>\n'
        ' </rdf:RDF>\n'
        '</x:xmpmeta>\n'
    )
    packet = (_XPACKET_START + xml + _XPACKET_END).encode("utf-8")
    if len(packet) > _XMP_PACKET_SIZE:
        raise ValueError("az új XMP-csomag túllépi a mért méretet")
    padding = b" " * (_XMP_PACKET_SIZE - len(packet))
    packet = packet[: -len(_XPACKET_END)] + padding + _XPACKET_END.encode("ascii")
    return _app1(_XMP_ID, packet)


def _app1_fits(identifier: bytes, payload: bytes) -> bool:
    return len(identifier) + len(payload) + 2 <= 0xFFFF


def _app1(identifier: bytes, payload: bytes) -> bytes:
    length = len(identifier) + len(payload) + 2
    return b"\xff\xe1" + length.to_bytes(2, "big") + identifier + payload
