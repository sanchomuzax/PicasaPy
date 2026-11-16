"""#7079: a keresősáv szövegei az eredeti szövegtár szerintiek, ezres tagolással.

Eredeti (`docs/specs/paritas-ellenorzes.md`, #7072 E4/E9): a sáv szövege
`CThumbUI::searchmatchstr` (`Search results for "%s"`), `CThumbUI::nomatch`
(`No matches`), a gombok szavai (`sfaces`, `sstarred`, `smovies`, `sgeotag`) a
`CThumbUI::sresults` (`%d results: `) sor után, és a darabszám 1000-től tagolt.

Amit ez a fájl NEM mér: azt, hogy a sáv a képernyőn a helyén látszik-e (a
`searchresult` elem helye Colab-képre vár, ld. Nyitott: `0x005715D0`); a
kirajzolt színt és a valódi kattintásos utat a
`qml_functional/test_keresomezo_szine_7079.py` méri.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from PySide6.QtCore import QLocale

from picasapy.app import formatting
from picasapy.app.formatting_search_bar import group_digits, search_bar_text


def _tr(text: str) -> str:
    return text


def _hu() -> QLocale:
    return QLocale(QLocale.Language.Hungarian, QLocale.Country.Hungary)


def _en() -> QLocale:
    return QLocale(QLocale.Language.English, QLocale.Country.UnitedStates)


def _sav(**kwargs) -> str:
    alap = dict(
        view_mode="search",
        query="",
        search_count=0,
        shown_count=0,
        status="",
        locale=_en(),
        tr=_tr,
    )
    alap.update(kwargs)
    return search_bar_text(**alap)


class TestEzresTagolas:
    @pytest.mark.parametrize(
        ("szam", "vart"),
        [(0, "0"), (7, "7"), (999, "999"), (1000, "1,000"), (1234, "1,234"),
         (12345, "12,345"), (1234567, "1,234,567")],
    )
    def test_angol_vesszovel_tagol(self, szam, vart):
        assert group_digits(szam, _en()) == vart

    def test_magyarul_az_ezer_is_tagolt(self):
        # A Qt magyar területi beállítása az 1000-1999 között NEM tagol
        # (CLDR: legalább két számjegy a csoport előtt), ezért a sima
        # `QLocale.toString` itt kevés: a #7079 szerint az 1000 fölött
        # tagolni kell.
        elvalaszto = _hu().groupSeparator()
        assert elvalaszto
        assert group_digits(1234, _hu()) == f"1{elvalaszto}234"
        assert group_digits(12345, _hu()) == f"12{elvalaszto}345"
        assert group_digits(999, _hu()) == "999"

    def test_c_helyi_beallitassal_is_tagol(self):
        # A C helyi beállításnak `OmitGroupSeparator` az alapja; a teszt- és
        # CI-környezet `QLocale()`-ja ilyen is lehet.
        assert group_digits(1234, QLocale.c()) == "1,234"

    def test_nem_negativ_szamot_is_helyesen_ir(self):
        assert group_digits(-1234, _en()) == "-1,234"


class TestKeresesiSavSzoveg:
    def test_talalatnal_az_eredeti_fejlec_a_kifejezessel(self):
        assert (
            _sav(query="naplemente", search_count=3, shown_count=3)
            == 'Search results for "naplemente"'
        )

    def test_a_darabszam_nem_kerul_a_fejlecbe(self):
        # A `CThumbUI::searchmatch` (` (%d matches)`) kulcsra az EXE-ben nincs
        # hivatkozó literál: a PicasaPy régi `(%2)` utótagjának nincs párja.
        szoveg = _sav(query="a", search_count=1234, shown_count=1234)
        assert "1,234" not in szoveg and "(" not in szoveg

    def test_nincs_talalat_az_eredeti_nincs_talalat_szoveg(self):
        assert _sav(query="zzz", search_count=0, shown_count=0) == "No matches"

    def test_a_kifejezes_helyorzo_jellegu_reszei_nem_cserelodnek(self):
        # `%2` a felhasználó szövegében maradjon betű szerint.
        assert (
            _sav(query="50% %2 %1", search_count=1, shown_count=1)
            == 'Search results for "50% %2 %1"'
        )

    def test_a_fordito_a_hivatalos_sablont_kapja(self):
        kapott: list[str] = []

        def tr(szoveg: str) -> str:
            kapott.append(szoveg)
            return {"Search results for \"%1\"": "Találatok a(z) \"%1\" kifejezésre"}.get(
                szoveg, szoveg
            )

        szoveg = _sav(query="kutya", search_count=2, shown_count=2, tr=tr)
        assert szoveg == 'Találatok a(z) "kutya" kifejezésre'
        assert kapott == ['Search results for "%1"']

    def test_a_nincs_talalat_a_forditotol_jon(self):
        szoveg = _sav(
            query="zzz", tr=lambda s: "Nincs találat" if s == "No matches" else s
        )
        assert szoveg == "Nincs találat"


class TestSzuroGombSor:
    @pytest.mark.parametrize(
        ("nezet", "szo"),
        [("faces", "faces"), ("starred", "starred"), ("videos", "movies"),
         ("geo", "geotagged")],
    )
    def test_gombos_szuro_a_talalatszam_es_a_gomb_szava(self, nezet, szo):
        assert (
            _sav(view_mode=nezet, shown_count=5, status="x") == f"5 results: {szo}"
        )

    def test_a_gombsor_darabszama_is_tagolt(self):
        assert _sav(view_mode="starred", shown_count=1234) == "1,234 results: starred"

    def test_a_sresults_sablon_a_forditotol_jon(self):
        szoveg = _sav(
            view_mode="faces",
            shown_count=1234,
            locale=_hu(),
            tr=lambda s: {"%1 results: ": "%1 találat: ", "faces": "arc"}.get(s, s),
        )
        elvalaszto = _hu().groupSeparator()
        assert szoveg == f"1{elvalaszto}234 találat: arc"

    def test_ismeretlen_nezetnel_a_meglevo_allapotszoveg_marad(self):
        # A viselkedést nem változtatjuk: másik szűrőnél (album, életkor, hasonló)
        # továbbra is a zöld sáv szövege látszik a keresési beállításokban.
        assert (
            _sav(view_mode="album", status="2 folders / 5 pictures visible")
            == "2 folders / 5 pictures visible"
        )

    def test_mappanezetben_ures_marad(self):
        assert _sav(view_mode="folder", status="") == ""

    def test_keresesi_nezet_kifejezes_nelkul_a_meglevo_szoveget_adja(self):
        # Védőháló: keresési mód üres kifejezéssel nem fordulhat elő, de ha mégis,
        # nem szabad `Search results for ""`-t kiírni.
        assert _sav(query="", status="") == ""


class TestAZoldSavDarabszamaTagolt:
    @staticmethod
    def _rekordok(darab: int, mappak: int):
        return [
            SimpleNamespace(folder_path=f"/f{i % mappak}", size=1024)
            for i in range(darab)
        ]

    def test_ezer_fole_a_kepek_es_a_mappak_szama_tagolt(self):
        szoveg = formatting.filter_status_text(
            self._rekordok(1234, 1100), 0.5, _en(), _tr
        )
        assert szoveg.startswith("1,100 folders / 1,234 pictures visible")

    def test_ezer_alatt_valtozatlan(self):
        szoveg = formatting.filter_status_text(
            self._rekordok(999, 3), 0.5, _en(), _tr
        )
        assert szoveg.startswith("3 folders / 999 pictures visible")
