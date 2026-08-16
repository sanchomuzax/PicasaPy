"""#711 — a `desat` szűrőkulcs: az `ansel` (Filtered B&W) örökölt,
Picasa 2-korabeli ini-alakja.

Háttér (`docs/specs/picasa-ini-format.md`, „A `desat`" szakasz,
`docs/specs/picasa-native-filter-registry.md` 1. pont): a natív
dekompiláció szerint a `CDesaturateFilter` UGYANAZT a munkafüggvényt
(`0x0090e680`) hívja, mint az `ansel` — a szín viszont három floatként
(`desat=1,r,g,b`) érkezik, nem pakolt hexként. Az átváltás egzakt:

    desat(r, g, b) == ansel( round(r*255)<<16 | round(g*255)<<8 | round(b*255) )

Mielőtt a `desat` regisztrálva lett, a szűrő ISMERETLEN névként a
kihagyott-listába került — a lánc TÖBBI TAGJA emiatt már a javítás előtt
sem veszett el (`apply_filters` #301 óta megengedő), de maga a `desat`
EFFEKT nem futott le (a kép a `desat` szemszögéből változatlan maradt).
Ez a modul mindkét szempontot teszteli: a saját renderelést ÉS azt, hogy a
lánc utána következő tagjai megmaradnak.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filter_registry import canonical_filter_name, max_param_count
from picasapy.ini.filters import FilterOp, parse_filters, serialize_filters_for_write
from picasapy.render.chain import apply_filters
from picasapy.render.tinting import apply_ansel


@pytest.fixture
def sample() -> np.ndarray:
    rng = np.random.default_rng(711)
    return rng.integers(20, 230, size=(32, 48, 3), dtype=np.uint8)


class TestDesatRegisztralva:
    """1. kész-feltétel: a `desat` a regiszterben van, 3 paraméteres korláttal."""

    def test_kanonikus_nev(self) -> None:
        assert canonical_filter_name("desat") == "desat"
        assert canonical_filter_name("DESAT") == "desat"

    def test_parameterszam_harom(self) -> None:
        assert max_param_count("desat") == 3


class TestDesatRenderelesAnsellelEgyezik:
    """2. kész-feltétel: a `desat` az `ansel` egzakt megfelelője, a
    dokumentált szín-átváltással."""

    def test_nem_marad_kihagyott_listaban(self, sample: np.ndarray) -> None:
        ops = parse_filters("desat=1,0.500000,0.300000,0.200000;")
        report = apply_filters(sample, ops)
        assert "desat" not in report.skipped

    def test_pontosan_az_ansel_atvaltott_szinevel_egyezik(
        self, sample: np.ndarray
    ) -> None:
        ops = parse_filters("desat=1,0.500000,0.300000,0.200000;")
        report = apply_filters(sample, ops)
        # r=0.5 -> round(127.5) = 128, g=0.3 -> round(76.5) = 76 (Python
        # banker's rounding, fél-az-párosra kerekít), b=0.2 -> 51
        vart = apply_ansel(sample, color=(128, 76, 51))
        assert np.array_equal(report.image, vart)

    def test_alapertek_a_semleges_0333_harmas(self, sample: np.ndarray) -> None:
        # A natív konstruktor mind a négy mezőt 0,333-ra állítja — paraméter
        # nélkül (csak a flag) ugyanez fusson.
        ops = parse_filters("desat=1;")
        report = apply_filters(sample, ops)
        vart = apply_ansel(sample, color=(85, 85, 85))  # round(0.333*255) = 85
        assert np.array_equal(report.image, vart)


class TestDesatNemViszEIALancTobbiTagjat:
    """3. kész-feltétel: `desat=…;bw=1;` láncnál a `bw` sem magában, sem az
    értékében nem veszik el — a `desat` TÉNYLEGESEN lefut előtte."""

    def test_bw_nem_kihagyott(self, sample: np.ndarray) -> None:
        ops = parse_filters("desat=1,0.500000,0.300000,0.200000;bw=1;")
        report = apply_filters(sample, ops)
        assert "desat" not in report.skipped
        assert "bw" not in report.skipped

    def test_a_lanc_eredmenye_a_ket_lepes_kompozicioja(
        self, sample: np.ndarray
    ) -> None:
        # A helyes kimenet: előbb a desat (ansel-ekvivalens), utána a bw
        # (luma) — mivel a desat kimenete már szürke, a bw ezen már no-op-
        # szerű, de az ÉRTÉKNEK a desat tónusgörbéjéből kell adódnia, nem
        # a nyers kép luma-jából.
        ops = parse_filters("desat=1,0.500000,0.300000,0.200000;bw=1;")
        report = apply_filters(sample, ops)

        after_desat = apply_ansel(sample, color=(128, 76, 51))
        from picasapy.render.color import apply_bw

        vart = apply_bw(after_desat)
        assert np.array_equal(report.image, vart)

        # Kontroll: ha a desat NEM futna le (a javítás előtti állapot), az
        # eredmény a NYERS kép bw-je lenne — ez MÁS, mint a fenti.
        raw_bw = apply_bw(sample)
        assert not np.array_equal(report.image, raw_bw)


class TestDesatRoundTrip:
    """4. kész-feltétel: a `.picasa.ini`-be írva a `desat` bejegyzés és a
    lánc utána következő tagjai bájtra megmaradnak (az író-oldali kapu nem
    dobja el az ismeretlen paraméterszámú vagy nevű bejegyzést)."""

    def test_desat_es_az_utana_kovetkezo_szuro_is_megmarad(self) -> None:
        ops = (
            FilterOp("desat", ("1", "0.500000", "0.300000", "0.200000")),
            FilterOp("bw", ("1",)),
        )
        kiirt = serialize_filters_for_write(ops)
        assert kiirt == "desat=1,0.500000,0.300000,0.200000;bw=1;"

    def test_regi_pikaza2_alaku_lanc_valtozatlan(self) -> None:
        eredeti = "desat=1,0.333000,0.333000,0.333000;sepia=1;grain2=1;"
        ops = parse_filters(eredeti)
        assert serialize_filters_for_write(ops) == eredeti
