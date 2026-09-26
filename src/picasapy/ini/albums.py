"""Virtuális albumok: `[.album:<token>]` szekciók és az `albums=` CSV kulcs.

Figyelem: a parse→serialize normalizál (üres tokeneket elhagy), a byte-pontos
megőrzést a document-réteg adja — nem módosított `albums=` értéket nem szabad
ezen a modulon átengedni.
"""

from __future__ import annotations

from dataclasses import dataclass

from .document import ALBUM_SECTION_PREFIX, IniDocument

#: A beépített „Mellőzött emberek" álalbum tokenje (#3670, a #2187 nyitva
#: hagyott pontja). A spec (`picasa-arcfelismeres.md` 8. és 15/b szakasza)
#: szerint az eredeti Picasa ezzel a tokennel jelöli a `.picasa.ini`-ben az
#: elvetett arc-javaslatot (`CThumbDB::ignorefacealbum`); a `faceheaderpanel/
#: ignore` és `.../removesel` közös kezelője (`0x005c9b00`) írja. Nálunk a
#: NORMÁL virtuális-album úton megy (`with_album`/`without_album` lent) —
#: a token ÉRTÉKE mért, a fotó↔album kapcsolat ÍRÁSA a saját `albums=`
#: mechanizmusunk, nem az eredeti (a régió-szintű pontosság nyitva marad).
IGNORE_FACE_ALBUM_TOKEN = "]ignoreface"


@dataclass(frozen=True)
class Album:
    token: str
    name: str | None
    date: str | None
    description: str | None
    location: str | None


def parse_album_refs(value: str) -> tuple[str, ...]:
    """Az `albums=` kulcs token-listája."""
    return tuple(token for token in value.split(",") if token)


def serialize_album_refs(refs: tuple[str, ...]) -> str:
    return ",".join(refs)


def albums_of(document: IniDocument) -> tuple[Album, ...]:
    """A dokumentum összes virtuális albuma, definíciós sorrendben."""
    return tuple(
        Album(
            # A szekciónévbeli token az azonosító, a token= kulcs redundáns.
            token=section.name[len(ALBUM_SECTION_PREFIX) :],
            name=section.get("name"),
            date=section.get("date"),
            description=section.get("description"),
            location=section.get("location"),
        )
        for section in document.sections
        if section.name.startswith(ALBUM_SECTION_PREFIX)
    )


def with_album(document: IniDocument, photo_name: str, token: str) -> IniDocument:
    """A kép felvétele az albumba — az `albums=` CSV bővítése (#9).

    Idempotens: a már bent lévő token nem kerül be másodszor, és a meglévő
    sorrend sem változik (a Picasa a hozzáadás sorrendjét őrzi).
    """
    section = document.section(photo_name)
    current = parse_album_refs(section.get("albums") or "") if section else ()
    if token in current:
        return document
    return document.with_value(
        photo_name, "albums", serialize_album_refs((*current, token))
    )


def without_album(
    document: IniDocument, photo_name: str, token: str
) -> IniDocument:
    """A kép kivétele az albumból.

    Az utolsó tagság törlésekor maga az `albums=` kulcs is kikerül — üres
    kulcsot a Picasa sem hagy maga után.
    """
    section = document.section(photo_name)
    if section is None:
        return document
    current = parse_album_refs(section.get("albums") or "")
    if token not in current:
        return document
    remaining = tuple(ref for ref in current if ref != token)
    if not remaining:
        return document.with_removed(photo_name, "albums")
    return document.with_value(
        photo_name, "albums", serialize_album_refs(remaining)
    )


#: A tulajdonság-párbeszéd MÉRT mezői → a `.picasa.ini` kulcsai.
#:
#: A párbeszéd elrendezése a szállított `album.fen`-ből van (a Picasa
#: `runtime/` mappájából), a feliratok a `referencia/i18n-hu/album.xml`-ből:
#: `Név:` · `Dátum:` · `Zene:` · `Felvétel készítésének helye (opcionális):` ·
#: `Leírás (opcionális):`.
#:
#: ⛔ A leírás mező NEVE az `album.fen`-ben `caption`, a `.picasa.ini` KULCSA
#: viszont `description` (ezt olvassa az `albums_of`) — a kettő nem
#: keverhető össze.
#:
#: ⚠️ A `music` mező szándékosan NINCS itt: diavetítés-/mozgófilm-zene a
#: programban egyáltalán nincs, tehát nem is menthető (#3173).
_ALBUM_MEZOK = ("name", "date", "location", "description")

#: A NÉV nem törölhető: névtelen album a listában azonosíthatatlan volna.
_KOTELEZO_MEZO = "name"


def with_album_fields(
    document: IniDocument,
    token: str,
    *,
    name: str | None = None,
    date: str | None = None,
    location: str | None = None,
    description: str | None = None,
) -> IniDocument:
    """Egy MEGLÉVŐ album tulajdonságainak írása (#3173).

    A `None` azt jelenti: „ezt a mezőt nem szerkesztettük" — marad, ami volt.
    Az **üres** (vagy csak szóközös) érték a kulcs TÖRLÉSE, mert üres kulcsot
    a Picasa sem hagy maga után; a `name` ez alól kivétel (ott az üres érték
    nem törli a meglévő nevet).

    ⛔ Nem létező `[.album:<token>]` szekcióra **nem csinál semmit**: a
    tulajdonság-szerkesztés meglévő albumra szól, és egy elírt token nem
    hozhat létre szellem-albumot minden mappa ini-jében.
    """
    section_name = f"{ALBUM_SECTION_PREFIX}{token}"
    if document.section(section_name) is None:
        return document
    ertekek = {
        "name": name,
        "date": date,
        "location": location,
        "description": description,
    }
    eredmeny = document
    for kulcs in _ALBUM_MEZOK:
        ertek = ertekek[kulcs]
        if ertek is None:
            continue
        tisztitott = ertek.strip()
        if not tisztitott:
            if kulcs == _KOTELEZO_MEZO:
                continue
            eredmeny = eredmeny.with_removed(section_name, kulcs)
            continue
        eredmeny = eredmeny.with_value(section_name, kulcs, tisztitott)
    return eredmeny


def ensure_album(
    document: IniDocument, token: str, name: str | None = None
) -> IniDocument:
    """A `[.album:<token>]` definíció megléte a dokumentumban.

    A MEGLÉVŐ definíciót nem írja át: ha az album már szerepel az ini-ben,
    a neve marad (a Picasa oldali átnevezés a felhasználó szándéka, nem a
    miénk). Új szekciónál a `token=` kulcsot is kiírjuk, ahogy a Picasa is.
    """
    section_name = f"{ALBUM_SECTION_PREFIX}{token}"
    if document.section(section_name) is not None:
        return document
    result = document.with_value(section_name, "token", token)
    if name is not None:
        result = result.with_value(section_name, "name", name)
    return result
