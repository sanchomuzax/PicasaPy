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
#: Egy szegmens legfeljebb 64 KiB (a hosszmező 16 bites).
_SOS = 0xDA
_EOI = 0xD9


def jpeg_quality_text(path: str | Path) -> str | None:
    """`"<minőség>"` + mintavétel-utótag, vagy None (nem JPEG / nincs tábla).

    A fájlt szegmensenként olvassa, és az SOS-nál (a képadat előtt) megáll,
    ezért egy nagy fájlból is csak a fejléc (jellemzően néhány tíz kB) jön be
    — a hívás hálózati meghajtón, kijelölésenként is olcsó.

    A minőség az utolsó DQT-tábla átlagos arányából becsült érték. Telítődés:
    a 8 bites táblaelemek 255-nél megállnak, ezért a nagyon alacsony beállított
    minőség (Q ≲ 5, mérve: Q = 1…3 → „13”) nem adható vissza pontosan; a
    becslés alulról kb. 13-nál megáll.
    """
    try:
        with open(path, "rb") as handle:
            minoseg, utotag = _fejlec_adatai(handle)
    except (OSError, ValueError):
        return None
    if not minoseg:
        return None
    return f"{minoseg}{utotag}"


def _fejlec_adatai(handle) -> tuple[int | None, str]:
    if handle.read(2) != b"\xff\xd8":
        return None, ""
    minoseg = None
    utotag = ""
    for marker, szegmens in _szegmensek(handle):
        if marker == 0xDB:
            becsles = _utolso_tabla_becslese(szegmens)
            if becsles:
                minoseg = becsles
        elif marker in _SOF_MARKEREK:
            utotag = _mintavetel_utotag(szegmens)
    return minoseg, utotag


def _szegmensek(handle):
    """(marker, tartalom) párok az SOS-ig; a hibás szerkezetnél megáll."""
    while True:
        fej = handle.read(2)
        if len(fej) < 2 or fej[0] != 0xFF:
            return
        marker = fej[1]
        while marker == 0xFF:  # kitöltő bájt
            kovetkezo = handle.read(1)
            if not kovetkezo:
                return
            marker = kovetkezo[0]
        if marker in (_SOS, _EOI):
            return
        if marker == 0x00 or 0xD0 <= marker <= 0xD7 or marker == 0x01:
            continue  # hosszmező nélküli jelölő
        hossz_bajt = handle.read(2)
        if len(hossz_bajt) < 2:
            return
        hossz = int.from_bytes(hossz_bajt, "big")
        if hossz < 2:
            return
        tartalom = handle.read(hossz - 2)
        if len(tartalom) < hossz - 2:
            return
        yield marker, tartalom


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
