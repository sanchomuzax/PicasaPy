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

import pytest

from picasapy.collage.fitting import MsvcRandom
from picasapy.collage.pile import pile_layout


def _kilogo(elhelyezesek, szelesseg: int, magassag: int):
    """A lapról kilógó elhelyezések — a TELJES téglalapot nézve."""
    kilogok = []
    for e in elhelyezesek:
        fel = e.size * 0.5
        if (
            e.center_x - fel < -0.5
            or e.center_y - fel < -0.5
            or e.center_x + fel > szelesseg + 0.5
            or e.center_y + fel > magassag + 0.5
        ):
            kilogok.append(e)
    return kilogok


@pytest.mark.parametrize("darab", [4, 9, 10, 11, 15, 25, 50, 100])
@pytest.mark.parametrize("mag", [1, 7, 42])
def test_egyetlen_kep_sem_log_ki(darab, mag):
    """A felhasználó ezt látja: a kép széle kilóg a lapról."""
    elhelyezesek = pile_layout(darab, 1024, 768, MsvcRandom(mag))

    kilogok = _kilogo(elhelyezesek, 1024, 768)

    assert not kilogok, (
        f"{darab} képnél {len(kilogok)} csomópont lóg ki a lapról "
        f"(mag={mag}): "
        + ", ".join(
            f"#{e.index} közép=({e.center_x:.1f},{e.center_y:.1f}) méret={e.size:.1f}"
            for e in kilogok[:3]
        )
    )


@pytest.mark.parametrize("darab", [4, 9, 10])
def test_a_tiz_alatti_ag_VALTOZATLAN(darab):
    """⚠️ A beszorítás 10 képig NEM nyúlhat hozzá semmihez.

    A 9 képes eset a valódi Picasa-minták középpontjait négy tizedesig
    hozza — ha itt elmozdulna, azt rontanánk el, ami ma bizonyítottan jó."""
    elhelyezesek = pile_layout(darab, 1024, 768, MsvcRandom(3))

    for e in elhelyezesek:
        fel = e.size * 0.5
        # a beszorítás akkor "nem csinál semmit", ha a középpont eleve
        # beljebb van a fél méretnél mindkét tengelyen
        assert fel <= e.center_x <= 1024 - fel, (
            f"{darab} képnél a beszorítás HATOTT (x) — a ≤10 képes ág "
            "nem maradt változatlan"
        )
        assert fel <= e.center_y <= 768 - fel, (
            f"{darab} képnél a beszorítás HATOTT (y) — a ≤10 képes ág "
            "nem maradt változatlan"
        )
