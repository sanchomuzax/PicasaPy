"""#907: két egymás utáni szemcse FÜGGETLEN zajmintát ad, nem ugyanazt.

## A mérés, ami eldöntötte (a #685 mérőszettből)

| lánc | ΔE |
|---|---:|
| `grain=1;` | 1,804 |
| `grain=1;grain=1;` | **2,671** |

A két hipotézis várt értéke messze van egymástól:

* **azonos minta** → az amplitúdó DUPLÁZÓDIK → ~3,6
* **független minta** → a szórás √2-szeres → ~2,55

A mért 2,671 egyértelműen a függetlené (az arány 1,48, közel a √2 = 1,414-hez,
nem a 2,0-hoz).

## Miért nem elég „a mag legyen véletlen"

A determinizmus a TESZTEKNEK kell. A megoldás ezért nem a mag eldobása,
hanem hogy a **termelő kód ne rögzítse**: alapból változik, a hívó viszont
megadhatja. Az itteni tesztek explicit magot adnak, ahol az számít.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render import glimmer_artistic as a


@pytest.fixture
def sima_kep():
    """Egyenletes SÖTÉT szürke: így a kimenet szórása TISZTÁN a zajé.

    ⚠️ Az érték nem közömbös. A `lighten` ág zaja a `[0, 2,55·Grain]`
    tartományon áll, és `lighten` módban `max(kép, zaj)` a kimenet — egy
    128-as középszürkén tehát `grain=20` (zaj 0…51) EGYÁLTALÁN nem hat, a
    kép bájtazonos marad. Az első próbaképem ezért nem a magot mérte, hanem
    a semmit. A 25-ös alapon a zaj az esetek nagyjából felében fölé megy,
    tehát a szórás valóban a zajé.
    """
    return np.full((120, 120, 3), 25, dtype=np.uint8)


def _zaj_szoras(kep: np.ndarray) -> float:
    return float(np.std(kep.astype(np.float64)))


class TestAKetSzemcseFuggetlen:
    """⚠️ A jegy √2-es érvelése IDE NEM vihető át — kimérve.

    A jegy a ΔE-ből következtet: `grain=1;` → 1,804, `grain=1;grain=1;` →
    2,671, és ebből a √2-es szórásnövekedésre jut. Az az érvelés ÖSSZEADÓDÓ
    zajt feltételez, és a FORRÁSHOZ mért ΔE-ről szól.

    A `PicnikGrain` viszont `lighten` módban `max(kép, zaj)`-t számol, ami
    **nem összeadás**: két független zajréteg maximuma a szórást alig
    növeli. Mérve egy 25-ös sima lapon, `grain=20`:

    ```
    független mag:  σ 8,483 → 8,937   (arány 1,054)
    FIX mag:        σ 8,404 → 8,404   (arány 1,000, BÁJTAZONOS)
    ```

    A √2-t (1,414) tehát egyik sem adja — a szintetikus lapon mért σ és a
    forráshoz mért ΔE nem ugyanaz a mennyiség. **A jegy következtetése
    ettől nem dől meg**, csak nem ezzel a méréssel igazolható.

    Ami viszont ELDŐLT, és élesebb is: fix maggal a második alkalmazás
    **teljesen hatástalan** — bájtra ugyanaz a kép jön ki. Az idempotencia
    a `max` következménye. Az eredetiben a második szemcse HAT; nálunk nem
    hatott. Ezt állítják az alábbi tesztek.
    """

    def test_FIX_maggal_a_masodik_szemcse_hatastalan(self, sima_kep):
        """A régi viselkedés — ezt szünteti meg a változás."""
        elso = a.apply_picnik_grain(sima_kep, grain=20.0, lighten=True, seed=1)
        masodik = a.apply_picnik_grain(elso, grain=20.0, lighten=True, seed=1)

        assert np.array_equal(elso, masodik), (
            "ez a teszt a RÉGI hibát rögzíti: azonos maggal a `max` "
            "idempotens, tehát a második szemcse nyomtalan"
        )

    def test_valtozo_maggal_a_masodik_szemcse_HAT(self, sima_kep):
        elso = a.apply_picnik_grain(sima_kep, grain=20.0, lighten=True)
        masodik = a.apply_picnik_grain(elso, grain=20.0, lighten=True)

        assert not np.array_equal(elso, masodik), (
            "a második szemcse nem változtatott a képen — a mag rögzítve "
            "maradt, és a `max` idempotenciája elnyelte"
        )
        assert _zaj_szoras(masodik) > _zaj_szoras(elso), (
            "a második, független réteg a szórást növelni tartozik"
        )

    def test_ket_hivas_KULONBOZO_zajt_ad(self, sima_kep):
        """A közvetlen állítás: ugyanarra a képre kétszer hívva más jön ki."""
        elso = a.apply_picnik_grain(sima_kep, grain=20.0, lighten=True)
        masodik = a.apply_picnik_grain(sima_kep, grain=20.0, lighten=True)

        assert not np.array_equal(elso, masodik), (
            "két hívás bájtazonos képet adott — a mag rögzítve maradt"
        )


class TestAzExplicitMagTovabbraIsDeterminisztikus:
    def test_azonos_mag_azonos_kep(self, sima_kep):
        elso = a.apply_picnik_grain(sima_kep, grain=20.0, lighten=True, seed=7)
        masodik = a.apply_picnik_grain(sima_kep, grain=20.0, lighten=True, seed=7)

        assert np.array_equal(elso, masodik), (
            "explicit maggal a kimenetnek reprodukálhatónak kell lennie — "
            "enélkül egyetlen szemcsés teszt sem írható"
        )

    def test_mas_mag_mas_kep(self, sima_kep):
        elso = a.apply_picnik_grain(sima_kep, grain=20.0, lighten=True, seed=7)
        masik = a.apply_picnik_grain(sima_kep, grain=20.0, lighten=True, seed=8)

        assert not np.array_equal(elso, masik)


def test_a_nulla_szemcse_valtozatlanul_no_op(sima_kep):
    """A 0-s erősség tétlen marad — a véletlen mag ezt nem ronthatja el.

    `lighten=False` mellett a zaj a `[255, 255]` tartományra szűkül, és
    `darken` módban `min(kép, 255)` = a kép.
    """
    eredmeny = a.apply_picnik_grain(sima_kep, grain=0.0, lighten=False)
    assert np.array_equal(eredmeny, sima_kep)
