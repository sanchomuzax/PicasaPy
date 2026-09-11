"""#2989: a bal hasáb sor-ikonja EGYETLEN bélyegkép, nem négylapos kupac.

A tulajdonos három felvétele (`research/#2984-indexkepek-mappa-ikonokon/`)
cáfolja a #2049 kupacát ezen a felületen: a négy fotót tartalmazó
`Duplikátumok (4)` sor is **egy sima, tengelypárhuzamos négyszöget** kap.
Mérve az 1. képen (nagyítva, a háttérszíntől eltérő képpontok befoglalója):

| sor | az ikon befoglalója |
|---|---|
| `screenshot` | 17 × 12 px |
| `Hátterek`, `Captures`, `Duplikátumok`, `04-…`, `11-…`, `12-…` | 17 × 15 px |

Tehát a hely **17 × 15**, és a kép ARÁNYTARTÓN fér bele — a szélesebb
képernyőkép alacsonyabb lett, nem torzult. Nincs elforgatás, nincs második
lap, nincs árnyék.

⚠️ A kupac-rajzoló (`thumbs.album_borito`, #2049) **megmarad** — a
`0x00423780` visszafejtése érvényes, csak nem EZ a felület használja.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from picasapy.app.folder_cover_provider import keszits_mappa_boritot
from support.jpeg_factory import make_jpeg


def _kepek(gyoker: Path, darab: int, meret=(120, 90)) -> list[Path]:
    gyoker.mkdir(parents=True, exist_ok=True)
    fajlok = []
    for i in range(darab):
        fajl = gyoker / f"k{i}.jpg"
        make_jpeg(fajl, size=meret)
        fajlok.append(fajl)
    return fajlok


class TestEgyetlenBelyegkep:
    def test_a_NEGY_fotos_mappa_ikonja_ugyanaz_mint_az_egy_fotose(self, tmp_path):
        """MAGVETÉS: ha valaki visszaköti a kupacot, ez a próba bukik.

        A kupac mérete a lapok számával nő (a #2049 mérése szerint
        78×62 … 84×77), tehát négy fotóra MÁS alakot adna, mint egyre.
        """
        negy = _kepek(tmp_path / "negy", 4)
        egy = _kepek(tmp_path / "egy", 1)
        assert (
            keszits_mappa_boritot(str(tmp_path / "negy"), negy).shape
            == keszits_mappa_boritot(str(tmp_path / "egy"), egy).shape
        ), "a négy fotós mappa ikonja eltér — kupac készült"

    def test_az_aranyt_TARTJA(self, tmp_path):
        fajlok = _kepek(tmp_path / "m", 1, meret=(120, 90))
        borito = keszits_mappa_boritot(str(tmp_path / "m"), fajlok)
        magassag, szelesseg = borito.shape[:2]
        assert abs(szelesseg / magassag - 120 / 90) < 0.02

    def test_az_allo_kep_arany_is_megmarad(self, tmp_path):
        fajlok = _kepek(tmp_path / "m", 1, meret=(90, 120))
        borito = keszits_mappa_boritot(str(tmp_path / "m"), fajlok)
        magassag, szelesseg = borito.shape[:2]
        assert magassag > szelesseg, "az álló kép fekvővé vált"

    def test_TELJESEN_atlatszatlan_nincs_kupac_hattere(self, tmp_path):
        """A kupac körül átlátszó sarkok maradnak; egyetlen kép esetén nem."""
        fajlok = _kepek(tmp_path / "m", 3)
        borito = keszits_mappa_boritot(str(tmp_path / "m"), fajlok)
        assert np.all(borito[:, :, 3] == 255), "átlátszó képpont — kupac-háttér"

    def test_a_LISTA_ELSO_olvashato_fajlja_kerul_bele(self, tmp_path):
        mappa = tmp_path / "m"
        mappa.mkdir()
        elso = mappa / "a.jpg"
        make_jpeg(elso, size=(160, 40))
        masodik = mappa / "b.jpg"
        make_jpeg(masodik, size=(40, 160))
        borito = keszits_mappa_boritot(str(mappa), [elso, masodik])
        magassag, szelesseg = borito.shape[:2]
        assert szelesseg > magassag, "nem az első fájl került az ikonra"

    def test_a_ROMLOTT_elso_fajl_utan_a_kovetkezo_jon(self, tmp_path):
        mappa = tmp_path / "m"
        mappa.mkdir()
        romlott = mappa / "romlott.jpg"
        romlott.write_bytes(b"ez nem JPEG")
        jo = mappa / "jo.jpg"
        make_jpeg(jo, size=(160, 40))
        borito = keszits_mappa_boritot(str(mappa), [romlott, jo])
        assert borito is not None, "a romlott fájl elnyelte a jó képet is"

    def test_kep_nelkul_nincs_ikon(self, tmp_path):
        assert keszits_mappa_boritot(str(tmp_path), []) is None
