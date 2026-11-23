"""#7367: az újravágás a lánc VÉGÉN álló `crop64`-et helyben frissíti.

Az eredeti Picasa (`0x006b4300`) a lista utolsó elemét a `crop64` névhez
hasonlítja: egyezéskor a meglévő rekord koordinátáit írja át, más végrekordnál
új `crop64` elemet fűz a végére. A `recrop` ezt a döntést hozza meg; az
`append_crop` változatlanul feltétel nélküli hozzáfűzés marad.
"""

from __future__ import annotations

from picasapy.edit.recrop import recrop, vegi_crop_frissitheto
from picasapy.edit.session import EditSession
from picasapy.ini.rect64 import Rect64, encode_rect64

ELSO = Rect64(left=0.0, top=0.0, right=0.5, bottom=0.5)
MASODIK = Rect64(left=0.25, top=0.25, right=0.75, bottom=0.75)
HARMADIK = Rect64(left=0.5, top=0.5, right=1.0, bottom=1.0)


def _crop(rect: Rect64) -> str:
    return f"crop64=1,{encode_rect64(rect)};"


class TestVegiCropHelybenFrissul:
    def test_a_lanc_vegi_crop64_koordinatai_valtoznak(self):
        session = EditSession.from_value(f"bw=1;{_crop(ELSO)}")

        eredmeny = recrop(session, MASODIK)

        assert eredmeny.to_value() == f"bw=1;{_crop(MASODIK)}"

    def test_a_rekordok_szama_nem_no(self):
        session = EditSession.from_value(_crop(ELSO))

        eredmeny = recrop(session, MASODIK)

        assert len(eredmeny.ops) == len(session.ops) == 1

    def test_csak_az_utolso_crop64_valtozik_a_korabbiak_megmaradnak(self):
        session = EditSession.from_value(f"{_crop(ELSO)}bw=1;{_crop(MASODIK)}")

        eredmeny = recrop(session, HARMADIK)

        assert eredmeny.to_value() == f"{_crop(ELSO)}bw=1;{_crop(HARMADIK)}"

    def test_a_hatalyos_vagas_az_uj_teglalap(self):
        session = EditSession.from_value(f"bw=1;{_crop(ELSO)}")

        eredmeny = recrop(session, MASODIK)

        assert encode_rect64(eredmeny.crop()) == encode_rect64(MASODIK)

    def test_az_eredeti_munkamenet_valtozatlan(self):
        session = EditSession.from_value(f"bw=1;{_crop(ELSO)}")

        recrop(session, MASODIK)

        assert session.to_value() == f"bw=1;{_crop(ELSO)}"


class TestMasVegrekordnalHozzafuz:
    def test_ures_lancnal_uj_crop64_kerul_a_lancba(self):
        eredmeny = recrop(EditSession(), MASODIK)

        assert eredmeny.to_value() == _crop(MASODIK)

    def test_bw_vegu_lancnal_uj_rekord_kerul_a_vegere(self):
        session = EditSession.from_value(f"{_crop(ELSO)}bw=1;")

        eredmeny = recrop(session, MASODIK)

        assert eredmeny.to_value() == f"{_crop(ELSO)}bw=1;{_crop(MASODIK)}"

    def test_a_hatalyos_vagas_az_utoljara_fuzott_rekord(self):
        session = EditSession.from_value(f"{_crop(ELSO)}bw=1;")

        eredmeny = recrop(session, MASODIK)

        assert encode_rect64(eredmeny.crop()) == encode_rect64(MASODIK)


class TestUresTeglalap:
    def test_crop64_vegu_lancon_torli_az_utolso_crop64_et(self):
        session = EditSession.from_value(f"{_crop(ELSO)}bw=1;{_crop(MASODIK)}")

        eredmeny = recrop(session, None)

        assert eredmeny.to_value() == f"{_crop(ELSO)}bw=1;"

    def test_egyetlen_crop64_torlese_ures_lancot_ad(self):
        eredmeny = recrop(EditSession.from_value(_crop(ELSO)), None)

        assert eredmeny.ops == ()

    def test_mas_vegrekordnal_nem_valtoztat_a_lancon(self):
        session = EditSession.from_value(f"{_crop(ELSO)}bw=1;")

        assert recrop(session, None).to_value() == session.to_value()

    def test_ures_lancon_nem_valtoztat(self):
        assert recrop(EditSession(), None).ops == ()


class TestVegiCropFrissitheto:
    def test_crop64_vegu_lanc_frissitheto(self):
        assert vegi_crop_frissitheto(EditSession.from_value(f"bw=1;{_crop(ELSO)}"))

    def test_bw_vegu_lanc_nem_frissitheto(self):
        assert not vegi_crop_frissitheto(EditSession.from_value(f"{_crop(ELSO)}bw=1;"))

    def test_ures_lanc_nem_frissitheto(self):
        assert not vegi_crop_frissitheto(EditSession())


class TestAzAppendCropValtozatlan:
    """Az `append_crop` marad feltétlen hozzáfűzés (a #1553 őrei rá épülnek)."""

    def test_crop64_vegu_lancra_is_uj_rekordot_fuz(self):
        session = EditSession.from_value(_crop(ELSO))

        eredmeny = session.append_crop(MASODIK)

        assert eredmeny.to_value() == f"{_crop(ELSO)}{_crop(MASODIK)}"
