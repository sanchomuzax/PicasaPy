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


def _komponens_neve(fajl: str, elem: str) -> str:
    """Melyik QML-komponens példánya hordozza ezt az elemnevet.

    A blokk-nyitó sor (`… {`) a KERESETT sor fölött, a legközelebbi olyan
    sor, ami `{`-re végződik — a QML-ben ez a példányosított típus neve.
    """
    sorok = (_QML / fajl).read_text(encoding="utf-8").splitlines()
    for i, sor in enumerate(sorok):
        if f'objectName: "{elem}"' in sor:
            for elozo in reversed(sorok[:i]):
                csupasz = elozo.strip()
                if csupasz.endswith("{"):
                    return csupasz[:-1].strip().split()[-1]
            raise AssertionError(f"{elem}: nincs blokk-nyitó sor fölötte")
    raise AssertionError(f"{elem} nincs a(z) {fajl}-ban")


def _blokk(fajl: str, elem: str) -> str:
    forras = (_QML / fajl).read_text(encoding="utf-8")
    return blokk_horgonyra(forras, f'objectName: "{elem}"')


#: #710: a mért számok EGY helyen élnek — a közös komponensben.
_KOZOS = "EditorSlider.qml"


class TestAMertGeometria:
    """A mérés-lánc két lépésben áll (#710 óta): az elem megnevezi a
    CSALÁDJÁT, a közös komponens pedig a családhoz tartozó SZÁMOKAT. Mindkét
    lépést külön próba állítja — így a refaktor nem tudja elnémítani egyiket
    sem, és a számok nem csúszhatnak el három panel között."""

    @pytest.mark.parametrize(
        ("fajl", "elem", "sav", "szeles", "magas", "csalad"),
        MERT_CSUSZKAK,
        ids=[c[1] for c in MERT_CSUSZKAK],
    )
    def test_a_csuszka_a_MERT_csaladot_nevezi_meg(
        self, fajl, elem, sav, szeles, magas, csalad
    ):
        blokk = _blokk(fajl, elem)
        assert _komponens_neve(fajl, elem) == "EditorSlider", (
            f"{elem}: nem a közös `EditorSlider`-t használja (#710)"
        )
        if csalad == "scaleslider":
            assert 'csalad: "scaleslider"' in blokk, (
                f"{elem}: a `scaleslider` családot KI KELL mondani — "
                "az alapértelmezés az `editslider` (fogantyú 16 × 26)"
            )
        else:
            assert "csalad:" not in blokk, (
                f"{elem}: az `editslider` az alapértelmezés, ne írjuk ki"
            )

    def test_a_KOZOS_komponens_a_mert_ertekeket_tartja(self):
        """A számok helyét is meg kell mérni, különben a fenti próba egy
        rossz konstansra hivatkozna. Mindkét mért család itt áll."""
        forras = (_QML / _KOZOS).read_text(encoding="utf-8")
        for sor in (
            "grooveThickness: 9",
            "handleWidth: 16",
            "handleRadius: 3",
        ):
            assert sor in forras, f"hiányzik vagy más az érték: {sor}"
        assert "? 22 : 26" in forras, (
            "a két mért család fogantyú-magassága (scaleslider 22, "
            "editslider 26) nem a közös komponensben dől el"
        )

    def test_a_fogantyu_NEM_kor(self):
        """Az eredeti fogantyúja álló téglalap (16 × 26, illetve 16 × 22).
        A `PicasaSlider` alapértéke KEREK (`handleRadius` = fél oldal) —
        a közös komponensnek ezt felül kell írnia."""
        forras = (_QML / _KOZOS).read_text(encoding="utf-8")
        assert "handleRadius" in forras, (
            "nincs `handleRadius` a közös komponensben — a fogantyú KEREK maradna"
        )
        for _fajl, _elem, _s, szeles, magas, _cs in MERT_CSUSZKAK:
            assert magas > szeles, "a mért fogantyú ÁLLÓ téglalap"

    def test_egyetlen_panel_sem_ismetli_a_szamokat(self):
        """#710: a három panel egyike sem tarthatja meg a saját másolatát —
        épp ettől ment át a #2626 javítása csak kettőn."""
        for fajl in (
            "EditorFinetunePanel.qml",
            "EditorParamPanel.qml",
            "EditorTabCommonFixes.qml",
        ):
            forras = (_QML / fajl).read_text(encoding="utf-8")
            for nev in ("grooveThickness", "handleWidth", "handleHeight"):
                assert f"{nev}:" not in forras, (
                    f"{fajl}: a(z) `{nev}` ismét a panelben áll — a mért "
                    f"számok helye a `{_KOZOS}` (#710)"
                )
