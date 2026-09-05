"""#1977 (7. pont): a mozgófilm mind a HÉT eredeti felbontást kínálja.

## A mérés

A `docs/specs/picasa-create-features.md` 2.6/c hét méretet ad:

    320×240 · 640×480 · 800×600 · 1024×768 · 1600×1200 · 1280×720 · 1920×1080

Nálunk kettő volt (`720p`, `1080p`), és a szélesség **16:9-ből
számolódott**. Ez a **négy 4:3-as méretre hibás**: 1024-es magasságból
1820 jönne ki 768 helyett — a kép torzulna.

Ezért a szélesség KÜLÖN paraméter. A régi, négyargumentumos hívási alak
(`width` nélkül) megmarad: ott továbbra is 16:9-ből számolunk, tehát a
meglévő 720p/1080p hívások és tesztek változatlanok.
"""

from __future__ import annotations

import pytest

#: A spec 2.6/c hét mérete, (szélesség, magasság).
MERETEK = [
    (320, 240), (640, 480), (800, 600), (1024, 768),
    (1600, 1200), (1280, 720), (1920, 1080),
]


@pytest.mark.parametrize("szeles,magas", MERETEK)
def test_a_kapott_szelesseg_megy_at(szeles, magas) -> None:
    from picasapy.app.create_controller import CreateMixin

    beallitas = CreateMixin._film_beallitas(szeles, magas, 1.0)
    assert (beallitas.width, beallitas.height) == (szeles, magas)


def test_a_regi_negyargumentumos_alak_tovabbra_is_16_9() -> None:
    """`width=0` (a régi hívási alak) ⇒ a magasságból, 16:9-cel."""
    from picasapy.app.create_controller import CreateMixin

    beallitas = CreateMixin._film_beallitas(0, 720, 1.0)
    assert (beallitas.width, beallitas.height) == (1280, 720)


def test_a_negy_haromnegyedes_meretet_a_regi_keplet_elrontana() -> None:
    """A foga: van olyan méret, amit a 16:9-es származtatás elrontana."""
    rossz = [
        (sz, m) for sz, m in MERETEK if sz != (m * 16 // 9) // 2 * 2
    ]
    assert rossz, "a hét méret mindegyike 16:9 — az őr nem állítana semmit"
    assert len(rossz) == 5, rossz
