"""A `.cxf` `scale` mezője LAPEGYSÉGBEN megy ki (#1071) — P0.

## A lelet

A tulajdonos megnyitotta a PicasaPy-vel készült kollázst a valódi Picasa
3-ban, és **szerkesztéskor szétesett**: óriási, felnagyított töredékek.

Az ok: a `scale`-t **kimeneti képpontban** írtuk, a Picasa viszont
**lapegységben** (1024 egység széles lap) olvassa. A hiba pontosan
`settings.width / 1024`:

| lap | `settings.width` | a mi `scale`-ünk | a Picasa értéke | szorzó |
|---|---:|---:|---:|---:|
| a tulajdonos lapja | 5120 | **1685,00** | 337 | **5,00×** |
| álló A4-szerű | 3841 | 1264,08 | 337 | 3,75× |
| lapegység | 1024 | 337,00 | 337 | 1,00× |

## ⚠️ Miért nem fogta meg SEMMI

Két, egymást kiegészítő vakfolt:

1. **A saját oda-vissza utunk hibátlan.** Az olvasónk
   (`collage_node_of`) a `scale`-t **egyáltalán nem használja** — a
   geometriát az `x/y/w/h`-ból építi vissza. A kódolás tehát **önmagában
   konzisztens, csak nem szabványos**: a hiba csak akkor látszik, ha a
   fájlt MÁS program nyitja meg.
2. **A golden `.cxf`-ek bájtazonossági tesztje** a **beolvasott** `scale`-t
   írja vissza — sosem a **generáltat**. Szerkezetileg vak erre a hibára.

Ezért állít ez a fájl a GENERÁLT kimenetre, és köti a golden számaihoz.

## Az invariáns

A csomópont méretei MÁR lapegységben vannak. A `scale` a doboz **nagyobbik
oldala** ugyanabban az egységben — tehát átváltás NEM kell, és a
`settings.width` nem hathat rá.
"""

from __future__ import annotations

import pytest

from picasapy.collage.draft import cxf_node_of, project_from_nodes
from picasapy.collage.nodes import SHEET_UNITS, CollageNode
from picasapy.collage.picasa_render import PicasaCollageSettings
from picasapy.collage.themes import NOBORDER, PICTUREPILE

#: A tulajdonos `AI1.cxf`-jének kilenc `scale` mezője (a #1059 mérése).
GOLDEN_SCALE = (337, 337, 337, 337, 303, 280, 263, 249, 238)


def _csomopont(szeles: float, magas: float) -> CollageNode:
    return CollageNode(
        path="/nincs/a.jpg",
        center_x=SHEET_UNITS * 0.5,
        center_y=SHEET_UNITS * 0.3,
        width=szeles,
        height=magas,
        theta=0.0,
        border=NOBORDER,
    )


class TestAScaleLapegysegben:
    """⚠️ A `settings.width` NEM hathat a `scale`-re."""

    @pytest.mark.parametrize("lapszelesseg", [1024, 1600, 3841, 5120])
    def test_a_kimeneti_szelesseg_nem_valtoztat_rajta(self, lapszelesseg):
        csomopont = _csomopont(280.8, 337.0)

        eredmeny = cxf_node_of(
            csomopont, page_width=lapszelesseg, page_ratio=0.75
        )

        assert eredmeny.scale == pytest.approx(337.0, abs=0.01)

    def test_a_NAGYOBBIK_oldal_adja(self):
        """A spec 1.6 mintája ezt dönti el: a `scale` a doboz nagyobbik
        oldala, nem a szélessége."""
        fekvo = cxf_node_of(_csomopont(400.0, 200.0), page_width=5120, page_ratio=0.75)
        allo = cxf_node_of(_csomopont(200.0, 400.0), page_width=5120, page_ratio=0.75)

        assert (fekvo.scale, allo.scale) == (400.0, 400.0)

    def test_a_teljes_projekt_scale_ei_is_lapegysegben(self):
        beallitas = PicasaCollageSettings(
            theme=PICTUREPILE, border=NOBORDER, width=5120, height=3840
        )

        projekt = project_from_nodes([_csomopont(280.8, 337.0)], beallitas)

        assert projekt.nodes[0].scale == pytest.approx(337.0, abs=0.01)


class TestAGoldenSzamok:
    """A generált érték a tulajdonos fájljainak számaihoz kötve."""

    def test_a_kupac_scale_ei_a_golden_ertekeket_adjak(self):
        """A Képkupac `pile_size`-ja 1024-es lapon pontosan ezeket adja
        (#1059) — és a `.cxf`-be UGYANEZEKNEK kell kimenniük."""
        from picasapy.collage.pile import pile_size

        beallitas = PicasaCollageSettings(
            theme=PICTUREPILE, border=NOBORDER, width=5120, height=3840
        )
        # álló képek: a magasság a korlátozó méret, tehát az a `scale`
        csomopontok = [
            _csomopont(pile_size(i, SHEET_UNITS) * 0.8, pile_size(i, SHEET_UNITS))
            for i in range(1, len(GOLDEN_SCALE) + 1)
        ]

        projekt = project_from_nodes(csomopontok, beallitas)

        assert [round(n.scale) for n in projekt.nodes] == list(GOLDEN_SCALE)


class TestAzOlvasoErintetlen:
    """Az olvasónk a `scale`-t nem használja — a változás nem törheti el."""

    def test_a_geometria_az_x_y_w_h_bol_jon(self):
        from picasapy.collage.draft import collage_node_of

        eredeti = _csomopont(280.8, 337.0)
        kiirt = cxf_node_of(eredeti, page_width=5120, page_ratio=0.75)

        vissza = collage_node_of(kiirt, page_ratio=0.75)

        assert vissza.width == pytest.approx(eredeti.width, abs=0.01)
        assert vissza.height == pytest.approx(eredeti.height, abs=0.01)
        assert vissza.center_x == pytest.approx(eredeti.center_x, abs=0.01)
        assert vissza.center_y == pytest.approx(eredeti.center_y, abs=0.01)
