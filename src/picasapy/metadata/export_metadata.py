"""Az EXPORT kimenetének metaadat-frissítése, ahogy az eredeti Picasa (#3961).

Mérés és forrás: `docs/specs/picasa-metaadat-tulajdonsagok.md` 16. szakasz
(204 eredeti export).

## A főszabály: a frissítés csak KIEGÉSZÍTÉS

A régi út (#136) a forrás APP1- és APP13-szegmenseit bájtra másolta. Az új út
ebből **semmit nem veszíthet el és nem ronthat el**: minden szegmens
bájtra átmegy (a kiterjesztett XMP, a második EXIF, az ismeretlen APP1 is),
és csak az első EXIF- és az első XMP-szegmens frissül. Ha bármelyik
frissítése nem sikerül vagy nem fér el (sérült blokk, kivétel, 64 KiB-os
APP1-határ), AZ a szegmens a forrás bájtjaival megy; a másik frissítése
ettől független. A teljes frissítés körül is ott a háló: bármilyen váratlan
hibánál a régi bájtmásolás a kimenet (`bajtmasolas`).

## Mit frissítünk

* EXIF (`tiff_helyben`: a forrás blokkja bájtra marad, a meglévő érték
  helyben íródik, az új tag a blokk végére fűzött IFD-másolatba kerül):
  `DateTime` = az export ideje; `PixelX/YDimension` = a KIMENET mérete;
  `Software`, `Artist` (`PicasaPy`, #1642), `DateTimeOriginal` (a
  forrásfájl ideje), `ExifVersion` (`0220`) csak ha HIÁNYZIK.
  `Orientation` = `1`, csak ha MEGVAN (#3966): a dekódolás a képpontokat
  már elforgatta, a forrás tagje kétszer fordítaná a képet (16. E: a
  meglévő `0x0d` kulcs üres értékkel kerül a halmazba).
  Az IFD1 beágyazott előnézete a kimenetből újragenerálva (160×120-ba),
  ha a forrásnak volt; ha nem generálható, a forrásé marad.
* XMP: a meglévő megmarad, `xmp:ModifyDate` = az export ideje, az `exif:`
  névtérből csak a két dátum marad (16. B). Ha a forrásnak nincs XMP-je:
  metaadat nélküli forrásnál (se EXIF, se XMP) a `copy_signature` mért
  csomagja; EXIF-es forrásnál csak egy `xmp:ModifyDate`-es csomag (a spec
  a `dc:creator`-t és az `exif:DateTimeOriginal`-t csak a metaadat nélküli
  forrásnál mérte). A burok (`x:xmpmeta`) nélküli vagy értelmezhetetlen
  XMP nem cserélődik le: bájtra megy.

* Interop IFD (#3989, 16. G): minden kimenetben; `InteropVersion` = `0100`
  (csak ha hiányzik), `0x1001`/`0x1002` = a FORRÁS pixelmérete (csak ha
  hiányzik), az `InteropIndex` NEM kerül be. A forrás mérete a JPEG SOF-jából
  jön, és a tájolás szerint állítva (5–8: felcserélve), mert a kimenet mérete
  is a már elforgatott képé — a tájolt forrás esete nincs mérve.

Amit a spec NEM rögzít, azt nem találjuk ki: az `ImageUniqueID` képzése
(16. C) 1.) és az APP13 tartalma nincs feltárva.
"""

from __future__ import annotations

import io
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

from picasapy.metadata.copy_signature import (
    ALAIRAS,
    _app1,
    _exif_datetime,
    _xmp_datetime,
    _xmp_packet,
    source_taken_at,
)
from picasapy.metadata.tiff_helyben import (
    LONG,
    SHORT,
    UNDEFINED,
    Ertek,
    Valtozas,
    ascii_ertek,
    frissitett_tiff,
    tajolas_1_helyben,
    tajolas_olvas,
)

_LOG = logging.getLogger(__name__)

_EXIF_ID = b"Exif\x00\x00"
_XMP_ID = b"http://ns.adobe.com/xap/1.0/\x00"
_SOI = b"\xff\xd8"
_SOS = 0xDA
#: a régi út (#136) is ezeket vitte át: APP1 (EXIF, XMP, kiterjesztett XMP)
#: és APP13 (Photoshop/IPTC). Az APP2 ICC-t az eredeti is elhagyja (16. A).
_MASOLT_MARKEREK = frozenset({0xE1, 0xED})
_MAX_SZEGMENS = 0xFFFF  # a hosszmező maga is beleszámít
_NS_XMP = "http://ns.adobe.com/xap/1.0/"
_NS_EXIF = "http://ns.adobe.com/exif/1.0/"
_NS_RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
#: az `exif:` névtérből ezek maradnak (spec 16. B) 5.)
_EXIF_MARAD = frozenset({"DateTimeOriginal", "DateTimeDigitized"})
_EXIF_VERZIO = b"0220"  # a metaadat nélküli forrás eredeti exportjában mért
_INTEROP_VERZIO = b"0100"  # spec 16. G) 3d
#: a JPEG SOF-markerei (a 0xC4 DHT, 0xC8 JPG és 0xCC DAC nem az)
_SOF_MARKEREK = frozenset({0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF})
_ELONEZET_MAX = (160, 120)
_XPACKET_KEZDET = '<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>\n'
_XPACKET_VEG = '\n<?xpacket end="w"?>'


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


def _app1_ha_elfer(azonosito: bytes, torzs: bytes) -> bytes | None:
    """Az APP1-szegmens, vagy `None`, ha túllépné a 65 535 bájtos hosszmezőt."""
    if 2 + len(azonosito) + len(torzs) > _MAX_SZEGMENS:
        return None
    return _app1(azonosito, torzs)


def _beszur(encoded: bytes, szegmensek: list[bytes]) -> bytes:
    """A szegmensek a kódolt JPEG vezető APP0-ja (JFIF) után, vagy az SOI után."""
    if not szegmensek:
        return encoded
    pont = 4 + int.from_bytes(encoded[4:6], "big") if encoded[2:4] == b"\xff\xe0" else 2
    return encoded[:pont] + b"".join(szegmensek) + encoded[pont:]


def _masolando(forras_bajt: bytes) -> list[bytes]:
    return [s for m, s in _szegmensek(forras_bajt) if m in _MASOLT_MARKEREK]


def _tajolas_egyre(szegmens: bytes) -> bytes:
    """Tartalék út (#3966): a forrás EXIF-szegmensében a meglévő tájolás-tagek
    (IFD0, IFD1) helyben `1`-re — a képpontok már állnak. Más szegmens, vagy
    hiba esetén a szegmens változatlan (a kép akkor is kimegy, figyelmeztetéssel)."""
    if szegmens[1:2] != b"\xe1" or not szegmens[4:].startswith(_EXIF_ID):
        return szegmens
    try:
        torzs = tajolas_1_helyben(szegmens[4 + len(_EXIF_ID) :])
        return szegmens[: 4 + len(_EXIF_ID)] + torzs
    except Exception:  # noqa: BLE001 — a kép a tájolás miatt sem bukhat el
        _LOG.warning("export: a tájolás-tag nem írható át, a forrásé marad", exc_info=True)
        return szegmens


def bajtmasolas(source: Path, encoded: bytes) -> bytes:
    """A régi út (#136): a forrás APP1/APP13-szegmensei bájtra, változatlanul.
    Ez a háló, ha a spec szerinti frissítés bármiért nem sikerül."""
    try:
        forras_bajt = source.read_bytes()
    except OSError:
        return encoded
    if not forras_bajt.startswith(_SOI) or not encoded.startswith(_SOI):
        return encoded
    return _beszur(encoded, [_tajolas_egyre(s) for s in _masolando(forras_bajt)])


# --- EXIF ---------------------------------------------------------------------


def _elonezet(encoded: bytes, size: tuple[int, int] = (0, 0)) -> bytes | None:
    """A kimenet 160×120-ba férő JPEG-előnézete, vagy `None`."""
    import cv2
    import numpy as np

    szel, mag = size
    flag = next(
        (
            flag
            for f, flag in (
                (8, cv2.IMREAD_REDUCED_COLOR_8),
                (4, cv2.IMREAD_REDUCED_COLOR_4),
                (2, cv2.IMREAD_REDUCED_COLOR_2),
            )
            if szel // f >= _ELONEZET_MAX[0] and mag // f >= _ELONEZET_MAX[1]
        ),
        cv2.IMREAD_COLOR,
    )
    kep = cv2.imdecode(np.frombuffer(encoded, np.uint8), flag)
    if kep is None:
        return None
    h, w = kep.shape[:2]
    arany = min(_ELONEZET_MAX[0] / w, _ELONEZET_MAX[1] / h, 1.0)
    uj = (max(1, round(w * arany)), max(1, round(h * arany)))
    if uj != (w, h):
        kep = cv2.resize(kep, uj, interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", kep, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return buf.tobytes() if ok else None


def _forras_meret(forras_bajt: bytes) -> tuple[int, int] | None:
    """A forrás-JPEG TÁROLT `(szélesség, magasság)`-a a SOF-ból, vagy `None`."""
    for marker, seg in _szegmensek(forras_bajt):
        if marker in _SOF_MARKEREK and len(seg) >= 9:
            mag = int.from_bytes(seg[5:7], "big")
            szel = int.from_bytes(seg[7:9], "big")
            return (szel, mag) if szel > 0 and mag > 0 else None
    return None


def _dekodolt_meret(meret: tuple[int, int], tiff: bytes | None) -> tuple[int, int]:
    """A tárolt méret a tájolás szerint (5–8: felcserélve): a dekódolás a
    képpontokat elforgatja, a kimenet mérete is ilyen."""
    if tiff is not None and (tajolas_olvas(tiff) or 1) >= 5:
        return meret[1], meret[0]
    return meret


def _interop_valtozasok(forras_meret: tuple[int, int] | None) -> list[Valtozas]:
    """Csak ha a forrásnak van mérete (spec 16. G): egyébként az Interop IFD
    üres lenne. Minden tag csak HIÁNYZÓKÉNT íródik; `InteropIndex` nincs."""
    if forras_meret is None:
        return []
    return [
        Valtozas("Interop", 0x0002, Ertek(UNDEFINED, _INTEROP_VERZIO), csak_ha_hianyzik=True),
        Valtozas("Interop", 0x1001, Ertek(LONG, int(forras_meret[0])), csak_ha_hianyzik=True),
        Valtozas("Interop", 0x1002, Ertek(LONG, int(forras_meret[1])), csak_ha_hianyzik=True),
    ]


def _exif_valtozasok(
    size: tuple[int, int], now: datetime, taken_at: datetime | None
) -> list[Valtozas]:
    nev = ascii_ertek(ALAIRAS)
    valtozasok = [
        Valtozas("0th", 0x0131, nev, csak_ha_hianyzik=True),  # Software
        Valtozas("0th", 0x013B, nev, csak_ha_hianyzik=True),  # Artist
        Valtozas("0th", 0x0132, ascii_ertek(_exif_datetime(now))),  # DateTime
        Valtozas("Exif", 0x9000, Ertek(UNDEFINED, _EXIF_VERZIO), csak_ha_hianyzik=True),
        Valtozas("Exif", 0xA002, Ertek(SHORT, int(size[0]))),  # PixelXDimension
        Valtozas("Exif", 0xA003, Ertek(SHORT, int(size[1]))),  # PixelYDimension
        # Orientation (#3966): a képpontok már állnak, a tag nem forgathat újra
        Valtozas("0th", 0x0112, Ertek(SHORT, 1), csak_ha_megvan=True),
        # az IFD1 (előnézet) tagje is: az újragenerált előnézet már áll
        Valtozas("1st", 0x0112, Ertek(SHORT, 1), csak_ha_megvan=True),
    ]
    if taken_at is not None:
        valtozasok.append(
            Valtozas(
                "Exif", 0x9003, ascii_ertek(_exif_datetime(taken_at)), csak_ha_hianyzik=True
            )
        )
    return valtozasok


def _exif_szegmens(
    tiff: bytes | None,
    *,
    source: Path,
    encoded: bytes,
    size: tuple[int, int],
    now: datetime,
    forras_meret: tuple[int, int] | None = None,
) -> bytes | None:
    """A frissített EXIF-APP1, vagy `None` (akkor a forrásé megy bájtra)."""
    valtozasok = _exif_valtozasok(size, now, source_taken_at(source))
    if forras_meret is not None:
        valtozasok += _interop_valtozasok(
            _vedett_meret(lambda: _dekodolt_meret(forras_meret, tiff))
        )
    torzs = frissitett_tiff(
        tiff, valtozasok, elonezet=lambda: _vedett("előnézet", lambda: _elonezet(encoded, size))
    )
    szegmens = _app1_ha_elfer(_EXIF_ID, torzs)
    if szegmens is None:
        # az új előnézettel nem fér el: a forrás előnézete marad
        szegmens = _app1_ha_elfer(_EXIF_ID, frissitett_tiff(tiff, valtozasok))
    return szegmens


# --- XMP ----------------------------------------------------------------------


def _nevterek_regisztralasa(torzs: str) -> None:
    for _esemeny, (prefix, uri) in ET.iterparse(io.StringIO(torzs), events=("start-ns",)):
        # az alapértelmezett névtér ("") és a foglalt `nsN` alak kimarad:
        # az ET ilyenkor maga ad előtagot, a tartalom ugyanaz
        if prefix and not prefix.startswith("ns"):
            ET.register_namespace(prefix, uri)


def _xmp_frissitve(xmp: bytes, now: datetime) -> bytes | None:
    """A meglévő XMP-csomag: `xmp:ModifyDate` beállítva, az `exif:` névtér a
    két dátumon kívül üres. `None`, ha a csomag nem értelmezhető, vagy nincs
    `x:xmpmeta` burka — ilyenkor a forrásé megy bájtra."""
    szoveg = xmp.decode("utf-8")
    kezdet, veg = szoveg.find("<x:xmpmeta"), szoveg.rfind("</x:xmpmeta>")
    if kezdet < 0 or veg < 0:
        return None
    torzs = szoveg[kezdet : veg + len("</x:xmpmeta>")]
    try:
        _nevterek_regisztralasa(torzs)
        gyoker = ET.fromstring(torzs)
    except (ET.ParseError, ValueError):
        return None
    ET.register_namespace("xmp", _NS_XMP)
    ET.register_namespace("exif", _NS_EXIF)
    ET.register_namespace("rdf", _NS_RDF)
    leirasok = list(gyoker.iter(f"{{{_NS_RDF}}}Description"))
    if not leirasok:
        return None
    mostani = _xmp_datetime(now)
    beallitva = False
    for leiras in leirasok:
        beallitva |= _leiras_frissitese(leiras, mostani)
    if not beallitva:
        leirasok[0].set(f"{{{_NS_XMP}}}ModifyDate", mostani)
    kiiras = ET.tostring(gyoker, encoding="unicode")
    ET.fromstring(kiiras)  # önellenőrzés: jól formált maradt
    return (_XPACKET_KEZDET + kiiras + _XPACKET_VEG).encode("utf-8")


def _leiras_frissitese(leiras: ET.Element, mostani: str) -> bool:
    """Egy `rdf:Description`: az `exif:` mezők (attribútum- ÉS elemalakban)
    a két dátumon kívül törölve, a meglévő `xmp:ModifyDate` frissítve."""
    exif_elotag = f"{{{_NS_EXIF}}}"
    for kulcs in [k for k in leiras.attrib if k.startswith(exif_elotag)]:
        if kulcs[len(exif_elotag) :] not in _EXIF_MARAD:
            del leiras.attrib[kulcs]
    for gyerek in [g for g in leiras if g.tag.startswith(exif_elotag)]:
        if gyerek.tag[len(exif_elotag) :] not in _EXIF_MARAD:
            leiras.remove(gyerek)
    kulcs = f"{{{_NS_XMP}}}ModifyDate"
    beallitva = False
    if kulcs in leiras.attrib:
        leiras.set(kulcs, mostani)
        beallitva = True
    for gyerek in leiras.findall(kulcs):
        gyerek.text = mostani
        beallitva = True
    return beallitva


def _xmp_csak_modositas(now: datetime) -> bytes:
    """EXIF-es, XMP nélküli forráshoz: csak az `xmp:ModifyDate` (J2)."""
    return (
        _XPACKET_KEZDET
        + '<x:xmpmeta xmlns:x="adobe:ns:meta/">\n'
        ' <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n'
        '  <rdf:Description rdf:about=""\n'
        '    xmlns:xmp="http://ns.adobe.com/xap/1.0/"\n'
        f'    xmp:ModifyDate="{_xmp_datetime(now)}"/>\n'
        " </rdf:RDF>\n"
        "</x:xmpmeta>"
        + _XPACKET_VEG
    ).encode("utf-8")


def _xmp_szegmens(
    forras_xmp: bytes | None, *, source: Path, now: datetime, metaadat_nelkuli: bool
) -> bytes | None:
    """A frissített/új XMP-APP1, vagy `None` (a forrásé megy, ha volt)."""
    if forras_xmp is not None:
        csomag = _xmp_frissitve(forras_xmp, now)
    elif metaadat_nelkuli:
        csomag = _xmp_packet(now, source_taken_at(source))
    else:
        csomag = _xmp_csak_modositas(now)
    return _app1_ha_elfer(_XMP_ID, csomag) if csomag is not None else None


# --- összeállítás -------------------------------------------------------------


def _elso(szegmensek: list[bytes], azonosito: bytes) -> int | None:
    return next(
        (i for i, s in enumerate(szegmensek) if s[1] == 0xE1 and s[4:].startswith(azonosito)),
        None,
    )


def _vedett_meret(fuggveny) -> tuple[int, int] | None:
    """A forrás méretének háló: hibánál `None` (Interop IFD nélkül megy tovább)."""
    try:
        return fuggveny()
    except Exception:  # noqa: BLE001 — a metaadat soha nem buktathat exportot
        _LOG.warning("export: a forrás mérete nem állapítható meg", exc_info=True)
        return None


def _vedett(nev: str, fuggveny) -> bytes | None:
    """Mezőnkénti háló: hibánál `None` (a forrás szegmense megy bájtra)."""
    try:
        return fuggveny()
    except Exception:  # noqa: BLE001 — a metaadat soha nem buktathat exportot
        _LOG.warning("export: a(z) %s frissítése kimaradt, a forrásé megy", nev, exc_info=True)
        return None


def _frissitett_szegmensek(
    source: Path,
    szegmensek: list[bytes],
    encoded: bytes,
    size: tuple[int, int],
    now: datetime,
    forras_meret: tuple[int, int] | None = None,
) -> list[bytes]:
    exif_i, xmp_i = _elso(szegmensek, _EXIF_ID), _elso(szegmensek, _XMP_ID)
    exif_uj = _vedett(
        "EXIF",
        lambda: _exif_szegmens(
            szegmensek[exif_i][4 + len(_EXIF_ID) :] if exif_i is not None else None,
            source=source,
            encoded=encoded,
            size=size,
            now=now,
            forras_meret=forras_meret,
        ),
    )
    xmp_uj = _vedett(
        "XMP",
        lambda: _xmp_szegmens(
            szegmensek[xmp_i][4 + len(_XMP_ID) :] if xmp_i is not None else None,
            source=source,
            now=now,
            metaadat_nelkuli=exif_i is None,
        ),
    )
    ki = list(szegmensek)
    if exif_uj is None and exif_i is not None:
        ki[exif_i] = _tajolas_egyre(ki[exif_i])  # a forrásé megy: a tájolása 1
    if xmp_uj is not None:
        if xmp_i is not None:
            ki[xmp_i] = xmp_uj
        else:
            ki.insert(exif_i + 1 if exif_i is not None else 0, xmp_uj)
    if exif_uj is not None:
        if exif_i is not None:
            ki[exif_i] = exif_uj
        else:
            ki.insert(0, exif_uj)
    return ki


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
    (a spec csak a JPEG-forrás exportját méri). Bármely hibánál a régi
    bájtmásolás eredménye a kimenet."""
    try:
        forras_bajt = source.read_bytes()
    except OSError:
        return encoded
    if not forras_bajt.startswith(_SOI) or not encoded.startswith(_SOI):
        return encoded
    ido = now if now is not None else datetime.now()
    szegmensek = _masolando(forras_bajt)
    try:
        forras_meret = _vedett_meret(lambda: _forras_meret(forras_bajt))
        uj = _frissitett_szegmensek(
            source, szegmensek, encoded, size, ido, forras_meret=forras_meret
        )
    except Exception:  # noqa: BLE001 — a metaadat soha nem buktathat exportot
        _LOG.warning("export: a metaadat-frissítés kimaradt, bájtmásolás", exc_info=True)
        uj = [_tajolas_egyre(s) for s in szegmensek]
    return _beszur(encoded, uj)
