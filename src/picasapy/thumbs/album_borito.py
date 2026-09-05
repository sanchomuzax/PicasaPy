"""A mappa-/album-borító fotó-kupacának elrendezése (#2049).

A Picasa a bal hasáb fastruktúrájában és a tálca „Kiválasztott mappa"
tokenjén nem sárga mappaikont mutat, hanem egy kis **fotó-kupacot**: egy
elülső kép, mögötte legfeljebb három további, kissé elforgatva és
kifordítva. Ez a modul a kupac **geometriáját** számolja ki — a rajzolás
külön lépés.

Minden szabály a `Picasa3.exe` diszasszemblátumából van kiolvasva; a
címek a `docs/specs/pmp-database.md` 7. szakaszában állnak
(összeállító: `0x00423780`, 2167 bájt).

## Miért determinisztikus a „véletlen"

A vetemítés véletlenszerűnek látszik, de az eredeti a szórást
`srand(mag)`-gal indítja, és a magot az album tárolóbeli rés-indexéből
képezi (`rés ^ 0x133475`, `0x00423a24`–`0x00423a2b`). Ugyanaz a mappa
tehát **mindig ugyanúgy** néz ki — ez nem apró részlet: ha futásonként
átrendeződne, a felhasználó nem ismerné fel a saját mappáit.

⚠️ **A mag nálunk MÁS forrásból jön.** Picasa-tárolóbeli rés-indexünk
nincs, ezért a mappa útvonalából képezünk stabil magot
(`mappa_magja`). A követelmény, amit teljesítünk, ugyanaz: azonos mappa
→ azonos elrendezés, futások között is.
"""

from __future__ import annotations

import hashlib
import math

import numpy as np
from dataclasses import dataclass
from typing import Iterator

#: A kupacba legfeljebb ennyi kép kerül (`0x004237ab`: `cmp eax, 4`).
LAPOK_MAXIMUMA = 4

#: A vetemítés magjának keverője (`0x00423a2b`: `xor eax, 0x133475`).
MAG_KEVERO = 0x133475

#: Az MSVCRT lineáris kongruens generátor együtthatói (`0x00c08229`).
_SZORZO = 0x343FD
_ELTOLAS = 0x269EC3

#: A forgatás félsávja radiánban (`α = 0.2·(r−1.5)`, r ∈ [1,2)).
_FORGATAS_EGYUTTHATO = 0.2


def msvcrt_rand(mag: int) -> Iterator[int]:
    """Az MSVCRT `rand()` sorozata a megadott maggal.

    `seed = seed·0x343FD + 0x269EC3`, a visszaadott érték
    `(seed >> 16) & 0x7FFF` (`0x00c08229`–`0x00c0823d`).
    """
    allapot = mag & 0xFFFFFFFF
    while True:
        allapot = (allapot * _SZORZO + _ELTOLAS) & 0xFFFFFFFF
        yield (allapot >> 16) & 0x7FFF


def _egy_es_ketto_kozott(nyers: int) -> float:
    """A `rand()` kimenetéből `[1, 2)` intervallumú szám.

    Az eredeti a klasszikus kitevő-trükköt használja (`add eax, 0x3f8000;
    shl eax, 8`), ami float32-ként olvasva pontosan `1 + nyers/32768`.
    """
    return 1.0 + nyers / 32768.0


@dataclass(frozen=True)
class Lap:
    """A kupac egy lapja. A `0.` index a LEGFELSŐ kép."""

    index: int
    szog: float
    tx: float
    ty: float


def mappa_magja(utvonal: str) -> int:
    """Stabil vetemítés-mag egy mappa útvonalából.

    A beépített `hash()` NEM használható: a `PYTHONHASHSEED` miatt
    futásonként más értéket ad, és a borító minden indításnál
    átrendeződne.
    """
    lenyomat = hashlib.md5(
        utvonal.encode("utf-8", "surrogateescape"), usedforsecurity=False
    ).digest()
    return int.from_bytes(lenyomat[:4], "little")


def kupac_elrendezes(darab: int, mag: int) -> tuple[Lap, ...]:
    """A kupac lapjainak geometriája, a LEGFELSŐ laptól kezdve.

    Args:
        darab: hány kép áll rendelkezésre (a lista eleje számít).
        mag: a vetemítés magja (ld. `mappa_magja`).

    Returns:
        Legfeljebb `LAPOK_MAXIMUMA` lap, index szerint növekvő
        sorrendben (`0` = legfelül).

    Raises:
        ValueError: negatív darabszámra.
    """
    if darab < 0:
        raise ValueError(f"a képek száma nem lehet negatív: {darab}")
    lapszam = min(darab, LAPOK_MAXIMUMA)
    if lapszam == 0:
        return ()

    veletlen = msvcrt_rand(mag ^ MAG_KEVERO)
    # A rajzoló ciklus VISSZAFELÉ megy (`0x00423f45`): előbb a kupac alja
    # készül el, utoljára a teteje. A `rand()`-hívások sorrendje emiatt a
    # legalsó laptól indul — bitre pontos újraalkotásnál ez számít.
    lapok: dict[int, Lap] = {}
    for i in range(lapszam - 1, -1, -1):
        # ⚠️ A LEGALSÓ lapra a forgatás-ág át van ugorva (`0x00423ba6`:
        # `cmp [esp+0x70], ecx; jge`), tehát rá EGGYEL KEVESEBB `rand()`
        # jut. Ez az egész további sorozatot eltolja.
        if i == lapszam - 1:
            szog = 0.0
        else:
            szog = _FORGATAS_EGYUTTHATO * (_egy_es_ketto_kozott(next(veletlen)) - 1.5)

        # tₓ = 4·i·uₓ, ahol uₓ = 2(r₂−1) − 1 ∈ [−1, 1)
        ux = 2.0 * (_egy_es_ketto_kozott(next(veletlen)) - 1.0) - 1.0
        tx = 4.0 * i * ux

        # t_y = −i·(4·r₃ + 1), r₃ ∈ [1,2)  ⇒  t_y ∈ (−9i, −5i]
        ty = -i * (4.0 * _egy_es_ketto_kozott(next(veletlen)) + 1.0)

        lapok[i] = Lap(index=i, szog=szog, tx=tx, ty=ty)

    return tuple(lapok[i] for i in range(lapszam))


def befoglalo_meret(
    lapok: tuple[Lap, ...], szelesseg: int, magassag: int
) -> tuple[int, int]:
    """A kupac befoglaló téglalapja azonos méretű lapokra.

    Az eredeti kétszer járja végig a lapokat: a 0. menet MÉRI a
    befoglalót, az 1. rajzol rá (`0x00423f70`–`0x00423f75`). A borító
    mérete ezért nem rögzített — élő adaton a leghosszabb oldal 72…119
    képpont.
    """
    if not lapok:
        return (0, 0)
    minx = miny = math.inf
    maxx = maxy = -math.inf
    fel_sz, fel_ma = szelesseg / 2.0, magassag / 2.0
    for lap in lapok:
        koszinusz, szinusz = math.cos(lap.szog), math.sin(lap.szog)
        for jelx, jely in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            x = jelx * fel_sz
            y = jely * fel_ma
            fx = x * koszinusz - y * szinusz + lap.tx
            fy = x * szinusz + y * koszinusz + lap.ty
            minx, maxx = min(minx, fx), max(maxx, fx)
            miny, maxy = min(miny, fy), max(maxy, fy)
    return (math.ceil(maxx - minx), math.ceil(maxy - miny))


#: Az árnyék átlátszatlansága: `0.6f × 255.0` egészre kerekítve
#: (`0x00a6e2f5`–`0x00a6e32e`). Kódból van, nem mérésből — a látható
#: árnyék mindig csak a lefutó perem, a belseje a fotó alatt van.
ARNYEK_ALFA = 153

#: Az árnyék sugara képpontban (`0xcf3a58` = `5.0f`, `0x00a6e33b`).
#: Élő adaton megerősítve: az alfa-lefutás egy-egy fotó szélénél kb. 5
#: képpont széles (37 valódi borító a `Picasa2-arcok` adatbázisból).
ARNYEK_SUGAR = 5.0


def keszits_boritot(kepek, mag: int):
    """A fotó-kupac megrajzolása RGBA képpé.

    Args:
        kepek: BGR vagy BGRA bélyegképek; csak az első `LAPOK_MAXIMUMA`
            számít, az elsőből lesz a kupac teteje.
        mag: a vetemítés magja (ld. `mappa_magja`).

    Returns:
        `uint8` RGBA tömb (magasság, szélesség, 4) — a kupac befoglaló
        téglalapja, körülötte átlátszó.

    Raises:
        ValueError: üres képlistára.
    """
    import cv2

    kepek = list(kepek)[:LAPOK_MAXIMUMA]
    if not kepek:
        raise ValueError("a borítóhoz legalább egy kép kell")

    lapok = kupac_elrendezes(len(kepek), mag)
    # A lapok mérete eltérhet; a befoglalót a LEGNAGYOBBRA számoljuk, így
    # egyik lap sem lóghat le a vászonról.
    max_sz = max(k.shape[1] for k in kepek)
    max_ma = max(k.shape[0] for k in kepek)
    vaszon_sz, vaszon_ma = befoglalo_meret(lapok, max_sz, max_ma)
    # Az árnyék a lapokon TÚL is terjed, ezért kap saját peremet.
    perem = int(math.ceil(ARNYEK_SUGAR * 2))
    vaszon_sz += 2 * perem
    vaszon_ma += 2 * perem

    vaszon = np.zeros((vaszon_ma, vaszon_sz, 4), dtype=np.uint8)
    kozep_x, kozep_y = vaszon_sz / 2.0, vaszon_ma / 2.0

    # Hátulról előre: a legalsó lap (`N−1`) rajzolódik először, a `0.`
    # utoljára — így az kerül legfelülre (`0x00423f45`).
    for lap in reversed(lapok):
        kep = kepek[lap.index]
        if kep.shape[2] == 4:
            kep = cv2.cvtColor(kep, cv2.COLOR_BGRA2BGR)
        sz, ma = kep.shape[1], kep.shape[0]

        koszinusz, szinusz = math.cos(lap.szog), math.sin(lap.szog)
        matrix = np.array(
            [
                [koszinusz, -szinusz, kozep_x + lap.tx - (koszinusz * sz / 2 - szinusz * ma / 2)],
                [szinusz, koszinusz, kozep_y + lap.ty - (szinusz * sz / 2 + koszinusz * ma / 2)],
            ],
            dtype=np.float64,
        )

        forgatott = cv2.warpAffine(
            kep, matrix, (vaszon_sz, vaszon_ma), flags=cv2.INTER_LINEAR
        )
        maszk = cv2.warpAffine(
            np.full((ma, sz), 255, dtype=np.uint8),
            matrix,
            (vaszon_sz, vaszon_ma),
            flags=cv2.INTER_LINEAR,
        )

        _rajzolj_arnyekot(vaszon, maszk)

        # A lap maga: ahol a maszk takar, ott a lap színe és alfája.
        arany = (maszk.astype(np.float32) / 255.0)[..., None]
        vaszon[..., :3] = (
            forgatott.astype(np.float32) * arany
            + vaszon[..., :3].astype(np.float32) * (1.0 - arany)
        ).astype(np.uint8)
        vaszon[..., 3] = np.maximum(vaszon[..., 3], maszk)

    return _vagd_korbe(vaszon)


def _rajzolj_arnyekot(vaszon, maszk) -> None:
    """Lágy árnyék a lap alá: elmosott sziluett, `ARNYEK_ALFA` csúccsal."""
    import cv2

    meret = int(ARNYEK_SUGAR) * 2 + 1
    elmosott = cv2.GaussianBlur(maszk, (meret, meret), ARNYEK_SUGAR)
    arnyek = (elmosott.astype(np.float32) * (ARNYEK_ALFA / 255.0)).astype(np.uint8)
    # Az árnyék csak sötétít és alfát ad; a színt nem húzza el ott, ahol
    # már takar egy korábbi lap.
    vaszon[..., 3] = np.maximum(vaszon[..., 3], arnyek)


def _vagd_korbe(vaszon):
    """A teljesen átlátszó peremek levágása — a borító a kupac doboza."""
    latszik = vaszon[..., 3] > 0
    if not latszik.any():
        return vaszon
    sorok = np.flatnonzero(latszik.any(axis=1))
    oszlopok = np.flatnonzero(latszik.any(axis=0))
    return vaszon[sorok[0] : sorok[-1] + 1, oszlopok[0] : oszlopok[-1] + 1]
