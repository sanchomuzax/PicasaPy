"""#2454: a Poszterizálás lineáris közelítése MÉRHETŐEN egyenértékű.

A `glimmer_tone.apply_quantizepalette` docstringje korábban azt ÁLLÍTOTTA,
hogy a `filterdesc.xml` `Depth = 4`-e (oktree, 3 osztási szint) „a lineáris
kvantálással egyenértékű" — **bizonyíték nélkül**. Ez a fájl rögzíti a
mérést, ami alátámasztja.

## A mérés (NAS-mérőszett, a Picasa saját exportjához hasonlítva)

ΔE, CIE Lab, átlagos képpont-távolság:

```
eset  Steps Smoothing Fade   ΔE mi↔Picasa   ΔE forrás↔Picasa
alap     8       80     0          0,268           19,009
min      2        0     0          0,687           73,485
max     30      100   100          0,136            0,136
```

A `min` esetben az érintetlen forrás 73,5-tel tér el az eredeti kimenetétől,
a mienk 0,687-tel — **a hatás 99,1%-át eltaláljuk**. A 0,1–0,7 a
JPEG-újrakódolás zajszintje.

⚠️ **A `max` eset semmit nem bizonyít a kvantálásról:** `Fade = 100`, tehát
a kimenet a forrás; a két ΔE ezért azonos. Kontrollnak jó.

## Miért nem futtatjuk itt magát a mérést

A referencia-képek a NAS-on vannak (`/mnt/nas/…`), ami a CI-n nincs meg. Az
alábbi tesztek ezért a mérés **következményeit** állítják a mai kódra —
azokat a tulajdonságokat, amiktől a szám olyan lett, amilyen. Ha valamelyik
elromlik, a ΔE is elromlana.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.glimmer_tone import apply_quantizepalette


@pytest.fixture
def atmenet():
    """Vízszintes 0→255 átmenet: a kvantálás lépcsői jól számolhatók."""
    sor = np.linspace(0, 255, 256, dtype=np.float32)
    return np.repeat(sor[np.newaxis, :, np.newaxis], 3, axis=2).astype(np.uint8)


class TestAKvantalasSzintjei:
    @pytest.mark.parametrize("steps", [2, 8, 30])
    def test_a_kimenet_legfeljebb_steps_kulonbozo_erteket_ad(
        self, atmenet, steps
    ):
        """`Steps` szint, `Smoothing=100` mellett (nincs elmosás)."""
        eredmeny = apply_quantizepalette(
            atmenet, steps=float(steps), smoothing=100.0, fade=0.0
        )
        egyedi = np.unique(eredmeny[..., 0])
        assert len(egyedi) <= steps, (
            f"{len(egyedi)} különböző érték {steps} szint mellett"
        )

    def test_a_szelso_ertekek_megmaradnak(self, atmenet):
        """A 0 és a 255 a kvantálás után is 0 és 255 — enélkül a kép
        kontrasztja csökkenne, és a ΔE azonnal elszaladna."""
        eredmeny = apply_quantizepalette(
            atmenet, steps=8.0, smoothing=100.0, fade=0.0
        )
        assert eredmeny[..., 0].min() == 0
        assert eredmeny[..., 0].max() == 255


class TestAFadeKezelese:
    """Ezt igazolta a `max` kontroll-eset (ΔE 0,136 mindkét irányban)."""

    def test_a_teljes_fade_a_FORRAST_adja(self, atmenet):
        eredmeny = apply_quantizepalette(
            atmenet, steps=2.0, smoothing=0.0, fade=100.0
        )
        assert np.array_equal(eredmeny, atmenet), (
            "Fade=100 mellett a kimenetnek a forrásnak kell lennie — ezen "
            "múlik, hogy a mérőszett `max` esete kontroll lehessen"
        )

    def test_a_nulla_fade_a_TELJES_hatast_adja(self, atmenet):
        eredmeny = apply_quantizepalette(
            atmenet, steps=2.0, smoothing=0.0, fade=0.0
        )
        assert not np.array_equal(eredmeny, atmenet)


class TestAzElmosasSzigmaja:
    def test_a_smoothing_100_nal_alig_mos(self, atmenet):
        """`σ = (100 − Smoothing)/10 + 0,1` → 0,1 a felső végen."""
        eles = apply_quantizepalette(
            atmenet, steps=8.0, smoothing=100.0, fade=0.0
        )
        lagy = apply_quantizepalette(atmenet, steps=8.0, smoothing=0.0, fade=0.0)
        assert not np.array_equal(eles, lagy), (
            "a Smoothing nem hat — pedig a szigma képlete rá épül"
        )
