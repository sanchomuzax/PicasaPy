"""#3871: fordított fekete-/fehérpont → CSÖKKENŐ tábla, előjel nélküli eltolás.

Spec: `docs/specs/picasa-native-filter-workers.md`, „2.2/d Csökkenő tábla”
(kutatás: #3867).

- A táblaépítő (`0x0090c1e0`) `black > white`-nál is a natív képlettel
  számol: a skála `1 / (white − black)` negatív, a kimenet előjelesen vágódik
  `[0, 0xFF00]`-ra ⇒ csökkenő tábla (nincs „teljes fehér” külön ág).
- Az alkalmazó (`0x0090bc60`) a `(delta · r)` szorzatot 32 bites, ELŐJEL
  NÉLKÜLI eltolással (`shr`) osztja 256-tal; a `delta >> 1` és a végső `>> 8`
  előjeles (`sar`). Csökkenő táblánál (`delta < 0`) ezért `r > 0` → 255,
  `r = 0` → a tábla értéke, `delta = 0` (köztük a 255-ös bemenet) →
  `LUT[255] >> 8`.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render import native_tone
from picasapy.render.native_tone import (
    NATIVE_LUT_FULL,
    apply_native_lut16,
    native_level_lut,
)
from picasapy.render.tone import finetune_level_lut


def _vart_tabla(black: float, white: float) -> np.ndarray:
    """A spec 2.2/d képlete, szándékosan újra leírva (gamma = 1,0)."""
    i = np.arange(256, dtype=np.float64)
    ertek = (i / 255.0 * 65280.0 - black * 65280.0) * (1.0 / (white - black))
    return np.clip(np.rint(ertek), 0, 0xFF00).astype(np.int64)


def _alkalmaz_mintaval(
    monkeypatch: pytest.MonkeyPatch, kep: np.ndarray, tabla: np.ndarray, minta
) -> np.ndarray:
    """Az alkalmazó futtatása RÖGZÍTETT, képpontonkénti mintákkal."""
    minta = np.asarray(minta, dtype=np.int64)
    monkeypatch.setattr(
        native_tone, "_dither_minta", lambda darab: minta.reshape(-1)[:darab]
    )
    return apply_native_lut16(kep, tabla)


class TestCsokkenoTablaEpitese:
    @pytest.mark.parametrize(("black", "white"), [(1.0, 0.5), (0.8, 0.2), (0.6, 0.4)])
    def test_a_nativ_kepletet_koveti(self, black: float, white: float) -> None:
        np.testing.assert_array_equal(native_level_lut(black, white), _vart_tabla(black, white))

    def test_a_tabla_csokkeno_es_nem_teljes_feher(self) -> None:
        tabla = native_level_lut(1.0, 0.5)
        assert np.all(np.diff(tabla) <= 0)
        assert int(tabla[0]) == NATIVE_LUT_FULL
        assert int(tabla[255]) == 0

    def test_a_finetune_max_sora_ugyanezt_kapja(self) -> None:
        # 684-es készlet `max` sora: Árnyékok = 1,0, Kiemelések = 0,5
        np.testing.assert_array_equal(finetune_level_lut(0.5, 1.0), _vart_tabla(1.0, 0.5))


class TestElojelNelkuliEltolas:
    #: mérsékelten csökkenő tábla, hogy a `r = 0` érték a tartomány belsejébe essen
    TABLA = native_level_lut(0.8, 0.2)

    @pytest.mark.parametrize("r", [1, 2, 128, 255])
    def test_pozitiv_minta_feher(self, monkeypatch: pytest.MonkeyPatch, r: int) -> None:
        kep = np.full((1, 1, 3), 120, dtype=np.uint8)
        assert int(self.TABLA[121] - self.TABLA[120]) < 0
        eredmeny = _alkalmaz_mintaval(monkeypatch, kep, self.TABLA, [r])
        assert eredmeny.tolist() == [[[255, 255, 255]]]

    def test_nulla_minta_a_tabla_erteke(self, monkeypatch: pytest.MonkeyPatch) -> None:
        kep = np.full((1, 1, 3), 120, dtype=np.uint8)
        lo = int(self.TABLA[120])
        delta = int(self.TABLA[121]) - lo
        vart = (lo - (delta >> 1)) >> 8
        assert 0 < vart < 255
        eredmeny = _alkalmaz_mintaval(monkeypatch, kep, self.TABLA, [0])
        assert eredmeny.tolist() == [[[vart, vart, vart]]]

    @pytest.mark.parametrize("r", [0, 1, 200, 255])
    def test_a_255_os_bemenet_a_tabla_utolso_erteke(
        self, monkeypatch: pytest.MonkeyPatch, r: int
    ) -> None:
        # `LUT[256] = LUT[255]` ⇒ `delta = 0`
        kep = np.full((1, 1, 3), 255, dtype=np.uint8)
        vart = int(self.TABLA[255]) >> 8
        eredmeny = _alkalmaz_mintaval(monkeypatch, kep, self.TABLA, [r])
        assert eredmeny.tolist() == [[[vart, vart, vart]]]

    def test_novekvo_tablan_nem_valtozik_semmi(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """`delta ≥ 0`-nál a logikai és az aritmetikai eltolás azonos."""
        tabla = native_level_lut(0.2, 0.8)
        kep = np.tile(np.arange(256, dtype=np.uint8), (256, 1))[..., None].repeat(3, axis=2)
        minta = np.tile(np.arange(256, dtype=np.int64), (256, 1)).T
        eredmeny = _alkalmaz_mintaval(monkeypatch, kep, tabla, minta)

        teljes = np.concatenate([tabla, tabla[-1:]])
        lo = teljes[:256][kep.astype(np.int64)]
        delta = (teljes[1:] - teljes[:256])[kep.astype(np.int64)]
        vart = np.clip((lo + ((delta * minta[..., None]) >> 8) - (delta >> 1)) >> 8, 0, 255)
        np.testing.assert_array_equal(eredmeny, vart.astype(np.uint8))


class TestMaxSorKepe:
    def test_szinte_csupa_feher_a_tiszta_feher_fekete(self) -> None:
        """A 684-es `max` sor mechanizmusa a valódi generátorral."""
        magassag = 64
        sor = np.arange(256, dtype=np.uint8)
        kep = np.tile(sor, (magassag, 1))[..., None].repeat(3, axis=2)
        eredmeny = apply_native_lut16(kep, finetune_level_lut(0.5, 1.0))

        # a tiszta fehér bemenet: LUT[255] = 0 ⇒ fekete
        assert np.all(eredmeny[:, 255] == 0)
        # a többi képpont zöme fehér; a nem fehérek aránya ≈ 1/256 (r = 0)
        tobbi = eredmeny[:, :255, 0]
        nem_feher = np.count_nonzero(tobbi != 255) / tobbi.size
        assert nem_feher < 3.0 / 256
        # a sötét képpontok a fordított tónust mutatják: szürke, nem fekete
        assert np.any((tobbi > 0) & (tobbi < 255))
