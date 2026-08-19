"""#1045 — a kupac egyetlen képe se lógjon ki a lapról.

## A lelet

A `scatter_centers` a KÖZÉPPONTOKAT tartja a sávon belül, a képnek viszont
MÉRETE van a középpont körül. A sávot `pile_scale(count)` szűkíti — ez a
**legkisebb** kép szorzója —, a margót viszont a **legnagyobb** kép igényli,
és annak a szorzója mindig 1,0.

Ezért a hiba **darabszámfüggő**: a legnagyobb kép bal széle 9 képnél
+0,0100, 10-nél +0,0033, **11-nél −0,0024**, 25-nél −0,0412.

⚠️ Egyetlen korábbi teszt sem fogta meg, mert a golden minták és a saját
eseteink is **mind 9 képesek** voltak. A felhasználó többel dolgozik, és ő
látta meg.

## Amit ez a fájl őriz

1. **4–100 képig** egyetlen csomópont teljes téglalapja se essen a lapon
   kívülre, több véletlen maggal.
2. **A ≤10 képes ág VÁLTOZATLAN** — ott a sáv már elfér, tehát a
   beszorítás nem csinál semmit. Ez azért fontos, mert a 9 képes eset a
   valódi minták középpontjait négy tizedesig hozza: ha ott elmozdulna,
   elrontanánk azt, ami ma bizonyítottan jó.
"""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from picasapy.collage.picasa_render import (
    _lapra_szorit,
    PicasaCollageSettings,
    layout_nodes_for_aspects,
)
from picasapy.collage.nodes import SHEET_UNITS
from picasapy.collage.themes import PICTUREPILE


#: A `layout_nodes_for_aspects` KÉPPONTBAN adja vissza a csomópontokat (a
#: `settings.width`/`height` rendszerében). A kirajzolt csempe a KERETES
#: méret (`outer_box`), ezért a kilógást ezen a szinten kell nézni — nem a
#: `pile_layout` fotó-négyzetén, ahol a keret még nem ismert.
_TURES = 0.5


def _csomopontok(darab: int, keret: str, szelesseg: int = 1600, magassag: int = 1200):
    """A ténylegesen kirajzolt csomópontok — ez a felhasználó látja."""
    beallitas = PicasaCollageSettings(
        theme=PICTUREPILE, width=szelesseg, height=magassag, border=keret
    )
    # vegyes tájolású képek, ahogy egy valódi gyűjteményben
    aranyok = [(0.7 if i % 3 == 0 else 1.45) for i in range(darab)]
    utak = [Path(f"/nincs/k{i}.jpg") for i in range(darab)]
    return layout_nodes_for_aspects(aranyok, utak, beallitas), beallitas


def _befoglalo(cs) -> tuple[float, float]:
    """Az ELFORGATOTT csempe tengelypárhuzamos befoglalója.

    ⚠️ A kupac csempéi döntve állnak (`theta`). Aki a csempe saját
    szélességét/magasságát nézi, egy 8°-kal döntött polaroidról azt hiszi,
    hogy elfér — közben a sarka túllóg a lapon, és a felhasználó pontosan
    azt a csonka képet látja, ami miatt ez a jegy megszületett."""
    koszinusz = abs(math.cos(cs.theta))
    szinusz = abs(math.sin(cs.theta))
    return (
        cs.width * koszinusz + cs.height * szinusz,
        cs.width * szinusz + cs.height * koszinusz,
    )


def _lap_hatarai(beallitas) -> tuple[float, float]:
    """A lap mérete LAPEGYSÉGBEN — a csomópontok ebben élnek, nem képpontban.

    ⚠️ Ez a teszt egyszer már rosszul állt: a képpontos `beallitas.width`
    (1600) és `height` (1200) volt a határ, miközben a csomópontok
    lapegységben jönnek, ahol a lap **1024 × 768**. A túl bő határ mellett a
    „semmi nem lóg ki" állítás jóval kevesebbet jelentett, mint amennyinek
    látszott — a durva kilógást megfogta, a néhány egységnyit nem.

    A lapegység a SZÉLESSÉGRE van normálva (`pixels_to_sheet` mindkét
    tengelyen a szélességgel oszt), ezért a magasság az oldalarányból jön."""
    return SHEET_UNITS, SHEET_UNITS * beallitas.height / beallitas.width


def _kilogo(csomopontok, beallitas):
    """A lapról kilógó csomópontok — a TELJES, keretes, ELFORGATOTT téglalap."""
    lap_szeles, lap_magas = _lap_hatarai(beallitas)
    kilogok = []
    for cs in csomopontok:
        szeles, magas = _befoglalo(cs)
        if (
            cs.center_x - szeles * 0.5 < -_TURES
            or cs.center_y - magas * 0.5 < -_TURES
            or cs.center_x + szeles * 0.5 > lap_szeles + _TURES
            or cs.center_y + magas * 0.5 > lap_magas + _TURES
        ):
            kilogok.append(cs)
    return kilogok


@pytest.mark.parametrize("darab", [4, 9, 10, 11, 15, 25, 50, 100])
@pytest.mark.parametrize("keret", ["noborder", "whiteborder", "polaroid"])
def test_egyetlen_kep_sem_log_ki(darab, keret):
    """A felhasználó ezt látja: a kép széle kilóg a lapról.

    ⚠️ Mind a három kerettel: a kilógást a KERETES méret dönti el. Az első
    javítás a fotó négyzetére szorított be, és egy 15 képes próbarenderen
    így is KÉT csempe lógott ki — a keret azon kívül nő."""
    csomopontok, beallitas = _csomopontok(darab, keret)

    kilogok = _kilogo(csomopontok, beallitas)

    assert not kilogok, (
        f"{darab} képnél, {keret} kerettel {len(kilogok)} csempe lóg ki: "
        + ", ".join(
            f"közép=({cs.center_x:.3f},{cs.center_y:.3f}) "
            f"méret=({cs.width:.3f}×{cs.height:.3f})"
            for cs in kilogok[:3]
        )
    )


@pytest.mark.parametrize("darab", [4, 9, 10])
def test_a_tiz_alatti_ag_VALTOZATLAN(darab):
    """⚠️ A beszorítás 10 képig NEM nyúlhat hozzá semmihez.

    A 9 képes eset a valódi Picasa-minták középpontjait négy tizedesig
    hozza — ha itt elmozdulna, azt rontanánk el, ami ma bizonyítottan jó.
    Ezt úgy állítjuk, hogy a csempék eleve beljebb vannak a fél méretüknél:
    ilyenkor a beszorításnak nincs mit tennie."""
    csomopontok, beallitas = _csomopontok(darab, "whiteborder")

    for cs in csomopontok:
        assert cs.width * 0.5 <= cs.center_x <= beallitas.width - cs.width * 0.5, (
            f"{darab} képnél a beszorítás HATOTT (x) — a ≤10 képes ág nem "
            "maradt változatlan"
        )
        assert (
            cs.height * 0.5 <= cs.center_y <= beallitas.height - cs.height * 0.5
        ), (
            f"{darab} képnél a beszorítás HATOTT (y) — a ≤10 képes ág nem "
            "maradt változatlan"
        )


# --------------------------------------------------------------------------
# A beszorító függvény maga
# --------------------------------------------------------------------------
def test_a_lapon_belul_maradot_nem_mozgatja():
    assert _lapra_szorit(500.0, 200.0, 1000) == 500.0


@pytest.mark.parametrize(
    ("kozep", "vart"), [(10.0, 100.0), (990.0, 900.0), (-50.0, 100.0)]
)
def test_a_szelen_tullogot_befele_huzza(kozep, vart):
    assert _lapra_szorit(kozep, 200.0, 1000) == pytest.approx(vart)


def test_a_lapnal_szelesebb_csempe_a_lap_kozepere_kerul():
    """⚠️ Nincs olyan középpont, amivel elférne — de a naiv `min(max(...))`
    ilyenkor a NEGATÍV oldalra vinné (a felső korlát az alsó alá csúszik),
    vagyis pont azt a kilógást okozná, amit meg akarunk előzni."""
    assert _lapra_szorit(300.0, 1500.0, 1000) == 500.0
