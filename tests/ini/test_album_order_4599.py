"""#4599 (ADR-016): az album képsorrendje a kép szakaszában, `albumorder=`.

Tiszta függvények az immutable dokumentumon. A lényeg: csak az érintett
album párja változik, a szakasz és a fájl minden más sora bájtra azonos.
"""

from __future__ import annotations

import pytest

from picasapy.ini.album_order import (
    AlbumOrderWriteError,
    parse_places,
    places_of,
    serialize_places,
    with_album_places,
    without_album_place,
    write_album_places,
)
from picasapy.ini.albums import without_album, without_album_everywhere
from picasapy.ini.document import parse_document

_A = "604c294a68b0de9cc9222c4714f289d5"
_B = "1f2e3d4c5b6a79880123456789abcdef"


class TestFormat:
    def test_a_hely_mindig_tizedes_alakban_megy_ki(self):
        assert serialize_places({_A: 3}) == f"{_A}:3.0"
        assert serialize_places({_A: 0.5, _B: 12}) == f"{_A}:0.5,{_B}:12.0"

    def test_pont_a_tizedesjel_es_visszaolvashato(self):
        assert parse_places(f"{_A}:3.5") == {_A: 3.5}

    @pytest.mark.parametrize(
        "nyers",
        ["", f"{_A}", f"{_A}:", f"{_A}:abc", f"{_A}:nan", f"{_A}:inf", ":3.0", ",,"],
    )
    def test_romlott_par_kimarad_es_nem_dob(self, nyers):
        assert parse_places(nyers) == {}

    def test_romlott_par_nem_viszi_el_a_szomszedjat(self):
        assert parse_places(f"{_A}:x,{_B}:2.0") == {_B: 2.0}

    def test_ismetlodo_tokennel_az_elso_nyer(self):
        assert parse_places(f"{_A}:1.0,{_A}:9.0") == {_A: 1.0}


class TestOlvasas:
    def test_csak_az_albums_kulcsban_szereplo_token_ervenyes(self):
        document = parse_document(
            f"[a.jpg]\nalbums={_A}\nalbumorder={_A}:2.0,{_B}:7.0\n"
        )
        assert places_of(document) == {"a.jpg": {_A: 2.0}}

    def test_elarvult_par_kimarad(self):
        document = parse_document(f"[a.jpg]\nalbumorder={_A}:2.0\n")
        assert places_of(document) == {}

    def test_hely_nelkuli_kep_nem_szerepel(self):
        document = parse_document(f"[a.jpg]\nalbums={_A}\n[b.jpg]\nstar=yes\n")
        assert places_of(document) == {}


class TestIras:
    def test_az_album_helyet_kap_a_tobbi_sor_erintetlen(self):
        forras = (
            f"[a.jpg]\nstar=yes\nalbums={_A},{_B}\ncaption=nyár\n"
            f"[b.jpg]\nalbums={_A}\npriority=4.0\n"
        )
        document = parse_document(forras)

        result = with_album_places(document, _A, {"a.jpg": 1.0, "b.jpg": 2.0})

        a = result.section("a.jpg")
        assert a.get("albumorder") == f"{_A}:1.0"
        assert a.get("star") == "yes"
        assert a.get("albums") == f"{_A},{_B}"
        assert a.get("caption") == "nyár"
        b = result.section("b.jpg")
        assert b.get("albumorder") == f"{_A}:2.0"
        assert b.get("priority") == "4.0"

    def test_a_masik_album_parja_valtozatlan(self):
        document = parse_document(
            f"[a.jpg]\nalbums={_A},{_B}\nalbumorder={_B}:5.0,{_A}:9.0\n"
        )

        result = with_album_places(document, _A, {"a.jpg": 1.0})

        assert places_of(result)["a.jpg"] == {_B: 5.0, _A: 1.0}

    def test_nem_tag_kepre_nem_ir(self):
        document = parse_document(f"[a.jpg]\nalbums={_B}\n")
        result = with_album_places(document, _A, {"a.jpg": 1.0})
        assert result.serialize() == document.serialize()

    def test_nem_letezo_szakaszt_nem_hoz_letre(self):
        document = parse_document(f"[a.jpg]\nalbums={_A}\n")
        result = with_album_places(document, _A, {"szellem.jpg": 1.0})
        assert result.section("szellem.jpg") is None

    def test_a_nem_erintett_szakasz_bajtra_azonos(self):
        forras = (
            "[x.jpg]\r\nstar=yes\r\nfaces=rect64(1),abc\r\n"
            f"[a.jpg]\r\nalbums={_A}\r\n"
        )
        document = parse_document(forras)
        result = with_album_places(document, _A, {"a.jpg": 1.0})
        assert result.serialize().startswith(
            "[x.jpg]\r\nstar=yes\r\nfaces=rect64(1),abc\r\n"
        )

    def test_nem_modositja_a_bemenetet(self):
        document = parse_document(f"[a.jpg]\nalbums={_A}\n")
        with_album_places(document, _A, {"a.jpg": 1.0})
        assert document.section("a.jpg").get("albumorder") is None


class TestKivetel:
    def test_a_kep_kivetele_az_part_is_viszi_ugyanabban_az_irasban(self):
        document = parse_document(
            f"[a.jpg]\nalbums={_A},{_B}\nalbumorder={_A}:1.0,{_B}:2.0\n"
        )

        result = without_album(document, "a.jpg", _A)

        section = result.section("a.jpg")
        assert section.get("albums") == _B
        assert section.get("albumorder") == f"{_B}:2.0"

    def test_az_utolso_par_kivetelekor_a_kulcs_torlodik(self):
        document = parse_document(
            f"[a.jpg]\nalbums={_A}\nalbumorder={_A}:1.0\n"
        )

        result = without_album(document, "a.jpg", _A)

        section = result.section("a.jpg")
        assert section is None or section.get("albums") is None
        assert section is None or section.get("albumorder") is None

    def test_az_album_torlese_minden_kepen_kiveszi_a_part(self):
        document = parse_document(
            f"[.album:{_A}]\ntoken={_A}\nname=X\n"
            f"[a.jpg]\nalbums={_A},{_B}\nalbumorder={_A}:1.0,{_B}:2.0\n"
            f"[b.jpg]\nalbums={_A}\nalbumorder={_A}:2.0\nstar=yes\n"
        )

        result = without_album_everywhere(document, _A)

        assert result.section(f".album:{_A}") is None
        assert result.section("a.jpg").get("albumorder") == f"{_B}:2.0"
        b = result.section("b.jpg")
        assert b.get("albumorder") is None
        assert b.get("star") == "yes"

    def test_hely_nelkuli_kep_kivetele_valtozatlanul_hagyja_a_dokumentumot(self):
        document = parse_document(f"[a.jpg]\nalbums={_A}\n")
        result = without_album_place(document, "a.jpg", _A)
        assert result.serialize() == document.serialize()


class TestMappankentiIras:
    def test_mappankent_egy_irassal_es_banat_nelkul(self, tmp_path):
        egy = tmp_path / "egy"
        ketto = tmp_path / "ketto"
        egy.mkdir()
        ketto.mkdir()
        (egy / ".picasa.ini").write_text(
            f"[a.jpg]\nalbums={_A}\n[b.jpg]\nalbums={_A}\n", encoding="utf-8"
        )
        (ketto / ".picasa.ini").write_text(
            f"[c.jpg]\nalbums={_A}\n", encoding="utf-8"
        )
        irt = []

        write_album_places(
            _A,
            [
                (egy / ".picasa.ini", {"a.jpg": 3.0, "b.jpg": 1.0}),
                (ketto / ".picasa.ini", {"c.jpg": 2.0}),
            ],
            on_written=irt.append,
        )

        assert len(irt) == 2
        egy_doc = parse_document((egy / ".picasa.ini").read_text(encoding="utf-8"))
        assert places_of(egy_doc) == {"a.jpg": {_A: 3.0}, "b.jpg": {_A: 1.0}}
        ketto_doc = parse_document((ketto / ".picasa.ini").read_text(encoding="utf-8"))
        assert places_of(ketto_doc) == {"c.jpg": {_A: 2.0}}

    def test_bukott_iras_megnevezi_a_mappat_es_a_tobbit_kiirja(
        self, tmp_path, monkeypatch
    ):
        jo = tmp_path / "jo"
        rossz = tmp_path / "rossz_mappa"
        jo.mkdir()
        rossz.mkdir()
        (jo / ".picasa.ini").write_text(f"[a.jpg]\nalbums={_A}\n", encoding="utf-8")
        (rossz / ".picasa.ini").write_text(f"[b.jpg]\nalbums={_A}\n", encoding="utf-8")
        import picasapy.ini.album_order as modul

        eredeti = modul.update_document

        def hibas(path, mutate, **kwargs):
            if "rossz_mappa" in str(path):
                raise OSError("nem írható")
            return eredeti(path, mutate, **kwargs)

        monkeypatch.setattr(modul, "update_document", hibas)

        with pytest.raises(AlbumOrderWriteError) as hiba:
            write_album_places(
                _A,
                [
                    (rossz / ".picasa.ini", {"b.jpg": 1.0}),
                    (jo / ".picasa.ini", {"a.jpg": 2.0}),
                ],
            )

        assert "rossz_mappa" in str(hiba.value)
        jo_doc = parse_document((jo / ".picasa.ini").read_text(encoding="utf-8"))
        assert places_of(jo_doc) == {"a.jpg": {_A: 2.0}}
