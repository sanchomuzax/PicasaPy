"""#3092: a natív tónus-magok DITHERELÉSE.

## A mérés

`docs/specs/picasa-native-filter-workers.md` **2.2**, **2.2/b**, **2.2/c**
(#2926, #2868, #2874):

```c
r = MT19937_next() & 0xff;              // KÉPPONTONKÉNT EGY minta
for c in (R, G, B):
    lo    = LUT[c];  delta = LUT[c+1] - lo;
    v     = lo + ((delta * r) >> 8) - (delta >> 1);
    out_c = clamp(v >> 8, 0, 255);
```

- a bejárás **sorfolytonos**, fentről le, balról jobbra (2.2/b.1);
- **egy minta képpontonként**, mindhárom csatornára ugyanaz ⇒ a zaj
  **szürke**, nem színes (2.2/b.2);
- **nincs csempézés és nincs szálindítás** a hét burkolóban (2.2/c.1), a
  munkafüggvény **egyszer** fut egy téglalapra (2.2/b.3);
- a generátor MT19937, vetőmag `0x2D8228BE` (#2868).

## ⚠️ Amit ez a lap NEM állít

**Nem** a Picasa kimenetével való bitre egyezést. A natív generátor
állapota folyamat-globális (az index `0x00d67f74` a hívások közt tovább
él), tehát ugyanannak a képnek a zaja attól is függ, mit dolgozott fel
előtte a program. Nálunk a kezdőállapot **képenként rögzített** — ezt a
jegy is kimondja, és a cél a **sávosodás megszüntetése**, nem az egyezés.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.native_tone import (
    NATIVE_DITHER_SEED,
    apply_native_lut16,
    native_level_lut,
)


def _atmenet(magassag: int = 32, szelesseg: int = 256) -> np.ndarray:
    """Vízszintes szürke átmenet — a sávosodás itt látszik a legjobban."""
    sor = (np.arange(szelesseg) % 256).astype(np.uint8)
    return np.repeat(sor[np.newaxis, :, np.newaxis], magassag, axis=0).repeat(
        3, axis=2
    )


class TestADitherDeterminisztikus:
    def test_ketszer_futtatva_bajtra_ugyanaz(self) -> None:
        """A #2868 mérése: a magozásban nincs entrópiaforrás."""
        kep = _atmenet()
        lut = native_level_lut(0.2, 0.8)
        assert np.array_equal(
            apply_native_lut16(kep, lut), apply_native_lut16(kep, lut)
        )

    def test_a_vetomag_a_MERT_ertek(self) -> None:
        assert NATIVE_DITHER_SEED == 0x2D8228BE


class TestAZajSZURKE:
    def test_a_harom_csatorna_eltolasa_azonos(self) -> None:
        """Egy minta jut egy képpontra ⇒ a három csatorna UGYANAZT kapja.

        Szürke bemeneten a kimenetnek is szürkének kell maradnia: ha
        csatornánként külön mintát húznánk, színes zaj keletkezne."""
        kep = _atmenet()
        eredmeny = apply_native_lut16(kep, native_level_lut(0.2, 0.8))
        assert np.array_equal(eredmeny[:, :, 0], eredmeny[:, :, 1])
        assert np.array_equal(eredmeny[:, :, 1], eredmeny[:, :, 2])


class TestADitherHATASA:
    def test_a_savosodas_csokken(self) -> None:
        """A LÉNYEG: a széthúzott hisztogram ne lépcsőzzön.

        Mérőszám: hány KÜLÖNBÖZŐ kimeneti szint áll elő egy sima átmenetből.
        Dither nélkül a szinthúzás összevonja a szinteket (lépcsők), a
        ditherrel a köztes értékek is előfordulnak."""
        kep = _atmenet()
        lut = native_level_lut(0.35, 0.65)   # erős széthúzás

        ditherelt = apply_native_lut16(kep, lut)
        nyers = np.clip(lut[:256] >> 8, 0, 255).astype(np.uint8)[kep]

        assert len(np.unique(ditherelt)) > len(np.unique(nyers)), (
            "a dither nem növelte a kimeneti szintek számát — nem fut"
        )

    def test_a_hisztogram_LYUKAI_eltunnek(self) -> None:
        """A sávosodás közvetlen mérőszáma: hány üres rekesz van a
        hisztogramban. Egy széthúzott görbe alatt a nyers kimenet átugrik
        szinteket — a dither kitölti őket.

        Mérve a #685 mérőszett `contrast__alap` képén (640 × 960):
        erős szinthúzásnál (0,35–0,65) **117 → 0** lyuk, közepesnél
        (0,2–0,8) **46 → 0**. Ez a jegy tényleges haszna."""
        kep = _atmenet(magassag=64)
        lut = native_level_lut(0.35, 0.65)

        ditherelt = apply_native_lut16(kep, lut)
        nyers = np.clip(lut[:256] >> 8, 0, 255).astype(np.uint8)[kep]

        def lyukak(k: np.ndarray) -> int:
            h = np.histogram(k[:, :, 0], bins=256, range=(0, 256))[0]
            hasznalt = np.nonzero(h)[0]
            return int((h[hasznalt.min() : hasznalt.max() + 1] == 0).sum())

        assert lyukak(ditherelt) < lyukak(nyers), (
            f"a dither nem töltötte ki a hisztogram lyukait "
            f"({lyukak(nyers)} → {lyukak(ditherelt)})"
        )

    def test_a_kozepertek_nem_tolodik_el(self) -> None:
        """A zaj nulla várható értékű (`− delta >> 1` az eltolás)."""
        kep = _atmenet(magassag=64)
        lut = native_level_lut(0.2, 0.8)

        ditherelt = apply_native_lut16(kep, lut).astype(np.float64)
        nyers = np.clip(lut[:256] >> 8, 0, 255).astype(np.uint8)[kep].astype(
            np.float64
        )

        assert abs(ditherelt.mean() - nyers.mean()) < 1.0, (
            "a dither elmozdította a kép átlagos világosságát"
        )


class TestAHatarok:
    def test_lapos_LUT_eseten_nincs_zaj(self) -> None:
        """Ahol a görbe vízszintes (`delta == 0`), ott nincs mit ditherelni —
        a zaj amplitúdója a helyi meredekséggel arányos.

        Ez a KONTROLL: ha a próba zajt látna itt is, akkor a modellünk nem a
        meredekséghez kötné az amplitúdót."""
        kep = _atmenet()
        lapos = np.full(257, 0x8000, dtype=np.int64)
        eredmeny = apply_native_lut16(kep, lapos)
        assert len(np.unique(eredmeny)) == 1

    @pytest.mark.parametrize("ertek", [0, 255])
    def test_a_szelso_szintek_nem_csordulnak_tul(self, ertek: int) -> None:
        kep = np.full((8, 8, 3), ertek, dtype=np.uint8)
        eredmeny = apply_native_lut16(kep, native_level_lut(0.0, 1.0))
        assert eredmeny.min() >= 0 and eredmeny.max() <= 255
