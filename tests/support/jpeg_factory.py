"""Közös teszt-fixture: kis JPEG generálás EXIF (piexif) és IPTC (kézi APP13)
adattal."""

import piexif
from PIL import Image


_CHARSET_MARKER = b"\x1b%G"  # IPTC 1:90 — UTF-8 karakterkészlet-jelölő


def _app13_segment(
    caption: str | None,
    keywords: tuple[str, ...],
    encoding: str = "utf-8",
    charset_marker: bool = False,
) -> bytes:
    data = b""
    if charset_marker:
        data += (
            b"\x1c\x01\x5a"
            + len(_CHARSET_MARKER).to_bytes(2, "big")
            + _CHARSET_MARKER
        )
    for keyword in keywords:
        raw = keyword.encode(encoding)
        data += b"\x1c\x02\x19" + len(raw).to_bytes(2, "big") + raw
    if caption is not None:
        raw = caption.encode(encoding)
        data += b"\x1c\x02\x78" + len(raw).to_bytes(2, "big") + raw
    block = b"8BIM\x04\x04\x00\x00" + len(data).to_bytes(4, "big") + data
    if len(data) % 2:
        block += b"\x00"
    payload = b"Photoshop 3.0\x00" + block
    return b"\xff\xed" + (len(payload) + 2).to_bytes(2, "big") + payload


def _dms(value: float) -> tuple:
    """Tizedes fok → EXIF (fok, perc, másodperc) racionális hármas."""
    degrees = int(abs(value))
    minutes_full = (abs(value) - degrees) * 60
    minutes = int(minutes_full)
    seconds = round((minutes_full - minutes) * 60 * 100)
    return ((degrees, 1), (minutes, 1), (seconds, 100))


def _gps_ifd(latitude: float, longitude: float) -> dict:
    """GPS-IFD a #30-as tesztekhez (féltekejelölővel)."""
    return {
        piexif.GPSIFD.GPSLatitudeRef: "N" if latitude >= 0 else "S",
        piexif.GPSIFD.GPSLatitude: _dms(latitude),
        piexif.GPSIFD.GPSLongitudeRef: "E" if longitude >= 0 else "W",
        piexif.GPSIFD.GPSLongitude: _dms(longitude),
    }


def make_jpeg(
    path,
    size=(8, 6),
    taken_at: str | None = None,
    datetime_0th: str | None = None,
    orientation: int | None = None,
    caption: str | None = None,
    keywords: tuple[str, ...] = (),
    encoding: str = "utf-8",
    charset_marker: bool = False,
    gps: tuple[float, float] | None = None,
    camera: tuple[str, str] | None = None,
):
    """`encoding`/`charset_marker`: legacy (nem UTF-8) IPTC szimulálásához
    (#133) — pl. CP1250, jelölő nélkül, ahogy a régi Picasa írta."""
    Image.new("RGB", size, "red").save(path, "JPEG")
    zeroth, exif_ifd = {}, {}
    gps_ifd = _gps_ifd(*gps) if gps is not None else {}
    if orientation is not None:
        zeroth[piexif.ImageIFD.Orientation] = orientation
    if camera is not None:
        # #440: fényképezőgép-adat (`Make`/`Model`) — a mentés-készlet
        # harmadik fájlszűrője („csak JPEG-ek fényképezőgép-adatokkal")
        # ezt keresi.
        gyarto, modell = camera
        zeroth[piexif.ImageIFD.Make] = gyarto
        zeroth[piexif.ImageIFD.Model] = modell
    if datetime_0th is not None:
        zeroth[piexif.ImageIFD.DateTime] = datetime_0th
    if taken_at is not None:
        exif_ifd[piexif.ExifIFD.DateTimeOriginal] = taken_at
    if zeroth or exif_ifd or gps_ifd:
        piexif.insert(
            piexif.dump({"0th": zeroth, "Exif": exif_ifd, "GPS": gps_ifd}), str(path)
        )
    if caption is not None or keywords:
        raw = path.read_bytes()
        segment = _app13_segment(caption, keywords, encoding, charset_marker)
        path.write_bytes(raw[:2] + segment + raw[2:])
    return path


def make_minta_jpeg(path, size=(320, 240), seed: int = 0) -> None:
    """Mintázatos szintetikus próbakép: színátmenet, csíkok és körök.

    A kiadásképeken a rács csempéinek látható képet kell mutatniuk; az
    egyszínű próbakép a felületen üres négyzetnek látszik (picasapy-agent
    #225). A `seed` képenként más színt és elrendezést ad.
    """
    from PIL import ImageDraw

    szel, mag = size
    alap = ((seed * 67) % 256, (seed * 131 + 80) % 256, (seed * 29 + 160) % 256)
    kep = Image.new("RGB", size)
    rajz = ImageDraw.Draw(kep)
    for y in range(mag):
        arany = y / max(mag - 1, 1)
        szin = tuple(int(c * (1 - arany) + (255 - c) * arany) for c in alap)
        rajz.line((0, y, szel, y), fill=szin)
    lepes = max(szel // 8, 4)
    for x in range(-mag, szel, lepes):
        rajz.line((x, mag, x + mag, 0), fill=(255 - alap[0], alap[2], alap[1]), width=3)
    for i in range(3):
        r = max(min(szel, mag) // (4 + i), 4)
        cx = (seed * 37 + i * szel // 3) % szel
        cy = (seed * 53 + i * mag // 2) % mag
        rajz.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(alap[2], 255 - alap[1], alap[0]))
    kep.save(path, "JPEG", quality=92)
