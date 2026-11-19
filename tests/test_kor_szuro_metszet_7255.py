"""#7255: a kor-szűrő a keresés állapotának része, és a sáv felirata `Date Range:` előtagú.

Az eredetiben (mérve a `picasa-colab-jobs` #744 és #748 köreiben) a szöveges
keresés és az idő-csúszka közös állapot: a találat a szöveges találat ÉS a
`kor <= N nap` metszete. A felirat a zöld sáv jobb szélén
`Date Range:  Pictures up to N <egység> old.` alakú (két szóköz a kettőspont
után), a bal szélső (0) állásban nincs felirat.

Ez a fájl a tiszta rétegeket méri, Qt és ablak nélkül: az index-szintű
metszetet (`intersect_with_age`) és a felirat szövegét (`sav_felirat`). A
vezérlő- és felületi próbák a `tests/app/` alatt vannak.

A `tests/` gyökerében van (nem a `tests/app/` alatt): nem indít alkalmazást,
tehát az app-harness környezete (és a #1054 őr) nem kell hozzá.
"""

from __future__ import annotations

import pytest

from picasapy.app import kor_szuro
from picasapy.app.search_button_filter import intersect_with_age
from picasapy.index import all_photos, open_index


def _tr(szoveg: str) -> str:
    """A `tr` helyettesítője: a magyar szöveget itt nem mérjük."""
    return szoveg


@pytest.fixture
def index(tmp_path):
    """Három dátumos és egy dátum nélküli kép, ismert korral."""
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        conn.execute(
            "INSERT INTO folders(id, path, has_ini) VALUES (1, ?, 0)",
            (str(tmp_path),),
        )
        for nev, mikor in (
            ("a_friss.jpg", "2026-09-09T10:00:00"),
            ("b_kozepso.jpg", "2025-01-01T10:00:00"),
            ("c_regi.jpg", "2020-01-01T10:00:00"),
            ("d_datum_nelkul.jpg", None),
        ):
            conn.execute(
                "INSERT INTO photos(folder_id, name, kind, size,"
                " mtime_ns, taken_at) VALUES (1, ?, 'image', 10, 1, ?)",
                (nev, mikor),
            )
        conn.commit()
        yield conn


class TestAMetszetIndexSzinten:
    def test_csak_a_vagopont_utani_talalatok_maradnak(self, index):
        talalatok = all_photos(index)

        metszet = intersect_with_age(index, talalatok, "2025-06-01T00:00:00")

        assert [r.name for r in metszet] == ["a_friss.jpg"]

    def test_a_datum_nelkuli_kep_kimarad_mert_kora_nincs(self, index):
        talalatok = all_photos(index)

        metszet = intersect_with_age(index, talalatok, "2000-01-01T00:00:00")

        assert {r.name for r in metszet} == {
            "a_friss.jpg",
            "b_kozepso.jpg",
            "c_regi.jpg",
        }

    def test_a_metszet_a_talalatok_sorrendjet_orzi(self, index):
        talalatok = tuple(reversed(all_photos(index)))

        metszet = intersect_with_age(index, talalatok, "2000-01-01T00:00:00")

        assert [r.name for r in metszet] == [
            r.name for r in talalatok if r.name != "d_datum_nelkul.jpg"
        ]

    def test_csak_a_megadott_talalatokbol_valogat(self, index):
        """A metszet nem hoz be olyan képet, ami nem volt a találatok közt."""
        csak_a_regi = tuple(r for r in all_photos(index) if r.name == "c_regi.jpg")

        metszet = intersect_with_age(index, csak_a_regi, "2025-06-01T00:00:00")

        assert metszet == ()

    def test_ures_talalatra_ures(self, index):
        assert intersect_with_age(index, (), "2000-01-01T00:00:00") == ()


class TestASavFelirata:
    """A három mért állás: 0 nincs, kb. 0,53 `2 months`, 1,0 `2 days`."""

    def test_nulla_allasban_nincs_felirat(self):
        assert kor_szuro.napok(0.0) is None

    def test_a_felirat_ket_szokozzel_kezdodik_a_kettospont_utan(self):
        assert (
            kor_szuro.sav_felirat(70.1, _tr)
            == "Date Range:  Pictures up to 2 months old."
        )

    def test_kb_0_53_ket_honap(self):
        nap = kor_szuro.napok(0.53)

        assert nap is not None
        assert (
            kor_szuro.sav_felirat(nap, _tr)
            == "Date Range:  Pictures up to 2 months old."
        )

    def test_a_jobb_szelso_allas_ket_nap(self):
        nap = kor_szuro.napok(1.0)

        assert nap is not None
        assert (
            kor_szuro.sav_felirat(nap, _tr)
            == "Date Range:  Pictures up to 2 days old."
        )

    def test_az_elotag_a_tr_en_at_megy(self):
        """Az előtag fordítható: a `tr` az erőforrás szövegét kapja."""
        kerdesek: list[str] = []

        def tr(szoveg: str) -> str:
            kerdesek.append(szoveg)
            return szoveg

        kor_szuro.sav_felirat(2.0, tr)

        assert "Date Range: " in kerdesek

    def test_a_ketszeres_szokoz_akkor_is_megvan_ha_a_fordito_mast_ad(self):
        """Az eredeti az erőforrásszöveg után MINDIG tesz egy szóközt."""

        def magyar(szoveg: str) -> str:
            return {"Date Range: ": "Dátumtartomány: "}.get(szoveg, szoveg)

        assert kor_szuro.sav_felirat(2.0, magyar).startswith(
            "Dátumtartomány:  Pictures up to"
        )
