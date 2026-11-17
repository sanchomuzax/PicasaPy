"""A hét ismert felhasználói mappa nem mozgatható (#7108).

Az eredeti Picasa a `0x00995c90` táblából a hét ismert mappát (My Pictures,
Desktop, My Music, My Videos, My Documents, Application Data, Common
Application Data) pontos egyezéssel rendszerútnak veszi: a mozgatás tétele
szürke, és a végrehajtó a célválasztó UTÁN is megáll a `Unable to Move a
System Path` üzenettel. A mappák ALATTI könyvtárak mozgathatók maradnak.

Itt a végrehajtás oldalát mérjük. A Qt szabványos útvonalait (a
`QStandardPaths`-t) a modul fogantyúin át váltjuk ki, hogy a teszt ne függjön
a gép valódi profiljától (#1217, #1375).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QStandardPaths

from picasapy.fileops import known_folders
from picasapy.fileops.move_folder import (
    FolderMoveError,
    is_system_path,
    move_folder,
)
from picasapy.fileops.rename_folder import rename_folder
from support.ismert_mappak_7108 import ISMERT_NEVEK, kiegyenesit, profil_utak

_HELY = QStandardPaths.StandardLocation

_ISMERT_NEVEK = ISMERT_NEVEK


@pytest.fixture
def profil(monkeypatch, tmp_path) -> dict[str, Path]:
    """Hamis felhasználói profil, a Qt szabványos útvonalai erre mutatnak."""
    utak = profil_utak(tmp_path / "profil")
    for ut in utak.values():
        ut.mkdir(parents=True)
    kiegyenesit(monkeypatch, utak)
    return utak


def _kepes_mappa(szulo: Path, nev: str) -> Path:
    mappa = szulo / nev
    mappa.mkdir(parents=True)
    (mappa / "a.jpg").write_bytes(b"kep")
    (mappa / ".picasa.ini").write_text("[a.jpg]\ncaption=x\n", encoding="utf-8")
    return mappa


class TestAHetIsmertMappaRendszerut:
    @pytest.mark.parametrize("nev", _ISMERT_NEVEK)
    def test_az_ismert_mappa_rendszerut(self, profil, nev):
        assert is_system_path(profil[nev]) is True, nev

    @pytest.mark.parametrize("nev", _ISMERT_NEVEK)
    def test_a_vegrehajtas_megall_es_a_forras_erintetlen(
        self, profil, tmp_path, nev
    ):
        cel = tmp_path / "cel"
        cel.mkdir()
        forras = profil[nev]
        (forras / "a.jpg").write_bytes(b"kep")

        with pytest.raises(FolderMoveError, match="Rendszermappa"):
            move_folder(forras, cel)

        assert (forras / "a.jpg").exists()
        assert list(cel.iterdir()) == []

    def test_windowson_a_kisbetus_nagybetus_irasmod_is_egyezik(
        self, profil, monkeypatch
    ):
        """A Windows útvonalai kis- és nagybetűre érzéketlenek (a fogantyú
        a `os.path.normcase` helyettesítője, #1217)."""
        monkeypatch.setattr(known_folders, "_normcase", str.casefold)
        valtozat = profil["Pictures"].parent / "PICTURES"
        assert is_system_path(valtozat) is True

    @pytest.mark.skipif(
        os.name == "nt",
        reason="kis- és nagybetűre érzékeny fájlrendszer kell (a Windows "
        "`Path.resolve()` a valódi írásmódra normalizál)",
    )
    def test_posixon_a_kisbetus_testver_masik_mappa(self, profil, monkeypatch):
        """POSIX alatt a `pictures` MÁS mappa, mint a `Pictures`: pontos
        egyezés kell, nem a kisbetűsített."""
        monkeypatch.setattr(known_folders, "_normcase", lambda szoveg: szoveg)
        valtozat = profil["Pictures"].parent / "pictures"
        assert is_system_path(valtozat) is False


class TestAzAlattukAlloMappakMozgathatok:
    @pytest.mark.parametrize("nev", _ISMERT_NEVEK)
    def test_az_alkonyvtar_nem_rendszerut(self, profil, nev):
        alatta = _kepes_mappa(profil[nev], "nyaralas")
        assert is_system_path(alatta) is False, nev

    @pytest.mark.parametrize("nev", _ISMERT_NEVEK)
    def test_az_alkonyvtar_atmozgathato(self, profil, tmp_path, nev):
        alatta = _kepes_mappa(profil[nev], "nyaralas")
        cel = tmp_path / "cel"
        cel.mkdir()

        uj = move_folder(alatta, cel)

        assert uj == cel / "nyaralas"
        assert (uj / "a.jpg").exists()
        assert (uj / ".picasa.ini").exists()
        assert not alatta.exists()

    def test_a_testver_mappa_nem_vedett(self, profil):
        """Pontos egyezés: a név előtagja vagy utótagja nem elég."""
        for nev in ("Pictures2", "My Pictures", "Pictures-old"):
            testver = profil["Pictures"].parent / nev
            testver.mkdir()
            assert is_system_path(testver) is False, nev


class TestAFelhasznaloiAlkalmazasadat:
    def test_a_roaming_gyoker_a_szervezet_es_alkalmazasnev_nelkul_vedett(
        self, profil
    ):
        """A Qt `AppDataLocation`-ja `…/Roaming/<szervezet>/<alkalmazás>`;
        az eredeti `Application Data` (CSIDL_APPDATA) a `Roaming` maga."""
        assert is_system_path(profil["Roaming"]) is True
        assert is_system_path(profil["Roaming"] / "Szervezet") is False

    def test_a_kozos_alkalmazasadat_a_nem_irhato_bejegyzesbol_jon(self, profil):
        assert is_system_path(profil["ProgramData"]) is True


class TestAFeloldatlanNemVed:
    def test_ures_feloldas_nem_ad_vedett_utat(self, monkeypatch, tmp_path):
        """Az üres szöveg `Path("")`-je a munkakönyvtárra oldódna fel: ha egy
        hely nem oldható fel, a munkakönyvtár sem lehet „ismert mappa"."""
        monkeypatch.setattr(known_folders, "_writable_location", lambda hely: "")
        monkeypatch.setattr(known_folders, "_standard_locations", lambda hely: [])
        monkeypatch.setattr(known_folders, "_alkalmazas_nevek", lambda: ("", ""))
        munka = tmp_path / "munka"
        munka.mkdir()
        monkeypatch.chdir(munka)

        assert known_folders.known_folder_paths() == ()
        assert is_system_path(munka) is False


class TestAMaiVedelemNemSzukul:
    def test_a_home_maga_tovabbra_is_vedett(self):
        assert is_system_path(Path.home()) is True

    def test_a_meghajto_gyokere_tovabbra_is_vedett(self, tmp_path):
        assert is_system_path(Path(tmp_path.anchor)) is True

    @pytest.mark.skipif(os.name == "nt", reason="POSIX-utak")
    def test_a_posix_rendszerutak_tovabbra_is_vedettek(self, profil):
        assert is_system_path("/etc") is True
        assert is_system_path("/usr") is True

    def test_egy_hétköznapi_mappa_nem_rendszerut(self, profil, tmp_path):
        assert is_system_path(_kepes_mappa(tmp_path / "innen", "kepek")) is False


class TestAzAtnevezesNemValtozik:
    """A jegy az ÁTHELYEZÉSRŐL szól: az átnevezés védelme a mai maradt."""

    def test_az_atnevezes_nem_kapja_az_ismert_mappa_tiltast(self, profil):
        assert is_system_path(profil["Pictures"], known_folders=False) is False

    def test_az_ismert_mappa_atnevezese_nem_valtozott(self, profil):
        uj = rename_folder(profil["Pictures"], "Kepek")

        assert uj == profil["Pictures"].with_name("Kepek")
        assert uj.is_dir()

    def test_az_atnevezes_a_rendszerutat_tovabbra_is_visszautasitja(self):
        from picasapy.fileops.rename_folder import FolderRenameError

        with pytest.raises(FolderRenameError, match="Rendszermappa"):
            rename_folder(Path.home(), "masik")


class TestAValodiQtUtvonalak:
    def test_a_kep_mappa_a_valodi_feloldasbol_is_vedett(self):
        """Nincs kiváltás: a modul tényleg a `QStandardPaths`-ot kérdezi."""
        kepek = QStandardPaths.writableLocation(_HELY.PicturesLocation)
        if not kepek:
            pytest.skip("a gépen nincs képmappa")
        assert Path(kepek).resolve() in {
            Path(ut).resolve() for ut in known_folders.known_folder_paths()
        }
