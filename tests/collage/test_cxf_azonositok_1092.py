"""A `.cxf` három hiányzó azonosítója: `albumUID`, `albumDate`, `<uid>` (#1092).

## A lelet

A `collage/cxf.py` MINDHÁROM mezőt ismeri — írja is, olvassa is —, csak
üresen hagyottan sosem kerülnek a fájlba. A gyártó oldal (`draft.py`
`project_from_nodes`, illetve a panel) egyszerűen nem tölti ki őket, tehát
a PicasaPy `.cxf`-jeiből mind a három hiányzik. A saját körbejárásunk ettől
zöld marad; az eltérés csak idegen programban látszik.

## A mért alak (12 golden minta, `referencia/kollazs-golden/`)

| mező | minden mintában | alak |
|---|---|---|
| `albumUID` | 12 / 12 | 32 kisbetűs hexa |
| `<albumDate>` | 12 / 12 | `2023. november` — év + honos hónapnév |
| `<uid>` | csomópontonként | 16 hexa + **16 nulla** |

Két invariáns, amit ugyanez a mérés ad, és amit a teszt őriz:

1. **Ugyanabból a forrásalbumból készült 11 kollázs `albumUID`-ja AZONOS**
   (`a4ef8e0f…`) — az azonosító tehát a forrásalbumé, nem a kollázsé, és
   determinisztikus. Véletlen azonosító ezt az invariánst megsértené.
2. **Ugyanaz a kép ugyanazt a `<uid>`-ot kapja két külön kollázsban is**
   (`AI1.cxf` és `AI7.cxf` közös képei) — a képazonosító is stabil.

## Amit NEM tudunk

Az eredeti `uid64` a Picasa BELSŐ adatbázisából (`imagedata`) jön; sem az
útvonalból, sem a `.picasa.ini`-ből nem vezethető le (a mérés: a korpusz
6045 `IIDLIST_*` értéke mind `4…` prefixű, feltöltési időbélyeggel — más
azonosító-család, mint a `.cxf` egyenletesen szórt uid-jai). A mi
származtatásunk ezért **SAJÁT FUNKCIÓ**: a teszt az ALAKOT, az
egyediséget és a stabilitást állítja, nem konkrét értékeket.
"""

from __future__ import annotations

import re

import pytest

from picasapy.collage.cxf import CxfNode, CxfProject, dumps, loads
from picasapy.collage.draft import project_from_nodes
from picasapy.collage.nodes import CollageNode
from picasapy.collage.picasa_render import PicasaCollageSettings
from picasapy.collage.uids import album_uid_for, node_uid_for

#: A mért csomópont-azonosító alakja: 16 hexa, majd 16 nulla.
NODE_UID = re.compile(r"^[0-9a-f]{16}0{16}$")

#: A mért `albumUID` alakja: 32 kisbetűs hexa.
ALBUM_UID = re.compile(r"^[0-9a-f]{32}$")


def _beallitas() -> PicasaCollageSettings:
    return PicasaCollageSettings(
        theme="picturepile", border="noborder", width=1024, height=768
    )


def _vaszon_csomopont(ut: str) -> CollageNode:
    return CollageNode(
        path=ut,
        center_x=512.0,
        center_y=384.0,
        width=300.0,
        height=200.0,
        theta=0.0,
        border="noborder",
    )


class TestACsomopontAzonosito:
    """`<uid>` — a 32 karakteres, félig nullázott képazonosító."""

    def test_a_projekt_minden_csomopontja_kap_uid_ot(self, tmp_path):
        projekt = project_from_nodes(
            [
                _vaszon_csomopont(str(tmp_path / "a.jpg")),
                _vaszon_csomopont(str(tmp_path / "b.jpg")),
            ],
            _beallitas(),
        )

        assert [node.uid for node in projekt.nodes] != ["", ""], (
            "a `.cxf` csomópontjaiból teljesen hiányzik a <uid> (#1092)"
        )
        for node in projekt.nodes:
            assert NODE_UID.match(node.uid), f"nem a mért alak: {node.uid!r}"

    def test_kulon_kep_kulon_azonosito(self, tmp_path):
        projekt = project_from_nodes(
            [
                _vaszon_csomopont(str(tmp_path / "a.jpg")),
                _vaszon_csomopont(str(tmp_path / "b.jpg")),
            ],
            _beallitas(),
        )

        azonositok = {node.uid for node in projekt.nodes}
        assert len(azonositok) == 2, "két kép ugyanazt az azonosítót kapta"

    def test_ugyanaz_a_kep_ugyanazt_kapja_masik_kollazsban(self, tmp_path):
        """A mért invariáns: `AI1.cxf` és `AI7.cxf` közös képei egyeznek."""
        elso = project_from_nodes(
            [_vaszon_csomopont(str(tmp_path / "a.jpg"))], _beallitas()
        )
        masodik = project_from_nodes(
            [
                _vaszon_csomopont(str(tmp_path / "z.jpg")),
                _vaszon_csomopont(str(tmp_path / "a.jpg")),
            ],
            _beallitas(),
        )

        assert elso.nodes[0].uid, "üres azonosító — az egyezés vacuous volna"
        assert elso.nodes[0].uid == masodik.nodes[1].uid

    def test_a_megnyitott_projekt_azonositoi_tulelik_az_ujramentest(self, tmp_path):
        """A Picasa ÍRTA azonosítót nem szabad a sajátunkra cserélni.

        Ugyanaz a hibaosztály, amit a #1274 az `albumUID`-nál javított: a
        körbejárás nem veszíthet adatot. A panel a megnyitáskor látott
        `src → uid` párokat adja vissza."""
        ut = str(tmp_path / "a.jpg")
        eredeti = "c91b4354e61f4a5a0000000000000000"

        projekt = project_from_nodes(
            [_vaszon_csomopont(ut)], _beallitas(), node_uids={ut: eredeti}
        )

        assert projekt.nodes[0].uid == eredeti

    def test_ures_forrasnal_nincs_azonosito(self, tmp_path):
        """Kép nélküli csomópontra nem gyártunk azonosítót — nincs mihez."""
        assert node_uid_for("") == ""


class TestAzAlbumAzonosito:
    """`albumUID` — a FORRÁSALBUM 32 hexás azonosítója."""

    def test_a_mert_alak(self, tmp_path):
        assert ALBUM_UID.match(album_uid_for(tmp_path / "AI"))

    def test_ugyanarra_a_mappara_ugyanaz(self, tmp_path):
        """A 11 golden minta invariánsa: egy forrásalbum → egy albumUID."""
        assert album_uid_for(tmp_path / "AI") == album_uid_for(tmp_path / "AI")

    def test_mas_mappara_mas(self, tmp_path):
        assert album_uid_for(tmp_path / "AI") != album_uid_for(tmp_path / "lake")

    def test_ures_mappara_ures(self):
        assert album_uid_for("") == ""


class TestAKorbejaras:
    """Kiírás → beolvasás → ugyanaz: a legerősebb állítás (#1092)."""

    def test_a_harom_mezo_atmegy_a_fajlon(self, tmp_path):
        projekt = project_from_nodes(
            [
                _vaszon_csomopont(str(tmp_path / "a.jpg")),
                _vaszon_csomopont(str(tmp_path / "b.jpg")),
            ],
            _beallitas(),
            album_title="AI",
            album_date="2023. november",
            album_uid=album_uid_for(tmp_path / "AI"),
        )

        visszaolvasott = loads(dumps(projekt))

        assert visszaolvasott.album_uid == projekt.album_uid != ""
        assert visszaolvasott.album_date == "2023. november"
        assert all(n.uid for n in projekt.nodes), "üres uid — az egyezés vacuous"
        assert [n.uid for n in visszaolvasott.nodes] == [
            n.uid for n in projekt.nodes
        ]

    def test_a_kiirt_szoveg_tartalmazza_mindharmat(self, tmp_path):
        projekt = project_from_nodes(
            [_vaszon_csomopont(str(tmp_path / "a.jpg"))],
            _beallitas(),
            album_date="2023. november",
            album_uid=album_uid_for(tmp_path / "AI"),
        )

        szoveg = dumps(projekt).decode("utf-8")

        assert "albumUID=" in szoveg
        assert "<albumDate>2023. november</albumDate>" in szoveg
        assert "<uid>" in szoveg


class TestAzOlvasoMegengedo:
    """Az ELLENKEZŐ irányú őr: idegen alakú azonosító nem törhet el semmit.

    Az alakot a MI kimenetünkre állítjuk (fent), az olvasóra nem: egy
    idegen — akár csonka, akár nagybetűs — `<uid>` sem teheti
    visszaállíthatatlanná a felhasználó munkáját (ugyanaz az elv, amit a
    `collage_node_of` a `dimmed` keretnél már kimond)."""

    @pytest.mark.parametrize(
        "furcsa",
        [
            "c91b4354e61f4a5a",  # csak 16 karakter
            "C91B4354E61F4A5A0000000000000000",  # nagybetűs
            "akármi",
        ],
    )
    def test_az_idegen_uid_valtozatlanul_johet_vissza(self, furcsa):
        adat = (
            '<?xml version="1.0" encoding="utf-8" ?>\r\n'
            '<collage version="2" format="4:3" orientation="landscape"'
            ' theme="picturepile" shadows="0" captions="0">\r\n'
            ' <background type="solid" color="FFFFFFFF"/>\r\n'
            ' <spacing value="0.000000"/>\r\n'
            ' <node x="0.1" y="0.1" w="0.2" h="0.2" theta="0.0" scale="1.0">\r\n'
            "  <theme>noborder</theme>\r\n"
            "  <src>kep.jpg</src>\r\n"
            f"  <uid>{furcsa}</uid>\r\n"
            " </node>\r\n"
            "</collage>\r\n"
        )

        projekt = loads(adat)

        assert projekt.nodes[0].uid == furcsa

    def test_az_azonosito_nelkuli_regi_fajl_is_olvashato(self):
        assert CxfNode(0.1, 0.1, 0.2, 0.2, 0.0, 100.0).uid == ""
        assert CxfProject().album_uid == ""
