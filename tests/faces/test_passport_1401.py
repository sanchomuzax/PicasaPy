"""#1401: az Útlevélkép döntési fája és arc-központú kivágása.

`docs/specs/picasa-menu-parancsok-viselkedes.md`, 24. szakasz."""

from __future__ import annotations

from picasapy.faces.passport import (
    MULTIPLE_FACES,
    NO_FACE,
    SINGLE_FACE,
    PixelRect,
    classify_face_count,
    passport_crop_rect,
)


class TestClassifyFaceCount:
    def test_nulla_arc(self):
        assert classify_face_count(0) == NO_FACE

    def test_egy_arc(self):
        assert classify_face_count(1) == SINGLE_FACE

    def test_ket_arc(self):
        assert classify_face_count(2) == MULTIPLE_FACES

    def test_tobb_arc(self):
        assert classify_face_count(5) == MULTIPLE_FACES


class TestPassportCropRect:
    def test_negyzet_kivagas_arc_kozepen_ranagas_nelkul(self):
        """Egy nagy képen, a szélektől távol álló arcnál a kivágás PONTOS
        NÉGYZET, a képlet szerint (fejtér 1/3, váll 0,6) — a számokat úgy
        választottuk, hogy egyetlen osztás se okozzon fél-egészes
        kerekítési kétértelműséget."""
        # arc: 150x150, bal=350, felül=300, jobb=500, alul=450
        rect = passport_crop_rect(
            face_left=350,
            face_top=300,
            face_right=500,
            face_bottom=450,
            image_width=1000,
            image_height=1000,
        )
        # arcMagassag = 150; fent: 150/3=50 -> 300-50=250
        # lent: 150*0.6=90 -> 450+90=540; kivagasMagas = 290
        # kozepX = (350+500)/2 = 425; fel = 290/2 = 145
        # bal = 425-145=280; jobb=425+145=570
        assert rect == PixelRect(left=280, top=250, right=570, bottom=540)
        assert rect.width == rect.height == 290

    def test_kepbe_nem_illeszkedo_arc_fuggetlen_korlatokkal_vagodik(self):
        """A kép bal felső sarkához közeli arcnál a kivágás túllógna a
        határon — a bal/felső oldal 0-ra vágódik, a jobb/alsó oldal
        VÁLTOZATLAN marad: a végeredmény emiatt NEM feltétlenül négyzet
        (ld. a modul docstringjét, 5. lépés, FÜGGETLEN korlátok)."""
        # arc: 150x150, bal=0, felül=10, jobb=150, alul=160
        rect = passport_crop_rect(
            face_left=0,
            face_top=10,
            face_right=150,
            face_bottom=160,
            image_width=1000,
            image_height=1000,
        )
        # arcMagassag = 150; kivagasFent = 10-50=-40; kivagasLent=160+90=250
        # kozepX=(0+150)/2=75; fel=(250-(-40))/2=145
        # bal=75-145=-70 -> 0 ; jobb=75+145=220 (nem vágódik)
        # felul=-40 -> 0 ; alul=250 (nem vágódik)
        assert rect == PixelRect(left=0, top=0, right=220, bottom=250)
        assert rect.width != rect.height

    def test_arc_a_kep_jobb_alsokent_sarkanal_a_jobb_es_also_oldal_vagodik(self):
        """A jobb/alsó szélhez közeli arcnál a jobb/alsó oldal vágódik a
        kép méretére, a bal/felső változatlan marad."""
        rect = passport_crop_rect(
            face_left=900,
            face_top=850,
            face_right=1000,
            face_bottom=950,
            image_width=1000,
            image_height=1000,
        )
        # arcMagassag=100; kivagasFent=850-33.333=816.667->kerekitve 817
        # kivagasLent=950+60=1010; kozepX=(900+1000)/2=950
        # fel=(1010-817)/2=96.5 -> bal=950-96.5=853.5->kerekitve 854 (round-half-to-even? 853.5 -> 854)
        # jobb=950+96.5=1046.5->1046 (banker's rounding) -> vágva 1000-re
        assert rect.right == 1000
        assert rect.bottom == 1000
        assert rect.left < 1000
        assert rect.top < 1000

    def test_arc_koordinatak_nem_egesz_pixelek_is_kifele_kerekednek(self):
        """A felismerő tört (szubpixeles) koordinátákat is adhat — a
        kerekítés a doksinak megfelelően KIFELÉ történik (floor/ceil), nem
        a legközelebbi egészre."""
        rect_szuk = passport_crop_rect(
            face_left=100.2,
            face_top=100.2,
            face_right=199.8,
            face_bottom=199.8,
            image_width=1000,
            image_height=1000,
        )
        rect_egesz = passport_crop_rect(
            face_left=100,
            face_top=100,
            face_right=200,
            face_bottom=200,
            image_width=1000,
            image_height=1000,
        )
        # a tört bemenet kifelé kerekítve UGYANAZT az arc-befoglalót adja,
        # mint a kerek (100..200) bemenet — tehát ugyanaz a kivágás is.
        assert rect_szuk == rect_egesz
