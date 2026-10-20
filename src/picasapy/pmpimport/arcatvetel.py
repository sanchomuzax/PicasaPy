"""A db3 arcadatának átvétele a `.picasa.ini`-be (#3002, a #26 negyedik része).

## Miért kell

Az olvasó oldal a #5180 után a `deferredface` azonosítót és a kontaktlistát
részesíti előnyben; a `deferredregion` csak visszaesési pillanatkép. A **hívó**
hiányzott — a db3-ban álló arcok sehogy nem jutottak el a `.picasa.ini`-be,
pedig az az igazságforrás, és az eredeti Picasa is oda írja őket.

## A SZABÁLY: csak a hiányzó régiókat pótoljuk (#5180)

> A db3-régiót csak akkor vesszük át, ha a rect64 még nincs a fotó `faces=`
> sorában. A meglévő bejegyzések szövegét érintetlenül hagyjuk.

Az import nem írja felül az ini-ben lévő régiót. A más rect64-ű db3-régiót
viszont hozzáadja, így egyetlen meglévő arc sem rejti el az ütközésmentes
db3-adatot.

⚠️ **A kontakt is csak a régió beírásával EGYÜTT keletkezik.** Ha a rect64
már szerepel, a `[Contacts2]`-be sem írunk árva bejegyzést.

## Amit a spec 10. táblája kimond

* **6. sor** — az ini `ffffffffffffffff` értéke mellőzést jelent. A db3
  `deferredface`-beli ugyanez a szentinel ismeretlen arc, azt a külön
  indexút veszi át a Név nélküliek közé.
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

from collections.abc import Callable

from picasapy.ini.contacts import (
    ensure_contact,
    find_contact_id,
    generate_contact_id,
)
from picasapy.ini.document import IniDocument
from picasapy.ini.faces import Face, parse_faces, serialize_faces, with_face
from picasapy.pmpimport.deferredregion import DeferredFace

#: A db3 `deferredface` ismeretlen-személy szentinelje. Az INI `faces=`
#: mezőjében ugyanez mellőzést jelent, ezért az ismeretlen db3 arc külön
#: indexútba kerül.
ISMERETLEN_SZEMELY = "ffffffffffffffff"

#: A spec 10/10: importáláskor ezt az arcfelismerő-verziót írjuk.
FRVERSION = "1.5"

#: A `[Picasa]` szakasz neve — a `frversion` ide megy.
_PICASA_SZAKASZ = "Picasa"


def atveendo_arcok(arcok: tuple[DeferredFace, ...]) -> tuple[DeferredFace, ...]:
    """A ténylegesen az ini-be átveendő arcok — névtelen arc nélkül.

    A db3 ismeretlen sentineljét külön indexút veszi át; az INI-beli
    `ffffffffffffffff` mellőzési jelentés miatt itt nem személy.
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
    azonosito_gyar: Callable[[], str] | None = None,
) -> IniDocument:
    """A db3 arcainak átvétele EGY fotóra, az „A" szabály szerint.

    Csak a még hiányzó rect64-régiókat adja hozzá; a meglévő `faces=` érték
    bájtjai változatlan előtagként maradnak meg.

    `azonosito_gyar`: az új személyazonosítót adó hívható — a teszt így tud
    determinisztikus azonosítót adni; alapértelmezésben a közös, `%I64x`
    alakú kontaktazonosító-gyár dolgozik.
    """
    atveendo = atveendo_arcok(arcok)
    if not atveendo:
        return document
    if azonosito_gyar is None:
        azonosito_gyar = generate_contact_id
    szakasz = document.section(photo_name)
    nyers_faces = szakasz.get("faces") if szakasz is not None else None
    meglévok = parse_faces(nyers_faces or "")
    foglalt_rectek = {face.rect for face in meglévok}

    eredmeny = document
    uj_arcok: list[Face] = []
    for arc in atveendo:
        if arc.rect in foglalt_rectek:
            continue
        azonosito = find_contact_id(eredmeny, arc.name)
        if azonosito is None:
            azonosito = azonosito_gyar()
            eredmeny = ensure_contact(eredmeny, azonosito, arc.name)
        uj_arcok.append(Face(rect=arc.rect, contact_id=azonosito))
        foglalt_rectek.add(arc.rect)
    if not uj_arcok:
        return document

    if nyers_faces:
        elvalaszto = "" if nyers_faces.endswith(";") else ";"
        uj_ertek = nyers_faces + elvalaszto + serialize_faces(tuple(uj_arcok))
        eredmeny = eredmeny.with_value(photo_name, "faces", uj_ertek)
    else:
        for arc in uj_arcok:
            eredmeny = with_face(eredmeny, photo_name, arc)
    return eredmeny.with_value(_PICASA_SZAKASZ, "frversion", FRVERSION)


__all__ = [
    "FRVERSION",
    "ISMERETLEN_SZEMELY",
    "arcokat_atvesz",
    "atveendo_arcok",
]
