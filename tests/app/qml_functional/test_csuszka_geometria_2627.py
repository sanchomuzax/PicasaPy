"""#2627 — a szerkesztő csúszkáinak BELSŐ geometriája a respackből.

## A mérés (`tools/picasa/respack.py`, a 13 bájtos rétegfejléc + képpontok)

| réteg | méret | amit ad |
|---|---|---|
| `editslider/sliderbase` | 191 × 27 | a SÁV a 8…16. sor ⇒ **9 képpont**; a 8. sor a felső szegély `RGB(154,162,174)`, a belseje kékesfehér (239…249) |
| `editslider/thumb` | 16 × 26 | a fogantyú **álló téglalap** (22 tömör sor + 3 lágy árnyék) |
| `scaleslider/sliderbase` | 121 × 9 | a sáv szintén **9 képpont** |
| `scaleslider/thumb` | 16 × 22 | álló fogantyú |

A CSALÁD nem átvitel, hanem a saját mérésük:

* a négy **finomhangoló** csúszka az eredetiben `editslider1…4`
  (`editpanel/clip(editslider,editsliderN)`) ⇒ fogantyú 16 × **26**;
* a **Gyakori javítások** Derítőfénye `flightslider1`
  (`editpanel/clip(scaleslider,flightslider1): backlight_container`)
  ⇒ fogantyú 16 × **22**.

A `PicasaSlider` a #700 óta tudja ezt a három paramétert; az
`EditorParamPanel` (effekt-alpanel) már használta is — a szerkesztő többi
csúszkája maradt a 4 képpontos sínen és a 14-es KEREK fogantyún.

⚠️ Amit ez a fájl NEM mér: a SZÍNT. A sáv nálunk semleges
(`Theme.chromeBg`), az eredetié kékes — az a #2627 másik fele, és az egész
alkalmazás csúszkáit érinti.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app as app_csomag
import pytest

from tests.support.qml_blokk import blokk_horgonyra

_QML = Path(app_csomag.__file__).parent / "qml" / "PicasaPy"

#: (fájl, elemnév, sáv, fogantyú szélesség × magasság, forrás-család)
MERT_CSUSZKAK = (
    ("EditorFinetunePanel.qml", "finetuneFillSlider", 9, 16, 26, "editslider"),
    ("EditorFinetunePanel.qml", "finetuneHighlightsSlider", 9, 16, 26, "editslider"),
    ("EditorFinetunePanel.qml", "finetuneShadowsSlider", 9, 16, 26, "editslider"),
    ("EditorFinetunePanel.qml", "finetuneTempSlider", 9, 16, 26, "editslider"),
    ("EditorTabCommonFixes.qml", "fixesFillSlider", 9, 16, 22, "scaleslider"),
)


def _blokk(fajl: str, elem: str) -> str:
    forras = (_QML / fajl).read_text(encoding="utf-8")
    return blokk_horgonyra(forras, f'objectName: "{elem}"')


class TestAMertGeometria:
    @pytest.mark.parametrize(
        ("fajl", "elem", "sav", "szeles", "magas", "csalad"),
        MERT_CSUSZKAK,
        ids=[c[1] for c in MERT_CSUSZKAK],
    )
    def test_a_csuszka_a_MERT_meretet_viszi(
        self, fajl, elem, sav, szeles, magas, csalad
    ):
        blokk = _blokk(fajl, elem)
        for nev, ertek in (
            ("grooveThickness", sav),
            ("handleWidth", szeles),
            ("handleHeight", magas),
        ):
            assert (
                f"{nev}: {ertek}" in blokk
                or f"{nev}: finetunePanel." in blokk
            ), (
                f"{elem}: a(z) `{nev}` nem a mért {ertek} (a `{csalad}` "
                "családból, `respack.yt`)"
            )

    def test_a_finomhangolo_KONSTANSAI_a_mert_ertekek(self):
        """A négy finomhangoló csúszka egy helyen tartja a számokat —
        ezt a helyet is meg kell mérni, különben a fenti próba egy rossz
        konstansra hivatkozna."""
        forras = (_QML / "EditorFinetunePanel.qml").read_text(encoding="utf-8")
        for sor in (
            "readonly property int savVastagsag: 9",
            "readonly property int fogantyuSzeles: 16",
            "readonly property int fogantyuMagas: 26",
        ):
            assert sor in forras, f"hiányzik vagy más az érték: {sor}"

    def test_a_fogantyu_NEM_kor(self):
        """Az eredeti fogantyúja álló téglalap (16 × 26, illetve 16 × 22).
        A `PicasaSlider` alapértéke KEREK (`handleRadius` = fél oldal) —
        a szerkesztő csúszkáin ezt felül kell írni."""
        for fajl, elem, _s, szeles, magas, _cs in MERT_CSUSZKAK:
            blokk = _blokk(fajl, elem)
            assert "handleRadius" in blokk, (
                f"{elem}: nincs `handleRadius` — a fogantyú KEREK maradna"
            )
            assert magas > szeles, "a mért fogantyú ÁLLÓ téglalap"
