"""A `picasapy.render.ops` műveletek tesztjei: szintetikus numpy képeken,
fájl-IO nélkül, determinisztikus asszertekkel."""

from __future__ import annotations

import cv2
import numpy as np
import pytest

from picasapy.ini.rect64 import Rect64
from picasapy.render.ops import (
    apply_autocolor,
    apply_autolight,
    apply_channel_levels_stretch,
    apply_crop,
    apply_enhance,
    apply_redeye,
    apply_tilt,
)
from tests.support.realistic_photo import make_realistic_photo


def _gradient_image(width: int = 20, height: int = 10) -> np.ndarray:
    """Determinisztikus, alacsony kontrasztú RGB gradiens teszt-kép."""
    row = np.linspace(80, 180, width, dtype=np.uint8)
    image = np.tile(row, (height, 1))
    return np.stack([image, image, image], axis=-1).astype(np.uint8)


def _teljes_tartomanyu_kep(height: int = 40, width: int = 60) -> np.ndarray:
    """Már full-range kép: a fekete/fehér pont mindhárom csatornán a
    hisztogram-darabszám küszöb FÖLÖTT van (nem csak egy-egy szélső pixel) —
    ez a Picasa „Night Seascape"-típusú, már kihasznált-tartományú fotója
    (#535/#540). A közép sáv egy folytonos, sima szürke gradiens."""
    image = np.full((height, width, 3), 128, dtype=np.uint8)
    body_rows = height - 8
    ramp = np.linspace(10, 245, width, dtype=np.uint8)
    image[:body_rows] = ramp[np.newaxis, :, np.newaxis]
    # elég sok tiszta fekete/fehér sor ahhoz, hogy a darabszám-küszöböt
    # (fix 0,5% / 0,2%) mindhárom csatornán átlépje
    image[body_rows : body_rows + 5] = 0
    image[body_rows + 5 :] = 255
    return image


def _realistic_rgb(height: int = 200, width: int = 260, seed: int = 11) -> np.ndarray:
    """Élethű, folytonos hisztogramú szintetikus fotó RGB sorrendben."""
    return cv2.cvtColor(make_realistic_photo(height=height, width=width, seed=seed), cv2.COLOR_BGR2RGB)


class TestApplyCrop:
    def test_pixel_pontos_meret(self) -> None:
        image = _gradient_image(width=20, height=10)
        rect = Rect64(left=0.25, top=0.2, right=0.75, bottom=0.8)
        result = apply_crop(image, rect)
        assert result.shape == (6, 10, 3)

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _gradient_image()
        original = image.copy()
        apply_crop(image, Rect64(0.0, 0.0, 1.0, 1.0))[0, 0, 0] = 255
        np.testing.assert_array_equal(image, original)

    def test_ures_kivagas_value_error(self) -> None:
        image = _gradient_image()
        with pytest.raises(ValueError):
            apply_crop(image, Rect64(0.5, 0.5, 0.5, 0.9))

    def test_teljes_kep_valtozatlan(self) -> None:
        image = _gradient_image()
        result = apply_crop(image, Rect64(0.0, 0.0, 1.0, 1.0))
        np.testing.assert_array_equal(result, image)


class TestApplyTilt:
    def test_nulla_szog_identitas_meret(self) -> None:
        image = _gradient_image()
        result = apply_tilt(image, angle=0.0, scale=1.0)
        assert result.shape == image.shape

    def test_kimenet_merete_megegyezik_bemenettel(self) -> None:
        image = _gradient_image(width=30, height=15)
        result = apply_tilt(image, angle=0.2, scale=1.1)
        assert result.shape == image.shape

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _gradient_image()
        original = image.copy()
        apply_tilt(image, angle=0.3, scale=1.0)
        np.testing.assert_array_equal(image, original)


class TestApplyAutolight:
    """Auto Contrast — megfejtve #540-ben: KÖZÖS (mindhárom csatornán azonos)
    hisztogram-darabszám alapú vágás — ez a megkülönböztető tulajdonsága a
    csatornánként külön vágó Auto Colourtól."""

    def test_szethuzza_a_hisztogramot(self) -> None:
        image = _gradient_image()
        result = apply_autolight(image)
        assert result.min() == 0
        assert result.max() == 255

    def test_globalis_kozos_vagas_linearis(self) -> None:
        # megfejtve (#540): ki = (be − lo)·255/(hi − lo), egyetlen KÖZÖS
        # lo/hi az egész képre (hisztogram-darabszám alapján, #535 módszere)
        image = np.zeros((1, 3, 3), dtype=np.uint8)
        image[0, 0] = 80
        image[0, 1] = 130
        image[0, 2] = 180
        result = apply_autolight(image)
        assert result[0, 0, 0] == 0
        assert abs(int(result[0, 1, 0]) - 128) <= 1
        assert result[0, 2, 0] == 255

    def test_kozos_csatorna_transzformacio(self) -> None:
        # a stretch KÖZÖS mindhárom csatornára — a színegyensúly megmarad
        image = np.zeros((1, 2, 3), dtype=np.uint8)
        image[0, 0] = (60, 80, 100)
        image[0, 1] = (180, 200, 220)
        result = apply_autolight(image)
        # lo=60, hi=220 → skála 255/160
        assert result[0, 0, 0] == 0
        assert abs(int(result[0, 0, 1]) - 32) <= 1
        assert result[0, 1, 2] == 255

    def test_mindharom_csatorna_azonos_meredekseget_kap(self) -> None:
        # a MEGKÜLÖNBÖZTETŐ tulajdonság (#540): akkor is közös lo/hi-t
        # használ, ha a bemeneti csatornáknak eltérő a tartománya — tehát
        # nincs fehéregyensúly-hatása, a színezet a kimeneten is megmarad
        height, width = 50, 60
        red = np.linspace(40, 200, width, dtype=np.uint8)
        green = np.linspace(0, 255, width, dtype=np.uint8)
        blue = np.linspace(80, 180, width, dtype=np.uint8)
        image = np.tile(np.stack([red, green, blue], axis=-1), (height, 1, 1))

        result = apply_autolight(image)

        def slope(channel: int) -> float:
            lo_in, hi_in = int(image[0, 0, channel]), int(image[0, -1, channel])
            lo_out, hi_out = int(result[0, 0, channel]), int(result[0, -1, channel])
            return (hi_out - lo_out) / (hi_in - lo_in)

        slopes = [slope(0), slope(1), slope(2)]
        # mindhárom csatorna UGYANAZT a meredekséget kapja (közös lo/hi)
        assert max(slopes) - min(slopes) < 0.01
        # a piros és a kék csatorna EGYMÁSHOZ KÉPESTI aránya (a "színezet")
        # nem változik: a kék minden pontban ugyanannyival marad a piros
        # fölött, mint a bemeneten (közös eltolás+skála)
        offset_before = int(blue[0]) - int(red[0])
        offset_after = int(result[0, 0, 2]) - int(result[0, 0, 0])
        assert abs(offset_after - round(offset_before * slopes[0])) <= 1

    def test_teljes_tartomanyu_kepen_no_op(self) -> None:
        # megfejtve (#540): full-range bemeneten az autolightnak nincs dolga
        # — a küszöböt (fix 0,5%/0,2%) is átlépő, valódi méretű képen kell
        # tesztelni (a #535 tanulsága: pár pixel nem elég a darabszámhoz)
        image = _teljes_tartomanyu_kep()
        result = apply_autolight(image)
        np.testing.assert_array_equal(result, image)

    def test_elethu_foton_nem_dob_hibat_es_uint8_marad(self) -> None:
        image = _realistic_rgb()
        result = apply_autolight(image)
        assert result.shape == image.shape
        assert result.dtype == np.uint8

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _gradient_image()
        original = image.copy()
        apply_autolight(image)
        np.testing.assert_array_equal(image, original)

    def test_dtype_uint8(self) -> None:
        image = _gradient_image()
        result = apply_autolight(image)
        assert result.dtype == np.uint8


class TestApplyAutocolor:
    """Auto Colour — #541: csatornánkénti ERŐSÍTÉS (`ki = be · gain`), az
    erősítés a SEMLEGES képpontokra számolt szürkevilág-becslésből. A
    feketepont nem mozdul; a 12 referencia-képen az eltérés 2,35 (az
    érintetlen képé 5,29, a mért erősítésekkel elérhető alsó korlát 1,08)."""

    def test_semleges_kepen_no_op(self) -> None:
        # megfejtve: semleges (szürke) bemeneten az autocolor nem csinál semmit
        image = _gradient_image()
        np.testing.assert_array_equal(apply_autocolor(image), image)

    def test_csatornankent_kulon_erosites_a_semleges_pixelekbol(self) -> None:
        """#541: az Auto Colour tiszta csatorna-ERŐSÍTÉS (a feketepont nem
        mozdul), és az erősítést a SEMLEGES képpontok szürkevilág-becslése
        adja — a telített részletek kimaradnak.

        Itt egy kékes árnyalatú, semleges-közeli felület mellé teszünk egy
        erősen telített (tiszta vörös) foltot: a becslésnek a kék elhajlást
        kell kiegyenlítenie, a vörös foltnak pedig NEM szabad elhúznia.
        """
        image = np.zeros((80, 80, 3), dtype=np.uint8)
        image[:, :] = (110, 120, 150)  # semleges-közeli, kékes
        image[:, 60:] = (230, 10, 10)  # erősen telített vörös folt

        result = apply_autocolor(image)

        neutral_before = image[0, 0].astype(int)
        neutral_after = result[0, 0].astype(int)
        # a kékes elhajlás csökken: a csatornák közelebb kerülnek egymáshoz
        assert max(neutral_after) - min(neutral_after) < max(neutral_before) - min(
            neutral_before
        )
        # a feketepont nem mozdul: a 0 marad 0 (tiszta erősítés, nem szinthúzás)
        black = apply_autocolor(
            np.concatenate([image, np.zeros((10, 80, 3), dtype=np.uint8)], axis=0)
        )
        assert int(black[-1, 0, 0]) == 0

    def test_a_telitett_kepreszlet_nem_huzza_el_a_becslest(self) -> None:
        """A telített folt színe nem számít bele: ha csak a folt színét
        cseréljük (vörösről zöldre), a semleges felület kimenete ugyanaz."""
        base = np.zeros((80, 80, 3), dtype=np.uint8)
        base[:, :] = (110, 120, 150)
        red_patch = base.copy()
        red_patch[:, 60:] = (230, 10, 10)
        green_patch = base.copy()
        green_patch[:, 60:] = (10, 230, 10)

        assert list(apply_autocolor(red_patch)[0, 0]) == list(
            apply_autocolor(green_patch)[0, 0]
        )
    def test_elethu_fotoval_szinesitett_kepen_kulonbozo_csatorna_lut(self) -> None:
        # élethű, térben strukturált szintetikus fotó (#504 tanulsága: sík
        # zaj nem elég), mesterséges színezettel ellátva
        base = _realistic_rgb()
        image = base.astype(np.int16)
        image[..., 0] = np.clip(image[..., 0] + 15, 0, 255)
        image[..., 2] = np.clip(image[..., 2] - 15, 0, 255)
        image = image.astype(np.uint8)
        result = apply_autocolor(image)
        assert result.shape == image.shape
        assert result.dtype == np.uint8
        # a piros/kék eltolás (színezet) átlagosan csökken a korrekció után
        cast_before = abs(float(image[..., 0].mean()) - float(image[..., 2].mean()))
        cast_after = abs(float(result[..., 0].mean()) - float(result[..., 2].mean()))
        assert cast_after < cast_before

    def test_teljes_tartomanyu_kepen_no_op(self) -> None:
        # megfejtve (#540): ha mindhárom csatorna vágópontja már megegyezik
        # (pl. teljes tartományú, semleges kép), a kimenet bájtra azonos
        image = _teljes_tartomanyu_kep()
        result = apply_autocolor(image)
        np.testing.assert_array_equal(result, image)

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _gradient_image()
        original = image.copy()
        apply_autocolor(image)
        np.testing.assert_array_equal(image, original)

    def test_clip_0_255(self) -> None:
        image = _gradient_image()
        result = apply_autocolor(image)
        assert result.min() >= 0
        assert result.max() <= 255


class TestApplyEnhance:
    def test_azonossag_teljes_tartomanyu_kepen(self) -> None:
        # megfejtve (#535): ha egy csatorna lo/hi-je már 0/255, a Picasa
        # NEM nyúl hozzá — a kimenet bájtra azonos a bemenettel.
        image = _teljes_tartomanyu_kep()
        result = apply_enhance(image)
        np.testing.assert_array_equal(result, image)

    def test_linearis_es_csatornankent_kulon_vag(self) -> None:
        # megfejtve (#535): ki = (be − lo)·255/(hi − lo), csatornánként
        # KÜLÖN lo/hi (fehéregyensúly-hatás). Építsünk képet, ahol a három
        # csatorna eltérő tartományt használ ki, és ellenőrizzük a
        # linearitást + hogy a csatornák tényleg különböző LUT-ot kapnak.
        height, width = 50, 60
        red = np.linspace(40, 200, width, dtype=np.uint8)
        green = np.linspace(0, 255, width, dtype=np.uint8)
        blue = np.linspace(80, 180, width, dtype=np.uint8)
        # elég sok sor, hogy minden érték-darabszám a küszöb fölé kerüljön
        image = np.tile(np.stack([red, green, blue], axis=-1), (height, 1, 1))

        result = apply_enhance(image)

        # a piros és a kék csatornát is széthúzta (nem full-range bemenet)
        assert result[..., 0].min() == 0
        assert result[..., 0].max() == 255
        assert result[..., 2].min() == 0
        assert result[..., 2].max() == 255
        # a zöld már full-range volt → azonosság
        np.testing.assert_array_equal(result[..., 1], image[..., 1])

        # linearitás: a piros csatorna középső mintapontjára illik a
        # (be − lo)·255/(hi − lo) képlet a mért lo/hi-vel
        lo, hi = int(red.min()), int(red.max())
        mid_input = int(red[width // 2])
        expected = round((mid_input - lo) * 255.0 / (hi - lo))
        assert abs(int(result[0, width // 2, 0]) - expected) <= 1

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _gradient_image()
        original = image.copy()
        apply_enhance(image)
        np.testing.assert_array_equal(image, original)


class TestApplyRedeye:
    def _kep_voros_pupillaval(self) -> np.ndarray:
        image = np.full((20, 20, 3), 120, dtype=np.uint8)  # semleges bőrtónus-szerű háttér
        image[8:12, 8:12] = (200, 30, 30)  # erősen vörös "pupilla"
        return image

    def test_csak_a_voros_regiot_modositja(self) -> None:
        image = self._kep_voros_pupillaval()
        result = apply_redeye(image)
        # a háttér változatlan
        np.testing.assert_array_equal(result[0:8, 0:8], image[0:8, 0:8])
        # a vörös régió R csatornája csökken
        assert result[10, 10, 0] < image[10, 10, 0]

    def test_bortonust_nem_bantja(self) -> None:
        image = np.full((10, 10, 3), (180, 140, 120), dtype=np.uint8)
        result = apply_redeye(image)
        np.testing.assert_array_equal(result, image)

    def test_regiokra_korlatozhato(self) -> None:
        image = self._kep_voros_pupillaval()
        # a régión kívüli terület nem kap figyelmet, még ha lenne is benne vörös
        regions = (Rect64(0.0, 0.0, 0.3, 0.3),)  # nem fedi a vörös foltot (0.4-0.6)
        result = apply_redeye(image, regions=regions)
        np.testing.assert_array_equal(result, image)

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = self._kep_voros_pupillaval()
        original = image.copy()
        apply_redeye(image)
        np.testing.assert_array_equal(image, original)


class TestMinStretchSpan:
    """#539: a nagyon szűk hisztogramú csatornát a szinthúzás nem feszíti
    ki a teljes tartományra.

    A `referencia/imfeellucky/` „Utopic Unicorn" képén — a 12-ből az
    egyetlen szélső eset — a két szűk csatorna kimért bemeneti tartománya
    58,1 és 59,2, holott a nyers tartományuk 35 és 41 volt. A korlát a
    feketepontot tartja, a fehérpontot tolja feljebb.
    """

    def test_szuk_csatorna_nem_feszul_a_teljes_tartomanyra(self) -> None:
        # 30 szintnyi tartomány (100..130): a naiv nyújtás 0..255-re vinné
        narrow = np.tile(
            np.linspace(100, 130, 64, dtype=np.uint8)[:, np.newaxis, np.newaxis],
            (1, 64, 3),
        )
        result = apply_channel_levels_stretch(narrow)
        spread = int(result.max()) - int(result.min())
        assert spread < 200, f"a szűk csatorna teljesen kifeszült ({spread})"
        # a feketepont a horgony: a legsötétebb képpont marad a legsötétebb
        assert int(result.min()) == 0

    def test_szeles_csatorna_tovabbra_is_kifeszul(self) -> None:
        """A korlát csak a szűk esetre vonatkozik — a szokásos képeken a
        szinthúzás változatlanul a teljes tartományra visz."""
        wide = np.tile(
            np.linspace(40, 200, 64, dtype=np.uint8)[:, np.newaxis, np.newaxis],
            (1, 64, 3),
        )
        result = apply_channel_levels_stretch(wide)
        assert int(result.max()) - int(result.min()) > 240
