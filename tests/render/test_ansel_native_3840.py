"""#3840 — az `ansel` (Filtered B&W) a natív mag (`0x0090e680`) egész
aritmetikájával.

Spec: `docs/specs/filters-decoded.md`, „`ansel` — a `k` erősség kiolvasva,
a mag TELJES". A várt értékek KÉZZEL levezetettek a spec képleteiből (a
levezetés a tesztek megjegyzéseiben), nem a kódunk kimenetéből:

1. `W_c = csonk(256 · f32(w_c / Σw))`, `w_c = szín_c / 255`;
2. `Y = W_r·R + W_g·G + W_b·B`;
3. `S₁ = Σ (2R + 5G + B + 4) >> 3`, `S₂ = Σ Y >> 8`,
   `N = Σⱼ hist[j]·(((256 − j)·j) >> 6)`;
4. `t = f32((S₁ − S₂) / N)` `[−1, 1]`-re szorítva, `k = csonk(256 · t)`;
5. `v = Y + ((((0xffff − Y)·Y) >> 14)·k >> 8)`, kimenet `v >> 8`.
"""

# rontás-kontroll: az `apply_ansel`-be visszatéve a mért töréspontsort
# (`_ANSEL_ANCHOR_CURVE`, np.interp) a vörös szűrős `k = −16` próba 112
# helyett 133-at, a fehér szűrős középszürke 128 helyett 133-at ad →
# ezek a próbák FAILED; a `_ansel_weights`-ben csonkítás helyett
# kerekítéssel a narancs szűrő súlya (170, 85, 0) helyett (170, 86, 0) —
# az a próba is FAILED.

from __future__ import annotations

import numpy as np

from picasapy.render.tinting import _ansel_strength, _ansel_weights, apply_ansel


def _image(*pixels: tuple[int, int, int]) -> np.ndarray:
    return np.array([pixels], dtype=np.uint8)


def _gray(result: np.ndarray) -> list[int]:
    assert (result[..., 0] == result[..., 1]).all()
    assert (result[..., 1] == result[..., 2]).all()
    return [int(value) for value in result[0, :, 0]]


class TestSulyok:
    def test_feher_szuro_85_85_85(self) -> None:
        # 256 · f32(1/3) = 85,33 → 85; az összeg 255, nem 256
        assert _ansel_weights((255, 255, 255)) == (85, 85, 85)

    def test_tiszta_szinszuro_egy_csatornara_256(self) -> None:
        assert _ansel_weights((255, 0, 0)) == (256, 0, 0)
        assert _ansel_weights((0, 0, 255)) == (0, 0, 256)

    def test_a_sulyok_csonkolodnak_nem_kerekulnek(self) -> None:
        # w = (1, f32(128/255)) / 1,50196… → (0,66579…, 0,33420…);
        # 256·w = (170,44…, 85,55…) — csonkítva (170, 85), kerekítve
        # (170, 86) lenne
        assert _ansel_weights((255, 128, 0)) == (170, 85, 0)

    def test_a_skala_kozombos_csak_az_arany_szamit(self) -> None:
        assert _ansel_weights((100, 100, 100)) == (85, 85, 85)

    def test_fekete_szuro_a_feher_sulyait_kapja(self) -> None:
        # Az eredeti az összeg = 0 esetet NEM kezeli (0-val oszt). Mi a
        # semleges, egyenlő súlyt adjuk — ugyanazt, mint a fehér szűrő.
        assert _ansel_weights((0, 0, 0)) == (85, 85, 85)


class TestErosseg:
    def test_voros_szuro_negativ_k(self) -> None:
        # W = (256, 0, 0). (128,0,0): Y=32768, j=128, luma (256+4)>>3=32.
        # (128,255,0): Y=32768, j=128, luma (256+1275+4)>>3=191.
        # S₁=223, S₂=256, N=2·((128·128)>>6)=512 → t=−33/512 → k=−16
        image = _image((128, 0, 0), (128, 255, 0))
        assert _ansel_strength(image, (256, 0, 0)) == -16

    def test_kek_szuro_pozitiv_k(self) -> None:
        # W = (0, 0, 256). (200,200,64): Y=16384, j=64,
        # luma (400+1000+64+4)>>3=183; N=(192·64)>>6=192
        # t=(183−64)/192=0,6198 → k=csonk(158,67)=158
        image = _image((200, 200, 64))
        assert _ansel_strength(image, (0, 0, 256)) == 158

    def test_t_egyre_szorul(self) -> None:
        # (255,255,1) kék szűrővel: Y=256, j=1, luma 223, S₂=1,
        # N=(255·1)>>6=3 → t=74 → 1 → k=256
        image = _image((255, 255, 1))
        assert _ansel_strength(image, (0, 0, 256)) == 256

    def test_n_nulla_eseten_nincs_erosseg(self) -> None:
        # minden Y < 256 → csak a j=0 rekesz telik, a súlya 0 → N = 0
        image = _image((0, 0, 0), (1, 1, 0))
        assert _ansel_strength(image, (85, 85, 85)) is None


class TestKimenet:
    def test_voros_szuro_k_minusz_16(self) -> None:
        # Y=32768: ((32767·32768)>>14)=65534; 65534·(−16)>>8=−4096
        # v=28672 → 112, mindkét képpontra
        result = apply_ansel(_image((128, 0, 0), (128, 255, 0)), (255, 0, 0))
        assert _gray(result) == [112, 112]

    def test_kek_szuro_k_158(self) -> None:
        # Y=16384: ((49151·16384)>>14)=49151; 49151·158>>8=30335
        # v=46719 → 182
        result = apply_ansel(_image((200, 200, 64)), (0, 0, 255))
        assert _gray(result) == [182]

    def test_kek_szuro_k_256(self) -> None:
        # Y=256: ((65279·256)>>14)=1019; 1019·256>>8=1019 → v=1275 → 4
        result = apply_ansel(_image((255, 255, 1)), (0, 0, 255))
        assert _gray(result) == [4]

    def test_feher_szuro_kozepszurke_k_egy(self) -> None:
        # (128,128,128): Y=85·384=32640, j=127, luma 128, S₂=127,
        # N=(129·127)>>6=255 → t=1/255 → k=1;
        # ((32895·32640)>>14)=65533; ·1>>8=255 → v=32895 → 128
        result = apply_ansel(_image((128, 128, 128)), (255, 255, 255))
        assert _gray(result) == [128]

    def test_voros_szuron_at_a_voros_folt_vilagos_a_kek_fekete(self) -> None:
        # vörös (200,40,40): Y=51200, j=200, luma 80;
        # kék (40,40,200): Y=10240, j=40, luma 60.
        # S₁−S₂ = 140−240 = −100, N = 175+135 = 310 → k=csonk(−82,58)=−82
        # vörös: 51200 + ⌊44796·(−82)/256⌋ = 36851 → 143;
        # kék: 10240 + ⌊34559·(−82)/256⌋ = −830 → 0-ra vágva → 0
        result = apply_ansel(_image((200, 40, 40), (40, 40, 200)), (255, 0, 0))
        assert _gray(result) == [143, 0]

    def test_n_nulla_fekete_marad(self) -> None:
        # Az eredeti a második menet nélkül kilép, és a nyers 16 bites Y
        # dwordokat hagyja a pufferben; mi a k = 0 ágat adjuk (v = Y), ami
        # itt Y >> 8 = 0, azaz fekete.
        result = apply_ansel(_image((0, 0, 0), (1, 1, 0)), (255, 255, 255))
        assert _gray(result) == [0, 0]

    def test_fekete_szuro_a_feher_szuroval_egyezik(self) -> None:
        image = _image((10, 200, 30), (250, 20, 90), (128, 128, 128))
        np.testing.assert_array_equal(
            apply_ansel(image, (0, 0, 0)), apply_ansel(image, (255, 255, 255))
        )

    def test_a_desat_ut_ugyanazt_a_magot_hasznalja(self) -> None:
        from picasapy.ini.filters import parse_filters
        from picasapy.render.chain import apply_filters

        image = _image((200, 40, 40), (40, 40, 200))
        report = apply_filters(image, parse_filters("desat=1,1.000000,0,0;"))
        assert "desat" not in report.skipped
        assert _gray(report.image) == [143, 0]
