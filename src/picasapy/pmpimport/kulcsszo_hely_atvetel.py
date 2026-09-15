"""A db3 kulcsszavainak és helyadatának átvétele a `.picasa.ini`-be (#2336).

## Miért kell

Az OLVASÓ oldal a #2342 óta kész: az `importer.iter_photo_records` behozza a
`tags`, `lat` és `long` oszlopokat, és a geotag tényleges jelzője a
`geoview` üressége (képenkénti egyezésre mérve a tulajdonos adatmappáján:
219/219). A **fogyasztó** hiányzott — a tulajdonos szava a jegyen:

> „Az adat ma nem az importon vész el, hanem azon, hogy nincs fogyasztója."

A `.picasa.ini` az igazságforrás (7. rögzített döntés), és az eredeti Picasa
is oda írja a `keywords=` és `geotag=` kulcsot, tehát az átvétel oda megy.

## A SZABÁLY: csak a hiányzót pótoljuk

Ugyanaz az „A" szabály, ami a #3002 arcátvételét vezeti: ahol a fotónak már
van értéke, ahhoz **hozzá sem nyúlunk**. Ha ott már áll adat, azt vagy a
felhasználó, vagy az eredeti Picasa írta — az import nem tudja, melyik a
frissebb, tehát nem is dönthet helyette. Így az átvétel **soha nem ír felül
meglévő adatot**, tehát nem ronthat el semmit.

A két adatfajta **külön** dől el: a meglévő `keywords=` nem akadálya annak,
hogy a hiányzó `geotag=` bekerüljön.

## Ami ebben a modulban NINCS benne

A mappánkénti végigjárás és az ini kiírása — az a hívó dolga (az
`ini.io.save_document`-en át, sávinvariáns). Itt csak a dokumentum-szintű,
tiszta átalakítás van, ahogy az `arcatvetel`-ben is.
"""

from __future__ import annotations

from picasapy.ini.document import IniDocument
from picasapy.metadata.gps import format_geotag

#: a `.picasa.ini` kulcsai, amikbe az átvétel ír
_KULCSSZO_KULCS = "keywords"
_GEOTAG_KULCS = "geotag"


def atveendo_kulcsszavak(kulcsszavak: tuple[str, ...]) -> tuple[str, ...]:
    """A ténylegesen átveendő kulcsszavak: trimmelve, üresek és
    ismétlődések nélkül, az ELSŐ előfordulás sorrendjében.

    A `.picasa.ini` `keywords=` kulcsa vesszővel elválasztott lista, tehát
    az üres elem ott két egymás melletti vesszőként jelenne meg — a Picasa
    ilyet nem ír.
    """
    eredmeny: list[str] = []
    for nyers in kulcsszavak:
        szo = (nyers or "").strip()
        if szo and szo not in eredmeny:
            eredmeny.append(szo)
    return tuple(eredmeny)


def _van_erteke(document: IniDocument, photo_name: str, kulcs: str) -> bool:
    """Van-e a fotónak NEM ÜRES értéke a megadott kulcson.

    Az üres érték (`keywords=`) nem „meglévő adat": azt pótoljuk.
    """
    szakasz = document.section(photo_name)
    if szakasz is None:
        return False
    return bool((szakasz.get(kulcs) or "").strip())


def kulcsszavakat_atvesz(
    document: IniDocument, photo_name: str, kulcsszavak: tuple[str, ...]
) -> IniDocument:
    """A db3 kulcsszavainak átvétele EGY fotóra, az „A" szabály szerint.

    Érintetlenül adja vissza a dokumentumot, ha nincs átveendő kulcsszó,
    vagy ha a fotónak **már van** nem üres `keywords=` kulcsa.
    """
    atveendo = atveendo_kulcsszavak(kulcsszavak)
    if not atveendo:
        return document
    if _van_erteke(document, photo_name, _KULCSSZO_KULCS):
        # ⛔ az „A" szabály lelke: meglévő adathoz hozzá sem nyúlunk
        return document
    return document.with_value(photo_name, _KULCSSZO_KULCS, ",".join(atveendo))


def helyet_atvesz(
    document: IniDocument,
    photo_name: str,
    latitude: float | None,
    longitude: float | None,
) -> IniDocument:
    """A db3 helyadatának átvétele EGY fotóra, az „A" szabály szerint.

    Érintetlenül adja vissza a dokumentumot, ha bármelyik koordináta
    hiányzik, ha az érték értelmetlen (a `GeoPoint` validálása szerint),
    vagy ha a fotónak **már van** nem üres `geotag=` kulcsa.

    ⚠️ A `0,0` koordinátát KIÍRJA: a hamis nullákat már az olvasó oldal
    kiszűrte a `geoview` üressége alapján, tehát ami idáig eljut, valódi
    hely (a jegy 2. tulajdonosi észrevétele).
    """
    if latitude is None or longitude is None:
        return document
    if _van_erteke(document, photo_name, _GEOTAG_KULCS):
        return document
    try:
        ertek = format_geotag(latitude, longitude)
    except (ValueError, TypeError):
        # sérült adat `None`-t ér, nem kivételt (#301 elve)
        return document
    return document.with_value(photo_name, _GEOTAG_KULCS, ertek)


__all__ = [
    "atveendo_kulcsszavak",
    "helyet_atvesz",
    "kulcsszavakat_atvesz",
]
