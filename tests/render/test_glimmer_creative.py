"""#381: `glimmer_creative` — Cinemascope/Orton/PencilSketch/Holga/Lomo/IR/
Neon min/alap/max határeset-tesztjei.
"""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

from picasapy.render import glimmer_creative as c
from tests.support.realistic_photo import make_realistic_photo


@pytest.fixture
def image() -> np.ndarray:
    rng = np.random.default_rng(21)
    img = rng.integers(20, 235, size=(64, 96, 3), dtype=np.uint8)
    img[:20, :, 0] = 220
    return img


def _real_photo_rgb(height: int, width: int, seed: int = 7) -> np.ndarray:
    """#504 (j1): VALÓDI, folytonos hisztogramú fotó-szerű kép, a
    `render/chain.py`/`export/exporter.py` mintáját követve BGR→RGB
    konvertálva (a glimmer-csővezeték RGB-terű, ld. `glimmer_ops.py`)."""
    return cv2.cvtColor(make_realistic_photo(height=height, width=width, seed=seed), cv2.COLOR_BGR2RGB)


def _assert_valid(result):
    assert result.dtype == np.uint8
    assert result.shape[2] == 3


class TestCinemascope:
    def test_letterbox_be(self, image):
        result = c.apply_cinemascope(image, letterbox=True)
        _assert_valid(result)
        assert result.shape[0] != image.shape[0] or result.shape[1] != image.shape[1]

    def test_letterbox_ki(self, image):
        result = c.apply_cinemascope(image, letterbox=False)
        _assert_valid(result)
        assert result.shape[1] == image.shape[1]

    def test_letterbox_sav_fekete(self, image):
        result = c.apply_cinemascope(image, letterbox=True)
        assert tuple(result[0, result.shape[1] // 2]) == (0, 0, 0)


class TestOrton:
    @pytest.mark.parametrize("bloom,brightness,fade", [(0.0, 0.0, 0.0), (25.0, 50.0, 0.0), (50.0, 100.0, 100.0)])
    def test_hatarok(self, image, bloom, brightness, fade):
        _assert_valid(c.apply_orton(image, bloom=bloom, brightness=brightness, fade=fade))

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(c.apply_orton(image, fade=100.0), image)


class TestPencilSketch:
    @pytest.mark.parametrize("radius,contrast,fade", [(1.3, 0.0, 0.0), (2.0, 100.0, 0.0), (5.0, 200.0, 100.0)])
    def test_hatarok(self, image, radius, contrast, fade):
        _assert_valid(c.apply_pencil_sketch(image, radius=radius, contrast=contrast, fade=fade))

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(c.apply_pencil_sketch(image, fade=100.0), image)


class TestHolga:
    @pytest.mark.parametrize("blur,grain,fade", [(0.0, 0.0, 0.0), (70.0, 30.0, 0.0), (100.0, 100.0, 100.0)])
    def test_hatarok(self, image, blur, grain, fade):
        _assert_valid(c.apply_holga(image, blur=blur, grain=grain, fade=fade))

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(c.apply_holga(image, fade=100.0), image)

    @pytest.mark.parametrize("height,width", [(64, 96), (600, 800)])
    def test_nem_fekete_a_kimenet(self, height, width):
        """#504: a Holga kisképe feketedett be nagy szigmájú belső
        ragyogásnál — a kimenet átlagos fényessége maradjon érdemben
        nulla fölött kicsi ÉS nagy képen is.
        """
        rng = np.random.default_rng(11)
        img = rng.integers(20, 235, size=(height, width, 3), dtype=np.uint8)
        result = c.apply_holga(img)
        assert result.mean() > 5.0


class TestLomo:
    @pytest.mark.parametrize("blur,fade", [(0.0, 0.0), (50.0, 0.0), (100.0, 100.0)])
    def test_hatarok(self, image, blur, fade):
        _assert_valid(c.apply_lomo(image, blur=blur, fade=fade))

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(c.apply_lomo(image, fade=100.0), image)

    @pytest.mark.parametrize("height,width", [(64, 96), (600, 800)])
    def test_nem_fekete_a_kimenet(self, height, width):
        """#504: a Lomo kisképe feketedett be (a 800×600-as eset a
        bejelentés szerint teljesen fekete volt, átlag ~0) — a kimenet
        átlagos fényessége maradjon érdemben nulla fölött kicsi ÉS nagy
        képen is.
        """
        rng = np.random.default_rng(11)
        img = rng.integers(20, 235, size=(height, width, 3), dtype=np.uint8)
        result = c.apply_lomo(img)
        assert result.mean() > 5.0

    def test_teljesitmeny_nagy_kepen_gyors(self):
        """#504: a nagy szigmájú belső ragyogás Gauss-elmosása O(percek)
        volt egy fényképméretű (2000×1500) képen — a leskálázott
        elmosásnak ez alá kell szorítania. Nagyvonalú korlát, hogy lassú
        CI-n se legyen ingatag (a mért érték ~1-1,5 s volt fejlesztői
        gépen, a régi kód ~37 s-ot vett igénybe ugyanitt).
        """
        from support.perf_baseline import merd_es_ellenorizd

        rng = np.random.default_rng(11)
        img = rng.integers(20, 235, size=(1500, 2000, 3), dtype=np.uint8)
        merd_es_ellenorizd("apply_lomo(2000x1500)", img, c.apply_lomo)


def _black_pct(img: np.ndarray) -> float:
    """A tiszta fekete (mindhárom csatornán 0) képpontok aránya, %."""
    return float(np.all(img == 0, axis=-1).mean() * 100.0)


class TestHolgaRealPhoto504510:
    """#504/#510 — VALÓDI (folytonos hisztogramú) fotóval mért regresszió,
    nem szintetikus szürke/zaj lappal (j1). A `main` állapotában a Holga
    sötét (~kétharmad tiszta fekete), de ez az `inner_glow`/`bw_tint`/
    kontraszt-lánc DOKUMENTÁLT, a `filterdesc.xml`-ből átvett receptjének
    a következménye, nem implementációs hiba — ld. a #504 utolsó
    kommentjét és a PR-jelentést. A teszt ezt a MÉRT állapotot rögzíti
    (nem "javítja meg" találgatással), plusz a #510 csatorna-sorrendet
    ellenőrzi.
    """

    def test_kimenet_szurke_r_egyenlo_b_vel(self):
        """#504 (Holga-referencia): a Picasa Holga-kimenete TISZTA SZÜRKE
        (R=G=B minden képponton) — a `#510` elfogadási feltétele (R>B, azaz
        SZÍNES kimenet) TÉVES volt: a `bw_tint` javítása után a kimenetnek
        éppen R=B kell legyen (ésszerű kerekítési tűréssel), nem R>B. Ld. a
        `glimmer_ops.bw_tint` docstringjét a bizonyítékért."""
        photo_rgb = _real_photo_rgb(200, 300)
        result_rgb = c.apply_holga(photo_rgb)
        result_bgr = cv2.cvtColor(result_rgb, cv2.COLOR_RGB2BGR)
        red_mean = float(result_bgr[..., 2].mean())
        blue_mean = float(result_bgr[..., 0].mean())
        assert abs(red_mean - blue_mean) < 1.0, (
            f"a kimenetnek szürkének kellene lennie, de R={red_mean:.1f} != B={blue_mean:.1f}"
        )

    @pytest.mark.parametrize("effect_name,apply_fn", [("Holga", c.apply_holga), ("Lomo", c.apply_lomo)])
    def test_meretfuggetlen_fekete_arany_a_korlat_ALATT(self, effect_name, apply_fn):
        """j2: a KORLÁT ALATTI tartományban a fekete-arány nagyságrendileg
        méretfüggetlen.

        #3158 óta nincs korlát: a σ MINDIG a képlet fele, tehát a
        méretfüggetlenség az egész tartományban áll. (A korábbi, #504-es
        255-ös korlát szándékosan megtörte — ezért szólt ez a próba csak a
        korlát alatti tartományról.) A korábbi, 96↔1600 px-es változat a két tartományt keverte,
        ezért kellett volna 30 pp-es (érdemi ellenőrzést nem adó) tűrés.

        A tűrés 10→15 pp-re nőtt a #535-ös `AutoFix`-átírás után: a Holga
        belül `AutoFix`-et hív, aminek most már csatornánkénti,
        HISZTOGRAM-DARABSZÁM alapú vágása van — ez érzékenyebb a kép
        TARTALMÁRA (nem csak a méretére), mint a korábbi globális min-max
        széthúzás, ezért a szintetikus fotógenerátor mérethez kötött
        tartalom-eltérése (#535 mérés: 96↔700 px, seedenként 0,6–12,2 pp)
        nagyobb szórást ad. A Lomo nem hív `AutoFix`-et, arra a régi 10 pp
        is bőven tartja magát."""

        small = apply_fn(_real_photo_rgb(96, 72))
        large = apply_fn(_real_photo_rgb(700, 525))
        diff = abs(_black_pct(small) - _black_pct(large))
        assert diff <= 15.0, (
            f"{effect_name}: fekete-arány 96px={_black_pct(small):.1f}% "
            f"vs 700px={_black_pct(large):.1f}% — {diff:.1f}pp eltérés"
        )

    def test_holga_perf_nagy_kepen(self):
        """j5: a ragyogás-lépés (közös `_border_glow`) nagy képen is
        gyors maradjon (a javítás előtt egy 4000×3000-es fotón egyetlen
        ragyogás-lépés 168 s volt — nagyvonalú korlát a lassú CI miatt)."""
        from support.perf_baseline import merd_es_ellenorizd

        photo_rgb = _real_photo_rgb(1500, 2000)
        merd_es_ellenorizd("apply_holga(2000x1500)", photo_rgb, c.apply_holga)


class TestIr:
    @pytest.mark.parametrize("fade", [0.0, 50.0, 100.0])
    def test_hatarok(self, image, fade):
        _assert_valid(c.apply_ir(image, fade=fade))

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(c.apply_ir(image, fade=100.0), image)


class TestNeon:
    @pytest.mark.parametrize("fade", [0.0, 50.0, 100.0])
    def test_hatarok(self, image, fade):
        _assert_valid(c.apply_neon(image, fade=fade))

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(c.apply_neon(image, fade=100.0), image)


# ---------------------------------------------------------------------------
# #3788: az Orton mestergörbe-középpontja ±75 (nem ±96) — golden-mérés a
# valódi Picasa-exporttal. Két forrás, mindkettő csak a FEJLESZTŐI GÉPEN
# elérhető (CI-n és felhős körben mindkettő kihagyja magát):
#   - a 684-merokeszlet (NAS) `orton__min`/`orton__alap` párja;
#   - a privát `picasapy-agent/referencia/ortonish` egyetlen forrásképe
#     (`Orton-ish fade max` bájtra azonos az eredetivel — `Fade=100` a
#     `apply_orton`-ban is visszaadja az eredetit), a Bloom/Brightness öt
#     csúszkaállásának Picasa-exportjával összevetve.
#
# rontás-kontroll: a `mid` képlet 75/50 helyett 96/50-re visszaírva a
# `test_684_merokeszlet_orton` mindkét esete (min, alap) és a
# `test_ortonish_referencia` négy Brightness-függő esete (brightness_max,
# brightness_min, alap, bloom_max, bloom_min) közül a brightness-es kettő
# bukik (4,45/4,18 ΔE messze a 0,96/0,83 határ fölött); a Brightness-t nem
# érintő alap/bloom-esetek változatlanok maradnak — ez önmagában igazolja,
# hogy a teszt a `mid`-képletet méri, nem valami mást. Ellenőrizve lefuttatva.
# ---------------------------------------------------------------------------


class TestOrtonGolden:
    _KIT = Path("/mnt/nas/My Pictures/684-merokeszlet")

    #: (név, lánc, a #3788 után mért ΔE) — a határ a mért érték + 0,01.
    _KIT_GOLDEN = [
        ("orton__min", "Orton=1,0,0,0;", 0.153),
        ("orton__alap", "Orton=1,25,50,0;", 0.211),
    ]

    @pytest.mark.skipif(not _KIT.is_dir(), reason="a 684-merokeszlet NAS-os mérőkészlet nem elérhető")
    @pytest.mark.parametrize(("nev", "lanc", "vart_de"), _KIT_GOLDEN, ids=[e[0] for e in _KIT_GOLDEN])
    def test_684_merokeszlet_orton(self, nev, lanc, vart_de):
        gyoker = Path(__file__).resolve().parents[2]
        if str(gyoker / "tools" / "golden") not in sys.path:
            sys.path.insert(0, str(gyoker / "tools" / "golden"))
        from compare_render import _read_rgb, delta_e_cie76
        from picasapy.ini.filters import parse_filters
        from picasapy.render.chain import apply_filters

        forras = _read_rgb(self._KIT / f"{nev}.jpg")
        export = _read_rgb(self._KIT / "export" / f"{nev}.jpg")
        kimenet = apply_filters(forras, parse_filters(lanc)).image
        assert kimenet.shape == export.shape
        de = float(delta_e_cie76(kimenet, export).mean())
        assert de <= vart_de + 0.01, f"{nev}: ΔE {de:.3f} > {vart_de + 0.01:.3f}"

    _ORTONISH = Path.home() / "picasapy-agent/referencia/ortonish"

    #: (név, mappa, bloom, brightness, fade, a #3788 után mért ΔE)
    _ORTONISH_GOLDEN = [
        ("brightness_max", "Orton-ish brightness max", 25.0, 100.0, 0.0, 0.950),
        ("brightness_min", "Orton-ish brightness min", 25.0, 0.0, 0.0, 0.815),
        ("alap", "Orton-ish default", 25.0, 50.0, 0.0, 0.840),
        ("bloom_max", "Orton-ish bloom max", 50.0, 50.0, 0.0, 0.850),
        ("bloom_min", "Orton-ish bloom min", 0.0, 50.0, 0.0, 0.963),
    ]

    @pytest.mark.skipif(
        not _ORTONISH.is_dir(), reason="a privát ortonish golden-anyag nincs a gépen"
    )
    @pytest.mark.parametrize(
        ("nev", "mappa", "bloom", "brightness", "fade", "vart_de"),
        _ORTONISH_GOLDEN,
        ids=[e[0] for e in _ORTONISH_GOLDEN],
    )
    def test_ortonish_referencia(self, nev, mappa, bloom, brightness, fade, vart_de):
        gyoker = Path(__file__).resolve().parents[2]
        if str(gyoker / "tools" / "golden") not in sys.path:
            sys.path.insert(0, str(gyoker / "tools" / "golden"))
        from compare_render import _read_rgb, delta_e_cie76

        kep = "Empty Space by Glenn Rayat.jpg"
        # a `Fade=100` az `apply_orton`-ban is bit-azonosan visszaadja az
        # eredetit (ld. `TestOrton.test_fade_100_valtozatlan`) — a
        # `Orton-ish fade max` export ezért a valódi, szűretlen forrás.
        forras = _read_rgb(self._ORTONISH / "Orton-ish fade max" / kep)
        export = _read_rgb(self._ORTONISH / mappa / kep)
        kimenet = c.apply_orton(forras, bloom=bloom, brightness=brightness, fade=fade)
        assert kimenet.shape == export.shape
        de = float(delta_e_cie76(kimenet, export).mean())
        assert de <= vart_de + 0.01, f"{nev}: ΔE {de:.3f} > {vart_de + 0.01:.3f}"
