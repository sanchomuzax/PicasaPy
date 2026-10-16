"""Forrás-őr a #5105-höz: a fogd-és-vidd tesztek nem csalhatnak.

A #5105-ben a húzás-tesztek valódi egérhúzás helyett közvetlenül hívták a
ledobási jelet (`QMetaObject.invokeMethod(..., "photosDroppedOnFolder", ...)`),
vagy átállították a termék Drag-módját (`setProperty("dragType", ...)`).
Ezért voltak zöldek, miközben a húzás a felhasználónál nem működött.

Ez az őr a tests/ összes Python-fájlját nézi (a saját fájlját kivéve), és
három csalási mintát tilt. Az ejtést a DropArea-nak kell elkapnia.
"""

from __future__ import annotations

import re
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent
SAJAT_FAJL = Path(__file__).resolve()

# A QML-ejtési jelek nevei. Mindegyik tartalmazza a "Dropped" részt.
EJTESI_JELEK = (
    "Dropped",
    "DroppedOn",
    "faceDropped",
    "photosDropped",
    "folderDropped",
    "newAlbumPhotosDropped",
)

# Kivételek: tests/-hez képest relatív, posix útvonal → indoklás.
# Szándékosan üres: a csalás nem kivétel.
KIVETELEK: dict[str, str] = {}

UZENET = "valódi egérhúzással teszteld, a ledobást a DropArea-nak kell elkapnia (#5105)"

TIPUS_INVOKE = "invokeMethod ejtési jellel"
TIPUS_DRAGTYPE = 'setProperty("dragType", ...)'
TIPUS_EMIT = "közvetlen .emit() ejtési jelen"

_JELNEVEK = "|".join(EJTESI_JELEK)
_INVOKE = re.compile(r"invokeMethod\(")
_JELNEV_LITERAL = re.compile(r"""["'][^"'\n]*(?:%s)[^"'\n]*["']""" % _JELNEVEK)
_DRAGTYPE = re.compile(r"""setProperty\(\s*["']dragType["']""")
_KOZVETLEN_EMIT = re.compile(r"(?:%s)\w*\.emit\(" % _JELNEVEK)


def _sor(szoveg: str, poz: int) -> int:
    return szoveg.count("\n", 0, poz) + 1


def _invoke_hivasok(szoveg: str):
    """Az invokeMethod(...) hívások (kezdőpozíció, szöveg) párjai, zárójelre egyensúlyozva."""
    for talalat in _INVOKE.finditer(szoveg):
        melyseg = 1
        vege = talalat.end()
        while vege < len(szoveg) and melyseg:
            if szoveg[vege] == "(":
                melyseg += 1
            elif szoveg[vege] == ")":
                melyseg -= 1
            vege += 1
        yield talalat.start(), szoveg[talalat.start() : vege]


def ejtesi_hibak(szoveg: str) -> list[tuple[int, str]]:
    """A csalási minták találatai egy forrásszövegben: (sor, tipus) párok."""
    hibak = []
    for poz, hivas in _invoke_hivasok(szoveg):
        if _JELNEV_LITERAL.search(hivas):
            hibak.append((_sor(szoveg, poz), TIPUS_INVOKE))
    for talalat in _DRAGTYPE.finditer(szoveg):
        hibak.append((_sor(szoveg, talalat.start()), TIPUS_DRAGTYPE))
    for talalat in _KOZVETLEN_EMIT.finditer(szoveg):
        hibak.append((_sor(szoveg, talalat.start()), TIPUS_EMIT))
    return sorted(hibak)


def _tesztfajlok():
    for utvonal in sorted(TESTS_DIR.rglob("*.py")):
        if utvonal.resolve() == SAJAT_FAJL or "__pycache__" in utvonal.parts:
            continue
        yield utvonal


def _talalatok() -> list[tuple[str, int, str]]:
    """Minden tests/-beli találat: (relatív útvonal, sor, tipus). A kivételek kimaradnak."""
    talalatok = []
    for utvonal in _tesztfajlok():
        rel = utvonal.relative_to(TESTS_DIR).as_posix()
        if rel in KIVETELEK:
            continue
        szoveg = utvonal.read_text(encoding="utf-8", errors="replace")
        talalatok.extend((rel, sor, tipus) for sor, tipus in ejtesi_hibak(szoveg))
    return talalatok


def _ellenoriz(tipus: str) -> None:
    hibak = [
        f"tests/{rel}:{sor}: {tipus} - {UZENET}"
        for rel, sor, t in _talalatok()
        if t == tipus
    ]
    assert not hibak, "\n".join(hibak)


def test_nincs_dragtype_hamisitas():
    _ellenoriz(TIPUS_DRAGTYPE)


def test_nincs_ejtesi_jel_invokemethod_hivassal():
    _ellenoriz(TIPUS_INVOKE)


def test_nincs_kozvetlen_ejtesi_jel_emit():
    _ellenoriz(TIPUS_EMIT)


def test_kivetelek_leteznek_es_indokoltak():
    for rel, indok in KIVETELEK.items():
        assert (TESTS_DIR / rel).is_file(), f"nincs ilyen kivétel-fájl: tests/{rel}"
        assert indok.strip(), f"üres indok: tests/{rel}"


def test_orzo_felismeri_a_csalo_mintakat():
    tobbsoros = 'QMetaObject.invokeMethod(\n    x,\n    "photosDroppedOnFolder",\n    Q,\n)'
    assert ejtesi_hibak(tobbsoros) == [(1, TIPUS_INVOKE)]
    assert ejtesi_hibak("obj.setProperty('dragType', 1)") == [(1, TIPUS_DRAGTYPE)]
    assert ejtesi_hibak("photosDropped.emit(rows)") == [(1, TIPUS_EMIT)]


def test_orzo_nem_fogja_a_tiszta_hivasokat():
    assert ejtesi_hibak('QMetaObject.invokeMethod(x, "submitUrls", Q_ARG("QVariant", u))') == []
    # QML-szöveg, nem Python-hívás: ez az őr hatókörén kívül esik
    assert ejtesi_hibak("root.photosDropped(rows)") == []
