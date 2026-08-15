"""#623: a Picasa KÖZÖS elmosó magja (`0x009dd0d0`) — kétmenetes IIR.

A szerkezet a `docs/specs/picasa-native-filter-workers.md` 4.2.1 pontjából
(elsőrendű IIR, tengelyenként oda-vissza futtatva, 9.7 fixpontos állapot),
a **sugár → együttható** leképezés pedig a 4.2.5 pont MÉRÉSÉBŐL származik:

```
r = exp(−1/R);   k = round(65536 · (1 − r))
```

A mérés a windowsos Picasa „Ragyogás" effektjének öt csúszkaállásán készült
(szintetikus éllépcső, veszteségmentes bemenet), és `k` értékei a
specifikáció táblázatában számszerűen benne állnak — az alábbi teszt
pontosan ezeket az értékeket követeli meg.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.iir_blur import apply_picasa_blur, blur_coefficient


class TestBlurCoefficient:
    """A mért `R → k` leképezés (4.2.5) számszerű pontjai."""

    @pytest.mark.parametrize(
        "slider,expected",
        [
            (0.25, 14572),  # R = 250^0.25 = 3,9764
            (0.50, 4017),  # R = 250^0.50 = 15,8114
            (0.75, 1034),  # R = 250^0.75 = 62,8716
        ],
    )
    def test_a_mert_egyutthatok(self, slider: float, expected: int) -> None:
        # a `filterdesc.xml` szerint a Sugár csúszka logaritmikus: R = 250^t
        assert blur_coefficient(250.0**slider) == expected

    def test_nagyobb_sugar_kisebb_egyutthato(self) -> None:
        assert blur_coefficient(2.0) > blur_coefficient(20.0) > blur_coefficient(200.0)

    def test_a_nulla_sugar_nem_mos(self) -> None:
        """A natív `pow(e, −1/R)` R=0-nál nem értelmezett — nálunk no-op."""
        assert blur_coefficient(0.0) == 65536


class TestApplyPicasaBlur:
    def test_egyszinu_kep_valtozatlan(self) -> None:
        """Az IIR állapota a peremen a szélső képpontból indul, ezért az
        egyszínű kép BÁJTRA változatlan marad (nincs sötét szegély)."""
        image = np.full((20, 30, 3), (90, 120, 200), dtype=np.uint8)
        assert np.array_equal(apply_picasa_blur(image, 8.0, 8.0), image)

    def test_a_nulla_sugar_azonossag(self) -> None:
        rng = np.random.default_rng(11)
        image = rng.integers(0, 256, size=(12, 14, 3), dtype=np.uint8)
        assert np.array_equal(apply_picasa_blur(image, 0.0, 0.0), image)

    def test_a_bemenetet_nem_modositja(self) -> None:
        image = np.full((8, 8, 3), 40, dtype=np.uint8)
        image[:, 4:] = 200
        eredeti = image.copy()
        apply_picasa_blur(image, 3.0, 3.0)
        assert np.array_equal(image, eredeti)

    def test_az_ellepcso_e_hajtasi_tavolsaga_a_sugar(self) -> None:
        """A 4.2.5 mérés lényege: az `R` paraméter KÉPPONTBAN az e-hajtási
        távolság. Egy éllépcsőn a lecsengés `R` képponttal 1/e-re esik."""
        image = np.zeros((8, 400, 3), dtype=np.uint8)
        image[:, 200:] = 255
        radius = 20.0
        profile = apply_picasa_blur(image, radius, 0.0)[4, :, 0].astype(float)
        # a sötét oldalra beszivárgó fény exponenciálisan cseng le, és az
        # élen pontosan félúton (≈128) áll
        assert profile[199] == pytest.approx(128.0, abs=8.0)
        arany = profile[199] / profile[int(199 - radius)]
        assert arany == pytest.approx(np.e, rel=0.15)

    def test_a_fuggoleges_tengely_kulon_sugarat_kap(self) -> None:
        image = np.zeros((60, 60, 3), dtype=np.uint8)
        image[30, 30] = 255
        csak_vizszintes = apply_picasa_blur(image, 6.0, 0.0)
        assert int(csak_vizszintes[30, 24].max()) > 0  # vízszintesen terjed
        assert int(csak_vizszintes[24, 30].max()) == 0  # függőlegesen nem

    def test_szimmetrikus_atvitel(self) -> None:
        """Az oda-vissza futtatás fázistorzítás-mentes: egy szimmetrikus
        bemenet (közel) szimmetrikus kimenetet ad.

        A maradék 1 szintnyi eltérés az EGÉSZ aritmetika sajátja: a
        visszamenet a már bájtra vágott előremenetet olvassa (a natív mag
        is így dolgozik) — ez nem javítható ki float munkatérrel anélkül,
        hogy eltávolodnánk az eredetitől.
        """
        image = np.zeros((5, 41, 3), dtype=np.uint8)
        image[:, 20] = 255
        profile = apply_picasa_blur(image, 5.0, 0.0)[2, :, 0].astype(int)
        np.testing.assert_allclose(profile, profile[::-1], atol=1)

    def test_ervenytelen_bemenet(self) -> None:
        with pytest.raises(ValueError):
            apply_picasa_blur(np.zeros((4, 4), dtype=np.uint8), 1.0, 1.0)


class TestBajtraEgyezikALeirassal:
    """A vektorizált menet a specifikáció (4.2.1) skalár pszeudokódjával
    vetve — képpontra azonos.

    Ez az a teszt, ami az egész aritmetika elcsúszását elkapja: a natív mag
    `>> 16` és `>> 7` ELŐJELES (padló) eltolással dolgozik, nem
    kerekítéssel, és a visszamenet a MÁR bájtra vágott előremenetet olvassa.
    """

    @staticmethod
    def _ref_sweep(line: list[int], coefficient: int) -> list[int]:
        state = line[0] << 7
        forward: list[int] = []
        for value in line:
            state += ((value << 7) - state) * coefficient >> 16
            forward.append(max(0, min(255, state >> 7)))
        state = forward[-1] << 7
        for index in range(len(forward) - 1, -1, -1):
            state += ((forward[index] << 7) - state) * coefficient >> 16
            forward[index] = max(0, min(255, state >> 7))
        return forward

    @classmethod
    def _ref_blur(cls, image: np.ndarray, radius: float) -> np.ndarray:
        coefficient = blur_coefficient(radius)
        work = image.astype(int)
        height, width = image.shape[:2]
        for y in range(height):
            for channel in range(3):
                work[y, :, channel] = cls._ref_sweep(
                    list(work[y, :, channel]), coefficient
                )
        for x in range(width):
            for channel in range(3):
                work[:, x, channel] = cls._ref_sweep(
                    list(work[:, x, channel]), coefficient
                )
        return work.astype(np.uint8)

    @pytest.mark.parametrize("radius", [1.0, 3.5, 40.0])
    def test_a_vektorizalt_menet_a_skalarral_egyezik(self, radius: float) -> None:
        image = np.random.default_rng(2).integers(0, 256, size=(9, 13, 3), dtype=np.uint8)
        np.testing.assert_array_equal(
            apply_picasa_blur(image, radius, radius), self._ref_blur(image, radius)
        )
