"""#2227 + #3805 — a `Resize` mintavételezője: kicsinyítéskor és 1:1-nél
DOBOZ, nagyításkor Mitchell–Netravali (B = C = 0,4), fixpontos súlyokkal.

## A lelet

Az eredeti `ResizeImageOperation` alkalmazója (`0x00bc3650`) a végén
ugyanazt a `0x00bcb5e0` segédfüggvényt hívja, amit a
`RotateImageOperation` — az pedig a `ytResampler`-t hívja **explicit**
móddal (spec: `docs/specs/filterdesc-registry.md`, 5/c):

* **A mód** a VÍZSZINTES cél/forrás léptékből: `≤ 1` (kicsinyítés vagy
  1:1) → **0-s doboz**, egyébként **3-as Mitchell**. Ugyanaz a mód fut
  MINDKÉT tengelyen.
* **A doboz**: súly 1, ha `|x| < 0,5` (a határon álló csap nem számít), a
  kicsinyítés léptékével nyújtva. Csap: `j + 0,5`, középpont
  `c = (i + 0,5) · forrás/cél`.
* **Egész súlyok**: `csonk(w · 16383 / Σw)`, a maradék a `csonk(c)` csapé.
* **A kimenet**: a vízszintes menetben `(Σ w·p + 255) >> 14`; a függőleges
  menet utolsó `W mod 4` oszlopán `(Σ w·p) >> 14` (#4004).

A #2227 előtt bilineáris, a #3805 előtt tengelyenként döntő, lebegőpontos
Mitchell volt — a `Pixelate` ettől elkent blokkszíneket adott (ΔE 4,64).

## Amit ezek a próbák mérnek

A Mitchell-mag **negatív oldallebenyt** visel, ezért nagyításkor egy éles
élen **túllövést** ad — a doboz soha nem lép a bemeneti szélsőértékeken
kívülre. A módválasztást ez a különbség azonosítja. A fixpontos képletet a
jegy 960 → 48-as példája és egy független, ciklusos referencia rögzíti; a
Picasa-egyezést a 684-es készlet golden-mérése.
"""

# rontás-kontroll: a `glimmer_ops._RESIZE_EGYSEG` 16383 → 16384 → 14 failed
# (a képletpróbák, a független referencia és a súlyösszegek); a `+ 255`
# kerekítő elhagyva → 13 failed; a módválasztás `<=` → `<` (1:1-nél Mitchell)
# → 1 failed (`csak_az_EGYIK_tengely`); `doboz = False` (a #3805 előtti
# Mitchell-kicsinyítés, fixpontosan) → 10 failed, köztük a golden
# `pixelate__alap`/`__min` és a két `picnikfocalpixelate`; a `focal.py`
# visszaírva `cv2.INTER_AREA`-ra → 2 failed (a közös-út próba és a golden
# `picnikfocalpixelate__alap`).

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

from picasapy.render.glimmer_ops import resize_image


def _elkep(szelesseg: int = 16, magassag: int = 16) -> np.ndarray:
    """Bal fele fekete, jobb fele fehér — egyetlen függőleges él."""
    kep = np.zeros((magassag, szelesseg, 3), dtype=np.uint8)
    kep[:, szelesseg // 2:] = 255
    return kep


# ---------------------------------------------------------------------------
# Független, ciklusos referencia a spec 5/c pontjából
# ---------------------------------------------------------------------------


def _mitchell(x: float) -> float:
    b = c = 0.4
    t = abs(x)
    if t < 1:
        return ((12 - 9 * b - 6 * c) * t**3 + (-18 + 12 * b + 6 * c) * t**2 + (6 - 2 * b)) / 6
    if t < 2:
        return (
            (-b - 6 * c) * t**3 + (6 * b + 30 * c) * t**2 + (-12 * b - 48 * c) * t + (8 * b + 24 * c)
        ) / 6
    return 0.0


def _ref_tengely(
    sorok: np.ndarray, ki: int, doboz: bool, *, fuggoleges: bool = False
) -> np.ndarray:
    """Független tengelyreferencia, a #4004 szerinti függőleges maradékkal."""
    n = sorok.shape[0]
    skala = np.float32(n) / np.float32(ki)
    nyujtas = max(1.0, float(skala))
    sugar = (0.5 if doboz else 2.0) * nyujtas
    kimenet = np.zeros((ki,) + sorok.shape[1:], dtype=np.int64)
    kerekito = 255
    if fuggoleges:
        kerekito = np.full(sorok.shape[1:], 255, dtype=np.int64)
        kerekito[sorok.shape[1] & ~3 :] = 0
    for i in range(ki):
        c = float(np.float32(np.float32(i + 0.5) * skala))
        csapok = [j for j in range(n) if abs(j + 0.5 - c) < sugar]
        if doboz:
            w = [1.0] * len(csapok)
        else:
            w = [_mitchell((j + 0.5 - c) / nyujtas) for j in csapok]
        osszeg = sum(w)
        egesz = [int(v * 16383 / osszeg) for v in w]
        also, felso = (csapok[0], csapok[-1]) if csapok else (0, n - 1)
        maradek_csap = min(max(int(c), also), felso)
        if maradek_csap not in csapok:
            csapok.append(maradek_csap)
            egesz.append(0)
        egesz[csapok.index(maradek_csap)] += 16383 - sum(egesz)
        acc = sum(wi * sorok[j].astype(np.int64) for wi, j in zip(egesz, csapok, strict=True))
        kimenet[i] = np.clip(acc + kerekito, 0, 0x3FFFFF) >> 14
    return kimenet.astype(np.uint8)


def _referencia(kep: np.ndarray, szelesseg: int, magassag: int) -> np.ndarray:
    doboz = szelesseg / kep.shape[1] <= 1.0
    vizszintes = np.swapaxes(_ref_tengely(np.swapaxes(kep, 0, 1), szelesseg, doboz), 0, 1)
    return _ref_tengely(vizszintes, magassag, doboz, fuggoleges=True)


class TestAFixpontosKeplet:
    """A jegy „Kész, ha" képletpróbája és a független referencia."""

    def test_960_48_a_jegy_keplete(self):
        """Lépték 20: a 20 csap súlya 819, a maradék 3 a `20i + 10`-esé."""
        sor = np.random.default_rng(3805).integers(0, 256, (1, 960, 3), dtype=np.uint8)
        ki = resize_image(sor, 48, 1)
        p = sor[0].astype(np.int64)
        blokkok = p.reshape(48, 20, 3)
        vart = (819 * blokkok.sum(axis=1) + 3 * p[10::20] + 255) >> 14
        np.testing.assert_array_equal(ki[0], vart.astype(np.uint8))

    def test_csonkol_nem_kerekit(self):
        """`[1, 1, 0]` átlaga 0,67; a lebegőpontos `rint` 1-et adna, a
        fixpontos `(2·5461 + 255) >> 14` 0-t."""
        kep = np.array([[[1, 1, 1], [1, 1, 1], [0, 0, 0]]], dtype=np.uint8)
        assert resize_image(kep, 1, 1)[0, 0].tolist() == [0, 0, 0]

    def test_a_koztes_kep_8_bites(self):
        """Két menet: a vízszintes kimenete egész, a függőleges erre épül.

        Vízszintesen `[2, 2, 1]` → 1 és `[3, 3, 2]` → 2 (csonkolva);
        függőlegesen `(8191·1 + 8192·2) >> 14 = 1`. Lebegőpontos
        köztes képpel (1,67 és 2,67) ugyanez 2 lenne."""
        kep = np.array([[[2] * 3, [2] * 3, [1] * 3], [[3] * 3, [3] * 3, [2] * 3]], dtype=np.uint8)
        assert resize_image(kep, 1, 1)[0, 0].tolist() == [1, 1, 1]

    @pytest.mark.parametrize(
        ("be", "ki"),
        [((13, 17), (5, 7)), ((9, 30), (4, 11)), ((6, 7), (13, 19)), ((10, 8), (3, 19)), ((5, 12), (11, 6))],
        ids=["kicsinyites", "nem-egesz-leptek", "nagyitas", "vizszintes-nagy-fuggoleges-kicsi",
             "vizszintes-kicsi-fuggoleges-nagy"],
    )
    def test_a_fuggetlen_referenciaval_BITRE(self, be, ki):
        magas, szeles = be
        kep = np.random.default_rng(sum(be) + sum(ki)).integers(
            0, 256, (magas, szeles, 3), dtype=np.uint8
        )
        np.testing.assert_array_equal(
            resize_image(kep, ki[1], ki[0]), _referencia(kep, ki[1], ki[0])
        )


class TestAModvalasztas:
    """A VÍZSZINTES lépték dönt, és a mód mindkét tengelyre ugyanaz."""

    def test_azonos_meretre_VALTOZATLAN(self):
        kep = np.random.default_rng(7).integers(0, 256, (24, 32, 3), dtype=np.uint8)
        assert np.array_equal(resize_image(kep, 32, 24), kep)

    def test_csak_az_EGYIK_tengely_valtozatlan(self):
        """Vízszintes lépték 1 → doboz mindkét tengelyen: a függőleges
        nagyítás sem lő túl, és a vízszintes menet azonosság."""
        kep = np.full((16, 16, 3), 64, dtype=np.uint8)
        kep[8:] = 192
        kep[:, 3] = 10
        eredmeny = resize_image(kep, 16, 40)
        assert eredmeny.shape == (40, 16, 3)
        assert eredmeny.min() == 10 and eredmeny.max() == 192
        assert (eredmeny[:, 3] == 10).all()

    def test_vizszintes_kicsinyites_a_fuggolegest_is_dobozolja(self):
        kep = np.full((16, 16, 3), 64, dtype=np.uint8)
        kep[8:] = 192
        eredmeny = resize_image(kep, 8, 64)
        assert eredmeny.min() == 64 and eredmeny.max() == 192

    def test_vizszintes_nagyitas_a_fuggolegest_is_Mitchellel_futtatja(self):
        """Függőleges KICSINYÍTÉS, mégis Mitchell: a vízszintes dönt."""
        kep = np.full((64, 8, 3), 64, dtype=np.uint8)
        kep[32:] = 192
        eredmeny = resize_image(kep, 16, 24).astype(np.int32)
        assert eredmeny.min() < 64 and eredmeny.max() > 192


class TestAMitchellTULLOVES:
    """Nagyításkor a magot a negatív oldallebeny azonosítja."""

    def test_nagyitaskor_TULLO_a_bemeneti_tartomanyon(self):
        """SZÜRKE él, hogy a 0/255 levágás ne rejtse el a túllövést."""
        kep = np.full((16, 16, 3), 64, dtype=np.uint8)
        kep[:, 8:] = 192
        eredmeny = resize_image(kep, 64, 16).astype(np.int32)
        assert eredmeny.min() < 64, f"nincs alullövés (min = {eredmeny.min()})"
        assert eredmeny.max() > 192, f"nincs túllövés (max = {eredmeny.max()})"

    def test_a_BILINEARIS_kimenete_MAS(self):
        import cv2

        kep = _elkep(16, 16)
        mienk = resize_image(kep, 64, 16)
        bilin = cv2.resize(kep, (64, 16), interpolation=cv2.INTER_LINEAR)
        assert not np.array_equal(mienk, bilin)

    def test_a_KOBOS_kimenete_is_MAS(self):
        """Az OpenCV `INTER_CUBIC` Catmull–Rom-szerű, NEM Mitchell."""
        import cv2

        kep = _elkep(16, 16)
        mienk = resize_image(kep, 64, 16)
        kobos = cv2.resize(kep, (64, 16), interpolation=cv2.INTER_CUBIC)
        assert not np.array_equal(mienk, kobos)


class TestAMagMAGA:
    def test_a_mag_ertekei_a_KEPLETBOL(self):
        from picasapy.render.glimmer_ops import mitchell_netravali

        assert mitchell_netravali(np.array([0.0]))[0] == pytest.approx(5.2 / 6, abs=1e-9)
        assert mitchell_netravali(np.array([1.0]))[0] == pytest.approx(
            (-2.8 + 14.4 - 24 + 12.8) / 6, abs=1e-9
        )
        assert mitchell_netravali(np.array([2.0]))[0] == pytest.approx(0.0, abs=1e-9)

    def test_a_mag_NEGATIV_az_oldallebenyen(self):
        from picasapy.render.glimmer_ops import mitchell_netravali

        assert (mitchell_netravali(np.linspace(1.05, 1.95, 19)) < 0).any()


class TestASmoothingAgaMarad:
    def test_smoothing_hamis_a_LEGKOZELEBBI_szomszed(self):
        """Mérve (5/a): `smoothing=false` a 9-es, legközelebbi-szomszéd ág."""
        import cv2

        kep = _elkep(16, 16)
        assert np.array_equal(
            resize_image(kep, 64, 16, smoothing=False),
            cv2.resize(kep, (64, 16), interpolation=cv2.INTER_NEAREST),
        )


class TestAKicsinyitesiNyujtas:
    """#3321: a mag KICSINYÍTÉSKOR a léptékkel nyúlik — mérve (5/b).

    A Mitchell-mag kicsinyítéskor csak akkor fut, ha a VÍZSZINTES tengely
    nagyít, ezért a próba a függőleges tengelyt kicsinyíti vízszintes
    csíkokkal. A kontroll megmutatja, hogy az állításnak van foga.
    """

    @staticmethod
    def _csikos(magassag: int = 64, szelesseg: int = 4) -> np.ndarray:
        """Egy képpont magas, vízszintes fekete-fehér csíkok (Nyquist)."""
        kep = np.zeros((magassag, szelesseg, 3), dtype=np.uint8)
        kep[::2] = 255
        return kep

    #: A 64 → 9 arány SZÁNDÉKOS: a kettő hatványainál a nyújtás nélküli
    #: kontroll is pontosan középszürkét adna, és a próba vakon átmenne.
    KI_MAGASSAG = 9

    def test_a_kicsinyites_ATLAGOL_nem_aliasol(self):
        kicsi = resize_image(self._csikos(), 8, self.KI_MAGASSAG)
        oszlop = kicsi[:, 3, 0].astype(np.float64)
        assert oszlop.std() < 12.0, f"a kimenet szórása {oszlop.std():.1f}"
        assert 96.0 < oszlop.mean() < 160.0

    def test_a_NYUJTAS_NELKULI_mag_ELBUKNA(self):
        """Ellenpróba: ugyanaz a mag rögzített 2-es támasszal aliasol."""
        from picasapy.render.glimmer_ops import mitchell_netravali

        be, ki = 64, self.KI_MAGASSAG
        kozep = (np.arange(ki) + 0.5) * (be / ki) - 0.5
        indexek = np.ceil(kozep - 2.0).astype(np.int64)[:, None] + np.arange(5)[None, :]
        sulyok = mitchell_netravali(kozep[:, None] - indexek)
        sulyok /= sulyok.sum(axis=1, keepdims=True)
        oszlop = (self._csikos()[np.clip(indexek, 0, be - 1), 0, 0] * sulyok).sum(axis=1)
        assert oszlop.std() > 50.0

    def test_a_sulyok_a_MERT_nyujtast_hasznaljak(self):
        from picasapy.render.glimmer_ops import _tengely_sulyok

        _, kicsi = _tengely_sulyok(64, 8, doboz=False)
        _, azonos = _tengely_sulyok(8, 8, doboz=False)
        assert kicsi.shape[1] > azonos.shape[1]

    def test_nagyitaskor_NINCS_nyujtas(self):
        from picasapy.render.glimmer_ops import _tengely_sulyok

        _, nagy = _tengely_sulyok(8, 64, doboz=False)
        _, azonos = _tengely_sulyok(8, 8, doboz=False)
        assert nagy.shape[1] == azonos.shape[1]

    @pytest.mark.parametrize(("be", "ki"), [(64, 8), (8, 64), (960, 48), (7, 3), (3, 7), (16, 40)])
    @pytest.mark.parametrize("doboz", [True, False])
    def test_a_sulyok_osszege_16383(self, be, ki, doboz):
        from picasapy.render.glimmer_ops import _tengely_sulyok

        _, sulyok = _tengely_sulyok(be, ki, doboz=doboz)
        assert (sulyok.sum(axis=1) == 16383).all()


class TestAFocalPixelateKozosUton:
    """#3805: a `PicnikFocalPixelate` kicsinyítése is a közös `resize_image`."""

    def test_maszk_nelkul_a_resize_image_blokkjai(self):
        import cv2

        from picasapy.render.focal import apply_focal_pixelate

        kep = np.random.default_rng(11).integers(0, 256, (60, 90, 3), dtype=np.uint8)
        # Reverse: a kör KÜLSEJE éles, a belseje pixeles — a nagy sugár a
        # teljes képet lefedi, tehát a kimenet maga a pixelesített kép
        ki = apply_focal_pixelate(kep, impact=7.0, radius=400.0, hardness=100.0, reverse=True)
        kicsi = resize_image(kep, int(90 / 7.0), int(60 / 7.0), smoothing=True)
        vart = resize_image(kicsi, 90, 60, smoothing=False)
        np.testing.assert_array_equal(ki, vart)
        area = cv2.resize(kep, (int(90 / 7.0), int(60 / 7.0)), interpolation=cv2.INTER_AREA)
        assert not np.array_equal(kicsi, area), "a kontroll nem különbözteti meg a két utat"


# ---------------------------------------------------------------------------
# FEJLESZTŐI GÉPEN futó golden-mérés a valódi Picasa-exporttal; ha a készlet
# nincs a gépen, skip.
# ---------------------------------------------------------------------------

_KIT = Path("/mnt/nas/My Pictures/684-merokeszlet")

#: A mért érték + 0,05-ös tűrés.
_TURES = 0.05

#: (név, lánc, mért ΔE a #3805 után; a megjegyzésben a #3805 előtti)
_GOLDEN_ESETEK = [
    ("pixelate__alap", "Pixelate=1,20.000000,9.000000,0.000000;", 0.098),  # előtte 4,638
    ("pixelate__min", "Pixelate=1,2.000000,0.000000,0.000000;", 0.128),  # előtte 0,783
    ("pixelate__max", "Pixelate=1,150.000000,9.000000,100.000000;", 0.121),  # előtte 0,121
    (
        "picnikfocalpixelate__alap",
        "PicnikFocalPixelate=1,0.500000,0.500000,20.000000,105.000000,50.000000,0.000000,0.000000;",
        0.231,  # előtte 0,321 (`cv2.INTER_AREA`)
    ),
    (
        "picnikfocalpixelate__min",
        "PicnikFocalPixelate=1,0.500000,0.500000,2.000000,10.000000,0.000000,0.000000,0.000000;",
        0.114,  # előtte 0,162 (`cv2.INTER_AREA`)
    ),
]


def _golden_eszkozok():
    gyoker = Path(__file__).resolve().parents[2]
    utvonal = str(gyoker / "tools" / "golden")
    if utvonal not in sys.path:
        sys.path.insert(0, utvonal)
    from analyze_validation_kit import load, mean_de

    return load, mean_de


@pytest.mark.parametrize(("nev", "lanc", "vart_de"), _GOLDEN_ESETEK, ids=[e[0] for e in _GOLDEN_ESETEK])
def test_golden_a_hatarertek_alatt(nev, lanc, vart_de):
    from picasapy.ini.filters import parse_filters
    from picasapy.render.chain import apply_filters

    export_ut = _KIT / "export" / f"{nev}.jpg"
    if not export_ut.is_file():
        pytest.skip(f"a mérőkészlet nem elérhető: {export_ut}")
    load, mean_de = _golden_eszkozok()
    kep = apply_filters(load(_KIT / f"{nev}.jpg"), parse_filters(lanc)).image
    de = mean_de(kep, load(export_ut))
    assert de <= vart_de + _TURES, f"{nev}: ΔE {de:.3f} > {vart_de + _TURES:.3f}"
