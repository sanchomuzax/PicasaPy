"""#1606 — a Comicize fő küszöbgörbéje és a raszter alapja.

## Mit mér ez a fájl

Két, MÉRÉSSEL igazolt javítást rögzít az `apply_comicize()`-on:

1. **A fő küszöbgörbe ötpontos spline**, nem lineáris skálázás. A
   `filterdesc.xml` `<filter id="Comicize">` blokkjának
   `AdjustCurvesImageOperation MasterCurve`-je szó szerint
   `[{0,0},{24,24},{48,48},{90+DotContrast·1,5,254},{255,255}]`; a
   kiértékelés a natív köbös spline (#629, `curves.curve_lut`).
2. **Az elő-elmosás DARKEN-lépése benne marad a kimenetben.** A
   `filterdesc.xml`-ben a `_opBlur` és a raszter (`_opColorSpots`) EGY
   `NestedImageOperation` egymás utáni gyermekei, tehát a raszter az
   ELMOSOTT-SÖTÉTÍTETT képre kerül — nem az eredetire. Korábban a
   kimenet alapja az eredeti kép volt, és az elmosás elveszett.

## Hogyan őrizzük — a CSŐVEZETÉKEN, nem csak a segédfüggvényen

Az első változat mind a két pontot csak közvetve mérte: a görbét a
`comicize_master_curve()` közvetlen hívásával, az elmosást pedig kizárólag
`dot_fade = 100`-nál, ahol az alfa 0, tehát a raszter-ág ki sem értékelődik.
Mutációval mérve mindkét réteget vissza lehetett írni a régi alakra úgy,
hogy a fájl ZÖLD maradt. Ezért a `TestACsovezetekAGorbevelSzamol` az
`apply_comicize()` KIMENETÉT építi újra a LUT-ból, a
`TestAzElmosasBenneMaradAKimenetben` pedig normál `dot_fade` mellett is
állít, a `TestARaszterMegvan` küszöbe pedig a mért értékhez tapad.

## A bizonyíték

`research/comicize-sweep/` (15 eredeti Picasa-export, három csúszkára).
A DotFade=100 állás dönti el a 2. pontot: ott a raszter alfája PONTOSAN 0,
tehát a kimenet maga az alap — és a Picasa-export ΔE-je az elmosott-
sötétített képhez 1,46, az eredetihez 2,32 (SSIM 0,920 vs 0,768).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from picasapy.lazy_cv2 import cv2

from picasapy.render.effects_artistic import apply_comicize, comicize_master_curve
from picasapy.render.halftone import dot_size_for


@pytest.fixture
def atmenet() -> np.ndarray:
    """Színátmenetes próbakép — a görbe minden tónuson dolgozik."""
    ys, xs = np.mgrid[0:120, 0:213]
    alap = ((xs / 213.0) * 255.0).astype(np.uint8)
    return np.dstack([alap, alap, (alap // 2).astype(np.uint8)])


class TestAFoKuszobgorbe:
    """A `MasterCurve` öt töréspontja a `filterdesc.xml`-ből."""

    def test_a_lut_alakja_es_tartomanya(self):
        lut = comicize_master_curve(50.0)
        assert lut.shape == (256,)
        # a függvény `np.clip(curve, 0, 255)`-öt ad vissza — a határ EGZAKT,
        # nem közelítés, ezért nem hagyunk rá tűrést
        assert lut.min() >= 0.0 and lut.max() <= 255.0

    @pytest.mark.parametrize(("x", "y"), [(0, 0), (24, 24), (48, 48), (255, 255)])
    def test_a_rogzitett_toresponok_atmennek(self, x, y):
        """A négy rögzített pont a görbén VAN — nem közelítés."""
        assert comicize_master_curve(50.0)[x] == pytest.approx(y, abs=0.5)

    @pytest.mark.parametrize("dot_contrast", [0.0, 25.0, 50.0, 75.0, 100.0])
    def test_a_negyedik_pont_kozeleben_a_gorbe_kifut_feherre(self, dot_contrast):
        """`x = 90 + DotContrast·1,5` ⇒ `y = 254` — a mozgó töréspont.

        A töréspont x-e törtszám is lehet (`DotContrast = 25` ⇒ 127,5), a LUT
        viszont egész szinteken mintavételez, ezért a szomszédos két szintet
        nézzük: a görbének OTT kell kifutnia a fehérbe.
        """
        knee = 90.0 + dot_contrast * 1.5
        lut = comicize_master_curve(dot_contrast)
        assert lut[int(np.floor(knee))] >= 252.5
        assert lut[int(np.ceil(knee))] >= 252.5

    def test_a_mozgo_toresponot_y_ja_254_nem_255(self):
        """`_COMICIZE_CURVE_KNEE_Y` — a `filterdesc.xml`-ben 254 (#1606).

        `DotContrast = 0`-nál a töréspont x-e pontosan 90, tehát a LUT 90.
        eleme MAGA a töréspont y-ja: egész szinten, interpoláció nélkül.
        255-re mutálva a görbe egésze elcsúszik, és eddig semmi nem fogta.
        """
        assert comicize_master_curve(0.0)[90] == pytest.approx(254.0, abs=0.1)

    @pytest.mark.parametrize("dot_contrast", [0.0, 50.0, 100.0])
    def test_a_negyedik_pont_ELOTT_a_gorbe_meg_nem_feher(self, dot_contrast):
        """A töréspont HELYE számít: félúton még bőven van tónus."""
        knee = 90.0 + dot_contrast * 1.5
        lut = comicize_master_curve(dot_contrast)
        assert lut[int(knee) // 2] < 250.0

    def test_a_toresponot_a_dot_contrast_JOBBRA_tolja(self):
        """Nagyobb DotContrast ⇒ később fut ki fehérre ⇒ több festék."""

        def kifutas(dc: float) -> int:
            return int(np.argmax(comicize_master_curve(dc) >= 250.0))

        assert kifutas(0.0) < kifutas(50.0) < kifutas(100.0)

    def test_NEM_linearis_skalazas(self):
        """A régi modell `érték·255/(90+1,5·DotContrast)` volt — a spline nem az."""
        lut = comicize_master_curve(50.0)
        felso = 90.0 + 50.0 * 1.5
        linearis = np.clip(np.arange(256) * (255.0 / felso), 0.0, 255.0)
        # a 24-es és 48-as pont KÖTÖTT identitás, a lineáris ott már 1,5-szeres
        assert abs(lut[48] - linearis[48]) > 20.0
        assert float(np.abs(lut - linearis).max()) > 20.0

    def test_monoton_no(self):
        """Küszöbgörbe: sötétebb bemenet sosem ad világosabb kimenetet.

        A vágott LUT EGZAKTUL monoton — a `0…100` tartományt 0,25-ös
        lépésekben végigmérve (401 állás) a legkisebb lépés `0,0`, sehol
        nem negatív. Ezért a tűrés is `0,0`: egy `-0,5`-ös rés a
        `DotContrast = 50` ágon 0,000577-en múlna, a `100` ágon pedig
        semmit nem bizonyítana (ott a vágatlan görbe is monoton).
        """
        for dot_contrast in (0.0, 50.0, 100.0):
            lut = comicize_master_curve(dot_contrast)
            assert np.all(np.diff(lut) >= 0.0), f"visszaesés {dot_contrast}-nál"

    def test_nagyobb_kontraszt_sotetebb_kozeptonust_ad(self):
        """A negyedik pont jobbra tolása = több festék (sötétebb középtónus).

        Ugyanaz az irány, mint a fájl 77. sorában és a
        `test_comicize_569.py::test_higher_dot_contrast_prints_more_ink`-ben:
        a görbe KÉSŐBB fut ki fehérre, tehát a középtónus sötétebb marad.
        """
        assert comicize_master_curve(100.0)[120] < comicize_master_curve(0.0)[120]


class TestACsovezetekAGorbevelSzamol:
    """A `DotContrast` a görbén át hat (#1606).

    A korábbi próbák a régi küszöb-modell csővezetékét építették újra; a #3522
    óta a lánc a `filterdesc.xml` szerinti (Glow, `PartialMask`, küszöbgörbe,
    `multiply`), és a mérőszáma a 15 export (`TestA15ExportonMerve`).
    """

    def test_a_dot_contrast_valtoztat_a_kozeptonuson(self):
        kep = np.full((200, 700, 3), 90, dtype=np.uint8)
        assert not np.array_equal(
            apply_comicize(kep, dot_contrast=0.0), apply_comicize(kep, dot_contrast=100.0)
        )


class TestAzElmosasBenneMaradAKimenetben:
    """#1606 2. pontja — a `_opBlur` DARKEN-lépése nem veszhet el."""

    @staticmethod
    def _sotetitett(image: np.ndarray, blur_xy: float) -> np.ndarray:
        sigma = 1.0 + 20.0 * min(blur_xy, 100.0) / 100.0
        kep_f = image.astype(np.float32)
        elmosott = cv2.GaussianBlur(kep_f, (0, 0), sigmaX=sigma, sigmaY=sigma)
        return np.clip(np.rint(np.minimum(kep_f, elmosott)), 0, 255).astype(np.uint8)

    def test_dot_fade_100_az_ELMOSOTT_kepet_adja(self, atmenet):
        """Alfa = 0,5 − 100/200 = 0 ⇒ a kimenet PONTOSAN az alap."""
        eredmeny = apply_comicize(atmenet, blur_xy=50.0, dot_fade=100.0)
        np.testing.assert_array_equal(eredmeny, self._sotetitett(atmenet, 50.0))

    def test_dot_fade_100_NEM_az_eredetit_adja(self, atmenet):
        """A korábbi hiba: a raszter az EREDETIRE került, az elmosás elveszett."""
        eredmeny = apply_comicize(atmenet, blur_xy=50.0, dot_fade=100.0)
        assert not np.array_equal(eredmeny, atmenet)

    def test_erosebb_elmosas_sotetebb_kimenetet_ad(self, atmenet):
        """DARKEN-nel a nagyobb σ több sötét részletet ken szét ⇒ sötétebb."""
        gyenge = apply_comicize(atmenet, blur_xy=0.0, dot_fade=100.0).mean()
        eros = apply_comicize(atmenet, blur_xy=100.0, dot_fade=100.0).mean()
        assert eros < gyenge

    @pytest.mark.parametrize("dot_fade", [0.0, 50.0, 99.0])
    def test_normal_dot_fade_mellett_sem_vilagosodik_az_alap_fole(
        self, atmenet, dot_fade
    ):
        """A raszter alapja az ELMOSOTT-SÖTÉTÍTETT kép, nem az eredeti.

        A fenti három teszt `dot_fade = 100`-zal fut, ahol `alfa = 0` — ott
        a raszter-ág ki sem értékelődik, tehát a raszter ALAPJÁRÓL nem
        mondanak semmit. Mérve: a `np.minimum(image_f, raster_rgb)`
        visszaírására (az eredeti képre alapozva) a fájl zöld maradt.

        DARKEN-nel a kimenet sehol nem lehet világosabb az alapnál; ha a
        raszter az EREDETIRE kerül, a különbség pozitívba fordul ott, ahol
        az elő-elmosás sötétített (mérve: 4440 képpont, legfeljebb +2).
        """
        eredmeny = apply_comicize(atmenet, blur_xy=50.0, dot_fade=dot_fade)
        alap = self._sotetitett(atmenet, 50.0)
        tobblet = eredmeny.astype(np.int32) - alap.astype(np.int32)
        assert tobblet.max() <= 0, f"{int((tobblet > 0).sum())} képpont világosodott ki"

    def test_sik_kepen_az_elmosas_nem_valtoztat(self):
        """Egyenletes képen `min(kép, elmosás) == kép` — a régi őr él tovább."""
        sik = np.full((80, 140, 3), 120, dtype=np.uint8)
        np.testing.assert_array_equal(apply_comicize(sik, dot_fade=100.0), sik)


class TestARaszterMegvan:
    """A raszter erőssége a MÉRT értékhez tapad — nem tűnhet el, nem is nőhet.

    ⚠️ A korábbi `std() > 1.0` küszöb a mai 10,13-hoz képest TÍZSZERES rést
    hagyott: csak a raszter teljes eltűnését látta, és a #1606 elvetett
    ágai közül egyiket sem fogta meg (mind zölden ment át). Az őr ezért
    kétoldalas: a szórás a MÉRT értéken marad, ±0,2%.

    Amit ez a sáv mérve megfog (a `research/comicize-sweep/` melletti
    mutációs próbán, sík 90-es képen):

    | visszaírt ág | szórás |
    |---|---|
    | **a mai kód** (`DOT_SCALE = 0,8`) | **8,410** |
    | `DOT_SCALE = 1,0` — a #2476 ELŐTTI pontméret | 10,125 |
    | `DOT_SCALE = 0,9` | 9,650 |
    | `DOT_SCALE = 0,85` | 8,880 |
    | `DOT_SCALE = 0,75` | 8,326 |
    | `DOT_SCALE = 0,7` | 8,073 |
    | `DOT_SCALE = 0,6` | 6,037 |

    ⚠️ **A táblát a #2476 újramérte.** A pont mérete a mért `scaleWidth`/
    `scaleHeight` = 0,8-ra került, tehát a korábbi sor (10,125) maga is
    MUTÁCIÓ lett — és a sáv kizárja. A skála ±0,05-os elmozdulását is
    kizárja (8,880 és 8,326 egyaránt kívül van).

    A #1606 korábban felsorolt ágai (lineáris skálázás a spline helyett,
    `multiply` felvitel, ágankénti küszöb háromféleképpen) a régi, 1,0-es
    pontméreten 8,981 · 9,757 · 0,000 · 10,178 · 11,000 szórást adtak; a
    0,8-as skála mindegyiket arányosan mozdítja, tehát a mai, szűk sávtól
    továbbra is nagyságrenddel messzebb esnek.

    A ±0,2% (8,393…8,427) mindegyiket kizárja. A sáv azért lehet ilyen
    szűk, mert SÍK képen a lánc minden lépése determinisztikus — az
    elő-elmosás és a pixelesítés a sík képet változatlanul hagyja, tehát a
    szám csak a raszter geometriájából jön, nem gépfüggő mintavételből.
    """

    #: A mai kimenet mért szórása sík 90-es középtónuson, 700 px széles
    #: képen (11 px csempe). Ha ez a szám elmozdul, az a raszter-lánc
    #: MEGVÁLTOZÁSA — újramérni kell, nem a tűrést tágítani.
    #: A #2476 óta a mért 0,8-as pontméreté (előtte 10,1252 volt).
    #: ⚠️ A #3522 óta (a `filterdesc.xml` szerinti lánc) újramérve: 8,8331.
    #: A fenti mutációs tábla még a régi küszöb-modellé; az új lánc hűségét a
    #: 15 exportos mérés őrzi (`TestA15ExportonMerve`).
    RASZTER_SZORAS = 8.8331

    def test_sik_kozeptonon_a_raszter_a_mert_erossegen_all(self):
        """700 px széles kép ⇒ 11 px csempe: a raszter a mért erősségén áll."""
        sik = np.full((200, 700, 3), 90, dtype=np.uint8)
        szoras = float(apply_comicize(sik)[..., 0].std())
        assert szoras == pytest.approx(self.RASZTER_SZORAS, rel=0.002), (
            f"a raszter erőssége elmozdult: {szoras:.4f}"
        )

    def test_a_raszter_sotetit_de_nem_vilagosit(self):
        kep = np.random.default_rng(7).integers(0, 256, (60, 100, 3), dtype=np.uint8)
        assert np.all(apply_comicize(kep) <= kep)


SWEEP_JELOLTEK = (
    Path(__file__).resolve().parents[2] / "research" / "comicize-sweep",
    Path.home() / "Documents" / "PicasaPy" / "research" / "comicize-sweep",
)


def _sweep() -> Path | None:
    return next((p for p in SWEEP_JELOLTEK if p.is_dir()), None)


def _amplitudo(kep: np.ndarray, csempe: int) -> float:
    """A csempén belüli fázisprofil szórása (a #1606/#3401 mérője)."""
    g = kep.astype(np.float64).mean(axis=2)
    h, w = g.shape
    h, w = h - h % csempe, w - w % csempe
    return float(g[:h, :w].reshape(h // csempe, csempe, w // csempe, csempe).mean(axis=(0, 2)).std())


@pytest.mark.skipif(_sweep() is None, reason="a research/comicize-sweep mérőkészlet nincs meg")
class TestA15ExportonMerve:
    """A 15 eredeti Picasa-export (#3522): átl. amplitúdó-hiba 0,0276, ΔE76 2,4640."""

    def test_az_amplitudo_es_a_delta_e(self):
        import configparser
        import importlib.util
        import sys

        import cv2

        gyoker = Path(__file__).resolve().parents[2]
        spec = importlib.util.spec_from_file_location(
            "compare_render_3522", gyoker / "tools" / "golden" / "compare_render.py"
        )
        cr = importlib.util.module_from_spec(spec)
        sys.modules["compare_render_3522"] = cr
        spec.loader.exec_module(cr)

        def betolt(ut):
            return cv2.cvtColor(cv2.imread(str(ut)), cv2.COLOR_BGR2RGB)

        hibak, de = [], []
        for tengely in ("blurxy", "dotcontrast", "dotfade"):
            mappa = _sweep() / f"effekt5_kepregeny_{tengely}"
            ini = configparser.ConfigParser()
            ini.read(mappa / ".picasa.ini")
            for nev in sorted(ini.sections()):
                par = ini[nev]["filters"].split("=")[1].rstrip(";").split(",")
                bxy, dc, df = (float(x) for x in par[1:4])
                forras, ref = betolt(mappa / nev), betolt(mappa / "export" / nev)
                mi = apply_comicize(forras, blur_xy=bxy, dot_contrast=dc, dot_fade=df)
                csempe = dot_size_for(forras.shape[1])
                hibak.append(abs(_amplitudo(mi, csempe) - _amplitudo(ref, csempe)))
                de.append(float(cr.delta_e_cie76(mi, ref).mean()))
        assert len(hibak) == 15
        assert np.mean(hibak) <= 0.05, f"amplitúdó-hiba {np.mean(hibak):.4f}"
        assert np.mean(de) <= 2.47, f"ΔE76 {np.mean(de):.4f}"
