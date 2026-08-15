"""A `picasapy.render.ops` műveletek tesztjei: szintetikus numpy képeken,
fájl-IO nélkül, determinisztikus asszertekkel."""

from __future__ import annotations

import cv2
import numpy as np
import pytest

from picasapy.ini.rect64 import Rect64
from picasapy.render.ops import (
    _channel_black_white_points,
    _levels_clip_threshold,
    _native_clip_points,
    _native_levels_lut,
    _union_black_white_point,
    apply_autocolor,
    apply_autolight,
    apply_channel_levels_stretch,
    apply_crop,
    apply_enhance,
    apply_redeye,
    apply_tilt,
    count_redeye_spots,
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
    """Auto Contrast — KÖZÖS (mindhárom csatornán azonos) vágás; ez a
    megkülönböztető tulajdonsága a csatornánként külön vágó Auto Colourtól
    (#540). A közös vágópont a #539 óta a csatornánkénti vágópontok
    UNIÓJA (`FUN_00a4bfd0`), nem az összeöntött hisztogramé."""

    def test_a_kozos_vagas_a_csatornak_unioja_nem_az_osszeontott_hisztogram(
        self,
    ) -> None:
        """A megkülönböztető eset: a piros csatorna képpontjainak 0,6%-a ül a
        nullán — a SAJÁT hisztogramjában ez átlépi a küszöböt (feketepont 0),
        az összeöntött, háromszor akkora hisztogramban viszont csak 0,2%,
        ott tehát nem lépné át. Az uniós szabály szerint a globális
        feketepont 0, az összeöntött szerint 100 lenne."""
        image = np.full((200, 200, 3), 100, dtype=np.uint8)
        image[0, :, 0] = 0  # 200 képpont = a 40 000 0,5%-a (a küszöb)
        image[1:3] = 200  # 400 képpont: a fehérpont mindhárom csatornán 200

        result = apply_autolight(image)

        # lo = 0, hi = 200 → gain = (255 << 16) // 200 = 83558
        assert int(result[50, 50, 1]) == (100 * 83558) >> 16
        assert int(result[50, 50, 1]) > 0

    def test_szethuzza_a_hisztogramot(self) -> None:
        image = _gradient_image()
        result = apply_autolight(image)
        assert result.min() == 0
        # #539: a natív egész osztás csonkolása miatt a fehérpont 254 is lehet
        assert result.max() >= 254

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
        assert result[0, 2, 0] >= 254

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
        # #539/#721: az elemzés a kép 90% × 90%-os, vízszintesen BALRA
        # igazított ablakáról készül, ezért a színátmenetet a BAL oldali
        # sávra építjük, a maradékot pedig a szélső értékkel töltjük — így
        # a vizsgált terület pontosan a teljes átmenetet fogja át.
        height, width = 50, 60
        span = width * 95 // 100 - width * 5 // 100  # az ablak szélessége
        pad = ((0, width - span),)
        red = np.pad(np.linspace(40, 200, span, dtype=np.uint8), pad, mode="edge")
        green = np.pad(np.linspace(0, 255, span, dtype=np.uint8), pad, mode="edge")
        blue = np.pad(np.linspace(80, 180, span, dtype=np.uint8), pad, mode="edge")
        # elég sok sor, hogy minden érték-darabszám a küszöb fölé kerüljön
        image = np.tile(np.stack([red, green, blue], axis=-1), (height, 1, 1))

        result = apply_enhance(image)

        # a piros és a kék csatornát is széthúzta (nem full-range bemenet).
        # #539: a fehérpont a natív EGÉSZ osztás csonkolása miatt 254-re is
        # eshet — a gain `(255 << 16) // (hi − lo)` lefelé kerekít.
        assert result[..., 0].min() == 0
        assert result[..., 0].max() >= 254
        assert result[..., 2].min() == 0
        assert result[..., 2].max() >= 254
        # a zöld már full-range volt → azonosság
        np.testing.assert_array_equal(result[..., 1], image[..., 1])

        # linearitás: a piros csatorna középső mintapontjára illik a
        # (be − lo)·255/(hi − lo) képlet a mért lo/hi-vel
        lo, hi = int(red.min()), int(red.max())
        mid_input = int(red[span // 2])
        expected = round((mid_input - lo) * 255.0 / (hi - lo))
        assert abs(int(result[0, span // 2, 0]) - expected) <= 1

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


class TestNativVagopontKereses:
    """#539: a natív vágópont-keresés BETŰ SZERINT (`FUN_00a4be40`,
    `0x009db610`).

    ```c
    kuszob = round(N * 0.005);  if (kuszob == 0) kuszob = 1;
    i = 0;   sum = 0;  do { sum += hist[i]; i++; } while (i <= 255 && sum < kuszob);
    lo = i - 1;
    i = 255; sum = 0;  do { sum += hist[i]; i--; } while (i >= 0  && sum < kuszob);
    hi = i + 1;
    ```
    """

    def test_a_kuszob_a_keppontszam_fel_szazaleka(self) -> None:
        assert _levels_clip_threshold(200 * 200) == 200
        assert _levels_clip_threshold(2560 * 1600) == 20480

    def test_a_kuszob_legalabb_egy(self) -> None:
        """A natív `if (kuszob == 0) kuszob = 1` — apró képen is van vágás."""
        assert _levels_clip_threshold(10 * 10) == 1
        assert _levels_clip_threshold(0) == 1

    def test_a_kuszob_a_MINTAVETELEZETT_keppontszamra_vonatkozik(self) -> None:
        """`N = W·H / lépés²` — ritkított hisztogramnál a küszöb is ritkul."""
        assert _levels_clip_threshold((2560 * 1600) // (2 * 2)) == 5120

    def test_a_ciklus_a_noveles_UTAN_ellenoriz(self) -> None:
        """`lo = i − 1` / `hi = i + 1`: a vágópont AZ a szint, amelyiknél a
        kumulált darabszám eléri a küszöböt — nem a következő."""
        histogram = np.zeros(256, dtype=np.int64)
        histogram[10] = 5
        histogram[200] = 5
        assert _native_clip_points(histogram, 1) == (10, 200)
        assert _native_clip_points(histogram, 5) == (10, 200)

    def test_a_kuszob_folott_atlep_a_masik_tuskere(self) -> None:
        """Hat darabhoz már a MÁSIK tüske is kell — a natív ciklus ilyenkor
        fordított párt ad vissza, és ezt nem szépítjük meg."""
        histogram = np.zeros(256, dtype=np.int64)
        histogram[10] = 5
        histogram[200] = 5
        assert _native_clip_points(histogram, 6) == (200, 10)

    def test_a_kuszobot_el_nem_ero_hisztogram_a_szelekre_fut(self) -> None:
        """Ha az egész hisztogram kevesebb a küszöbnél, a ciklus kifut a
        `break`-re: `lo = 255`, `hi = 0`."""
        histogram = np.zeros(256, dtype=np.int64)
        histogram[100] = 3
        assert _native_clip_points(histogram, 10) == (255, 0)

    def test_a_harom_csatorna_egybeesik_szurke_kepen(self) -> None:
        """Szürkeárnyalatos képen a három csatorna vágópontja azonos —
        ez mutatja, hogy tényleg egy szabály fut mindhármon."""
        gray = np.random.default_rng(7).integers(40, 200, size=(40, 40), dtype=np.uint8)
        image = np.stack([gray] * 3, axis=-1)
        piros, zold, kek = _channel_black_white_points(image)
        assert piros == zold == kek


class TestUnioVagopont:
    """#539: az `autolight` (Auto Contrast) GLOBÁLIS vágása a három csatorna
    UNIÓJA — `FUN_00a4bfd0`: `lo = min(lo_R, lo_G, lo_B)`,
    `hi = max(hi_R, hi_G, hi_B)`."""

    def test_a_legszelesebb_tartomanyt_veszi(self) -> None:
        columns = 100
        image = np.zeros((100, columns, 3), dtype=np.uint8)
        for channel, (start, stop) in enumerate(((40, 200), (20, 150), (80, 240))):
            ramp = np.linspace(start, stop, columns, dtype=np.uint8)
            image[..., channel] = ramp[np.newaxis, :]
        # lo = min(40, 20, 80) = 20 · hi = max(200, 150, 240) = 240
        assert _union_black_white_point(image) == (20, 240)


class TestNativSzinthuzoAtvitel:
    """#539: a natív átvitel FIXPONTOS (`0x009db610`):
    `gain = (255 << 16) / (hi − lo)` egész osztással, majd
    `ki = ((be − lo) · gain) >> 16`, végül vágás [0, 255]-re."""

    def test_teljes_tartomany_bajtra_azonossag(self) -> None:
        """`lo = 0`, `hi = 255` esetén a gain pontosan 65536 — a leképezés
        bájtra azonosság, kerekítési hiba nélkül."""
        np.testing.assert_array_equal(_native_levels_lut(0, 255), np.arange(256))

    def test_a_gain_egesz_osztas_lefele_kerekit(self) -> None:
        """(255 << 16) // 100 = 167116, tehát a 100..200 sáv felezőpontja
        127 lesz, nem a lebegőpontos 127,5-ből kerekített 128."""
        assert int(_native_levels_lut(100, 200)[150]) == 127

    def test_a_tartomanyon_kivul_vag(self) -> None:
        lut = _native_levels_lut(100, 200)
        assert int(lut[0]) == 0
        assert int(lut[99]) == 0
        assert int(lut[255]) == 255

    def test_a_feherpont_a_csonkolas_miatt_254_is_lehet(self) -> None:
        """A gain lefelé kerekítése miatt maga a fehérpont sem feltétlenül
        éri el a 255-öt: 100 széles sávnál a gain 167116, és
        `(100 · 167116) >> 16 = 254`. A natív kód nem korrigálja."""
        assert int(_native_levels_lut(100, 200)[200]) == 254


class TestNativLevelsGeometria:
    """#539/#721: a `0x009db610` natív geometriája — a hisztogram a kép
    90% × 90%-os, vízszintesen BALRA IGAZÍTOTT ablakáról készül, a vágási
    küszöb pedig a TELJES kép képpontszámának 1/200-a, mindkét végén
    azonosan.

    Mindkettőt a `referencia/imfeellucky/` 12 képpárján mértük ki: a
    csatornánként kiolvasott fehérpontok átlagos eltérése 3,85, a
    feketepontoké 2,05, és minden aszimmetrikus VÁGÁS rosszabbnak bizonyult.
    Az ablak vízszintes horgonyát a #721 döntötte el (ld. `_analysis_region`):
    a négy változat közül a balra igazított a legpontosabb (2,48 a középre
    igazított 2,61-ével szemben).
    """

    def test_a_perem_kimarad_az_elemzesbol(self) -> None:
        """A kihagyott peremen ülő szélsőérték nem mozdítja el a vágópontot.

        Az ablak függőlegesen mindkét oldalon 5%-ot hagy ki, vízszintesen
        viszont a JOBB 10%-ot (a bal perem benne van).
        """
        image = np.full((200, 200, 3), 120, dtype=np.uint8)
        image[0:6, :] = 0  # a felső perem (az ablak a 10. sortól indul)
        image[194:, :] = 0  # az alsó perem (az ablak a 190. sorig tart)
        image[:, 185:] = 0  # a kimaradó jobb sáv (az ablak a 180. oszlopig)
        tiszta = np.full((200, 200, 3), 120, dtype=np.uint8)
        assert _channel_black_white_points(image) == _channel_black_white_points(tiszta)

    def test_a_bal_perem_BENNE_van_az_ablakban(self) -> None:
        """#721: a natív ablak vízszintesen balra igazított, ezért a bal
        szélen ülő sötét sáv IGENIS elmozdítja a feketepontot."""
        image = np.full((200, 200, 3), 120, dtype=np.uint8)
        image[:, 0:6] = 0  # 6 oszlop × 180 ablaksor = 1080 kp > a 200-as küszöb
        assert _channel_black_white_points(image)[0][0] == 0

    def test_a_kuszob_darabszam_es_nem_percentilis(self) -> None:
        """A vágás a teljes képpontszám 1/200-a: az ez alatti tüske eltűnik,
        a fölötte lévő megmarad."""
        # 200×200 = 40 000 képpont → a küszöb 200 darab
        alap = np.tile(
            np.repeat(np.linspace(150, 199, 50, dtype=np.uint8), 4)[:, None, None],
            (1, 200, 3),
        )
        keves = alap.copy()
        keves[100:105, 100:120] = 20  # 100 képpont < 200 → beleesik a vágásba
        sok = alap.copy()
        sok[100:120, 100:130] = 20  # 600 képpont > 200 → nem vágódik le
        assert _channel_black_white_points(keves)[0][0] > 20
        assert _channel_black_white_points(sok)[0][0] == 20


def _szurke_rampa(width: int = 1000, height: int = 200) -> np.ndarray:
    """Determinisztikus, VÍZSZINTES szürke rámpa: balról 0, jobbról 255.

    Ez a #685 mérőszettjének mérőképe szintetikus alakban: az egyetlen
    képfajta, amelyen a hisztogram-elemzés ABLAKÁNAK a helye közvetlenül
    leolvasható a kimenetből, mert a szint és a vízszintes hely egy az
    egyben megfelel egymásnak.
    """
    ramp = (np.arange(width) * 255 // (width - 1)).astype(np.uint8)
    return np.repeat(np.tile(ramp, (height, 1))[..., np.newaxis], 3, axis=2)


def _mert_vagasi_pontok(image: np.ndarray, result: np.ndarray) -> tuple[int, int]:
    """A ténylegesen ALKALMAZOTT fekete-/fehér-vágás, a kimenetből visszaolvasva.

    A fekete-vágás a legnagyobb bemeneti szint, amit a szűrő még 0-ra vitt;
    a fehér-vágás a legkisebb, amit már 255-re. Így nem a belső segédeket
    tapogatjuk, hanem ugyanazt mérjük, amit a jegy (#721) a valódi
    Picasa-exportból mért.
    """
    levels = image[..., 0].reshape(-1)
    output = result[..., 0].reshape(-1)
    fekete = int(levels[output == 0].max()) if bool((output == 0).any()) else -1
    feher = int(levels[output == 255].min()) if bool((output == 255).any()) else 256
    return fekete, feher


class TestEnhanceVagasiPontok721:
    """#721: az `enhance` VÁGÁSI PONTJAI a valódi Picasáéhoz mérve.

    A #685 mérőszettjének szürke rámpáján, azonos bemeneten, valódi
    Picasa-exporthoz illesztve (`filters-decoded.md`, „`enhance`" szakasz):

    | szűrő | forrás | fekete-vágás | fehér-vágás |
    |---|---|---:|---:|
    | `autolight` | Picasa | 4,5 | 251,5 |
    | `enhance` | **Picasa** | **6,5** | **235,4** |
    | `enhance` | **mi (a javítás előtt)** | **18,4** | **240,4** |

    Az `autolight` sora mondja meg, hol van a rámpa két vége: a Picasa
    onnan a teljes képet elemzi, tehát a rámpa nagyjából **4,5-től
    251,5-ig** tart. A Picasa `enhance`-ének fekete-vágása (6,5) így a
    rámpa hosszának **~1 %-ánál** van.

    Ebből következik a teszt állítása, és ez FÜGGETLEN attól, hogy a
    rámpa pontosan milyen: egy vízszintesen KÖZÉPRE igazított, 90 %-os
    elemzőablak a rámpa 5 %-ánál kezdődik, tehát a fekete-vágása
    geometriailag **nem lehet a rámpa 5 %-a alatt** — a Picasáé viszont
    1 %-nál van. Az ablak vízszintesen tehát nem középre igazított; a
    fehér végén ugyanez fordítva látszik (a Picasa 235,4-nél vág, mi
    240,4-nél — vagyis a Picasa ablaka a világos oldalon RÖVIDEBB).
    """

    def test_a_fekete_vagas_nem_vagja_le_az_arnyekokat(self) -> None:
        """A fekete-vágás a rámpa SÖTÉT VÉGÉN van, nem 5 %-kal beljebb.

        A javítás előtt ez 14 volt (a rámpa 5,5 %-a) — pontosan az a
        ~12 szintnyi fölösleges árnyékvágás, amit a jegy mért.
        """
        rampa = _szurke_rampa()
        fekete, _ = _mert_vagasi_pontok(rampa, apply_enhance(rampa))
        assert fekete <= 5, f"a fekete-vágás {fekete} — a rámpa 2 %-a fölött"

    def test_a_feher_vagas_nem_enyhebb_a_picasaenal(self) -> None:
        """A fehér végén a Picasa AGRESSZÍVABB nálunk (235,4 vs 240,4).

        Az elemzőablak a világos oldalon rövidebb, mint a miénk volt.
        """
        rampa = _szurke_rampa()
        _, feher = _mert_vagasi_pontok(rampa, apply_enhance(rampa))
        assert feher <= 236, f"a fehér-vágás {feher} — a Picasa 235,4-e fölött"

    def test_az_autolight_a_teljes_rampat_latja(self) -> None:
        """Regresszió-őr: az `autolight` MÉRT állapota pontos (4,5 / 251,5),
        vagyis a TELJES képet elemzi — ehhez a jegy nem nyúlhat hozzá."""
        rampa = _szurke_rampa()
        fekete, feher = _mert_vagasi_pontok(rampa, apply_autolight(rampa))
        assert fekete <= 2, f"az autolight fekete-vágása elmozdult ({fekete})"
        assert feher >= 253, f"az autolight fehér-vágása elmozdult ({feher})"


class TestCountRedeyeSpots:
    """#445: a felhasználói visszajelzéshez („Picasa has found and corrected
    red eye(s)") az automatika KÜLÖNÁLLÓ foltjait számoljuk meg."""

    def test_ket_kulon_pupilla_ket_folt(self) -> None:
        image = np.full((60, 60, 3), 120, dtype=np.uint8)
        image[20:30, 10:20] = (220, 40, 40)
        image[20:30, 40:50] = (220, 40, 40)
        assert count_redeye_spots(image) == 2

    def test_tiszta_kepen_nulla(self) -> None:
        image = np.full((60, 60, 3), 120, dtype=np.uint8)
        assert count_redeye_spots(image) == 0

    def test_bortonust_nem_szamol(self) -> None:
        image = np.full((60, 60, 3), (180, 140, 120), dtype=np.uint8)
        assert count_redeye_spots(image) == 0

    def test_nehany_pixeles_szorvany_kiszurve(self) -> None:
        """A tömörítési eredetű, néhány pixeles vörös szórvány nem „szem"."""
        image = np.full((600, 600, 3), 120, dtype=np.uint8)
        image[10:12, 10:12] = (220, 40, 40)
        assert count_redeye_spots(image) == 0


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
