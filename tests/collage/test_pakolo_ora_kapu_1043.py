"""#1043 — a pakoló órájának rögzítése KAPUT kap, ne csak reményt.

## Mit mértünk, és mi lett a verdikt

A #942 bájtazonossági őre terhelés alatt hamisan bukott: a rácsos témákon
(`picturegrid`, `framegrid`) a 407×311-es próbavászon 61,8–72,9%-án tért el
a két oldal. A jegy hipotézise egy néma dekódolási hiba volt; a 2026-09-08-i
mérés ezt **megdöntötte**, és a valódi okot is megnevezte:

| a pakoló órája | mérés (load ≈ 8) | eltérő eset | dekódolás → `None` |
|---|---|---|---|
| valódi `time.perf_counter` | 108 | **5** (92 304 és 78 266 képpont) | 0 / 1512 |
| lépkedő számláló | 288 | **0** | 0 / 4032 |

Terhelés NÉLKÜL a valódi óra is tiszta volt (72 mérés, 0 eltérés) — ez
magyarázza, miért nem jött elő alacsony terhelésű ismétléssel.

Az ok tehát a `packing.pack` **időkorlátos keresése**: a két oldal külön-külön
sorsol, és terhelt gépen más-más számú jelöltet néz meg. Ezt a
`tests/collage/conftest.py` `determinisztikus_pakolas` fixture-je szünteti meg.

## Miért kell hozzá ez a lap

A fixture egyetlen néven áll: a `packing._perf_counter` modulszintű
hivatkozáson. Ha ez a név elmozdul — átnevezés, saját `clock=` a hívónál,
alapértelmezett paraméterbe égetett óra —, a fixture **némán hatástalanná**
válik, és a terhelésfüggés visszatér, „megváltozott a rajz" álruhában. A
lenti őrök pontosan ezt a láncot állítják.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from picasapy.collage import packing
from picasapy.collage.fitting import MsvcRandom
from picasapy.collage.packing import pack

#: A #942 őrének próbaképei ugyanezekkel az oldalarányokkal állnak elő
#: (`_mintakepek`: 60+17i széles, 40+(23i mod 70) magas, hét kép).
OR_OLDALARANYAI = tuple(
    (60 + i * 17) / (40 + (i * 23) % 70) for i in range(7)
)

#: A próbavászon oldalaránya a #942 őrében (407×311).
OR_LAPARANYA = 407 / 311


class _LepkedoOra:
    """Fix lépésű óra: pontosan `lepesek` jelöltet enged a keresésnek."""

    def __init__(self, lepesek: int) -> None:
        self._lepes = packing.PACK_TIME_LIMIT / lepesek
        self._t = 0.0

    def __call__(self) -> float:
        self._t += self._lepes
        return self._t


def test_a_pakolo_a_MODULSZINTU_orat_olvassa_ha_nem_kap_sajatot():
    """A fixture patch-pontja helyes: `clock=` nélkül a modulszintű név fut.

    Ez az egyetlen kapocs a fixture és a pakoló között. Ha egy későbbi
    változás máshonnan venné az órát (alapértelmezett paraméter, `time`
    közvetlen hívása), ez az őr azonnal elhasal — a bájtazonossági őr pedig
    nem esik vissza némán a gép terheltségének mérésére."""
    hivasok = {"n": 0}
    ora = _LepkedoOra(50)

    def _szamlalo() -> float:
        hivasok["n"] += 1
        return ora()

    eredeti = packing._perf_counter
    packing._perf_counter = _szamlalo
    try:
        pack(list(OR_OLDALARANYAI), OR_LAPARANYA, MsvcRandom(12345))
    finally:
        packing._perf_counter = eredeti

    assert hivasok["n"] > 0, (
        "#1043: a `pack` nem a `packing._perf_counter`-t olvasta — a "
        "`tests/collage/conftest.py` fixture-je ezzel hatástalanná vált."
    )


def test_a_kereses_KERETE_megvaltoztatja_az_elrendezest():
    """A jelöltek SZÁMA megváltoztatja a talált elrendezést — ez a #1043 magva.

    Ha ez az őr valaha zöldre fordulna „mindegy, hány jelölt", akkor a
    terhelésfüggés is megszűnt volna, és az óra rögzítése feleslegessé válna.
    Amíg piros marad — azaz amíg a keret SZÁMÍT —, a rögzítés kötelező."""
    szuk = pack(
        list(OR_OLDALARANYAI),
        OR_LAPARANYA,
        MsvcRandom(12345),
        clock=_LepkedoOra(5),
    )
    bo = pack(
        list(OR_OLDALARANYAI),
        OR_LAPARANYA,
        MsvcRandom(12345),
        clock=_LepkedoOra(4000),
    )
    assert szuk != bo, (
        "#1043: a keresési keret már nem befolyásolja az elrendezést. Ha ez "
        "tartósan így van, a valós órához kötött keresés sem tenné "
        "terhelésfüggővé az őrt — a jegy tanulságát ilyenkor felül kell "
        "vizsgálni, nem elnémítani."
    )


def test_ugyanaz_a_keret_UGYANAZT_az_elrendezest_adja():
    """A rögzített keret mellett a pakolás megismételhető — ez a javítás."""
    elso = pack(
        list(OR_OLDALARANYAI), OR_LAPARANYA, MsvcRandom(12345), clock=_LepkedoOra(400)
    )
    masodik = pack(
        list(OR_OLDALARANYAI), OR_LAPARANYA, MsvcRandom(12345), clock=_LepkedoOra(400)
    )
    assert elso == masodik


def test_a_termekkod_nem_ad_sajat_orat_a_pakolonak():
    """Forrás-szintű őr: az `src/` egyetlen hívása sem kerüli meg a fixture-t.

    A `clock=` paraméter a TESZTEK befecskendezési pontja. Ha a termékkód
    kezdene élni vele, a `packing._perf_counter` cseréje nem érné el azt a
    hívást, és a bájtazonossági őr ott ismét a gépet mérné.

    ⚠️ A pásztázás **ismert pozitívval** ellenőrzi magát: a `picasa_render.py`
    biztosan a pakoló hívói közt van. Ha a névre nulla fájl jönne vissza, az
    nem „tiszta kód", hanem elromlott minta — ezért az is bukás."""
    gyoker = Path(__file__).resolve().parents[2] / "src" / "picasapy"
    hivok = {
        ut: ut.read_text(encoding="utf-8")
        for ut in sorted(gyoker.rglob("*.py"))
        if "packing import" in ut.read_text(encoding="utf-8")
        or "from .packing" in ut.read_text(encoding="utf-8")
    }
    nevek = {ut.name for ut in hivok}
    assert "picasa_render.py" in nevek, (
        "#1043: a pakoló hívóinak pásztázása ELROMLOTT — a "
        f"`picasa_render.py` kimaradt a találatokból ({sorted(nevek)}). "
        "Nulla vagy hiányos találat esetén ez az őr nem állít semmit."
    )
    vetkesek = sorted(
        ut.relative_to(gyoker).as_posix()
        for ut, szoveg in hivok.items()
        if re.search(r"\bclock\s*=", szoveg)
    )
    assert not vetkesek, (
        "#1043: a termékkód saját órát ad a pakolónak "
        f"({vetkesek}) — a teszt óra-rögzítése így nem ér el odáig."
    )


@pytest.mark.parametrize("lepesek", (5, 50, 400))
def test_a_lepkedo_ora_pontosan_annyi_jeloltet_enged(lepesek):
    """A lépkedő óra keretet SZAB, nem véletlenszerűen enged.

    A `pack` addig sorsol, amíg `tick() - start < time_limit`; fix lépésnél ez
    mindig ugyanannyi kör. A számláló ezt teszi ellenőrizhetővé."""
    hivasok = {"n": 0}
    ora = _LepkedoOra(lepesek)

    def _szamlalo() -> float:
        hivasok["n"] += 1
        return ora()

    pack(list(OR_OLDALARANYAI), OR_LAPARANYA, MsvcRandom(1), clock=_szamlalo)
    elso = hivasok["n"]

    hivasok["n"] = 0
    ora2 = _LepkedoOra(lepesek)

    def _szamlalo2() -> float:
        hivasok["n"] += 1
        return ora2()

    pack(list(OR_OLDALARANYAI), OR_LAPARANYA, MsvcRandom(1), clock=_szamlalo2)
    assert hivasok["n"] == elso
