"""Személynevek a fájl XMP-régióiból (#4579, spec 17. F: `0x00baa500`).

MWG `mwg-rs:Name` vagy Microsoft `MPReg:PersonDisplayName`. Régiónként: a név
nem üres, a téglalap nem elfajult, a típus hiányzik vagy `Face` (kis-nagybetű
nélkül). **Az érvényes MWG-név kiszorítja az MP-t**: ha van legalább egy MWG-név, az MP
régióit az eredeti elhagyja; csupa érvénytelen MWG-régió mellett az MP-nevek
megmaradnak (a spec 17. F-jénél szigorúbb olvasat nem kell: nevet nem
veszítünk).

A régió mindhárom szokásos RDF-alakban olvasható: `parseType="Resource"`
(elemek és attribútumok), valamint az `<rdf:li><rdf:Description …/></rdf:li>`
(Lightroom, Windows Live Photo Gallery); az `Area` szintén.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

_RDF = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
_MWG = "{http://www.metadataworkinggroup.com/schemas/regions/}"
_ST_AREA = "{http://ns.adobe.com/xap/1.0/sType/Area#}"
_MPRI = "{http://ns.microsoft.com/photo/1.2/t/RegionInfo#}"
_MPREG = "{http://ns.microsoft.com/photo/1.2/t/Region#}"


def xmp_person_names(xmp) -> tuple[str, ...]:
    """A személynevek az XMP-csomagból, dokumentum-sorrendben; hibásra ()."""
    if isinstance(xmp, str):
        xmp = xmp.encode("utf-8", "replace")
    if not isinstance(xmp, bytes) or not xmp.strip():
        return ()
    try:
        gyoker = ET.fromstring(xmp.strip(b"\x00 \t\r\n"))
    except (ET.ParseError, ValueError):
        return ()
    mwg = list(gyoker.iter(_MWG + "RegionList"))
    mwg_regiok = [li for lista in mwg for li in lista.iter(_RDF + "li")]
    mwg_nevek = _nevek(_mwg_nev(li) for li in mwg_regiok)
    if mwg_nevek:
        return mwg_nevek
    mp_regiok = [
        li
        for lista in gyoker.iter(_MPRI + "Regions")
        for li in lista.iter(_RDF + "li")
    ]
    return _nevek(_mp_nev(li) for li in mp_regiok)


def _nevek(jeloltek) -> tuple[str, ...]:
    return tuple(nev for nev in jeloltek if nev)


def _nyit(elem):
    """Ha az elem egyetlen gyereke `rdf:Description`, annak tartalma számít
    (a `parseType="Resource"` helyett álló, explicit RDF-alak)."""
    gyerekek = list(elem)
    if len(gyerekek) == 1 and gyerekek[0].tag == _RDF + "Description":
        return gyerekek[0]
    return elem


def _ertek(li, kulcs: str) -> str | None:
    """Attribútum- vagy elemalakban álló érték."""
    if kulcs in li.attrib:
        return li.attrib[kulcs]
    elem = li.find(kulcs)
    return elem.text if elem is not None else None


def _mwg_nev(li) -> str | None:
    li = _nyit(li)
    nev = (_ertek(li, _MWG + "Name") or "").strip()
    tipus = _ertek(li, _MWG + "Type")
    if not nev or (tipus is not None and tipus.strip().casefold() != "face"):
        return None
    terulet = li.find(_MWG + "Area")
    forras = _nyit(terulet) if terulet is not None else li
    szeles = _szam(_ertek(forras, _ST_AREA + "w"))
    magas = _szam(_ertek(forras, _ST_AREA + "h"))
    if szeles is None or magas is None or szeles <= 0 or magas <= 0:
        return None
    return nev


def _mp_nev(li) -> str | None:
    li = _nyit(li)
    nev = (_ertek(li, _MPREG + "PersonDisplayName") or "").strip()
    if not nev:
        return None
    reszek = (_ertek(li, _MPREG + "Rectangle") or "").split(",")
    if len(reszek) != 4:
        return None
    szeles, magas = _szam(reszek[2]), _szam(reszek[3])
    if szeles is None or magas is None or szeles <= 0 or magas <= 0:
        return None
    return nev


def _szam(szoveg) -> float | None:
    try:
        return float(szoveg)
    except (TypeError, ValueError):
        return None
