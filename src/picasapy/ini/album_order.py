"""Az album képsorrendje: `albumorder=<token>:<hely>` a kép szakaszában (#4599).

Az ADR-016 (`docs/decisions/album-sorrend-a-kep-szakaszaban.md`) döntése: az
album tagjainak sorrendjét minden tag a SAJÁT szakaszában hordozza, az
`albums=` mellett, tagságonként egy `<token>:<hely>` párral. A tagságot
továbbra is az `albums=` adja; az `albumorder=` csak sorrend.

SAJÁT FUNKCIÓ (#4599): az eredeti Picasa az album sorrendjét a központi
keresőindex szólistájában tartja (`db3\\wordhash.dat`, `docs/specs/album-sorrend.md`),
nem a `.picasa.ini`-ben. A funkció (tárolt, átrendezhető album-sorrend) az
eredetiben is megvan; a TÁROLÁS helye a miénk, mert a központi adatbázist nem
írjuk (ADR-016). Nem mérve, hogy az eredeti megőrzi-e az ismeretlen kulcsot
(NY1/NY2, ADR-016) — a `priority=` (ADR-014) ugyanezt a kockázatot hordozza.

## A formátum

| | |
|---|---|
| kulcs | `albumorder` a **kép** szakaszában |
| érték | vesszővel elválasztott `<token>:<hely>` párok |
| hely | tizedes szám, **pont** tizedesjellel, mindig tizedes alakban (`3.0`) |
| érvényes pár | csak az, amelynek tokenje az `albums=`-ben is szerepel |
| elárvult / romlott pár | olvasáskor kimarad, nem dob |
| üres lista | a kulcs törlődik |
"""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path

from .document import IniDocument
from .io import IniSaveError, update_document

KEY = "albumorder"
_ALBUMS_KEY = "albums"


def _member_tokens(value: str | None) -> tuple[str, ...]:
    """Az `albums=` token-listája (az `albums.parse_album_refs` párja; itt
    külön áll, hogy az `albums` modul ide importálhasson körkörösség nélkül)."""
    return tuple(token for token in (value or "").split(",") if token)


def _format_place(place: float) -> str:
    text = format(float(place), ".10g")
    if "." not in text and "e" not in text and "n" not in text:
        text += ".0"
    return text


def parse_places(value: str | None) -> dict[str, float]:
    """Az `albumorder=` nyers értéke → token → hely.

    A romlott párt (nincs kettőspont, nem szám, nem véges) KIHAGYJA: egy
    kézzel elrontott sor nem vihet el egy album rendezését. Ismétlődő
    tokennél az első érvényes pár nyer.
    """
    places: dict[str, float] = {}
    for pair in (value or "").split(","):
        token, separator, raw = pair.partition(":")
        token = token.strip()
        if not separator or not token or token in places:
            continue
        try:
            place = float(raw.strip())
        except ValueError:
            continue
        if not math.isfinite(place):
            continue
        places[token] = place
    return places


def serialize_places(places: Mapping[str, float]) -> str:
    return ",".join(f"{token}:{_format_place(place)}" for token, place in places.items())


def places_of_section(section) -> dict[str, float]:
    """Egy kép szakaszának ÉRVÉNYES {token → hely} párjai.

    Érvényes az a pár, amelynek tokenje a kép `albums=` kulcsában is szerepel
    (a tagságot az `albums=` adja). Az olvasó, aki már megtalálta a szakaszt
    (kis-nagybetű-független névkereséssel), ezt hívja — a szakasznévvel
    kulcsolt `places_of` eltérő betűzésnél nem találná meg.
    """
    raw = section.get(KEY)
    if raw is None:
        return {}
    members = set(_member_tokens(section.get(_ALBUMS_KEY)))
    return {
        token: place
        for token, place in parse_places(raw).items()
        if token in members
    }


def places_of(document: IniDocument) -> dict[str, dict[str, float]]:
    """Fájlnév (a szakasz neve) → {token → hely}, csak az ÉRVÉNYES párokkal.

    Hely nélküli kép nem szerepel. Fájlnévvel keresni a `places_of_section`
    (a `document.section(név)` találatán) a helyes: a szakasznév betűzése
    eltérhet a lemezen lévő fájlnévétől.
    """
    result: dict[str, dict[str, float]] = {}
    for section in document.file_sections():
        valid = places_of_section(section)
        if valid:
            result[section.name] = valid
    return result


def _write_places(
    document: IniDocument, photo_name: str, places: Mapping[str, float]
) -> IniDocument:
    if not places:
        return document.with_removed(photo_name, KEY)
    return document.with_value(photo_name, KEY, serialize_places(places))


def with_album_places(
    document: IniDocument, token: str, places: Mapping[str, float]
) -> IniDocument:
    """Egy album tagjainak új helye (fájlnév → hely) EGY dokumentumban.

    Csak a megnevezett tokenű pár változik; a kép más albumokhoz tartozó
    párjai és a szakasz minden más sora érintetlen. Olyan képre, amely nem
    tagja az albumnak (az `albums=` nem tartalmazza a tokent), nem ír.
    """
    updated = document
    for photo_name, place in places.items():
        section = updated.section(photo_name)
        if section is None:
            continue
        if token not in _member_tokens(section.get(_ALBUMS_KEY)):
            continue
        updated = updated.with_value(
            photo_name,
            KEY,
            _replace_raw_pair(section.get(KEY), token, float(place)),
        )
    return updated


def _replace_raw_pair(raw: str | None, token: str, place: float) -> str:
    """A nyers `albumorder=` szövegben CSAK a `token` párja cserélődik.

    A többi nyers pár (romlott, elárvult, ismeretlen) bájtra érintetlen marad:
    más album párját vagy egy másik program írását nem normalizáljuk. Ha a
    tokennek még nincs (érvényes) párja, az új pár a végére kerül.
    """
    new_pair = f"{token}:{_format_place(place)}"
    pairs = (raw or "").split(",") if raw else []
    for index, pair in enumerate(pairs):
        if token in parse_places(pair):
            return ",".join([*pairs[:index], new_pair, *pairs[index + 1 :]])
    return ",".join([*pairs, new_pair])


def without_album_place(
    document: IniDocument, photo_name: str, token: str
) -> IniDocument:
    """Az album helyének (az `albumorder=` párjának) kivétele egy képről.

    Ha nincs ilyen pár, a dokumentum VÁLTOZATLAN marad (a kulcs más párjai és
    sorrendje, valamint a nem érintett képek bájtra azonosak).
    """
    section = document.section(photo_name)
    if section is None:
        return document
    raw = section.get(KEY)
    if raw is None:
        return document
    current = parse_places(raw)
    if token not in current:
        return document
    del current[token]
    return _write_places(document, photo_name, current)


class AlbumOrderWriteError(IniSaveError):
    """Az album átrendezése egy vagy több mappában nem íródott ki.

    A szöveg megnevezi a mappá(ka)t; a művelet megismételhető (a ki nem írt
    tagok a régi helyükkel maradtak, a sorrend determinisztikus).
    """


def write_album_places(
    token: str,
    placements: Iterable[tuple[Path, Mapping[str, float]]],
    *,
    on_written: Callable[[Path], None] | None = None,
) -> None:
    """Az album új sorrendjének kiírása: mappánként EGY `update_document`.

    `placements`: (a mappa `.picasa.ini`-je, fájlnév → hely). Minden mappát
    megpróbál; ha egy írás bukik, a többit akkor is megpróbálja, és a végén
    `AlbumOrderWriteError`-t dob, amely megnevezi a kimaradt mappá(ka)t.
    Az `on_written` minden sikeresen kiírt ini után lefut (index-szinkron).
    """
    failed: list[str] = []
    for ini_path, places in placements:
        if not places:
            continue
        try:
            update_document(
                ini_path,
                lambda document, places=places: with_album_places(
                    document, token, places
                ),
                backup=True,
            )
        except (OSError, RuntimeError) as error:
            failed.append(f"{ini_path.parent}: {error}")
            continue
        if on_written is not None:
            on_written(ini_path)
    if failed:
        raise AlbumOrderWriteError(
            "Az album sorrendje nem íródott ki ezekben a mappákban: "
            + "; ".join(failed)
        )
