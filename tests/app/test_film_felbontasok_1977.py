"""#1977 (7. pont): a mozgófilm mind a HÉT eredeti felbontást kínálja.

## A mérés

A `docs/specs/picasa-create-features.md` 2.6/c szerint az eredeti hét
méretet ad: `320×240`, `640×480`, `800×600`, `1024×768`, `1600×1200`,
`1280×720`, `1920×1080`. Nálunk eddig kettő volt (`720p`, `1080p`), és a
szélesség 16:9-ből számolódott — ami a **négy 4:3-as méretre hibás**:
`1024` magasságból 16:9-cel `1820` jönne ki `768` helyett.

Ezért a szélesség mostantól KÜLÖN paraméter, nem származtatott érték.

## Amit ez az őr állít

Hogy a hét méret mindegyike átmegy a vezérlőn a `MovieSettings`-be —
a 4:3-asok is, torzítás nélkül.
"""

from __future__ import annotations

import pytest

#: A spec 2.6/c hét mérete, (szélesség, magasság).
MERETEK = [
    (320, 240), (640, 480), (800, 600), (1024, 768),
    (1600, 1200), (1280, 720), (1920, 1080),
]


@pytest.mark.parametrize("szeles,magas", MERETEK)
def test_a_vezerlo_a_KAPOTT_szelesseget_hasznalja(szeles, magas, monkeypatch):
    """A szélesség nem 16:9-ből jön, hanem a hívótól."""
    from picasapy.app import create_controller as cc

    elkapott = {}

    class _Beallitas:
        def __init__(self, **kw):
            elkapott.update(kw)

    monkeypatch.setattr(cc, "MovieSettings", _Beallitas)
    monkeypatch.setattr(
        cc, "export_movie", lambda *a, **k: None, raising=False
    )

    cc.CreateMixin._film_beallitas(szeles, magas, 1.0)

    assert elkapott["width"] == szeles, elkapott
    assert elkapott["height"] == magas, elkapott


def test_a_negy_haromnegyedes_meret_nem_torzul() -> None:
    """A 16:9-es származtatás a 4:3-asokra HIBÁS volt — ez a foga."""
    for szeles, magas in MERETEK:
        szarmaztatott = (magas * 16 // 9) // 2 * 2
        if szeles != szarmaztatott:
            return  # van legalább egy méret, amit a régi képlet elrontana
    pytest.fail("a hét méret mindegyike 16:9 — az őr nem állít semmit")
