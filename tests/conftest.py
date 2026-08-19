"""Gyökér-szintű őr: a teszt NEM nyúlhat a felhasználó VALÓDI mappáihoz (#1054).

## Miért létezik ez a fájl

A kollázs kimeneti mappája beállítás, a TARTALÉKA viszont a valódi
`~/Pictures/Picasa/Kollázsok`. Egy fixture, ami ezt elfelejti eltéríteni,
némán a fejlesztő saját képmappájába ír — és a hiba nem ott jelentkezik,
ahol keletkezett.

Pontosan ez történt: a `tests/app/qml_functional/conftest.py` `qml_app`
fixture-e (a szülő azonos nevű fixture-ének FELÜLÍRÁSA, ami a #960
elszigetelését nem hozta magával) egy `autosave.cxf`-et hagyott a valódi
mappában. A fájl hónapokig ott állt, és a #1051 jegy „élő bizonyítékként"
hivatkozott rá, mint a TULAJDONOS elveszett munkájára — miközben a
csomópontjai egy `pytest` ideiglenes könyvtárára mutattak.

Egy szennyezés, ami egy jegy leletét hamisította meg. Ezért nem elég az
egy fixture javítása: az őr azt állítja, amit a javítás ígér.

## Miért fixture és nem külön teszt

Külön teszt csak azt tudná megnézni, hogy ÉPPEN most mi van a mappában.
Ez a fixture MINDEN teszt köré odaáll, és megnevezi azt az egyet, amelyik
hozzányúlt — a szennyezést így ott fogjuk meg, ahol keletkezik.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

#: A valódi felhasználói mappák, amikbe egyetlen teszt sem írhat.
VEDETT_MAPPAK = (Path.home() / "Pictures" / "Picasa",)


def _pillanatkep(mappa: Path) -> dict[str, tuple[int, float]]:
    """A mappa fájljai mérettel és módosítási idővel, rekurzívan.

    Nem létező mappára üres — a CI-n és a legtöbb gépen ez a normális
    állapot, és pont az a lelet, ha a teszt után MÁR létezik."""
    if not mappa.exists():
        return {}
    allapot: dict[str, tuple[int, float]] = {}
    for gyoker, _mappak, fajlok in os.walk(mappa):
        for nev in fajlok:
            ut = Path(gyoker) / nev
            try:
                adat = ut.stat()
            except OSError:  # közben eltűnt — a különbség így is látszik
                continue
            allapot[str(ut)] = (adat.st_size, adat.st_mtime)
    return allapot


def valtozas_szovege(mappa: Path, regi: dict, uj: dict) -> str:
    """A szennyezés leírása, vagy üres szöveg, ha nincs eltérés.

    Külön függvény, hogy a FOGA is tesztelhető legyen: egy őr, amiről csak
    annyit tudunk, hogy „zöld", pont annyit ér, mint a hiba, amit el
    akartunk kerülni."""
    if uj == regi:
        return ""
    keletkezett = sorted(set(uj) - set(regi))
    modosult = sorted(k for k in set(uj) & set(regi) if uj[k] != regi[k])
    eltunt = sorted(set(regi) - set(uj))
    return (
        f"a teszt a felhasználó VALÓDI mappájába írt (#1054): {mappa}\n"
        f"  keletkezett: {keletkezett}\n"
        f"  módosult:    {modosult}\n"
        f"  eltűnt:      {eltunt}\n"
        "A fixture nem térítette el a `collage/outputDir` beállítást."
    )


@pytest.fixture(autouse=True)
def nem_szennyezi_a_felhasznaloi_mappat():
    """Elhasal, ha a teszt a valódi képmappában bármit létrehoz vagy módosít."""
    elotte = {m: _pillanatkep(m) for m in VEDETT_MAPPAK}

    yield

    for mappa, regi in elotte.items():
        uzenet = valtozas_szovege(mappa, regi, _pillanatkep(mappa))
        if uzenet:
            raise AssertionError(uzenet)
