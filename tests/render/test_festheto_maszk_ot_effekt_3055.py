"""#3055: a festhető maszkos effektek halmaza — ÖT, nem kettő.

## A mérés

`docs/specs/filterdesc-registry.md` → „⛳ A festhető maszk: ÖT effekt, KÉT
család" (#1908, 296. kör). A `filterdesc.xml`-ben **öt** szűrő kap
`Mask="{_mctr.mask}"`-ot, és a `_mctr`-t **két különböző** befoglaló elem
adja:

| szűrő | a kanavász |
|---|---|
| `Boost`, `Pixelate`, `Soften`, `PicnikTint` | `cnt:PaintEffectCanvas` |
| `ReanimatedEyeColor` | `eff:PaintOnEffectBase` |

⛔ **Ezért csúszott el a kódunk:** a `PAINTABLE_MASK_OPS` egy-egy tagot
tartalmazott mindkét családból, a maradék három kimaradt — aki csak a
`PaintEffectCanvas`-ra keres, épp a `ReanimatedEyeColor`-t hagyja ki, aki
pedig a talált kettőt általánosítja, a többi hármat.

## Amit ez a lap mér

A halmaz NE kézi lista legyen: az őr a **spec táblájából** olvassa ki az öt
nevet, és ahhoz hasonlítja a kódot. Így ha a mérés bővül, az őr azonnal
megmondja, hol kell a kódot követni.

⚠️ **Miért a specből, és nem a `filterdesc.xml`-ből?** A `filterdesc.xml` a
`research/` alatti kutatási másolat, ami NEM része a repónak — a CI-n nem
létezik. A spec táblája ugyanennek a mérésnek a rögzített alakja, és a
repóval együtt utazik. (Ha a fájl mégis elérhető, a lap azt is ellenőrzi.)

⚠️ Amit NEM mér: hogy a render maszkkal futna. A #381/#685 szerint a hatás
a teljes képre fut, és a hiány a JELZÉSBEN van — ezt a `chain.py`
figyelmeztetése adja.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from picasapy.render.chain_glimmer_handlers import PAINTABLE_MASK_OPS

_SPEC = (
    Path(__file__).resolve().parents[2]
    / "docs" / "specs" / "filterdesc-registry.md"
)

#: a szakasz címe, amiben a mért tábla áll
_SZAKASZ = "## ⛳ A festhető maszk: ÖT effekt, KÉT család"


def _spec_nevek() -> set[str]:
    """Az öt szűrőnév a spec táblájából, kisbetűsen.

    A tábla sorai `| <sorszám> | **`Név`** | ... |` alakúak. A sorszám-oszlop
    adja a horgonyt: enélkül a szakasz többi, névre hivatkozó mondata is
    beszűrődne."""
    szoveg = _SPEC.read_text(encoding="utf-8")
    kezd = szoveg.index(_SZAKASZ)
    #: a következő `## ` szakaszcímig
    vege = szoveg.index("\n## ", kezd + len(_SZAKASZ))
    blokk = szoveg[kezd:vege]
    return {
        m.group(1).lower()
        for m in re.finditer(r"^\|\s*\d+\s*\|\s*\*\*`([A-Za-z]+)`\*\*", blokk,
                             re.MULTILINE)
    }


class TestASpecTablaOlvashato:
    """Előbb a mérőt mérjük: ha a kinyerés csúszik, minden alábbi állítás
    hamis biztonságot adna."""

    def test_ot_nevet_talal(self) -> None:
        nevek = _spec_nevek()
        assert len(nevek) == 5, f"a spec táblájából {len(nevek)} név jött: {nevek}"

    def test_a_ket_csalad_mindegyike_bent_van(self) -> None:
        """Kontroll a kiváltó hibára: a `ReanimatedEyeColor` MÁS bázison ül,
        és épp ezért maradt ki a másik három."""
        nevek = _spec_nevek()
        assert "reanimatedeyecolor" in nevek
        assert {"boost", "pixelate", "soften", "picniktint"} <= nevek


class TestAHalmazEgyezikAMeressel:
    def test_mind_az_ot_benne_van(self) -> None:
        hianyzik = _spec_nevek() - set(PAINTABLE_MASK_OPS)
        assert not hianyzik, (
            f"a PAINTABLE_MASK_OPS-ból hiányzik: {sorted(hianyzik)} — ezek az "
            "effektek nem kapnak festhető-maszk figyelmeztetést (#3055)"
        )

    def test_nincs_benne_tobb(self) -> None:
        """A másik irány is állítás: kézzel felvett, mérés nélküli tag se
        legyen benne."""
        felesleg = set(PAINTABLE_MASK_OPS) - _spec_nevek()
        assert not felesleg, (
            f"a PAINTABLE_MASK_OPS-ban mérés nélküli tag van: {sorted(felesleg)}"
        )


class TestAFigyelmeztetesMindOtnekJar:
    @pytest.mark.parametrize(
        "kulcs", ["boost", "pixelate", "soften", "picniktint", "reanimatedeyecolor"]
    )
    def test_a_lanc_figyelmeztet(self, kulcs: str) -> None:
        """A VISELKEDÉS: a lánc tegye a `range_warnings`-ba a jelzést."""
        import numpy as np

        from picasapy.ini.filter_registry import canonicalize_filter_name
        from picasapy.ini.filters import parse_filters
        from picasapy.render.chain import apply_filters

        minta = {
            "boost": "Boost=1,50.000000;",
            "pixelate": "Pixelate=1,10.000000;",
            "soften": "Soften=1,50.000000;",
            "picniktint": "PicnikTint=1,50.000000,00ff0000;",
            "reanimatedeyecolor": "ReanimatedEyeColor=1,6.000000,20.000000;",
        }[kulcs]
        kanonikus = canonicalize_filter_name(kulcs)
        ops = parse_filters(minta)
        assert ops, f"a minta nem parszolható: {minta}"

        kep = np.full((8, 8, 3), 128, dtype=np.uint8)
        jelentes = apply_filters(kep, ops)

        assert any(kanonikus in w for w in jelentes.range_warnings), (
            f"a(z) {kanonikus} nem kapott festhető-maszk figyelmeztetést; "
            f"a kapott jelzések: {jelentes.range_warnings}"
        )


class TestAFilterdescIsEgyezikHaMegvan:
    """Ha a kutatási másolat elérhető, a spec tábláját ELLENŐRIZZÜK is.

    ⚠️ A `research/` nincs a repóban, ezért a CI-n ez a próba kimarad — a
    `skip` itt SZÁNDÉKOS és kimondott: a kötelező állítást a `_spec_nevek()`
    adja, ez csak a spec és a forrás egyezését hitelesíti a fejlesztői
    gépen."""

    def test_a_filterdesc_ugyanezt_az_otot_adja(self) -> None:
        xml = (
            Path(__file__).resolve().parents[2]
            / "research" / "copy_Picasa_3_7" / "Picasa3" / "runtime"
            / "filterdesc.xml"
        )
        if not xml.is_file():
            pytest.skip("a kutatási másolat nincs meg (a CI-n ez a normális)")
        szoveg = xml.read_text(encoding="utf-8", errors="replace")
        nevek = set()
        aktualis = None
        for sor in szoveg.splitlines():
            talalat = re.search(r'<filter id="([A-Za-z]+)"', sor)
            if talalat:
                aktualis = talalat.group(1).lower()
            if 'Mask="{_mctr.mask}"' in sor and aktualis:
                nevek.add(aktualis)
        assert nevek == _spec_nevek(), (
            f"a spec táblája és a filterdesc.xml eltér: csak a specben "
            f"{sorted(_spec_nevek() - nevek)}, csak az XML-ben "
            f"{sorted(nevek - _spec_nevek())}"
        )
