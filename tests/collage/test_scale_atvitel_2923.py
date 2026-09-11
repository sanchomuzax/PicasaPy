"""#2923: a megnyitott `.cxf` `scale`-je VÁLTOZATLANUL megy vissza.

A #1412 277. köre kimérte, hogy az eredeti Picasa a csomópont `scale`-jét
**nem számolja**: az a fájlból jön (`_atof`, `0x008332b7`), az elrendezők a
`+0x2c`-hez nem nyúlnak, a másolók és a dokumentum-`reset` változatlanul
viszik tovább. Nálunk viszont a mentés a MAGA számolt értékét írta be —
tehát egy Picasával készült kollázs újramentése elrontotta a fájlt.

Az őr a `node_uids` (#1092) bevált mintáját méri a `scale`-re: ami a
megnyitott projektből jön, az érintetlen; ami új csomópont, az kapja a téma
szabálya szerinti értéket.
"""

from __future__ import annotations

import pytest

from picasapy.collage.cxf import CxfProject, dumps, loads
from picasapy.collage.draft import project_from_nodes
from picasapy.collage.nodes import CollageNode
from picasapy.collage.picasa_render import PicasaCollageSettings

#: Egy valódi, Picasával készült Indexkép-projekt szeletének mása: a
#: `scale` mind a három csomóponton **313**, és ez az érték semmilyen
#: általunk számolható képletből nem jön ki (a mi Indexkép-formulánk a
#: cellamagasságból számol).
MERT_SCALE = 313.0

_CXF = """<?xml version="1.0" encoding="utf-8" ?>
<collage version="2" format="4:3" orientation="portrait" theme="contactsheet"
 shadows="1" captions="1" albumUID="a4ef8e0fd2dbb152d25d79eb2bd2a28b">
 <albumTitle>AI</albumTitle>
 <albumDate>2023. november</albumDate>
 <background type="solid" color="FFD5D9AB"/>
 <spacing value="0.000000"/>
 <node x="0.087891" y="0.166300" w="0.236328" h="0.221612" theta="0.000000"
  scale="313.000000">
  <theme>whiteborder</theme>
  <src>elso.png</src>
  <uid>ec0932a3ccc166540000000000000000</uid>
 </node>
 <node x="0.380859" y="0.166300" w="0.236328" h="0.221612" theta="0.000000"
  scale="313.000000">
  <theme>whiteborder</theme>
  <src>masodik.png</src>
  <uid>ec0932a3ccc166540000000000000001</uid>
 </node>
</collage>
"""


@pytest.fixture
def projekt() -> CxfProject:
    return loads(_CXF)


def _csomopontok(projekt: CxfProject) -> tuple[CollageNode, ...]:
    from picasapy.collage.draft import nodes_from_project

    return nodes_from_project(projekt)


def _scale_map(projekt: CxfProject) -> dict[str, float]:
    return {
        node.src: node.scale for node in projekt.nodes if node.scale and node.src
    }


def _ujraments(projekt: CxfProject, **kwargs) -> CxfProject:
    settings = PicasaCollageSettings(
        theme=projekt.theme, border="whiteborder", width=1024, height=1365
    )
    return project_from_nodes(
        _csomopontok(projekt), settings, format_key="", **kwargs
    )


class TestAMegorzottScale:
    def test_a_megnyitott_ertek_VALTOZATLAN(self, projekt):
        ujra = _ujraments(projekt, node_scales=_scale_map(projekt))
        assert [node.scale for node in ujra.nodes] == [MERT_SCALE, MERT_SCALE]

    def test_a_megorzes_NELKUL_masik_szamot_kapnank(self, projekt):
        """Ez maga a hiba, amit a jegy leír: a mi számolt értékünk MÁS."""
        ujra = _ujraments(projekt)
        assert all(node.scale != MERT_SCALE for node in ujra.nodes), (
            "ha ez egyezik, a teszt nem azt méri, amit hisz"
        )

    def test_az_UJ_csomopont_szamolt_erteket_kap(self, projekt):
        """Csak ami a fájlból jött, azt őrizzük — az új kép nem maradhat
        `scale` nélkül."""
        csomopontok = _csomopontok(projekt)
        ujak = csomopontok + (
            CollageNode(
                path="uj.png",
                center_x=512.0,
                center_y=900.0,
                width=200.0,
                height=150.0,
                theta=0.0,
                border="whiteborder",
            ),
        )
        settings = PicasaCollageSettings(
            theme=projekt.theme, border="whiteborder", width=1024, height=1365
        )
        ujra = project_from_nodes(
            ujak, settings, format_key="", node_scales=_scale_map(projekt)
        )
        assert [node.scale for node in ujra.nodes][:2] == [MERT_SCALE, MERT_SCALE]
        assert ujra.nodes[-1].scale > 0.0

    def test_a_KULCS_a_feloldott_es_a_kodolt_alak_is(self, projekt):
        """A `.cxf` a Picasa változós útvonalát tárolja (#1096): a kulcs
        mindkét alakban találjon."""
        from picasapy.collage.win_paths import encode_cxf_path

        kodolt = {
            encode_cxf_path(node.src): node.scale
            for node in projekt.nodes
            if node.scale and node.src
        }
        ujra = _ujraments(projekt, node_scales=kodolt)
        assert [node.scale for node in ujra.nodes] == [MERT_SCALE, MERT_SCALE]


class TestAKorbenjaras:
    def test_a_kiirt_fajlban_ott_a_MERT_szam(self, projekt):
        """Végponttól végpontig: a szerializált `.cxf`-ben is a 313 áll."""
        ujra = _ujraments(projekt, node_scales=_scale_map(projekt))
        szoveg = dumps(ujra).decode("utf-8")
        assert szoveg.count('scale="313.000000"') == 2
