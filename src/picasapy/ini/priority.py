"""A kézi sorrend (`priority=`) a `.picasa.ini` kép-szakaszaiban (#1721).

Az ADR-014 (`docs/decisions/kezi-sorrend-a-picasa-iniben.md`) döntése: a
manuális sorrendet a mappa saját `.picasa.ini`-je hordozza, NEM a `db3`. Az
eredeti Picasa a kézi sorrendet a központi `albums_0.db`-ben, az album
tagsági listájának SORRENDJEKÉNT tartja (#1645) — azt a formátumot nem
írjuk.

⚠️ **Ez SZÁNDÉKOS ELTÉRÉS az eredetitől**, és a kulcs a mi kiterjesztésünk:
nincs mérve, hogy a Picasa megőrzi-e az általa nem ismert `priority=`
sort, amikor ő ír ugyanabba a fájlba. A MI oldalunk megőrzi az idegen
kulcsokat (mérve, ld. az ADR-t). Ha az eredeti eldobná, a kézi sorrend nem
vész el — csak a „hordozhatóság" érve gyengül.

## A formátum

| | |
|---|---|
| kulcs | `priority` a kép szakaszában |
| érték | tizedes szám, **pont** tizedesjellel (`docs/specs/tizedesjel.md`) |
| hiányzó érték | „nincs kézi hely" — a rendező a végére teszi, fájlnév szerint |
| ütközés | fájlnév dönt, hogy a sorrend determinisztikus legyen |

⚠️ A számozás **nem** egész (`kozteslepes`): beszúráskor két szomszéd közé a
felezőpont kerül, így egy áthelyezés EGY kulcsot ír, nem az egész mappát —
és nem termel tucatnyi `.picasa.ini`-írást.
"""

from __future__ import annotations

from .document import IniDocument

_KULCS = "priority"


def olvasd_a_prioritasokat(document: IniDocument) -> dict[str, float]:
    """fájlnév → kézi hely, a kép-szakaszokból.

    A romlott (nem számmá alakítható) értéket KIHAGYJA: a kép ilyenkor
    „nincs kézi helyen" állapotba esik. Nem dobhatunk — egy kézzel
    elrontott sor nem vihetné el a rács rendezését.
    """
    prioritasok: dict[str, float] = {}
    for section in document.file_sections():
        nyers = section.get(_KULCS)
        if nyers is None:
            continue
        try:
            prioritasok[section.name] = float(nyers.strip())
        except ValueError:
            continue
    return prioritasok


def prioritassal(
    document: IniDocument, nev: str, ertek: float
) -> IniDocument:
    """A kép kézi helyének beírása — a szakasz többi kulcsa érintetlen.

    Az érték MINDIG tizedes alakban megy ki (`3.0`, nem `3`): az olvasó
    `float`-ot vár, és így a fájl önmagában elmondja, hogy törtérték is
    lehet benne (a felezőpontos beszúrás épp ilyet termel).
    """
    szoveg = f"{float(ertek):.6g}"
    if "." not in szoveg and "e" not in szoveg:
        szoveg += ".0"
    return document.with_value(nev, _KULCS, szoveg)


def prioritas_nelkul(document: IniDocument, nev: str) -> IniDocument:
    """A kézi hely törlése — a kép visszaáll „nincs kézi hely" állapotba."""
    return document.with_removed(nev, _KULCS)


def kozteslepes(elozo: float | None, kovetkezo: float | None) -> float:
    """A beszúrás értéke két szomszéd KÖZÉ (vagy a lista szélére).

    `elozo`/`kovetkezo`: a beszúrási hely szomszédjainak kézi helye, vagy
    `None`, ha ott nincs szomszéd. A felezőpont az, ami miatt egy
    áthelyezés nem írja át a mappa összes kulcsát.
    """
    if elozo is None and kovetkezo is None:
        return 0.0
    if elozo is None:
        return float(kovetkezo) - 1.0
    if kovetkezo is None:
        return float(elozo) + 1.0
    return (float(elozo) + float(kovetkezo)) / 2.0
