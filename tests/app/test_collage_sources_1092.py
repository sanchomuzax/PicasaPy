"""A közös forrásmappa szabálya EGY példányban él (#1092).

A `.cxf` három mezője beszél a forrásalbumról — `<albumTitle>`,
`albumUID`, `<albumDate>` —, és mind a háromnak ugyanaz a forrása. A
szabály elsőre két helyen, két megvalósításban élt: a cím a vezérlőben, a
másik kettő az album-mezőknél. A teszt foga az utolsó állítás: a
vezérlő címe és az album-azonosító UGYANARRA a döntésre épül, tehát nem
mondhatnak ellent egymásnak.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from picasapy.app.collage_album_fields import album_fields_of
from picasapy.app.collage_sources import (
    common_source_folder,
    common_source_folder_name,
)
from picasapy.collage.uids import album_uid_for


@dataclass
class _Source:
    path: str


class TestAKozosMappa:
    def test_egy_mappa(self):
        forrasok = [_Source("/kepek/AI/a.jpg"), _Source("/kepek/AI/b.jpg")]

        assert common_source_folder(forrasok) == Path("/kepek/AI")
        assert common_source_folder_name(forrasok) == "AI"

    def test_ket_mappa_eseten_nincs(self):
        forrasok = [_Source("/kepek/AI/a.jpg"), _Source("/kepek/lake/b.jpg")]

        assert common_source_folder(forrasok) is None
        assert common_source_folder_name(forrasok) == ""

    def test_ures_utvonalu_forras_kimarad(self):
        forrasok = [_Source("/kepek/AI/a.jpg"), _Source("")]

        assert common_source_folder(forrasok) == Path("/kepek/AI")

    def test_egyaltalan_nincs_forras(self):
        assert common_source_folder([]) is None
        assert common_source_folder_name([]) == ""


class TestACimEsAzAzonositoEgyutt_Dont:
    """A vezérlő címe és az `albumUID` ugyanabból a döntésből jön."""

    def test_ket_mappanal_MINDKETTO_ures(self):
        forrasok = [_Source("/kepek/AI/a.jpg"), _Source("/kepek/lake/b.jpg")]

        assert common_source_folder_name(forrasok) == ""
        assert album_fields_of(forrasok, db_path=None, language="hu") == ("", "")

    def test_egy_mappanal_MINDKETTO_ugyanarra_a_mappara_mutat(self):
        forrasok = [_Source("/kepek/AI/a.jpg")]

        nev = common_source_folder_name(forrasok)
        uid, _ = album_fields_of(forrasok, db_path=None, language="hu")

        assert nev == "AI"
        assert uid == album_uid_for(Path("/kepek/AI"))
