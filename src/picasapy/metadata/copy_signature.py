"""A „Másolat mentése" kimenetének METAADAT-ALÁÍRÁSA (#1642).

## A mérés

A tulajdonos referencia-mérése (`research/testdata/1557-masolat-mentese/`,
valódi Picasa 3.9) szerint a másolat **saját aláírást kap**, a forrás
viszont érintetlen marad:

| | forrás | másolat |
|---|---|---|
| EXIF | nincs egyáltalán | `Software`, `Artist`, `DateTime` |
| XMP | nincs | van (`dc:creator`, `xmp:ModifyDate`, `exif:DateTimeOriginal`) |

⚠️ **A dátum-megőrzés a lényegi rész.** Az `exif:DateTimeOriginal` a
mintában **2026-07-16 20:04:11** — pontosan a FORRÁS eredeti ideje —,
miközben a `ModifyDate` a másolás pillanata. A Picasa tehát nem felejti el,
mikor készült a kép; csak azt jegyzi fel, mikor másolta.

## Amiben ELTÉRÜNK az eredetitől — szándékosan

Az eredeti mindhárom név-mezőbe (`Software`, `Artist`, `dc:creator`) a
`Picasa` szót írja. **Mi a sajátunkat írjuk (`PicasaPy`)**: nem adjuk ki
magunkat a Google termékének, és a felhasználó fájljaiból is lássa, mi
készítette őket. A jegy ezt kifejezetten előírja.

## Miért itt, és nem a mentésben

A JPEG-et mi magunk kódoljuk (`cv2.imencode`), tehát a kész bájtsorba
szúrjuk be a szegmenseket — nincs újrakódolás, a képadat érintetlen. Ez a
`metadata/iptc_writer.py` szegmens-sebészetének mintája: csak az érintett
APP-szegmens épül, minden más bájt marad.

Nem JPEG kimenetnél (PNG) a függvény a bemenetet változatlanul adja
vissza: az EXIF/XMP beágyazása ott másképp működik, és a mérés sem fedi le.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

#: A név, amit a saját mezőinkbe írunk. NEM „Picasa" — ld. a
#: modul-docstring „Amiben eltérünk" szakaszát.
ALAIRAS = "PicasaPy"

_SOI = b"\xff\xd8"
_APP1 = 0xE1
_EXIF_ID = b"Exif\x00\x00"
_XMP_ID = b"http://ns.adobe.com/xap/1.0/\x00"
#: az XMP-csomag maximális mérete egy APP1 szegmensben (2 bájt hossz + azonosító)
_MAX_APP1_BODY = 65535 - 2 - len(_XMP_ID)


def _exif_datetime(moment: datetime) -> str:
    """EXIF `DateTime` alak: `ÉÉÉÉ:HH:NN ÓÓ:PP:MM` (a szabvány szerint)."""
    return moment.strftime("%Y:%m:%d %H:%M:%S")


def _xmp_datetime(moment: datetime) -> str:
    """XMP-dátum: ISO 8601, időzónával — a mintában `+02:00` állt."""
    return moment.astimezone().isoformat(timespec="seconds")


def _xmp_packet(modified_at: datetime, taken_at: datetime | None) -> bytes:
    """A mért minta szerkezetét követő, minimális XMP-csomag."""
    eredeti = (
        f'\n    exif:DateTimeOriginal="{_xmp_datetime(taken_at)}"'
        if taken_at is not None
        else ""
    )
    return (
        '<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>\n'
        '<x:xmpmeta xmlns:x="adobe:ns:meta/">\n'
        ' <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n'
        '  <rdf:Description rdf:about=""\n'
        '    xmlns:xmp="http://ns.adobe.com/xap/1.0/"\n'
        '    xmlns:dc="http://purl.org/dc/elements/1.1/"\n'
        '    xmlns:exif="http://ns.adobe.com/exif/1.0/"\n'
        f'    xmp:ModifyDate="{_xmp_datetime(modified_at)}"{eredeti}>\n'
        f"   <dc:creator><rdf:Seq><rdf:li>{ALAIRAS}</rdf:li></rdf:Seq></dc:creator>\n"
        "  </rdf:Description>\n"
        " </rdf:RDF>\n"
        "</x:xmpmeta>\n"
        '<?xpacket end="w"?>'
    ).encode("utf-8")


def _exif_blokk(modified_at: datetime, taken_at: datetime | None) -> bytes | None:
    """A `Software`/`Artist`/`DateTime` (és ha van, `DateTimeOriginal`)
    mezőket tartalmazó EXIF-blokk. `None`, ha a `piexif` nem elérhető —
    egy hiányzó aláírás soha nem akadályozhatja meg a MENTÉST."""
    try:
        import piexif
    except ImportError:  # pragma: no cover — a piexif projektfüggőség
        return None

    zeroth = {
        piexif.ImageIFD.Software: ALAIRAS.encode("ascii"),
        piexif.ImageIFD.Artist: ALAIRAS.encode("ascii"),
        piexif.ImageIFD.DateTime: _exif_datetime(modified_at).encode("ascii"),
    }
    exif_ifd = {}
    if taken_at is not None:
        # #1642: a FORRÁS eredeti ideje — ezt a megőrzést mértük az
        # eredetiben, és ez a jegy lényegi kérése.
        exif_ifd[piexif.ExifIFD.DateTimeOriginal] = _exif_datetime(
            taken_at
        ).encode("ascii")
    try:
        return piexif.dump({"0th": zeroth, "Exif": exif_ifd, "1st": {}, "GPS": {}})
    except Exception:  # pragma: no cover — sérült bemenet nem buktathat mentést
        return None


def _app1(azonosito: bytes, torzs: bytes) -> bytes:
    hossz = len(azonosito) + len(torzs) + 2
    return bytes((0xFF, _APP1, hossz >> 8, hossz & 0xFF)) + azonosito + torzs


def _exif_torzs(blokk: bytes) -> bytes:
    """A `piexif.dump` teljes APP1-et ad (`FFE1` + hossz + `Exif\\0\\0` + …);
    nekünk csak a TIFF-törzs kell, mert a szegmenst magunk építjük."""
    if blokk[:2] == b"\xff\xe1":
        return blokk[4 + len(_EXIF_ID):]
    if blokk[: len(_EXIF_ID)] == _EXIF_ID:
        return blokk[len(_EXIF_ID):]
    return blokk


def sign_jpeg(
    payload: bytes,
    *,
    modified_at: datetime,
    taken_at: datetime | None = None,
) -> bytes:
    """A kész JPEG-bájtsor kiegészítése EXIF- és XMP-aláírással (#1642).

    Args:
        payload: a `cv2.imencode` kimenete — a KÉPADAT változatlan marad.
        modified_at: a másolás pillanata (`DateTime`, `xmp:ModifyDate`).
        taken_at: a FORRÁS eredeti ideje. `None` esetén a dátum-megőrző
            mezők kimaradnak — nem találunk ki adatot.

    Nem JPEG bemenetnél (vagy ha az aláírás nem építhető) a bemenetet adja
    vissza változatlanul: egy hiányzó aláírás nem akadályozhatja meg a
    mentést.
    """
    if payload[:2] != _SOI:
        return payload

    szegmensek = b""
    exif = _exif_blokk(modified_at, taken_at)
    if exif is not None:
        szegmensek += _app1(_EXIF_ID, _exif_torzs(exif))
    csomag = _xmp_packet(modified_at, taken_at)
    if len(csomag) <= _MAX_APP1_BODY:
        szegmensek += _app1(_XMP_ID, csomag)
    if not szegmensek:
        return payload
    # A szegmensek közvetlenül az SOI után jönnek — ez a JPEG-szabvány
    # szerinti helyük, és így a meglévő szegmensek sorrendje sem borul.
    return _SOI + szegmensek + payload[2:]


def source_taken_at(path: str | Path) -> datetime | None:
    """A forrás eredeti ideje: az EXIF `DateTimeOriginal`, ha van; ha
    nincs, a fájl módosítási ideje.

    A mért mintában a forrásnak EXIF-je sem volt, és a Picasa mégis
    kitöltötte az `exif:DateTimeOriginal`-t — a FÁJL módosítási idejével
    (2026-07-16 20:04:11). A tartalék tehát nem a mi kényelmünk, hanem a
    mért viselkedés."""
    utvonal = Path(path)
    try:
        import piexif

        adat = piexif.load(str(utvonal))
        nyers = adat.get("Exif", {}).get(piexif.ExifIFD.DateTimeOriginal)
        if nyers:
            szoveg = nyers.decode("ascii", "ignore").strip("\x00 ")
            return datetime.strptime(szoveg, "%Y:%m:%d %H:%M:%S")
    except Exception:
        pass
    try:
        return datetime.fromtimestamp(utvonal.stat().st_mtime)
    except OSError:
        return None
