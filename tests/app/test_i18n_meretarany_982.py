"""#982: egyetlen magyar szó a képarányra — „méretarány".

Ugyanarra a fogalomra két szót használtunk: a kollázs formátum-menüje
„méretarány"-t, a vágópanel „képarány"-t. A dolgot NEM ízlés dönti el,
hanem a Picasa saját honosítási táblája (memória-szabály: a `.tre`
szövegforrás az igazságforrás):

| azonosító | angol | hivatalos magyar |
|---|---|---|
| `AspectRatioList:AddCustomAspectRatio` | Add Custom Aspect Ratio... | **Egyéni méretarány hozzáadása...** |
| `AspectRatioList:CustomAspectRatios` | Custom Aspect Ratios | **Egyéni méretarányok** |
| `AspectRatioList:CurrentRatio` | Current ratio | **Jelenlegi méretarány** |
| `collagepanel/delete_custom_aspect` | Delete the current aspect ratio | **A jelenlegi méretarány törlése** |

Az `AspectRatioList` UGYANAZ a lista, amit a vágóeszköz és a kollázs is
használ — tehát a „képarány" a mi saját szóalkotásunk volt, nem átvétel.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app

_TS_FORRAS = (
    Path(picasapy.app.__file__).parent / "i18n" / "picasapy_hu.ts"
).read_text(encoding="utf-8")


def test_a_forditasokban_nincs_keparany():
    """Egyetlen fordítás sem használhatja a keparany alakot."""
    talalatok = [
        sor.strip()
        for sor in _TS_FORRAS.split("\n")
        if "<translation" in sor and "éparány" in sor.casefold()
    ]
    assert talalatok == [], f'a keparany alak maradt a forditasokban: {talalatok}'


def test_a_hivatalos_alak_all_a_helyen():
    """A Picasa saját magyarja SZÓ SZERINT — az „Add Custom Aspect
    Ratio…" felirat mindkét kontextusban ugyanaz."""
    assert (
        "<translation>Egyéni méretarány hozzáadása…</translation>" in _TS_FORRAS
    )
    assert "<translation>Egyéni méretarány hozzáadása</translation>" in _TS_FORRAS
