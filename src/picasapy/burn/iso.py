"""ISO 9660 lemezkép írása — a biztonsági mentés kimenete (#2074).

## Miért a SAJÁT író

A tulajdonos a **(b)** ágat választotta: „a gyűjtemény mentése több
lemezképre". Lemezíró a célgépen nincs, és az eredeti Picasa is lemezképet ír
helyette (`il_BurnPanel::InsertNext::7s/7p` — „1 ISO." / „%d ISO-fájl").

Külső ISO-eszköz (`xorriso`, `genisoimage`, `mkisofs`) a célkörnyezetben NINCS
telepítve — mérve —, és futásidejű Python-függőséget sem veszünk fel egyetlen
mentés-kimenetért. A formátum viszont nyilvános szabvány (ECMA-119), és a
projekt amúgy is maga írja a formátumkezelőit.

⚠️ **Az ÍRÓ helyességét nem magunkkal mérjük.** A próbák a kiírt képet a
`7z`-vel (p7zip — teljesen független megvalósítás) olvassák vissza: az
könyvtárneveket, fájlneveket és BÁJTOKAT ad. Egy saját olvasóval való
összevetés önigazolás volna.

## Amit ez a modul tud, és amit NEM

* ISO 9660 (ECMA-119) alapszerkezet + **Joliet** kiterjesztés. A Joliet adja a
  valódi (ékezetes, hosszú) fájlneveket; enélkül a fotók `IMG_0001.JPG` helyett
  csonkolt, csupa nagybetűs neveket kapnának. Linux és Windows egyaránt a
  Joliet-fát csatolja fel, ha van.
* Alkönyvtárak tetszőleges mélységben — a mentés a fotók **relatív útját**
  megőrzi, tehát a fa kell.
* **NINCS** Rock Ridge (POSIX-jogosultságok, hosszú nevek Unixon), nincs
  bootolható kép, nincs többmenetes (multisession) írás. A mentéshez egyik sem
  kell, és amit nem építünk meg, azt ki is mondjuk.

## A szerkezet, ahogy kiírjuk

| szektor | mi |
|---|---|
| 0–15 | rendszer-terület (nulla) |
| 16 | elsődleges kötetleíró (PVD) |
| 17 | kiegészítő kötetleíró (Joliet SVD) |
| 18 | lezáró kötetleíró |
| 19– | útvonal-táblák (ISO L/M, Joliet L/M) |
| … | könyvtár-kiterjedések (előbb az ISO-fa, majd a Joliet-fa) |
| … | a fájlok tartalma — **közös**: a két fa UGYANARRA a kiterjedésre mutat |
"""

from __future__ import annotations

import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

#: ECMA-119: a logikai blokk mérete. Ugyanaz a 2048, amit a kapacitás-képlet
#: is használ (`burn.SZEKTOR_BAJT`, `0x0066bf35`).
SZEKTOR = 2048

#: A rendszer-terület után az első kötetleíró helye (ECMA-119 6.2.1).
ELSO_LEIRO_SZEKTOR = 16

#: Joliet: UCS-2 szintek escape-sorozatai. A 3. szintet (`%/E`) írjuk — ezt
#: ismeri fel a Linux `iso9660` modul és a Windows is.
_JOLIET_ESCAPE = b"%/E"

#: Joliet: a névhossz felső korlátja UCS-2 karakterben (ECMA-119 amendment).
JOLIET_NEV_MAX = 64

_DKONYVTAR = 0x02  # könyvtár-jelző a katalógus-rekord flags mezőjében


def _egesz_le(ertek: int, bajt: int) -> bytes:
    return int(ertek).to_bytes(bajt, "little")


def _egesz_be(ertek: int, bajt: int) -> bytes:
    return int(ertek).to_bytes(bajt, "big")


def _mindket_veg(ertek: int, bajt: int) -> bytes:
    """ECMA-119 „both-byte-order" mező: előbb kis-, majd nagy-endián."""
    return _egesz_le(ertek, bajt) + _egesz_be(ertek, bajt)


def _szektorra(meret: int) -> int:
    """Hány szektort foglal `meret` bájt."""
    return (int(meret) + SZEKTOR - 1) // SZEKTOR


def _parnara(adat: bytes) -> bytes:
    """Páros hosszra tölti — a katalógus-rekordok mérete mindig páros."""
    return adat + (b"\x00" if len(adat) % 2 else b"")


def _datum7(masodperc: float) -> bytes:
    """A katalógus-rekordok 7 bájtos dátuma (ECMA-119 9.1.5)."""
    t = time.gmtime(masodperc)
    return bytes(
        (
            max(0, min(255, t.tm_year - 1900)),
            t.tm_mon,
            t.tm_mday,
            t.tm_hour,
            t.tm_min,
            min(59, t.tm_sec),
            0,  # GMT-eltolás negyedórákban
        )
    )


def _datum17(masodperc: float) -> bytes:
    """A kötetleírók 17 bájtos dátuma (ECMA-119 8.4.26)."""
    t = time.gmtime(masodperc)
    return (
        f"{t.tm_year:04d}{t.tm_mon:02d}{t.tm_mday:02d}"
        f"{t.tm_hour:02d}{t.tm_min:02d}{min(59, t.tm_sec):02d}00"
    ).encode("ascii") + b"\x00"


_ISO_ENGEDETT = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_")


def iso_nev(nev: str, *, konyvtar: bool) -> str:
    """A név ISO 9660 (1. szint) alakja: `8.3`, csupa nagybetű, `;1` verzió.

    Az ékezetes és hosszú neveket a **Joliet**-fa hordozza; ez az alak csak
    azért kell, hogy a képet a legegyszerűbb olvasó is meg tudja nyitni.
    """
    nyers = nev.upper()
    if konyvtar:
        tiszta = "".join(k if k in _ISO_ENGEDETT else "_" for k in nyers)
        return (tiszta[:8] or "_")
    torzs, _, kiterjesztes = nyers.rpartition(".")
    if not torzs:  # nincs pont a névben
        torzs, kiterjesztes = nyers, ""
    t = "".join(k if k in _ISO_ENGEDETT else "_" for k in torzs)[:8] or "_"
    e = "".join(k if k in _ISO_ENGEDETT else "_" for k in kiterjesztes)[:3]
    return f"{t}.{e};1" if e else f"{t}.;1"


def joliet_nev(nev: str, *, konyvtar: bool) -> str:
    """A név Joliet alakja: a VALÓDI név, legfeljebb 64 UCS-2 karakteren.

    A fájlnév végére `;1` kerül — a Joliet-képeket író eszközök is ezt teszik,
    és az olvasók (Linux, Windows) levágják."""
    if konyvtar:
        return nev[:JOLIET_NEV_MAX]
    utovel = nev[: JOLIET_NEV_MAX - 2] + ";1"
    return utovel


@dataclass
class _Bejegyzes:
    """Egy fájl a képben: a forrás, a neve és a helye a képen belül."""

    nev: str
    forras: Path
    meret: int
    kezdo_szektor: int = 0


@dataclass
class _Konyvtar:
    """Egy könyvtár a képben — mindkét fa ugyanebből épül."""

    nev: str
    szulo: "_Konyvtar | None" = None
    alkonyvtarak: "list[_Konyvtar]" = field(default_factory=list)
    fajlok: list[_Bejegyzes] = field(default_factory=list)
    #: a katalógus kiterjedése a két fában (ISO, illetve Joliet)
    iso_szektor: int = 0
    iso_meret: int = 0
    joliet_szektor: int = 0
    joliet_meret: int = 0
    #: az útvonal-tábla 1-alapú sorszáma (mindkét fában azonos)
    sorszam: int = 0

    def gyermek(self, nev: str) -> "_Konyvtar":
        for k in self.alkonyvtarak:
            if k.nev == nev:
                return k
        uj = _Konyvtar(nev=nev, szulo=self)
        self.alkonyvtarak.append(uj)
        return uj


def _fa_epitese(tetelek: Iterable[tuple[str, Path]]) -> _Konyvtar:
    """A relatív útvonalakból könyvtárfa. A sorrend a neveké — determinizmus."""
    gyoker = _Konyvtar(nev="")
    for relativ, forras in tetelek:
        ut = Path(str(relativ).replace("\\", "/"))
        aktualis = gyoker
        for resz in ut.parts[:-1]:
            aktualis = aktualis.gyermek(resz)
        p = Path(forras)
        aktualis.fajlok.append(
            _Bejegyzes(nev=ut.name, forras=p, meret=p.stat().st_size)
        )
    _rendezd(gyoker)
    return gyoker


def _rendezd(konyvtar: _Konyvtar) -> None:
    konyvtar.alkonyvtarak.sort(key=lambda k: k.nev)
    konyvtar.fajlok.sort(key=lambda f: f.nev)
    for gyermek in konyvtar.alkonyvtarak:
        _rendezd(gyermek)


def _szelessegi(gyoker: _Konyvtar) -> list[_Konyvtar]:
    """A könyvtárak szélességi sorrendben — az útvonal-tábla ezt kéri."""
    sor = [gyoker]
    index = 0
    while index < len(sor):
        sor.extend(sor[index].alkonyvtarak)
        index += 1
    for szam, konyvtar in enumerate(sor, start=1):
        konyvtar.sorszam = szam
    return sor


def _katalogus_rekord(
    nev: bytes, szektor: int, meret: int, *, konyvtar: bool, ido: float
) -> bytes:
    """Egy katalógus-rekord (ECMA-119 9.1)."""
    mag = (
        b"\x00"  # a hosszt utólag írjuk be
        + b"\x00"
        + _mindket_veg(szektor, 4)
        + _mindket_veg(meret, 4)
        + _datum7(ido)
        + bytes((_DKONYVTAR if konyvtar else 0,))
        + b"\x00\x00"
        + _mindket_veg(1, 2)
        + bytes((len(nev),))
        + nev
    )
    mag = _parnara(mag)
    return bytes((len(mag),)) + mag[1:]


def _katalogus(
    konyvtar: _Konyvtar, *, joliet: bool, ido: float
) -> bytes:
    """Egy könyvtár teljes katalógusa (`.`, `..`, majd a tartalma)."""

    def kodol(nev: str, *, kvt: bool) -> bytes:
        if joliet:
            return joliet_nev(nev, konyvtar=kvt).encode("utf-16-be")
        return iso_nev(nev, konyvtar=kvt).encode("ascii")

    sajat_sz = konyvtar.joliet_szektor if joliet else konyvtar.iso_szektor
    sajat_m = konyvtar.joliet_meret if joliet else konyvtar.iso_meret
    szulo = konyvtar.szulo or konyvtar
    szulo_sz = szulo.joliet_szektor if joliet else szulo.iso_szektor
    szulo_m = szulo.joliet_meret if joliet else szulo.iso_meret

    rekordok = [
        _katalogus_rekord(b"\x00", sajat_sz, sajat_m, konyvtar=True, ido=ido),
        _katalogus_rekord(b"\x01", szulo_sz, szulo_m, konyvtar=True, ido=ido),
    ]
    for gyermek in konyvtar.alkonyvtarak:
        rekordok.append(
            _katalogus_rekord(
                kodol(gyermek.nev, kvt=True),
                gyermek.joliet_szektor if joliet else gyermek.iso_szektor,
                gyermek.joliet_meret if joliet else gyermek.iso_meret,
                konyvtar=True,
                ido=ido,
            )
        )
    for fajl in konyvtar.fajlok:
        rekordok.append(
            _katalogus_rekord(
                kodol(fajl.nev, kvt=False),
                fajl.kezdo_szektor,
                fajl.meret,
                konyvtar=False,
                ido=ido,
            )
        )

    # A rekord nem lóghat át szektorhatáron (ECMA-119 6.8.1.1).
    ki = bytearray()
    for rekord in rekordok:
        hely = len(ki) % SZEKTOR
        if hely + len(rekord) > SZEKTOR:
            ki.extend(b"\x00" * (SZEKTOR - hely))
        ki.extend(rekord)
    return bytes(ki)


def _utvonal_tabla(
    konyvtarak: Sequence[_Konyvtar], *, joliet: bool, nagy_endian: bool
) -> bytes:
    ki = bytearray()
    for konyvtar in konyvtarak:
        if konyvtar.szulo is None:
            nev = b"\x00"
        elif joliet:
            nev = joliet_nev(konyvtar.nev, konyvtar=True).encode("utf-16-be")
        else:
            nev = iso_nev(konyvtar.nev, konyvtar=True).encode("ascii")
        szektor = konyvtar.joliet_szektor if joliet else konyvtar.iso_szektor
        szulo_sorszam = konyvtar.szulo.sorszam if konyvtar.szulo else 1
        rekord = (
            bytes((len(nev), 0))
            + (_egesz_be(szektor, 4) if nagy_endian else _egesz_le(szektor, 4))
            + (
                _egesz_be(szulo_sorszam, 2)
                if nagy_endian
                else _egesz_le(szulo_sorszam, 2)
            )
            + nev
        )
        ki.extend(_parnara(rekord))
    return bytes(ki)


def _szoveg_mezo(szoveg: str, hossz: int, *, joliet: bool) -> bytes:
    if joliet:
        nyers = szoveg.encode("utf-16-be")[:hossz]
        return nyers + b"\x00" * (hossz - len(nyers))
    nyers = szoveg.upper().encode("ascii", "replace")[:hossz]
    return nyers + b" " * (hossz - len(nyers))


def _kotetleiro(
    *,
    tipus: int,
    kotetnev: str,
    osszes_szektor: int,
    ut_tabla_meret: int,
    ut_tabla_l: int,
    ut_tabla_m: int,
    gyoker_rekord: bytes,
    joliet: bool,
    ido: float,
) -> bytes:
    ki = bytearray()
    ki += bytes((tipus,)) + b"CD001" + bytes((1,))
    ki += b"\x00" if not joliet else b"\x00"  # jelzők / nem használt
    ki += _szoveg_mezo("PICASAPY", 32, joliet=joliet)
    ki += _szoveg_mezo(kotetnev, 32, joliet=joliet)
    ki += b"\x00" * 8
    ki += _mindket_veg(osszes_szektor, 4)
    if joliet:
        ki += _JOLIET_ESCAPE + b"\x00" * (32 - len(_JOLIET_ESCAPE))
    else:
        ki += b"\x00" * 32
    ki += _mindket_veg(1, 2)  # kötetkészlet mérete
    ki += _mindket_veg(1, 2)  # sorszám
    ki += _mindket_veg(SZEKTOR, 2)
    ki += _mindket_veg(ut_tabla_meret, 4)
    ki += _egesz_le(ut_tabla_l, 4) + _egesz_le(0, 4)
    ki += _egesz_be(ut_tabla_m, 4) + _egesz_be(0, 4)
    ki += gyoker_rekord
    for hossz in (128, 128, 128, 128):
        ki += _szoveg_mezo("PICASAPY", hossz, joliet=joliet)
    for hossz in (37, 37, 37):
        ki += _szoveg_mezo("", hossz, joliet=joliet)
    ki += _datum17(ido) * 2
    ki += b"\x00" * 17 + b"\x00" * 17
    ki += bytes((1,)) + b"\x00"
    ki += b"\x00" * 512
    ki += b"\x00" * 653
    return bytes(ki[:SZEKTOR]).ljust(SZEKTOR, b"\x00")


def iso_kiirasa(
    tetelek: Iterable[tuple[str, Path]],
    cel: Path,
    *,
    kotetnev: str = "PICASAPY",
    ido: float | None = None,
) -> Path:
    """Egy ISO 9660 + Joliet lemezkép kiírása a megadott fájlokból.

    `tetelek`: `(relatív útvonal a képen belül, forrásfájl)` párok. A relatív
    útvonal könyvtárakat is tartalmazhat — a fa abból épül.

    A visszatérés a kiírt kép útja. A kép **determinisztikus**: ugyanabból a
    bemenetből ugyanazok a bájtok (az `ido` kivételével, ami megadható).
    """
    ido = time.time() if ido is None else float(ido)
    gyoker = _fa_epitese(tetelek)
    konyvtarak = _szelessegi(gyoker)

    # 1. menet: a katalógusok MÉRETE (a tartalmuk még nem végleges, de a
    # rekordok hossza nem függ a kiterjedés-számoktól)
    for konyvtar in konyvtarak:
        konyvtar.iso_meret = len(_katalogus(konyvtar, joliet=False, ido=ido))
        konyvtar.joliet_meret = len(_katalogus(konyvtar, joliet=True, ido=ido))

    iso_ut_l = _utvonal_tabla(konyvtarak, joliet=False, nagy_endian=False)
    iso_ut_m = _utvonal_tabla(konyvtarak, joliet=False, nagy_endian=True)
    jol_ut_l = _utvonal_tabla(konyvtarak, joliet=True, nagy_endian=False)
    jol_ut_m = _utvonal_tabla(konyvtarak, joliet=True, nagy_endian=True)

    szektor = ELSO_LEIRO_SZEKTOR + 3  # PVD, SVD, lezáró
    iso_ut_l_sz, szektor = szektor, szektor + _szektorra(len(iso_ut_l))
    iso_ut_m_sz, szektor = szektor, szektor + _szektorra(len(iso_ut_m))
    jol_ut_l_sz, szektor = szektor, szektor + _szektorra(len(jol_ut_l))
    jol_ut_m_sz, szektor = szektor, szektor + _szektorra(len(jol_ut_m))

    for konyvtar in konyvtarak:
        konyvtar.iso_szektor = szektor
        szektor += _szektorra(konyvtar.iso_meret)
    for konyvtar in konyvtarak:
        konyvtar.joliet_szektor = szektor
        szektor += _szektorra(konyvtar.joliet_meret)
    for konyvtar in konyvtarak:
        for fajl in konyvtar.fajlok:
            fajl.kezdo_szektor = szektor
            szektor += max(1, _szektorra(fajl.meret))
    osszes_szektor = szektor

    gyoker_iso = _katalogus_rekord(
        b"\x00", gyoker.iso_szektor, gyoker.iso_meret, konyvtar=True, ido=ido
    )
    gyoker_jol = _katalogus_rekord(
        b"\x00", gyoker.joliet_szektor, gyoker.joliet_meret,
        konyvtar=True, ido=ido,
    )

    cel = Path(cel)
    cel.parent.mkdir(parents=True, exist_ok=True)
    with cel.open("wb") as ki:
        ki.write(b"\x00" * SZEKTOR * ELSO_LEIRO_SZEKTOR)
        ki.write(
            _kotetleiro(
                tipus=1, kotetnev=kotetnev, osszes_szektor=osszes_szektor,
                ut_tabla_meret=len(iso_ut_l), ut_tabla_l=iso_ut_l_sz,
                ut_tabla_m=iso_ut_m_sz, gyoker_rekord=gyoker_iso,
                joliet=False, ido=ido,
            )
        )
        ki.write(
            _kotetleiro(
                tipus=2, kotetnev=kotetnev, osszes_szektor=osszes_szektor,
                ut_tabla_meret=len(jol_ut_l), ut_tabla_l=jol_ut_l_sz,
                ut_tabla_m=jol_ut_m_sz, gyoker_rekord=gyoker_jol,
                joliet=True, ido=ido,
            )
        )
        ki.write((bytes((255,)) + b"CD001" + bytes((1,))).ljust(SZEKTOR, b"\x00"))
        for tabla in (iso_ut_l, iso_ut_m, jol_ut_l, jol_ut_m):
            ki.write(tabla.ljust(_szektorra(len(tabla)) * SZEKTOR, b"\x00"))
        for joliet in (False, True):
            for konyvtar in konyvtarak:
                adat = _katalogus(konyvtar, joliet=joliet, ido=ido)
                ki.write(adat.ljust(_szektorra(len(adat)) * SZEKTOR, b"\x00"))
        for konyvtar in konyvtarak:
            for fajl in konyvtar.fajlok:
                irt = 0
                with fajl.forras.open("rb") as be:
                    while darab := be.read(1 << 20):
                        ki.write(darab)
                        irt += len(darab)
                toltes = max(1, _szektorra(irt)) * SZEKTOR - irt
                ki.write(b"\x00" * toltes)
    return cel


__all__ = ["JOLIET_NEV_MAX", "SZEKTOR", "iso_kiirasa", "iso_nev", "joliet_nev"]
