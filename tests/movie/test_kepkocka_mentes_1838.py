"""#1838 — a videóból mentett képkocka (`capture_frame`).

Az eredeti Picasa videó-vezérlősávján a `capture_frame` a **Rögzített
videoklipek** mappába ment egy **JPEG**-et, és a nevet a `%s-%03lu`
egyediesítővel teszi ütközésmentessé (`docs/specs/
picasa-menu-parancsok-viselkedes.md` 58.3/64):

* a sorszám **kötőjeles, háromjegyű**, nullákkal feltöltve;
* a számláló **`0x1000` = 4096**-ig megy, és a ciklusfeltétel a létezés;
* az egyediesítő a **kiterjesztést leválasztva** dolgozik — a sorszám a
  név VÉGÉRE kerül, nem a kiterjesztés mögé.

⚠️ Aki a kollázs/film `output_path()`-át emelné át ide, rossz nevet adna:
az `%s%lu` (szóköz és kötőjel nélküli) minta MÁS funkcióé.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.movie.frame_capture import (
    KEPKOCKA_KITERJESZTES,
    MAX_SORSZAM,
    egyedi_utvonal,
    kepkocka_alapneve,
    mentsd_a_kepkockat,
)


class TestEgyediUtvonal:
    def test_szabad_nev_valtozatlan(self, tmp_path):
        assert egyedi_utvonal(tmp_path, "klip") == tmp_path / "klip.jpg"

    def test_utkozesnel_kotojeles_haromjegyu_sorszam(self, tmp_path):
        (tmp_path / "klip.jpg").write_bytes(b"x")
        assert egyedi_utvonal(tmp_path, "klip") == tmp_path / "klip-001.jpg"

    def test_a_sorszam_tovabb_no(self, tmp_path):
        (tmp_path / "klip.jpg").write_bytes(b"x")
        for sorszam in range(1, 4):
            (tmp_path / f"klip-{sorszam:03d}.jpg").write_bytes(b"x")
        assert egyedi_utvonal(tmp_path, "klip") == tmp_path / "klip-004.jpg"

    def test_a_sorszam_a_nev_vegere_kerul_nem_a_kiterjesztes_moge(self, tmp_path):
        (tmp_path / "klip.jpg").write_bytes(b"x")
        eredmeny = egyedi_utvonal(tmp_path, "klip")
        assert eredmeny.suffix == KEPKOCKA_KITERJESZTES
        assert eredmeny.stem.endswith("-001")

    def test_a_szamlalo_4096_nal_megall(self, tmp_path, monkeypatch):
        """A natív ciklus `0x1000`-ig emel; efölött nincs név, tehát hiba —
        nem néma felülírás."""
        monkeypatch.setattr("picasapy.movie.frame_capture.MAX_SORSZAM", 3)
        (tmp_path / "klip.jpg").write_bytes(b"x")
        for sorszam in range(1, 4):
            (tmp_path / f"klip-{sorszam:03d}.jpg").write_bytes(b"x")
        with pytest.raises(ValueError):
            egyedi_utvonal(tmp_path, "klip")

    def test_a_hataert_ismerjuk(self):
        assert MAX_SORSZAM == 4096


class TestAlapnev:
    def test_a_videó_nevebol_jon(self):
        assert kepkocka_alapneve("/media/nyaralas.MOV") == "nyaralas"

    def test_a_tiltott_karakterek_kiesnek(self):
        assert "/" not in kepkocka_alapneve("/media/a/b:c*d.mp4")

    def test_ures_nevre_tartalek(self):
        assert kepkocka_alapneve("") != ""


class TestMentes:
    def test_a_kepkocka_jpeg_kent_kerul_a_mappaba(self, tmp_path):
        kep = np.zeros((8, 12, 3), dtype=np.uint8)
        kep[..., 0] = 200  # RGB-bemenet: vörös csatorna
        cel = mentsd_a_kepkockat(kep, tmp_path, "klip")
        assert cel.exists()
        assert cel.suffix == ".jpg"

    def test_a_mappa_letrejon_ha_nincs(self, tmp_path):
        kep = np.zeros((4, 4, 3), dtype=np.uint8)
        cel = mentsd_a_kepkockat(kep, tmp_path / "uj" / "melyebb", "klip")
        assert cel.exists()

    def test_ket_mentes_nem_irja_felul_egymast(self, tmp_path):
        kep = np.zeros((4, 4, 3), dtype=np.uint8)
        elso = mentsd_a_kepkockat(kep, tmp_path, "klip")
        masodik = mentsd_a_kepkockat(kep, tmp_path, "klip")
        assert elso != masodik
        assert elso.exists() and masodik.exists()

    def test_a_szinsorrend_megmarad(self, tmp_path):
        """A render-réteg konvenciója RGB; a lemezre írás BGR-t vár —
        ha a kettő felcserélődik, a vörös kék lesz."""
        from picasapy.lazy_cv2 import cv2

        kep = np.zeros((6, 6, 3), dtype=np.uint8)
        kep[..., 0] = 255
        cel = mentsd_a_kepkockat(kep, tmp_path, "klip")
        vissza = cv2.imread(str(cel))  # BGR
        assert int(vissza[..., 2].mean()) > 200, "a vörös csatorna elveszett"
        assert int(vissza[..., 0].mean()) < 60
