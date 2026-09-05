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

import numpy as np
import pytest
from picasapy.lazy_cv2 import cv2

from picasapy.render.effects_artistic import apply_comicize, comicize_master_curve
from picasapy.render.halftone import dot_size_for, halftone_branch


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
    """#1606 1. pontja a CSŐVEZETÉKEN — nem csak a LUT-függvényben.

    A `TestAFoKuszobgorbe` a `comicize_master_curve()`-öt KÖZVETLENÜL hívja,
    tehát önmagában nem mondja meg, hogy az `apply_comicize()` egyáltalán
    használja-e. Mérve: a 3. lépést a régi lineáris skálázásra
    (`érték · 255 / (90 + DotContrast·1,5)`) visszaírva az egész fájl zöld
    maradt. Az itteni tesztek a KIMENETET a LUT-ból építik újra.
    """

    @staticmethod
    def _sik_kimenet(
        level: float, festek: float, dot_fade: float = 50.0,
        height: int = 200, width: int = 700,
    ) -> np.ndarray:
        """A csővezeték 4-7. lépése SÍK szürke képre, adott festékszinttel.

        Síkon `min(kép, elmosás) == kép`, és a pixelesítés sem változtat,
        ezért a raszter EGYETLEN bemenete a görbe kimenete — a 3. lépés
        teljes hatása egyetlen számba (`festek`) sűrűsödik. Így a
        visszaépítés nem másolja le a görbét, csak a köré épülő ágakat.
        """
        alap = np.full((height, width, 3), float(level), dtype=np.float32)
        dot = dot_size_for(width)
        tinta = np.full((height, width), float(festek), dtype=np.float32)
        raszter = np.minimum(
            halftone_branch(tinta, dot, 0.0, 0.0),
            halftone_branch(tinta, dot, dot / 2.0, dot / 2.0),
        )
        raszter_rgb = np.repeat(raszter[..., np.newaxis], 3, axis=-1)
        alfa = 0.5 - dot_fade / 200.0
        kimenet = alap + alfa * (np.minimum(alap, raszter_rgb) - alap)
        return np.clip(np.rint(kimenet), 0, 255).astype(np.uint8)

    @classmethod
    def _varhato(cls, level: int, dot_contrast: float = 50.0, **kw) -> np.ndarray:
        festek = float(comicize_master_curve(dot_contrast)[level])
        return cls._sik_kimenet(level, festek, **kw)

    @pytest.mark.parametrize("level", [30, 60, 90, 120])
    def test_a_kimenet_a_spline_LUT_jabol_epul_fel(self, level):
        """A csővezeték festékszintje PONTOSAN `comicize_master_curve()[L]`."""
        kep = np.full((200, 700, 3), level, dtype=np.uint8)
        np.testing.assert_array_equal(apply_comicize(kep), self._varhato(level))

    @pytest.mark.parametrize("dot_contrast", [0.0, 100.0])
    def test_a_dot_contrast_a_LUT_on_keresztul_hat(self, dot_contrast):
        """A csúszka nem külön képleten, hanem a görbén át fejti ki hatását."""
        kep = np.full((200, 700, 3), 90, dtype=np.uint8)
        np.testing.assert_array_equal(
            apply_comicize(kep, dot_contrast=dot_contrast),
            self._varhato(90, dot_contrast=dot_contrast),
        )

    @pytest.mark.parametrize("level", [24, 36, 48])
    def test_az_arnyekokat_a_csovezetek_NEM_vilagositja_ki(self, level):
        """0…48 között a görbe IDENTITÁS ⇒ a festék maga a tónus.

        A régi lineáris modell ugyanezt 1,5-szeresére húzta (`48 → 74`),
        amitől kevesebb festék jutott a csempére, és a kimenet
        VILÁGOSABB lett. Az őr a lineáris modell festékszintjével épített
        kimenethez méri: a mienknek sötétebbnek kell lennie.
        """
        kep = np.full((200, 700, 3), level, dtype=np.uint8)
        linearis_festek = min(level * 255.0 / (90.0 + 50.0 * 1.5), 255.0)
        assert apply_comicize(kep).mean() < self._sik_kimenet(
            level, linearis_festek
        ).mean()


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
    | **a mai kód** | **10,125** |
    | régi lineáris skálázás a spline helyett | 8,981 |
    | a raszter felvitele `multiply` | 9,757 |
    | ágankénti küszöb az ág kimenetén + `add` | 0,000 |
    | ágankénti küszöb a tintán + `add` | 10,178 |
    | ágankénti küszöb az ág kimenetén + `darken` | 11,000 |

    A ±0,2% (10,105…10,146) mindegyiket kizárja. A sáv azért lehet ilyen
    szűk, mert SÍK képen a lánc minden lépése determinisztikus — az
    elő-elmosás és a pixelesítés a sík képet változatlanul hagyja, tehát a
    szám csak a raszter geometriájából jön, nem gépfüggő mintavételből.
    """

    #: A mai kimenet mért szórása sík 90-es középtónuson, 700 px széles
    #: képen (11 px csempe). Ha ez a szám elmozdul, az a raszter-lánc
    #: MEGVÁLTOZÁSA — újramérni kell, nem a tűrést tágítani.
    RASZTER_SZORAS = 10.1252

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
