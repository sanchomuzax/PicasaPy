"""#943: a képesség-maszk MARADÉK öt bitje (háttér, keverés, szétszórás,
gyűrű, forgatás).

A #923 a négy panelbeli vezérlőt fedte le (keret, térköz, árnyék,
kijelölés). A kollázs-panel vezérlője viszont a `collageCapabilities`
térképben MIND A KILENC képességet továbbadja a QML-nek — hogy témánkénti
`if` sehol ne szülessen. A tábla forrása a
`docs/specs/kollazs-panel-ui-spec.md` **5.** szakasza.
"""

from __future__ import annotations

import pytest

from picasapy.collage.themes import (
    CONTACTSHEET,
    FRAMEGRID,
    MULTIEXP,
    PICTUREGRID,
    PICTUREPILE,
    REGULARGRID,
    capabilities_for,
)

#: A spec 5. szakaszának mátrixa, a maszkoktól FÜGGETLENÜL leírva:
#: (háttér, összekeverés, szétszórás, gyűrű).
VART = {
    PICTUREPILE: (True, True, True, True),
    PICTUREGRID: (True, True, False, False),
    FRAMEGRID: (True, True, False, False),
    REGULARGRID: (True, True, False, False),
    CONTACTSHEET: (True, False, False, False),
    MULTIEXP: (False, False, False, False),
}


class TestMaradekBitek:
    @pytest.mark.parametrize("tema", sorted(VART))
    def test_a_negy_tovabbi_kepesseg_a_spec_matrixa_szerint(self, tema):
        c = capabilities_for(tema)
        assert (c.background, c.shuffle, c.scramble, c.ring) == VART[tema]

    def test_forgatni_csak_a_kepkupacban_lehet(self):
        """A maszk 7. bitje = elforgatás (spec 15., bizonyítottsági fok:
        erős). A rácsos témák celláiban nincs szabad szög."""
        forgathato = {t for t in VART if capabilities_for(t).rotate}
        assert forgathato == {PICTUREPILE}

    def test_a_tobbszoros_exponalasnak_semmi_nem_all(self):
        c = capabilities_for(MULTIEXP)
        assert not any(
            (
                c.borders,
                c.spacing,
                c.shadow,
                c.selection,
                c.background,
                c.shuffle,
                c.scramble,
                c.ring,
                c.rotate,
            )
        )

    def test_a_regi_mezok_a_helyukon_maradtak(self):
        """A #923 négy mezője NÉV szerint elérhető marad (a `picasa_render`
        ezekre épül) — a bővítés nem tolhatja el őket."""
        c = capabilities_for(PICTUREPILE)
        assert (c.borders, c.spacing, c.shadow, c.selection) == (
            True,
            False,
            True,
            True,
        )


class TestKepessegTerkep:
    """A `capability_map` az, amit a vezérlő a QML-nek átad (spec 8.1)."""

    def test_pontosan_a_tiz_kulcs(self):
        """#1170: a tizedik a `group_overlay` (6. bit) — a vászon
        csoport-eleme. A szám azért van kimondva, hogy egy MEZŐ NÉLKÜLI
        bővítés (csak a `NamedTuple`-be, a térképbe nem) kibukjon."""
        from picasapy.collage.themes import UI_CAPABILITY_FIELDS, capability_map

        terkep = capability_map(PICTUREPILE)
        assert set(terkep) == set(UI_CAPABILITY_FIELDS)
        assert len(UI_CAPABILITY_FIELDS) == 10

    def test_az_arnyek_ALAPERTEKE_nem_kerul_a_terkepbe(self):
        """A `shadow_default` az árnyék-jelölő kezdőértéke, nem vezérlő —
        a felületen nincs mit mutatni belőle."""
        from picasapy.collage.themes import capability_map

        assert "shadow_default" not in capability_map(PICTUREPILE)

    def test_az_ertekek_a_capabilities_for_bol_jonnek(self):
        from picasapy.collage.themes import capability_map

        for tema in VART:
            c = capabilities_for(tema)
            assert capability_map(tema) == {
                "borders": c.borders,
                "spacing": c.spacing,
                "shadow": c.shadow,
                "selection": c.selection,
                "background": c.background,
                "shuffle": c.shuffle,
                "scramble": c.scramble,
                "ring": c.ring,
                "rotate": c.rotate,
                "group_overlay": c.group_overlay,
            }
