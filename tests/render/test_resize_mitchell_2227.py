"""#2227 — a `Resize` mintavételezője Mitchell–Netravali (B = C = 0,4).

## A lelet

Az eredeti `ResizeImageOperation` alkalmazója (`0x00bc3650`) a végén
ugyanazt a `0x00bcb5e0` segédfüggvényt hívja, amit a
`RotateImageOperation` — az pedig a `ytResampler`-t hívja **explicit**
móddal: lépték = 1 → **0-s (doboz)**, egyébként **3-as
(Mitchell–Netravali, B = C = 0,4)**. A mi kódunk bilineáris volt.

## Amit ezek a próbák mérnek

A Mitchell-mag **negatív oldallebenyt** visel (`B = C = 0,4` mellett a
támasz 1 és 2 között negatív), ezért egy éles élen **túllövést** ad — a
bilineáris és a doboz soha nem lép a bemeneti szélsőértékeken kívülre.
Ez az a különbség, ami a magot azonosítja, nem a „valamivel élesebb".

⚠️ **A KICSINYÍTÉSI viselkedés nincs mérve.** A bináris annyit árul el,
hogy a mód 3-as; hogy a mag a léptékkel nyúlik-e (élsimítás), az NYITOTT
kérdés. Az implementáció a szokásos, nyújtott magot használja, és ezt a
docstring kimondja.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.glimmer_ops import resize_image


def _elkep(szelesseg: int = 16, magassag: int = 16) -> np.ndarray:
    """Bal fele fekete, jobb fele fehér — egyetlen függőleges él."""
    kep = np.zeros((magassag, szelesseg, 3), dtype=np.uint8)
    kep[:, szelesseg // 2:] = 255
    return kep


class TestALeptekEgyDOBOZ:
    """`lépték = 1 → 0-s (doboz)` — mérve. Doboz maggal ez azonosság."""

    def test_azonos_meretre_VALTOZATLAN(self):
        kep = np.random.default_rng(7).integers(
            0, 256, (24, 32, 3), dtype=np.uint8
        )
        assert np.array_equal(resize_image(kep, 32, 24), kep)

    def test_csak_az_EGYIK_tengely_valtozatlan(self):
        """A lépték tengelyenként számolódik (`src/dst`, `0x00bc3700`)."""
        kep = _elkep(16, 16)
        eredmeny = resize_image(kep, 16, 32)
        assert eredmeny.shape == (32, 16, 3)
        # a vízszintes tengely léptéke 1 → az él pontosan ott marad
        assert set(np.unique(eredmeny[:, :8])) == {0}
        assert set(np.unique(eredmeny[:, 8:])) == {255}


class TestAMitchellTULLOVES:
    """A magot a negatív oldallebeny azonosítja."""

    def test_nagyitaskor_TULLO_a_bemeneti_tartomanyon(self):
        """SZÜRKE él, hogy a 0/255 levágás ne rejtse el a túllövést.

        A negatív oldallebeny miatt az él két oldalán a kimenet a bemeneti
        `[64, 192]` tartományon KÍVÜLRE lép. Bilineárisnál és doboznál ez
        lehetetlen: azok konvex kombinációt adnak."""
        kep = np.full((16, 16, 3), 64, dtype=np.uint8)
        kep[:, 8:] = 192
        eredmeny = resize_image(kep, 64, 16).astype(np.int32)
        assert eredmeny.min() < 64, (
            f"nincs alullövés (min = {eredmeny.min()}, a bemenet alja 64) — "
            f"a mag nem visel negatív oldallebenyt"
        )
        assert eredmeny.max() > 192, (
            f"nincs túllövés (max = {eredmeny.max()}, a bemenet teteje 192)"
        )

    def test_a_BILINEARIS_kimenete_MAS(self):
        """Ha valaki visszaírja bilineárisra, ez a próba elbukik."""
        import cv2

        kep = _elkep(16, 16)
        mienk = resize_image(kep, 64, 16)
        bilin = cv2.resize(kep, (64, 16), interpolation=cv2.INTER_LINEAR)
        assert not np.array_equal(mienk, bilin), (
            "a kimenet a bilineárissal azonos — a Mitchell-mag nincs bekötve"
        )

    def test_a_KOBOS_kimenete_is_MAS(self):
        """Az OpenCV `INTER_CUBIC` Catmull–Rom-szerű (a = −0,75), NEM
        Mitchell B = C = 0,4 — a kényelmes helyettesítés kizárva."""
        import cv2

        kep = _elkep(16, 16)
        mienk = resize_image(kep, 64, 16)
        kobos = cv2.resize(kep, (64, 16), interpolation=cv2.INTER_CUBIC)
        assert not np.array_equal(mienk, kobos)


class TestAMagMAGA:
    """A magot közvetlenül is mérjük — a képleten át, nem a kimeneten."""

    def test_a_mag_ertekei_a_KEPLETBOL(self):
        from picasapy.render.glimmer_ops import mitchell_netravali

        # B = C = 0,4:  |x|<1 → (6|x|³ − 10,8|x|² + 5,2)/6
        assert mitchell_netravali(np.array([0.0]))[0] == pytest.approx(
            5.2 / 6, abs=1e-9
        )
        assert mitchell_netravali(np.array([1.0]))[0] == pytest.approx(
            (-2.8 + 14.4 - 24 + 12.8) / 6, abs=1e-9
        )
        assert mitchell_netravali(np.array([2.0]))[0] == pytest.approx(
            0.0, abs=1e-9
        )

    def test_a_mag_NEGATIV_az_oldallebenyen(self):
        from picasapy.render.glimmer_ops import mitchell_netravali

        ertekek = mitchell_netravali(np.linspace(1.05, 1.95, 19))
        assert (ertekek < 0).any(), (
            "nincs negatív oldallebeny — ez nem Mitchell B = C = 0,4"
        )


class TestASmoothingAgaMarad:
    def test_smoothing_hamis_a_LEGKOZELEBBI_szomszed(self):
        """⚠️ Ez NEM mérés: a bináris `smoothing=False` ága nincs
        visszafejtve (a 0-s dobozmódot használja-e, vagy tényleg
        legközelebbi szomszédot). A mai viselkedést rögzítjük."""
        import cv2

        kep = _elkep(16, 16)
        assert np.array_equal(
            resize_image(kep, 64, 16, smoothing=False),
            cv2.resize(kep, (64, 16), interpolation=cv2.INTER_NEAREST),
        )
