"""Közös teszt-fixture: kis JPEG generálás EXIF (piexif) és IPTC (kézi APP13)
adattal."""

import piexif
from PIL import Image


def _app13_segment(caption: str | None, keywords: tuple[str, ...]) -> bytes:
    data = b""
    for keyword in keywords:
        raw = keyword.encode("utf-8")
        data += b"\x1c\x02\x19" + len(raw).to_bytes(2, "big") + raw
    if caption is not None:
        raw = caption.encode("utf-8")
        data += b"\x1c\x02\x78" + len(raw).to_bytes(2, "big") + raw
    block = b"8BIM\x04\x04\x00\x00" + len(data).to_bytes(4, "big") + data
    if len(data) % 2:
        block += b"\x00"
    payload = b"Photoshop 3.0\x00" + block
    return b"\xff\xed" + (len(payload) + 2).to_bytes(2, "big") + payload


def make_jpeg(
    path,
    size=(8, 6),
    taken_at: str | None = None,
    datetime_0th: str | None = None,
    orientation: int | None = None,
    caption: str | None = None,
    keywords: tuple[str, ...] = (),
):
    Image.new("RGB", size, "red").save(path, "JPEG")
    zeroth, exif_ifd = {}, {}
    if orientation is not None:
        zeroth[piexif.ImageIFD.Orientation] = orientation
    if datetime_0th is not None:
        zeroth[piexif.ImageIFD.DateTime] = datetime_0th
    if taken_at is not None:
        exif_ifd[piexif.ExifIFD.DateTimeOriginal] = taken_at
    if zeroth or exif_ifd:
        piexif.insert(piexif.dump({"0th": zeroth, "Exif": exif_ifd}), str(path))
    if caption is not None or keywords:
        raw = path.read_bytes()
        path.write_bytes(raw[:2] + _app13_segment(caption, keywords) + raw[2:])
    return path
