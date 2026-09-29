"""Az EXPORT kimenetének metaadat-frissítése, ahogy az eredeti Picasa (#3961).

Mérés és forrás: `docs/specs/picasa-metaadat-tulajdonsagok.md` 16. szakasz
(204 eredeti export). A forrás EXIF-je és XMP-je nem kerül át bájtra
változatlanul, hanem:

* EXIF `DateTime` = az export ideje;
* EXIF `PixelXDimension`/`PixelYDimension` = a KIMENETI kép mérete;
* EXIF `Software`, `Artist`, `DateTimeOriginal`, `ExifVersion`: csak ha
  HIÁNYZIK (a meglévőt nem írjuk felül); a név a `copy_signature.ALAIRAS`
  (`PicasaPy`, #1642), a hiányzó `DateTimeOriginal` a forrásfájl
  módosítási ideje;
* XMP: a meglévő megmarad, `xmp:ModifyDate` = az export ideje, az `exif:`
  névtérből csak a két dátum (`DateTimeOriginal`, `DateTimeDigitized`)
  marad (az eredeti a többit TÖRLI). Ha a forrásnak nincs XMP-je, a
  `copy_signature` csomagja kerül be;
* APP13 (IPTC): a forrásé változatlanul.

Amit a spec NEM rögzít, azt nem találjuk ki: az `ImageUniqueID` képzése
(16. C) 1.) és az APP13 tartalma nincs feltárva, ezekhez nem nyúlunk.
A forrás beágyazott előnézete (IFD1) elavulna, ezért kimarad.
"""

from __future__ import annotations

import io
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from picasapy.metadata.copy_signature import (
    ALAIRAS,
    _MAX_APP1_BODY,
    _XMP_ID,
    _app1,
    _exif_datetime,
    _exif_torzs,
    _xmp_datetime,
    _xmp_packet,
    source_taken_at,
)

_EXIF_ID = b"Exif\x00\x00"
_SOI = b"\xff\xd8"
_SOS = 0xDA
_NS_XMP = "http://ns.adobe.com/xap/1.0/"
_NS_EXIF = "http://ns.adobe.com/exif/1.0/"
_NS_RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
#: az `exif:` névtérből ezek maradnak (spec 16. B) 5.)
_EXIF_MARAD = frozenset({"DateTimeOriginal", "DateTimeDigitized"})
_EXIF_VERZIO = b"0220"  # a metaadat nélküli forrás eredeti exportjában mért


def _szegmensek(data: bytes) -> list[tuple[int, bytes]]:
    """A SOI utáni APP-szegmensek `(marker, nyers bájtok)` párjai."""
    out: list[tuple[int, bytes]] = []
    pos = 2
    while pos + 4 <= len(data) and data[pos] == 0xFF:
        marker = data[pos + 1]
        if marker == 0xFF:
            pos += 1
            continue
        if marker == _SOS:
            break
        length = int.from_bytes(data[pos + 2 : pos + 4], "big")
        if length < 2 or pos + 2 + length > len(data):
            break
        out.append((marker, data[pos : pos + 2 + length]))
        pos += 2 + length
    return out


def _forras_exif(source_bytes: bytes) -> dict:
    """A forrás EXIF-szótára (piexif); sérült/hiányzó esetben üres."""
    import piexif

    ures = {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}}
    try:
        adat = piexif.load(source_bytes)
    except Exception:
        return ures
    return {ifd: dict(adat.get(ifd) or {}) for ifd in ures}


def _frissitett_exif(
    forras: dict, *, size: tuple[int, int], now: datetime, taken_at: datetime | None
) -> bytes | None:
    import piexif

    zeroth, exif_ifd = dict(forras["0th"]), dict(forras["Exif"])
    ures_nev = ALAIRAS.encode("ascii")
    zeroth.setdefault(piexif.ImageIFD.Software, ures_nev)
    zeroth.setdefault(piexif.ImageIFD.Artist, ures_nev)
    zeroth[piexif.ImageIFD.DateTime] = _exif_datetime(now).encode("ascii")
    exif_ifd.setdefault(piexif.ExifIFD.ExifVersion, _EXIF_VERZIO)
    if taken_at is not None:
        exif_ifd.setdefault(
            piexif.ExifIFD.DateTimeOriginal, _exif_datetime(taken_at).encode("ascii")
        )
    exif_ifd[piexif.ExifIFD.PixelXDimension] = int(size[0])
    exif_ifd[piexif.ExifIFD.PixelYDimension] = int(size[1])
    try:
        return piexif.dump(
            {"0th": zeroth, "Exif": exif_ifd, "GPS": forras["GPS"], "1st": {}}
        )
    except Exception:
        return None


def _xmp_frissitve(xmp: bytes, now: datetime) -> bytes | None:
    """A meglévő XMP-csomag: `xmp:ModifyDate` beállítva, az `exif:` névtér a
    két dátumon kívül üres. `None`, ha a csomag nem értelmezhető."""
    szoveg = xmp.decode("utf-8", "replace")
    kezdet, veg = szoveg.find("<x:xmpmeta"), szoveg.rfind("</x:xmpmeta>")
    if kezdet < 0 or veg < 0:
        return None
    torzs = szoveg[kezdet : veg + len("</x:xmpmeta>")]
    try:
        for _esemeny, (prefix, uri) in ET.iterparse(
            io.StringIO(torzs), events=("start-ns",)
        ):
            ET.register_namespace(prefix, uri)
        gyoker = ET.fromstring(torzs)
    except (ET.ParseError, ValueError):
        return None
    ET.register_namespace("xmp", _NS_XMP)
    ET.register_namespace("exif", _NS_EXIF)
    ET.register_namespace("rdf", _NS_RDF)
    mostani = _xmp_datetime(now)
    leirasok = list(gyoker.iter(f"{{{_NS_RDF}}}Description"))
    if not leirasok:
        return None
    beallitva = False
    for leiras in leirasok:
        for kulcs in [k for k in leiras.attrib if k.startswith(f"{{{_NS_EXIF}}}")]:
            if kulcs.split("}")[1] not in _EXIF_MARAD:
                del leiras.attrib[kulcs]
        for gyerek in [g for g in leiras if g.tag.startswith(f"{{{_NS_EXIF}}}")]:
            if gyerek.tag.split("}")[1] not in _EXIF_MARAD:
                leiras.remove(gyerek)
        kulcs = f"{{{_NS_XMP}}}ModifyDate"
        if kulcs in leiras.attrib:
            leiras.set(kulcs, mostani)
            beallitva = True
        for gyerek in leiras.findall(kulcs):
            gyerek.text = mostani
            beallitva = True
    if not beallitva:
        leirasok[0].set(f"{{{_NS_XMP}}}ModifyDate", mostani)
    kiiras = ET.tostring(gyoker, encoding="unicode")
    return (
        '<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>\n'
        + kiiras
        + '\n<?xpacket end="w"?>'
    ).encode("utf-8")


def frissitett_metaadat(
    source: Path,
    encoded: bytes,
    *,
    size: tuple[int, int],
    now: datetime | None = None,
) -> bytes:
    """Az újrakódolt export-JPEG (`encoded`) metaadatokkal, az eredeti
    Picasa szerint frissítve. `size` = a KIMENETI kép `(szélesség, magasság)`.

    Sérült/nem-JPEG forrásnál vagy kimenetnél a bemenetet adja vissza
    (a spec csak a JPEG-forrás exportját méri)."""
    try:
        forras_bajt = source.read_bytes()
    except OSError:
        return encoded
    if not forras_bajt.startswith(_SOI) or not encoded.startswith(_SOI):
        return encoded
    ido = now if now is not None else datetime.now()
    szegmensek = _szegmensek(forras_bajt)
    forras_xmp = next(
        (s[4 + len(_XMP_ID) :] for m, s in szegmensek if m == 0xE1 and s[4:].startswith(_XMP_ID)),
        None,
    )
    app13 = [s for m, s in szegmensek if m == 0xED]

    forras = _forras_exif(forras_bajt)
    taken_at = source_taken_at(source)
    exif = _frissitett_exif(forras, size=size, now=ido, taken_at=taken_at)

    xmp = _xmp_frissitve(forras_xmp, ido) if forras_xmp is not None else None
    if xmp is None:
        # metaadat nélküli (vagy értelmezhetetlen XMP-jű) forrás: a
        # `copy_signature` mért csomagja
        xmp = _xmp_packet(ido, taken_at)

    ki = b""
    if exif is not None:
        ki += _app1(_EXIF_ID, _exif_torzs(exif))
    if len(xmp) <= _MAX_APP1_BODY:
        ki += _app1(_XMP_ID, xmp)
    ki += b"".join(app13)
    if not ki:
        return encoded
    pont = 4 + int.from_bytes(encoded[4:6], "big") if encoded[2:4] == b"\xff\xe0" else 2
    return encoded[:pont] + ki + encoded[pont:]
