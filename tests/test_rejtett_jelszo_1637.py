"""#1637: a »Rejtett mappák« jelszava — Picasa-kompatibilis ÉS modern alak.

## A tulajdonos döntése (2026-09-03)

> „A régi kompatibilitás maradjon meg, és legyen egy modern változat is,
> plusz feature-ként."

Tehát KÉT alakot kell tudni, és az ellenőrzésnek MINDKETTŐT el kell fogadnia
— különben egy Picasában beállított jelszó kizárná a felhasználót a saját
mappáiból.

## Az eredeti alakja — MÉRVE a binárisból

A windowsos Picasa a jelszó **hex-kódolt MD5**-ét tárolja:

| lépés | cím |
|---|---|
| a jelszó-beállító ág | `0x005eb910` |
| MD5 (mind a négy init-konstans) | `0x00ab3640` (`0x67452301`, `0xEFCDAB89`, `0x98BADCFE`, `0x10325476`) |
| 16 bájt → 32 kisbetűs hex | `0x00a4d420`, ábécé `0x00cd8f5c` = `"0123456789abcdef"` |

⚠️ Ez **sózatlan MD5** — mai mércével gyenge. Ezért van a modern alak is.
"""

from __future__ import annotations

import pytest

from picasapy.hidden_password import (
    MODERN_ELOTAG,
    egyezik,
    modern_alak_e,
    modern_lenyomat,
    picasa_lenyomat,
)


class TestPicasaAlak:
    @pytest.mark.parametrize(
        ("jelszo", "vart"),
        [
            # ismert MD5-ek — a Picasa pontosan ezeket írja ki
            ("", "d41d8cd98f00b204e9800998ecf8427e"),
            ("a", "0cc175b9c0f1b6a831c399e269772661"),
            ("abc", "900150983cd24fb0d6963f7d28e17f72"),
            ("titok", "201016e8206a5f42aa527090511504d5"),
        ],
    )
    def test_a_MERT_alakot_adja(self, jelszo, vart):
        assert picasa_lenyomat(jelszo) == vart

    def test_pontosan_32_kisbetus_hex(self):
        h = picasa_lenyomat("Akármi")
        assert len(h) == 32
        assert h == h.lower()
        assert all(k in "0123456789abcdef" for k in h)

    def test_NEM_modern_alaknak_latszik(self):
        assert not modern_alak_e(picasa_lenyomat("titok"))


class TestModernAlak:
    def test_felismerheto_elotag(self):
        h = modern_lenyomat("titok")
        assert h.startswith(MODERN_ELOTAG)
        assert modern_alak_e(h)

    def test_UGYANAZ_a_jelszo_MAS_lenyomatot_ad(self):
        """Sózott: két beállítás nem adhat azonos tárolt értéket, különben
        a lenyomatból látszana, hogy két gyűjteménynek ugyanaz a jelszava."""
        assert modern_lenyomat("titok") != modern_lenyomat("titok")

    def test_a_Picasa_NEM_ertelmezi_felre(self):
        """A modern alak nem 32 hex jegy, tehát a windowsos Picasa
        összehasonlítása biztosan nem talál egyezést — nem nyit ki véletlenül."""
        h = modern_lenyomat("titok")
        assert len(h) != 32
        assert not all(k in "0123456789abcdef" for k in h)


class TestEllenorzes:
    @pytest.mark.parametrize("keszit", [picasa_lenyomat, modern_lenyomat])
    def test_MINDKET_alakot_elfogadja(self, keszit):
        assert egyezik(keszit("titok"), "titok")

    @pytest.mark.parametrize("keszit", [picasa_lenyomat, modern_lenyomat])
    def test_a_rossz_jelszot_elutasitja(self, keszit):
        assert not egyezik(keszit("titok"), "Titok")
        assert not egyezik(keszit("titok"), "")

    def test_ures_tarolt_ertek_semmit_nem_nyit(self):
        """Nincs beállított jelszó → nem a »bármi jó« ág, hanem a hívó dolga
        eldönteni, hogy egyáltalán kérjen-e jelszót."""
        assert not egyezik("", "titok")
        assert not egyezik("", "")

    def test_ertelmetlen_tarolt_ertek_nem_omlik_ossze(self):
        for szemet in ("nem-hex", "abc", MODERN_ELOTAG, MODERN_ELOTAG + "x$y$z"):
            assert not egyezik(szemet, "titok")

    def test_a_MODERN_ellenorzes_nem_fuggetlen_a_sotol(self):
        """Ellenkező irányú őr: ha a só figyelmen kívül maradna, két külön
        lenyomat közül a másikkal is nyílna."""
        a = modern_lenyomat("titok")
        b = modern_lenyomat("titok")
        assert egyezik(a, "titok") and egyezik(b, "titok")
        assert a != b
