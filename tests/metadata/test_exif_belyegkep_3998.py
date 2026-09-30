"""Az export EXIF-bélyegképe: méret, előfelezés, kódolás (#3998, spec 16. H, I).

A mért méretek a spec 16. H) 2. pontjából (186 export), a kódolási
tulajdonságok a 4. pontból: q85 (IJG-táblák), 4:2:0, baseline, optimalizált
Huffman, JFIF 1.01, sűrűségegység 0, 1:1.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.metadata import exif_belyegkep as bk

MERT = [
    ((960, 640), (160, 112)),
    ((964, 644), (160, 112)),
    ((988, 668), (160, 112)),
    ((1010, 690), (160, 112)),
    ((1090, 770), (160, 120)),
    ((1232, 912), (160, 120)),
    ((1360, 1040), (160, 128)),
    ((1360, 1103), (160, 136)),
    ((1600, 1200), (160, 120)),
    ((1650, 1250), (160, 128)),
    ((2560, 1696), (160, 112)),
    ((818, 950), (144, 160)),
    ((887, 1004), (144, 160)),
]


@pytest.mark.parametrize("forras,cel", MERT)
def test_a_13_mert_meret(forras, cel):
    assert bk.belyegkep_meret(*forras) == cel


@pytest.mark.parametrize(
    "forras,cel",
    [((1000, 651), (160, 104)), ((1000, 702), (160, 120))],  # a #3995 szétválasztó esetei
)
def test_a_keplet_nem_a_naiv_szabaly(forras, cel):
    assert bk.belyegkep_meret(*forras) == cel


def test_a_meret_a_8_tobbszorose_es_a_hosszabb_oldal_160():
    for w, h in [(301, 301), (5000, 301), (301, 5000), (4032, 3024), (3024, 4032)]:
        cw, ch = bk.belyegkep_meret(w, h)
        assert cw % 8 == 0 and ch % 8 == 0
        assert max(cw, ch) == 160 and min(cw, ch) >= 8


@pytest.mark.parametrize(
    "meret,kell",
    [((301, 301), True), ((300, 301), False), ((301, 300), False), ((300, 300), False), ((1, 5000), False)],
)
def test_kuszob_csak_ha_mindket_oldal_nagyobb_300(meret, kell):
    assert bk.kell_belyegkep(meret) is kell


def test_elofelezes_2x2_padlo_es_paratlan_szel_eldobva():
    kep = np.zeros((5, 5, 3), dtype=np.uint8)
    kep[0, 0], kep[0, 1], kep[1, 0], kep[1, 1] = 1, 1, 1, 0  # összeg 3 → ⌊3/4⌋ = 0
    kep[0, 2], kep[0, 3], kep[1, 2], kep[1, 3] = 255, 255, 255, 254  # 1019 → 254
    kep[4, :] = 99  # a páratlan utolsó sor eldobva
    kep[:, 4] = 99  # és az utolsó oszlop
    ki = bk.felez(kep)
    assert ki.shape == (2, 2, 3)
    assert ki[0, 0].tolist() == [0, 0, 0]
    assert ki[0, 1].tolist() == [254, 254, 254]
    assert 99 not in ki


def test_elofelezes_addig_amig_ketszeres():
    # 960×640 → 160×112: 960 → 480 (≥ 320) → 240 (< 320, megáll)
    kep = np.zeros((640, 960, 3), dtype=np.uint8)
    ki = bk.elofelezett(kep, 160, 112)
    assert ki.shape[:2] == (160, 240)  # két felezés (a spec példája)


def test_elofelezes_4000x3000_negy_felezes():
    kep = np.zeros((3000, 4000, 3), dtype=np.uint8)
    assert bk.elofelezett(kep, 160, 120).shape[:2] == (187, 250)


def test_elofelezes_nem_lep_ha_egyik_tengely_nem_eleg():
    kep = np.zeros((300, 1000, 3), dtype=np.uint8)
    # cél 160×140: a magasság 300 ≥ 280, de a felezés utáni 150 < 280 → egyszer felez
    assert bk.elofelezett(kep, 160, 140).shape[:2] == (150, 500)
    # cél 160×150: 300 ≥ 300 (az egyenlőség is felez) → egyszer, 150 < 300
    assert bk.elofelezett(kep, 160, 150).shape[:2] == (150, 500)
    # cél 160×151: 300 < 302 → egyszer sem
    assert bk.elofelezett(kep, 160, 151).shape[:2] == (300, 1000)


def test_belyegkep_merete_es_tartalma():
    kep = np.zeros((1250, 1650, 3), dtype=np.uint8)
    kep[:, :] = (30, 120, 200)
    jpeg = bk.belyegkep(kep, 85)
    import cv2

    ki = cv2.imdecode(np.frombuffer(jpeg, np.uint8), cv2.IMREAD_COLOR)
    assert ki.shape[:2] == (128, 160)
    assert abs(int(ki[64, 80, 0]) - 30) <= 3 and abs(int(ki[64, 80, 2]) - 200) <= 3


# --- a JPEG-kódolás tulajdonságai -------------------------------------------

_LUMA = [
    16, 11, 10, 16, 24, 40, 51, 61, 12, 12, 14, 19, 26, 58, 60, 55,
    14, 13, 16, 24, 40, 57, 69, 56, 14, 17, 22, 29, 51, 87, 80, 62,
    18, 22, 37, 56, 68, 109, 103, 77, 24, 35, 55, 64, 81, 104, 113, 92,
    49, 64, 78, 87, 103, 121, 120, 101, 72, 92, 95, 98, 112, 100, 103, 99,
]
_CHROMA = [
    17, 18, 24, 47, 99, 99, 99, 99, 18, 21, 26, 66, 99, 99, 99, 99,
    24, 26, 56, 99, 99, 99, 99, 99, 47, 66, 99, 99, 99, 99, 99, 99,
    99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99,
    99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99, 99,
]
_ZIGZAG = [
    0, 1, 8, 16, 9, 2, 3, 10, 17, 24, 32, 25, 18, 11, 4, 5, 12, 19, 26, 33, 40, 48, 41, 34,
    27, 20, 13, 6, 7, 14, 21, 28, 35, 42, 49, 56, 57, 50, 43, 36, 29, 22, 15, 23, 30, 37,
    44, 51, 58, 59, 52, 45, 38, 31, 39, 46, 53, 60, 61, 54, 47, 55, 62, 63,
]


def _q(alap, q):
    skala = 5000 // q if q < 50 else 200 - 2 * q
    return [min(max((b * skala + 50) // 100, 1), 255) for b in alap]


def _szegmensek(jpeg):
    out, pos = [], 2
    while pos < len(jpeg):
        assert jpeg[pos] == 0xFF
        marker = jpeg[pos + 1]
        hossz = int.from_bytes(jpeg[pos + 2 : pos + 4], "big")
        out.append((marker, jpeg[pos + 4 : pos + 2 + hossz]))
        if marker == 0xDA:
            break
        pos += 2 + hossz
    return out


@pytest.fixture(scope="module")
def jpeg():
    rng = np.random.default_rng(5)
    kep = rng.integers(0, 256, (640, 960, 3), dtype=np.uint8)
    return bk.belyegkep(kep, 85)


def test_jfif_1_01_egyseg_0_suruseg_1_1(jpeg):
    marker, torzs = _szegmensek(jpeg)[0]
    assert marker == 0xE0 and torzs[:5] == b"JFIF\x00"
    assert torzs[5:7] == b"\x01\x01"  # 1.01
    assert torzs[7] == 0  # sűrűségegység
    assert torzs[8:12] == b"\x00\x01\x00\x01"  # 1:1


def test_kvantalotablak_ijg_q85(jpeg):
    dqt = [t for m, t in _szegmensek(jpeg) if m == 0xDB]
    tablak = {}
    for t in dqt:
        while t:
            assert t[0] >> 4 == 0  # 8 bites
            tablak[t[0] & 15] = list(t[1:65])
            t = t[65:]
    elvart = [_q(_LUMA, 85)[i] for i in range(64)]
    assert tablak[0] == [_q(_LUMA, 85)[_ZIGZAG[i]] for i in range(64)]
    assert tablak[1] == [_q(_CHROMA, 85)[_ZIGZAG[i]] for i in range(64)]
    assert elvart[0] == 5


def test_baseline_420_optimalizalt_huffman(jpeg):
    szegm = _szegmensek(jpeg)
    markerek = [m for m, _ in szegm]
    assert 0xC0 in markerek and 0xC2 not in markerek  # baseline
    assert sum(len(_dht(t)) for m, t in szegm if m == 0xC4) == 4  # 2 DC + 2 AC
    sof = next(t for m, t in szegm if m == 0xC0)
    assert sof[5] == 3
    komp = {sof[6 + 3 * i]: sof[7 + 3 * i] for i in range(3)}
    assert sorted(komp.values()) == [0x11, 0x11, 0x22]  # 4:2:0
    assert komp[1] == 0x22
    assert 0xEE not in markerek  # nincs Adobe-jelölő


def _dht(t):
    tablak = []
    while t:
        db = sum(t[1:17])
        tablak.append(t[17 : 17 + db])
        t = t[17 + db :]
    return tablak


def test_a_huffman_nem_a_szabvanyos(jpeg):
    szegm = _szegmensek(jpeg)
    hosszak = [sum(t[1:17]) for m, tt in szegm if m == 0xC4 for t in [tt]]
    # a szabványos DC-táblák 12, az AC luma 162 kódot tartalmaznak; optimalizáltnál kevesebb a használt
    assert 162 not in hosszak


def test_a_minoseg_valtozik():
    kep = np.random.default_rng(9).integers(0, 256, (640, 960, 3), dtype=np.uint8)
    assert len(bk.belyegkep(kep, 40)) < len(bk.belyegkep(kep, 85))


def test_a_belyegkep_kicsi_marad():
    kep = np.random.default_rng(3).integers(0, 256, (1250, 1650, 3), dtype=np.uint8)
    assert len(bk.belyegkep(kep, 85)) < 20000
