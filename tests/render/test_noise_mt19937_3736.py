"""#3736: a `NoiseImageOperation` zajrétege a Picasa natív generátorát
számolja — MT19937, 1664525-ös magvetéssel.

A spec (`docs/specs/filterdesc-registry.md`, „A `NoiseImageOperation`
véletlengenerátora", #3747):

    s[0] = randomSeed
    s[i] = 1664525 · (s[i−1] ^ (s[i−1] >> 30)) + i     (i = 1…623)
    index = 624 ⇒ az első húzás twistet vált ki

Képpontonként EGY 32 bites húzás, felülről lefelé, balról jobbra. Színesen
R/G/B = a húzás 2./1./0. bájtja `% r + low`, szürkén a teljes húzás
`% r + low`; `r = high − low + 1`, a `low`/`high` 255-re vágva.

Az elvárt értékeket egy, a termékkódtól FÜGGETLEN, tiszta Python
MT19937 (`_mt_referencia`) adja — a szabványos szorzóval futtatva a
közismert első kimenetet (5489 → 3499211612) hozza, tehát a twist és a
temperálás szabványos, csak a magvetés tér el.

Mérve (684-merokeszlet, `analyze_validation_kit.mean_de`, CIE76 átlag-ΔE
a Picasa-exporthoz):

| eset | numpy-zaj (előtte) | natív MT (itt) |
|---|---:|---:|
| `NightVision` alap | 11,696 | **4,626** |
| `NightVision` min | 5,436 (a #3735 után) | **3,673** |
| `Holga` alap | 1,476 | **0,890** |
| `Cinemascope` alap | 2,152 | **1,367** |
| `Sixties` alap / min | 1,289 / 1,443 | **1,179 / 1,255** |

A `PicnikGrain` szándékosan a régi, magonként változó numpy-zajon marad
(#907: két alkalmazás független mintát ad, ami az állandó `randomSeed`-del
nem fér össze) — ezt a `TestPicnikGrainValtozatlan` őrzi.
"""

# rontás-kontroll: a `nativ_noise._MAGVETO_SZORZO` a szabványos 1812433253-ra
# átírva → 14 failed (a rögzített első képpontok, a tartomány- és
# maszkpróbák, a független referencia, mind a hat golden eset és a
# korreláció); a bejárás alulról felfelé fordítva (`[::-1]` a húzások
# rácsán) → 9 failed (`test_sorfolytonos_felulrol_lefele`, a független
# referencia, a hat golden eset és a korreláció); a `PicnikGrain` a natív
# `apply_noise`-ra kötve → a `TestPicnikGrainValtozatlan` bukik.

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render import glimmer_ops as g
from picasapy.render.chain import apply_filters
from picasapy.render.glimmer_artistic import apply_picnik_grain
from picasapy.render.nativ_noise import picasa_mt19937

# ---------------------------------------------------------------------------
# Független referencia: tiszta Python MT19937, paraméterezhető magvetéssel.
# ---------------------------------------------------------------------------


def _mt_referencia(seed: int, darab: int, szorzo: int = 1664525) -> list[int]:
    allapot = [seed & 0xFFFFFFFF]
    for i in range(1, 624):
        elozo = allapot[-1]
        allapot.append((szorzo * (elozo ^ (elozo >> 30)) + i) & 0xFFFFFFFF)
    kimenet: list[int] = []
    index = 624
    for _ in range(darab):
        if index >= 624:
            for k in range(624):
                y = (allapot[k] & 0x80000000) | (allapot[(k + 1) % 624] & 0x7FFFFFFF)
                allapot[k] = allapot[(k + 397) % 624] ^ (y >> 1) ^ (0x9908B0DF if y & 1 else 0)
            index = 0
        y = allapot[index]
        index += 1
        y ^= y >> 11
        y ^= (y << 7) & 0x9D2C5680
        y ^= (y << 15) & 0xEFC60000
        y ^= y >> 18
        kimenet.append(y & 0xFFFFFFFF)
    return kimenet


def test_a_referencia_szabvanyos_szorzoval_a_kozismert_elso_kimenet():
    assert _mt_referencia(5489, 1, szorzo=1812433253) == [3499211612]


# ---------------------------------------------------------------------------
# 1. Rögzített első képpontok: randomSeed = 30, low = 0, high = 180
# (a NightVision lánca). r = 181.
# ---------------------------------------------------------------------------

#: Az első hat húzás (`_mt_referencia(30, 6)`).
_ELSO_HUZASOK = (3261729888, 1376989456, 503658214, 2320572697, 1359432822, 3763186411)

#: Színes ág: (R, G, B) = ((y>>16)&255, (y>>8)&255, y&255) % 181.
_ELSO_SZINES = (
    (106, 12, 96),
    (19, 49, 16),
    (5, 54, 49),
    (81, 33, 25),
    (7, 76, 118),
    (77, 170, 54),
)

#: Szürke ág: y % 181, mindhárom csatornára.
_ELSO_SZURKE = (21, 100, 12, 114, 104, 26)


class TestElsoKeppontok:
    def test_a_generator_elso_huzasai(self):
        assert tuple(int(v) for v in picasa_mt19937(30, 6)) == _ELSO_HUZASOK
        assert tuple(_mt_referencia(30, 6)) == _ELSO_HUZASOK

    def test_szines_ag(self):
        reteg = g.noise_layer(1, 6, 30, 0, 180, False)
        assert reteg.shape == (1, 6, 3)
        assert [tuple(int(c) for c in px) for px in reteg[0]] == list(_ELSO_SZINES)

    def test_szurke_ag(self):
        reteg = g.noise_layer(1, 6, 30, 0, 180, True)
        for x, vart in enumerate(_ELSO_SZURKE):
            assert tuple(int(c) for c in reteg[0, x]) == (vart, vart, vart)

    def test_sorfolytonos_felulrol_lefele(self):
        """2×3-as rétegen a felső sor az 1–3., az alsó a 4–6. húzás."""
        reteg = g.noise_layer(2, 3, 30, 0, 180, False)
        kapott = [tuple(int(c) for c in reteg[y, x]) for y in range(2) for x in range(3)]
        assert kapott == list(_ELSO_SZINES)


class TestTartomany:
    def test_low_high_255_re_vagva(self):
        """`low = 250`, `high = 300` → `high` 255, `r = 6`: az érték
        `bájt % 6 + 250`, soha nem lép 255 fölé."""
        reteg = g.noise_layer(1, 6, 30, 250, 300, False)
        for x, y in enumerate(_ELSO_HUZASOK):
            vart = (((y >> 16) & 255) % 6 + 250, ((y >> 8) & 255) % 6 + 250, (y & 255) % 6 + 250)
            assert tuple(int(c) for c in reteg[0, x]) == vart

    def test_a_tartomany_szelei(self):
        reteg = g.noise_layer(40, 50, 5, 235, 255, True)
        assert reteg.min() >= 235 and reteg.max() <= 255
        assert reteg.dtype == np.float32

    def test_forditott_tartomany_hiba(self):
        with pytest.raises(ValueError):
            g.noise_layer(2, 2, 1, 200, 100, True)

    def test_csatorna_maszk(self):
        """`channelOptions` 0. bit R, 1. G, 2. B; a letiltott csatorna 0."""
        reteg = g.noise_layer(1, 6, 30, 0, 180, False, channel_options=5)
        assert np.all(reteg[0, :, 1] == 0)
        assert [int(v) for v in reteg[0, :, 0]] == [px[0] for px in _ELSO_SZINES]
        assert [int(v) for v in reteg[0, :, 2]] == [px[2] for px in _ELSO_SZINES]


class TestFuggetlenReferencia:
    """A twist-határon (624. húzás) át is egyezik a független kóddal."""

    def test_szines_es_szurke_700_kepponton(self):
        h, w = 25, 28
        huzasok = np.array(_mt_referencia(7, h * w), dtype=np.uint64).reshape(h, w)
        r = 21
        szines = g.noise_layer(h, w, 7, 10, 30, False)
        vart = np.stack([((huzasok >> s) & 255) % r + 10 for s in (16, 8, 0)], axis=-1).astype(
            np.float32
        )
        np.testing.assert_array_equal(szines, vart)
        szurke = g.noise_layer(h, w, 7, 10, 30, True)
        np.testing.assert_array_equal(szurke[..., 0], (huzasok % r + 10).astype(np.float32))


class TestPicnikGrainValtozatlan:
    """#907: a `PicnikGrain` a régi, `numpy`-os egyenletes zajon marad."""

    def test_a_regi_numpy_zajjal_egyezik(self):
        rng = np.random.default_rng(0)
        kep = rng.integers(0, 256, size=(12, 16, 3), dtype=np.uint8)
        grain = 10.0
        low, high = 255.0 - 2.55 * grain, 255.0
        sik = np.random.default_rng(1234).uniform(low, high, size=(12, 16)).astype(np.float32)
        zaj = np.repeat(sik[..., np.newaxis], 3, axis=2)
        vart = g.to_uint8(g.apply_blend_mode(g.to_float(kep), zaj, "darken", 1.0))
        np.testing.assert_array_equal(apply_picnik_grain(kep, grain, False, seed=1234), vart)


# ---------------------------------------------------------------------------
# 2. FEJLESZTŐI GÉPEN futó golden-mérés a valódi Picasa-exporttal (684-
# merokeszlet), a `test_simple_color_matrix_sorrend_3735.py` mintájára: ha
# a kit nincs a gépen, a teszt skip-pel lép ki.
# ---------------------------------------------------------------------------

_KIT = Path("/mnt/nas/My Pictures/684-merokeszlet")

#: A jegy táblázatának + 0,05-ös tűrése.
_TURES = 0.05

#: (címke, fájlnév, lánc, a natív generátorral mért ΔE a jegyből)
_GOLDEN_ESETEK = [
    (
        "NightVision alap",
        "nightvision__alap.jpg",
        "NightVision=1,0.000000,0.000000,0.000000;",
        4.626,
    ),
    (
        "NightVision min",
        "nightvision__min.jpg",
        "NightVision=1,-50.000000,-50.000000,0.000000;",
        3.673,
    ),
    ("Holga alap", "holga__alap.jpg", "Holga=1,70.000000,30.000000,0.000000;", 0.890),
    ("Cinemascope alap", "cinemascope__alap.jpg", "Cinemascope=1,0;", 1.367),
    ("Sixties alap", "sixties__alap.jpg", "Sixties=1,20.000000,00ffffff,0;", 1.179),
    ("Sixties min", "sixties__min.jpg", "Sixties=1,0.000000,00ffffff,0;", 1.255),
]


def _golden_eszkozok():
    gyoker = Path(__file__).resolve().parents[2]
    utvonal = str(gyoker / "tools" / "golden")
    if utvonal not in sys.path:
        sys.path.insert(0, utvonal)
    from analyze_validation_kit import load, mean_de

    return load, mean_de


@pytest.mark.skipif(not _KIT.is_dir(), reason="a 684-merokeszlet NAS-os mérőkészlet nem elérhető")
@pytest.mark.parametrize(
    ("cimke", "nev", "lanc", "vart_de"), _GOLDEN_ESETEK, ids=[e[0] for e in _GOLDEN_ESETEK]
)
def test_a_684_merokeszlettel_a_hatarertek_alatt(cimke, nev, lanc, vart_de):
    load, mean_de = _golden_eszkozok()
    forras = load(_KIT / nev)
    export = load(_KIT / "export" / nev)
    kep = apply_filters(forras, parse_filters(lanc)).image
    de = mean_de(kep, export)
    assert de <= vart_de + _TURES, f"{cimke}: ΔE {de:.3f} > {vart_de + _TURES:.3f}"


@pytest.mark.skipif(not _KIT.is_dir(), reason="a 684-merokeszlet NAS-os mérőkészlet nem elérhető")
def test_nightvision_alap_magasfrekvencias_korrelacio_g_ben():
    """A zajminta képpontra egyezik: a `x − Gauss(σ = 3)` összetevő
    Pearson-korrelációja a Picasa-exporttal G-ben ≥ 0,98. Mérve: 0,985
    (R 0,900, B 0,822); a korábbi `numpy`-zajjal G 0,869 (R 0,406, B
    0,108) — a G-t a zöld gradiens élei is viszik, a zaj egyezését az R és
    a B ugrása mutatja."""
    import cv2

    load, _ = _golden_eszkozok()
    nev = "nightvision__alap.jpg"
    forras = load(_KIT / nev)
    export = load(_KIT / "export" / nev).astype(np.float64)
    kep = apply_filters(forras, parse_filters(_GOLDEN_ESETEK[0][2])).image.astype(np.float64)

    def magas(x):
        return x - cv2.GaussianBlur(x, (0, 0), 3)

    korr = np.corrcoef(magas(kep)[..., 1].ravel(), magas(export)[..., 1].ravel())[0, 1]
    assert korr >= 0.98, f"G-korreláció {korr:.3f} < 0,98"
