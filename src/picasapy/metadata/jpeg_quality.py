"""JPEG-minőség becslése a kvantálótáblából + mintavétel-utótag (#4579).

Az eredeti Picasa „JPEG Quality" sora (spec `picasa-metaadat-tulajdonsagok.md`
17. E): az IJG-alaptáblához viszonyított átlagos arányból becsül
(`0x009ea1e0`), a SOF mintavételi tényezőiből pedig utótagot ír (`0x009ff490`).

⚠️ SZÁNDÉKOS ELTÉRÉS: az eredeti a ≥ 128-as 8 bites táblaelemet előjelesen
olvassa (`movsx`), ezért Q ≤ ~38 alatt nem ír sort. Ezt NEM vesszük át —
nálunk minden minőségre van sor (a hívó döntése, #4579).
"""

from __future__ import annotations

from pathlib import Path

#: IJG-alaptáblák (JPEG Annex K), természetes (sor-folytonos) sorrendben.
_FENYESSEG = (
    16, 11, 10, 16, 24, 40, 51, 61,
    12, 12, 14, 19, 26, 58, 60, 55,
    14, 13, 16, 24, 40, 57, 69, 56,
    14, 17, 22, 29, 51, 87, 80, 62,
    18, 22, 37, 56, 68, 109, 103, 77,
    24, 35, 55, 64, 81, 104, 113, 92,
    49, 64, 78, 87, 103, 121, 120, 101,
    72, 92, 95, 98, 112, 100, 103, 99,
)
_SZIN = (
    17, 18, 24, 47, 99, 99, 99, 99,
    18, 21, 26, 66, 99, 99, 99, 99,
    24, 26, 56, 99, 99, 99, 99, 99,
    47, 66, 99, 99, 99, 99, 99, 99,
    99, 99, 99, 99, 99, 99, 99, 99,
    99, 99, 99, 99, 99, 99, 99, 99,
    99, 99, 99, 99, 99, 99, 99, 99,
    99, 99, 99, 99, 99, 99, 99, 99,
)


def _cikkcakk_sorrend() -> tuple[int, ...]:
    """A cikkcakk-index -> természetes pozíció leképezés."""
    pozicio = []
    for osszeg in range(15):
        elemek = [
            (sor, osszeg - sor)
            for sor in range(8)
            if 0 <= osszeg - sor < 8
        ]
        if osszeg % 2 == 0:
            elemek.reverse()
        pozicio.extend(sor * 8 + oszlop for sor, oszlop in elemek)
    return tuple(pozicio)


_CIKKCAKK = _cikkcakk_sorrend()
#: Az alaptáblák a DQT-ban álló (cikkcakk) sorrendben.
_STANDARD = tuple(
    tuple(tabla[pozicio] for pozicio in _CIKKCAKK) for tabla in (_FENYESSEG, _SZIN)
)

_SOF_MARKEREK = frozenset(range(0xC0, 0xD0)) - {0xC4, 0xC8, 0xCC}
_MAX_FEJLEC = 4 * 1024 * 1024


def jpeg_quality_text(path: str | Path) -> str | None:
    """`"<minőség>"` + mintavétel-utótag, vagy None (nem JPEG / nincs tábla)."""
    try:
        with open(path, "rb") as handle:
            adat = handle.read(_MAX_FEJLEC)
    except OSError:
        return None
    if adat[:2] != b"\xff\xd8":
        return None
    minoseg = None
    utotag = ""
    for marker, szegmens in _szegmensek(adat):
        if marker == 0xDB:
            becsles = _utolso_tabla_becslese(szegmens)
            if becsles:
                minoseg = becsles
        elif marker in _SOF_MARKEREK:
            utotag = _mintavetel_utotag(szegmens)
    if not minoseg:
        return None
    return f"{minoseg}{utotag}"


def _szegmensek(adat: bytes):
    """(marker, tartalom) párok az SOS-ig; a hibás szerkezetnél megáll."""
    hely = 2
    while hely + 4 <= len(adat):
        if adat[hely] != 0xFF:
            return
        marker = adat[hely + 1]
        if marker == 0xFF:  # kitöltő bájt
            hely += 1
            continue
        if marker == 0xDA or marker == 0xD9:
            return
        hossz = int.from_bytes(adat[hely + 2 : hely + 4], "big")
        if hossz < 2 or hely + 2 + hossz > len(adat):
            return
        yield marker, adat[hely + 4 : hely + 2 + hossz]
        hely += 2 + hossz


def _utolso_tabla_becslese(szegmens: bytes) -> int:
    """A DQT-szegmens UTOLSÓ táblájának becslése (0, ha nincs/értelmezhetetlen)."""
    if len(szegmens) < 64:
        return 0
    hely = 0
    becsles = 0
    while hely < len(szegmens):
        pq_tq = szegmens[hely]
        hely += 1
        bajt = 2 if pq_tq >> 4 else 1
        veg = hely + 64 * bajt
        if veg > len(szegmens):
            break
        elemek = [
            int.from_bytes(szegmens[hely + i * bajt : hely + (i + 1) * bajt], "big")
            for i in range(64)
        ]
        hely = veg
        tq = pq_tq & 0x0F
        becsles = _becsles(elemek, tq) if tq < 2 else 0
    return becsles


def _becsles(elemek: list[int], tq: int) -> int:
    if all(elem == 1 for elem in elemek):
        return 100
    standard = _STANDARD[tq]
    atlag = sum(100.0 * q / s for q, s in zip(elemek, standard, strict=True)) / 64
    if atlag > 100:
        erteke = 5000.0 / atlag
    else:
        erteke = (200.0 - atlag) * 0.5
    return round(erteke)


def _mintavetel_utotag(szegmens: bytes) -> str:
    """A SOF komponenseinek mintavétele -> ` (444)` / ` (422)` / ` (411)`."""
    if len(szegmens) < 6:
        return ""
    db = szegmens[5]
    if len(szegmens) < 6 + 3 * db:
        return ""
    if db == 1:
        return " (444)"
    if db not in (3, 4):
        return ""
    tenyezok = [
        (szegmens[6 + 3 * i + 1] >> 4, szegmens[6 + 3 * i + 1] & 0x0F)
        for i in range(db)
    ]
    elso = tenyezok[0]
    if any(t != (1, 1) for t in tenyezok[1:3]):
        return ""
    negyedik_ok = db == 3 or tenyezok[3] == elso
    if not negyedik_ok:
        return ""
    if elso == (1, 1):
        return " (444)"
    if elso == (2, 1):
        return " (422)"
    if elso == (1, 2) and db == 3:
        return " (422)"
    if elso == (2, 2):
        return " (411)"
    return ""
