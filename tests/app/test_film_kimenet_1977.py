"""#1977: a mozgófilm KIMENETE — célmappa, fájlnév, sorszámozás, projekt-jelölés.

Az eredetiben a „Mozgófilm létrehozása" **nem kér célfájlt**: maga dönti
el a mappát, a nevet és a kiterjesztést, és a mappát projekt-mappaként be
is jelöli. Mérve (`docs/specs/picasa-create-features.md` 2.6/c):

| mit | hol |
|---|---|
| célmappa `My Pictures` → `Picasa` → honosított `Movies` | `0x0061cf20`, `0x00c9ce3c` |
| tartalék `My Videos`, ha a mappa nem hozható létre | `0x00620af9`–`0x00620b1d` |
| a mappa `.picasa.ini`-t kap `P2category=Projects (internal)` sorral | `0x0061d005` → `0x00445a30` |
| alapnév `slideshowmovie` / `diavetites_jellegu_film` | `CMakeMoviePanel::deffilename` |
| tiltott karakterek `\\ / : * ? " < > \\|` | `0x00620b61` → `0x009946f0` |
| sorszámozás `%s%lu` (szóköz nélkül) | `0x00993030` → `0x00992ed0` |

⚠️ A **kiterjesztés nálunk `.mp4`**, nem `.wmv`: a `wmvcore.dll` Linuxon
nincs. Ez KIMONDOTT, tudatos eltérés (a jegy 9. pontja).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.app.movie_output import (
    FILENAME_STEM,
    output_dir,
    output_path,
    safe_stem,
    tartalek_mappa,
)


class TestAzAlapnev:
    def test_a_MERT_magyar_alapnev(self):
        """`CMakeMoviePanel::deffilename` magyar oszlopa."""
        assert FILENAME_STEM == "diavetites_jellegu_film"

    def test_ures_cimre_az_alapnev_jon(self):
        assert safe_stem("") == FILENAME_STEM
        assert safe_stem(None) == FILENAME_STEM

    def test_a_tiltott_karakterek_kiesnek(self):
        assert safe_stem('nyar/2025:*?"<>|') == "nyar2025"

    def test_a_csak_pontokbol_allo_cim_is_az_alapnevre_esik(self):
        assert safe_stem("...") == FILENAME_STEM


class TestACelmappa:
    def test_a_beallitott_mappa_nyer(self, tmp_path):
        assert output_dir(str(tmp_path / "sajat")) == tmp_path / "sajat"

    def test_beallitas_nelkul_a_Picasa_alatti_honos_mappa(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "picasapy.app.movie_output.pictures_dir", lambda: tmp_path
        )
        assert output_dir(None, language="hu") == tmp_path / "Picasa" / "Filmek"
        assert output_dir(None, language="en") == tmp_path / "Picasa" / "Movies"

    def test_a_MEGLEVO_mas_nyelvu_mappa_nyer(self, tmp_path, monkeypatch):
        """#1131: nem nyitunk néma harmadikat a régi mellé. A tulajdonos
        gyűjteményében `Movies`, `Filmek` ÉS `Mozgófilmek` áll egymás
        mellett."""
        monkeypatch.setattr(
            "picasapy.app.movie_output.pictures_dir", lambda: tmp_path
        )
        (tmp_path / "Picasa" / "Mozgófilmek").mkdir(parents=True)
        assert output_dir(None, language="hu") == tmp_path / "Picasa" / "Mozgófilmek"


class TestACelfajl:
    def test_alap_eset_mp4(self, tmp_path):
        assert output_path(tmp_path, "Nyaralás") == tmp_path / "Nyaralás.mp4"

    def test_utkozeskor_SZOKOZ_NELKULI_sorszam(self, tmp_path):
        (tmp_path / "Nyaralás.mp4").write_bytes(b"")
        assert output_path(tmp_path, "Nyaralás") == tmp_path / "Nyaralás1.mp4"
        (tmp_path / "Nyaralás1.mp4").write_bytes(b"")
        assert output_path(tmp_path, "Nyaralás") == tmp_path / "Nyaralás2.mp4"

    def test_ures_cimre_az_alapnev(self, tmp_path):
        assert output_path(tmp_path, "") == tmp_path / f"{FILENAME_STEM}.mp4"


class TestATartalek:
    def test_ha_a_mappa_LETREHOZHATO_azt_adja(self, tmp_path):
        cel = tmp_path / "Picasa" / "Filmek"
        assert tartalek_mappa(cel) == cel
        assert cel.is_dir()

    def test_ha_NEM_hozhato_letre_a_rendszer_Videok_mappaja(
        self, tmp_path, monkeypatch
    ):
        """`0x00620af9`–`0x00620b1d`: a tartalék a `My Videos`."""
        videok = tmp_path / "Videók"
        videok.mkdir()
        monkeypatch.setattr(
            "picasapy.app.movie_output._rendszer_videok", lambda: videok
        )
        # fájl a mappa helyén -> a mkdir elbukik
        utban = tmp_path / "utban"
        utban.write_bytes(b"nem mappa")
        assert tartalek_mappa(utban / "Filmek") == videok

    def test_ha_a_tartalek_sincs_meg_KIVETEL_nem_nema_hiba(
        self, tmp_path, monkeypatch
    ):
        monkeypatch.setattr("picasapy.app.movie_output._rendszer_videok", lambda: None)
        utban = tmp_path / "utban2"
        utban.write_bytes(b"nem mappa")
        with pytest.raises(OSError):
            tartalek_mappa(utban / "Filmek")


class TestAProjektJeloles:
    def test_a_mappa_picasa_inije_a_MERT_alakot_kapja(self, tmp_path):
        """A valódi fájl a tulajdonos gyűjteményében pontosan ennyi:
        `[Picasa]` + `P2category=Projects (internal)` — `[encoding]`
        szekció a 67 fájlos korpuszban egyetlen sincs."""
        from picasapy.app.movie_output import write_album_ini

        mappa = tmp_path / "Filmek"
        ut = write_album_ini(mappa, "Filmek")
        szoveg = Path(ut).read_text(encoding="utf-8")
        assert "[Picasa]" in szoveg
        assert "P2category=Projects (internal)" in szoveg
        assert "[encoding]" not in szoveg
