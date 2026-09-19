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

⭐ **A KICSINYÍTÉSI viselkedés MÉRVE van** (#3321). Az eredeti
újramintavevő 3-as ága (`0x00a3f660`) a mag alap-tartósugarát a
LÉPTÉKKEL OSZTJA (`0x00a3f745`–`0x00a3f74b`): `scale < 1` mellett a mag a
forrástérben szélesedik. A mi `max(1, skala)`-nyújtásunk tehát nem
„szokásos feltevés", hanem a mért mechanizmus.

⚠️ Amit ez NEM bizonyít: a képpontra azonos kimenetet az eredetivel — a
mechanizmus statikus bizonyíték, a golden-egyezés külön mérési feladat.
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


class TestAKicsinyitesiNyujtas:
    """#3321: a mag KICSINYÍTÉSKOR a léptékkel nyúlik — mérve.

    Az eredeti 3-as ága (`0x00a3f660`) a mag alap-tartósugarát a léptékkel
    osztja (`0x00a3f745`–`0x00a3f74b`). A hatás élsimítás: `scale < 1`
    mellett a szélesebb mag ÁTLAGOL, tehát a Nyquist-határon lévő minta
    (egy képpont széles csíkok) nem alias-ol vissza.

    A próba ezt a HATÁST méri, és a kontroll megmutatja, hogy az állításnak
    van foga: ugyanaz a mag NYÚJTÁS NÉLKÜL látványos aliast ad.
    """

    @staticmethod
    def _csikos(szelesseg: int = 64, magassag: int = 8) -> np.ndarray:
        """Egy képpont széles, függőleges fekete-fehér csíkok (Nyquist)."""
        kep = np.zeros((magassag, szelesseg, 3), dtype=np.uint8)
        kep[:, ::2] = 255
        return kep

    @staticmethod
    def _nyujtas_nelkul(be_meret: int, ki_meret: int):
        """A KONTROLL súlyai: ugyanaz a mag, de rögzített, 1-es nyújtással."""
        from picasapy.render.glimmer_ops import mitchell_netravali

        skala = be_meret / ki_meret
        tamasz = 2.0
        kozep = (np.arange(ki_meret) + 0.5) * skala - 0.5
        elso = np.ceil(kozep - tamasz).astype(np.int64)
        ablak = int(np.ceil(2 * tamasz)) + 1
        indexek = elso[:, None] + np.arange(ablak)[None, :]
        sulyok = mitchell_netravali(kozep[:, None] - indexek)
        osszeg = sulyok.sum(axis=1, keepdims=True)
        osszeg[osszeg == 0] = 1.0
        return np.clip(indexek, 0, be_meret - 1), sulyok / osszeg

    def _kontroll_sor(self, kep: np.ndarray, ki_szelesseg: int) -> np.ndarray:
        indexek, sulyok = self._nyujtas_nelkul(kep.shape[1], ki_szelesseg)
        sor = kep[0, :, 0].astype(np.float64)
        return (sor[indexek] * sulyok).sum(axis=1)

    #: A 64 → 9 arány SZÁNDÉKOS. A kettő hatványainál (64 → 8, 64 → 16) a
    #: mintavételi fázis szimmetrikus a periódus-2 csíkokra, ezért a
    #: NYÚJTÁS NÉLKÜLI kontroll is pontosan 127,5-öt ad (szórás 0,0) — a
    #: próba ott vakon átmenne. Mérve: 64 → 9-nél a kontroll szórása 65,2,
    #: a nyújtotté 9,8.
    KI_SZELESSEG = 9

    def test_a_kicsinyites_ATLAGOL_nem_aliasol(self):
        """A mért nyújtással a csíkok egyenletes szürkévé olvadnak."""
        kep = self._csikos()
        kicsi = resize_image(kep, self.KI_SZELESSEG, 8)
        sor = kicsi[0, :, 0].astype(np.float64)
        assert sor.std() < 12.0, (
            f"a kimenet szórása {sor.std():.1f} — a szélesebb magnak "
            "át kellene átlagolnia a csíkokat")
        assert 96.0 < sor.mean() < 160.0, (
            f"a fekete-fehér csíkok átlaga {sor.mean():.1f}, a várt "
            "középszürke helyett")

    def test_a_NYUJTAS_NELKULI_mag_ELBUKNA(self):
        """Ellenpróba: az állításnak van foga.

        Ugyanaz a Mitchell-mag, rögzített 2-es támasszal — a kimenet a
        csíkokra ül rá, tehát nagy szórást ad. Ha ez a kontroll egyszer
        „átmenne", az azt jelentené, hogy a fenti próba bármit elfogad.
        """
        kep = self._csikos()
        sor = self._kontroll_sor(kep, self.KI_SZELESSEG)
        assert sor.std() > 50.0, (
            f"a nyújtás nélküli mag szórása {sor.std():.1f} — a kontroll "
            "nem különbözteti meg a két magot")

    def test_a_sulyok_a_MERT_nyujtast_hasznaljak(self):
        """A súlyablak szélessége a léptékkel nő — a mechanizmus maga."""
        from picasapy.render.glimmer_ops import _mintavetel_sulyok

        _, kicsi = _mintavetel_sulyok(64, 8)
        _, azonos = _mintavetel_sulyok(8, 8)
        assert kicsi.shape[1] > azonos.shape[1], (
            "kicsinyítéskor a mag NEM szélesedett — a mért osztás hiányzik")

    def test_nagyitaskor_NINCS_nyujtas(self):
        """A mért képlet `max(1, skala)`: `scale > 1` esetén a mag marad."""
        from picasapy.render.glimmer_ops import _mintavetel_sulyok

        _, nagy = _mintavetel_sulyok(8, 64)
        _, azonos = _mintavetel_sulyok(8, 8)
        assert nagy.shape[1] == azonos.shape[1]
