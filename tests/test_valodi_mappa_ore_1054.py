"""A „ne írj a felhasználó valódi mappájába" őr FOGA (#1054).

A `tests/conftest.py` autouse-fixture-e minden teszt köré odaáll. Egy őrről
azonban nem elég tudni, hogy zöld: azt kell állítani, hogy ELHASAL, amikor
tényleg szennyezés történt. A #1054 pont abból született, hogy egy fixture
hónapokig némán a valódi `~/Pictures/Picasa/Kollázsok`-ba írt, és a
lerakott `autosave.cxf`-et később a #1051 jegy a TULAJDONOS elveszett
munkájának nézte.

Itt ezért a felismerő logikát hajtjuk meg közvetlenül, ideiglenes mappán —
a valódi képmappához ez a teszt sem nyúl.
"""

from __future__ import annotations

from support.valodi_mappa_or import pillanatkep, valtozas_szovege


class TestAPillanatkep:
    def test_nem_letezo_mappara_ures(self, tmp_path):
        assert pillanatkep(tmp_path / "nincs-ilyen") == {}

    def test_az_alkonyvtarak_fajljait_is_latja(self, tmp_path):
        (tmp_path / "melyebb").mkdir()
        (tmp_path / "melyebb" / "a.cxf").write_text("x", encoding="utf-8")

        assert len(pillanatkep(tmp_path)) == 1


class TestAFelismeres:
    def test_valtozatlan_mappara_nincs_uzenet(self, tmp_path):
        (tmp_path / "a.cxf").write_text("x", encoding="utf-8")
        allapot = pillanatkep(tmp_path)

        assert valtozas_szovege(tmp_path, allapot, allapot) == ""

    def test_uj_fajlt_eszrevesz(self, tmp_path):
        elotte = pillanatkep(tmp_path)
        (tmp_path / "autosave.cxf").write_text("x", encoding="utf-8")

        uzenet = valtozas_szovege(tmp_path, elotte, pillanatkep(tmp_path))

        assert "autosave.cxf" in uzenet
        assert "keletkezett" in uzenet

    def test_megvaltozott_fajlt_eszrevesz(self, tmp_path):
        fajl = tmp_path / "autosave.cxf"
        fajl.write_text("regi", encoding="utf-8")
        elotte = pillanatkep(tmp_path)
        fajl.write_text("egeszen mas es hosszabb tartalom", encoding="utf-8")

        uzenet = valtozas_szovege(tmp_path, elotte, pillanatkep(tmp_path))

        assert "módosult" in uzenet
        assert "autosave.cxf" in uzenet

    def test_torolt_fajlt_eszrevesz(self, tmp_path):
        fajl = tmp_path / "autosave.cxf"
        fajl.write_text("x", encoding="utf-8")
        elotte = pillanatkep(tmp_path)
        fajl.unlink()

        uzenet = valtozas_szovege(tmp_path, elotte, pillanatkep(tmp_path))

        assert "eltűnt" in uzenet
