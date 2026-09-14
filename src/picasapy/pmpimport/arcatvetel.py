"""A db3 arcadatának átvétele a `.picasa.ini`-be (#3002, a #26 negyedik része).

## Miért kell

Az olvasó oldal régóta kész: az `importer.iter_photo_records` a
`deferredregion` oszlopból `DeferredFace(rect, név)` párokat ad. A **hívó**
hiányzott — a db3-ban álló arcok sehogy nem jutottak el a `.picasa.ini`-be,
pedig az az igazságforrás, és az eredeti Picasa is oda írja őket.

## A SZABÁLY: csak a hiányzót pótoljuk (#3002 „A")

> Ahol az ini-ben **nincs** `faces=`, oda beírjuk a db3-ból származót; ahol
> **van**, hozzá sem nyúlunk.

Miért ez, és nem az egyesítés: az `A` **soha nem ír felül meglévő adatot**,
tehát nem ronthat el semmit. Ha az ini-ben már áll arc, azt vagy a
felhasználó, vagy az eredeti Picasa írta — az import nem tudja, melyik a
frissebb, tehát nem is dönthet helyette. A részleges eltérések feloldása
(régiónkénti egyesítés átfedés-vizsgálattal) így nyitva marad; az a
felhasználó szeme elé való, nem néma automatikáé.

⚠️ **A kontakt is csak az írással EGYÜTT keletkezik.** Ha a `faces=` miatt
kihagyjuk a fotót, a `[Contacts2]`-be sem írunk — különben árva bejegyzés
maradna egy olyan személyről, aki a mappában sehol nem szerepel.

## Amit a spec 10. táblája kimond

* **6. sor** — a csupa `f` azonosító az „ismeretlen" szentinel: **nem
  személyként** importáljuk, tehát kihagyjuk.
* **7. sor** — a duplikált kontakt élesben előfordul: az importáló
  **tűrje**. Nálunk ez annyit tesz, hogy azonos névhez EGY azonosító
  tartozik (a `find_contact_id` újrahasznosít), több arc-téglalappal.
* **10. sor** — aki importál, `frversion = "1.5"`-öt írjon.

## Ami ebben a modulban NINCS benne

A `]ignoreface` albumba sorolt arcok „Figyelmen kívül hagyva" rekeszbe
irányítása: ahhoz a fotó↔album tagság kell a db3-ból, amit az
`importer._COLUMNS` ma nem olvas. Külön lépés, a #3002 nyitva marad rá.
"""

from __future__ import annotations

import secrets

from picasapy.ini.contacts import ensure_contact, find_contact_id
from picasapy.ini.document import IniDocument
from picasapy.ini.faces import Face, with_face
from picasapy.pmpimport.deferredregion import DeferredFace

#: A spec 10/6: az „ismeretlen" szentinel. A `deferredregion` NÉVMEZŐJÉBEN
#: is ez áll, amikor a Picasa arcot talált, de nem tudja, kihez tartozik.
ISMERETLEN_SZEMELY = "ffffffffffffffff"

#: A spec 10/10: importáláskor ezt az arcfelismerő-verziót írjuk.
FRVERSION = "1.5"

#: A `[Picasa]` szakasz neve — a `frversion` ide megy.
_PICASA_SZAKASZ = "Picasa"


def atveendo_arcok(arcok: tuple[DeferredFace, ...]) -> tuple[DeferredFace, ...]:
    """A ténylegesen átveendő arcok — a szentinel és a névtelen kihagyva.

    A kihagyás **tételes**, nem az egész fotóra szól: egy ismeretlen arc
    nem viszi magával a mellette álló, megnevezett arcokat.
    """
    return tuple(
        arc
        for arc in arcok
        if arc.name.strip() and arc.name.casefold() != ISMERETLEN_SZEMELY
    )


def arcokat_atvesz(
    document: IniDocument,
    photo_name: str,
    arcok: tuple[DeferredFace, ...],
    *,
    azonosito_gyar=lambda: secrets.token_hex(8),
) -> IniDocument:
    """A db3 arcainak átvétele EGY fotóra, az „A" szabály szerint.

    Érintetlenül adja vissza a dokumentumot, ha nincs átveendő arc, vagy ha
    a fotónak **már van** `faces=` kulcsa.

    `azonosito_gyar`: az új személyazonosítót adó hívható — a teszt így tud
    determinisztikus azonosítót adni, élesben `secrets.token_hex(8)` (a
    `people_controller` ugyanezt használja).
    """
    atveendo = atveendo_arcok(arcok)
    if not atveendo:
        return document
    szakasz = document.section(photo_name)
    if szakasz is not None and szakasz.get("faces"):
        # ⛔ az „A" szabály lelke: meglévő adathoz hozzá sem nyúlunk
        return document

    eredmeny = document
    for arc in atveendo:
        azonosito = find_contact_id(eredmeny, arc.name)
        if azonosito is None:
            azonosito = azonosito_gyar()
            eredmeny = ensure_contact(eredmeny, azonosito, arc.name)
        eredmeny = with_face(
            eredmeny, photo_name, Face(rect=arc.rect, contact_id=azonosito)
        )
    return eredmeny.with_value(_PICASA_SZAKASZ, "frversion", FRVERSION)


__all__ = [
    "FRVERSION",
    "ISMERETLEN_SZEMELY",
    "arcokat_atvesz",
    "atveendo_arcok",
]
