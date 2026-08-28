"""Új mappa létrehozása áthelyezéshez — a Fájl ▸ „Áthelyezés új mappába…"
magja (#1614).

A névellenőrzés a fájlrendszertől FÜGGETLEN, hogy a Windows-tiltott
karakterek (`<>:"/\\|?*`) Linuxon futva is kiszűrődjenek — enélkül egy itt
létrehozott mappa a NAS-on át futó eredeti Picasa vagy egy Windowsra
átvitt könyvtár számára használhatatlan volna (#1700 ugyanezt a
hibaosztályt fogta meg egy másik teszten).
"""

from __future__ import annotations

import pytest

from picasapy.fileops.new_folder import (
    InvalidFolderNameError,
    create_folder_for_move,
    validate_folder_name,
)

#: A brief által megkövetelt Windows-tiltott karakterkészlet — egyben a
#: mutációs bizonyíték (d) tétele: ha ezek bármelyike átcsúszna, ez a
#: teszt piros lenne.
_TILTOTT_KARAKTEREK = list('<>:"/\\|?*')


class TestValidateFolderName:
    def test_ures_nev_ervenytelen(self):
        with pytest.raises(InvalidFolderNameError):
            validate_folder_name("")

    def test_csak_szokoz_ervenytelen(self):
        with pytest.raises(InvalidFolderNameError):
            validate_folder_name("   ")

    @pytest.mark.parametrize("karakter", _TILTOTT_KARAKTEREK)
    def test_tiltott_karakter_ervenytelen(self, karakter):
        with pytest.raises(InvalidFolderNameError):
            validate_folder_name(f"nyaralás{karakter}2026")

    def test_ervenyes_nev_trimmelve_ter_vissza(self):
        assert validate_folder_name("  Nyaralás 2026  ") == "Nyaralás 2026"

    def test_ekezetes_es_szokozos_nev_ervenyes(self):
        # a magyar ékezet és a belső szóköz NEM tiltott — csak a Windows
        # fájlrendszer-karakterek azok
        assert validate_folder_name("Őszi túra") == "Őszi túra"


class TestCreateFolderForMove:
    def test_letrehozza_az_uj_mappat(self, tmp_path):
        target = create_folder_for_move(tmp_path, "Nyaralás")
        assert target == tmp_path / "Nyaralás"
        assert target.is_dir()

    def test_mar_letezo_mappanal_hibat_dob(self, tmp_path):
        (tmp_path / "Nyaralás").mkdir()
        with pytest.raises(FileExistsError):
            create_folder_for_move(tmp_path, "Nyaralás")
        # a meglévő mappa tartalma érintetlen marad — nem próbáljuk
        # felülírni vagy törölni

    def test_azonos_nevu_fajlnal_is_hibat_dob(self, tmp_path):
        (tmp_path / "Nyaralás").write_text("nem mappa", encoding="utf-8")
        with pytest.raises(FileExistsError):
            create_folder_for_move(tmp_path, "Nyaralás")
