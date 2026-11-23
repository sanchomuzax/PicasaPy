"""A Retusálás ecsetkörének mérete az eredeti szerint (#7406): lineáris csúszka, a nagyítással
arányos kör, a kép méretétől független forrásképi sugár.

Mért pontok (a `job-907`, `job-908`, `job-917`, `job-918` felvételein és a job #314 képén):
a bal vég R = 3,0, az induláskor R = 24,0 (z = 0,97) és R = 20,0 (z = 0,80), a futás 24,2%-án
R = 23,0, 73,5%-án R = 71,0, a jobb végen R = 97,0 (z = 0,97) és R = 107,0 (z = 1,07).

⚠️ Ezek a próbák számolnak (a modellt és a vezérlőt olvassák): a renderelt kört a
`tests/app/qml_functional/test_retouch_ecsetmeret_renderelt_7406.py` veti össze a képkockákkal.
"""

from __future__ import annotations

import math

import pytest

from picasapy.app import retouch_brush as brush
from picasapy.app.edit_controller_shared import _DEFAULT_BRUSH_SIZE
from picasapy.ini.retouch import RetouchPatch, decode_patch, encode_patch
from support.jpeg_factory import make_jpeg


@pytest.fixture
def provider(qt_app):
    from picasapy.app.edit_preview import EditPreviewProvider

    return EditPreviewProvider()


@pytest.fixture
def controller(qt_app, provider):
    from picasapy.app.edit_controller import EditController

    return EditController(provider)


@pytest.fixture
def photo(tmp_path):
    """640 x 480: a rövidebb oldal (480) nagyobb a legnagyobb ecsetnél (100)."""
    return make_jpeg(tmp_path / "IMG_0001.jpg", size=(640, 480))


# --- a tiszta számolás -------------------------------------------------------------------


def test_a_csuszka_helyzete_a_futasra_vetitve_lineáris() -> None:
    """t = (érték - 1) / 99: a fogantyú KÖZEPÉNEK helye a futásban."""
    assert brush.slider_position(1) == 0.0
    assert brush.slider_position(100) == 1.0
    assert brush.slider_position(50) == pytest.approx(49 / 99)
    # lineáris: egyenlő lépések egyenlő t-különbséget adnak
    lepesek = [brush.slider_position(v + 1) - brush.slider_position(v) for v in range(1, 100)]
    assert max(lepesek) - min(lepesek) < 1e-12


def test_a_csuszkan_kivuli_ertek_a_szelere_vagott() -> None:
    assert brush.slider_position(-7) == 0.0
    assert brush.slider_position(500) == 1.0


def test_erintetlen_csuszkanal_az_induloertek_el_megerintes_utan_s_egyenlo_t() -> None:
    """Induláskor s = 0,25 (a fogantyú közben középen áll); megérintés után s = t."""
    assert brush.brush_fraction(_DEFAULT_BRUSH_SIZE, touched=False) == 0.25
    assert brush.brush_fraction(_DEFAULT_BRUSH_SIZE, touched=True) == pytest.approx(49 / 99)
    assert brush.brush_fraction(1, touched=True) == 0.0
    assert brush.brush_fraction(100, touched=True) == 1.0
    # érintetlenül az érték nem számít: az induló s él
    assert brush.brush_fraction(100, touched=False) == 0.25


def test_az_alapallasnal_a_fogantyu_a_futas_kozepen_all() -> None:
    assert abs(brush.slider_position(_DEFAULT_BRUSH_SIZE) - 0.5) <= 0.01


@pytest.mark.parametrize(
    ("t", "z", "mert_r"),
    [
        (0.0, 0.97, 3.0),  # job-908 __14: bal vég
        (0.242, 0.97, 23.0),  # job-917 __14: a futás 24,2%-án
        (0.735, 0.97, 71.0),  # job-917 __20: a futás 73,5%-án
        (1.0, 0.97, 97.0),  # job-908 __20: jobb vég
        (1.0, 1.07, 107.0),  # job-918 __18: jobb vég, 768 x 512-es kép
        (0.0, 1.07, 3.0),  # job-918 __24: bal vég
    ],
)
def test_a_kepernyokor_sugara_a_mert_pontokon(t: float, z: float, mert_r: float) -> None:
    """R = max(3, 100 · s · z), s = t. A mért R ±1 képponton belül."""
    assert abs(brush.screen_radius(t, z) - mert_r) <= 1.0, (t, z, mert_r)


@pytest.mark.parametrize(("z", "mert_r"), [(0.97, 24.0), (1.07, 27.0), (0.80, 20.0)])
def test_az_indulo_kor_sugara_a_mert_pontokon(z: float, mert_r: float) -> None:
    """Induláskor s = 0,25: job-907 __12 (z = 0,97, R = 24,0), job-918 __12 (z = 1,07, R = 27,0),
    a job #314 kép (z = 0,80, R = 20,0)."""
    assert abs(brush.screen_radius(0.25, z) - mert_r) <= 1.0, (z, mert_r)


def test_a_cafolt_alakok_nem_illenek_a_mert_pontokhoz() -> None:
    """Az `s = t²` és az `s = 1,5·t - 0,5` a két köztes mért ponton elvéti az R-t (több mint 1 képpont)."""
    for t, z, mert_r in ((0.242, 0.97, 23.0), (0.735, 0.97, 71.0)):
        negyzetes = max(3.0, 100 * t * t * z)
        linearis_eltolt = max(3.0, 100 * max(0.0, 1.5 * t - 0.5) * z)
        assert abs(negyzetes - mert_r) > 1.0
        assert abs(linearis_eltolt - mert_r) > 1.0
        assert abs(brush.screen_radius(t, z) - mert_r) <= 1.0


@pytest.mark.parametrize("z", [0.25, 0.8, 0.97, 1.0, 1.07, 2.0, 4.0])
def test_a_forrasradius_a_kepernyokor_osztva_a_nagyitassal(z: float) -> None:
    for s in (0.0, 0.25, 0.5, 1.0):
        assert brush.source_radius(s, z) == pytest.approx(brush.screen_radius(s, z) / z)


def test_a_forrasradius_nagyitastol_fuggetlen_a_minimumon_felul() -> None:
    """A 3 képpontos minimum fölött a forrásképi sugár 100·s: nem függ a nagyítástól."""
    for z in (0.5, 0.97, 1.5, 3.0):
        assert brush.source_radius(1.0, z) == pytest.approx(100.0)
        assert brush.source_radius(0.5, z) == pytest.approx(50.0)


def test_a_megjelenitett_kor_a_nagyitassal_aranyos() -> None:
    """Az alapállású kör R-je 24,0 (z = 0,97) és 20,0 (z = 0,80): a nagyítások aranyával nő."""
    assert brush.screen_radius(0.25, 0.97) / brush.screen_radius(0.25, 0.80) == pytest.approx(0.97 / 0.80)


def test_a_minimum_harom_kepernyokepont() -> None:
    assert brush.screen_radius(0.0, 0.5) == 3.0
    assert brush.screen_radius(0.0, 2.0) == 3.0
    # a forrásképi sugár ilyenkor 3 / z
    assert brush.source_radius(0.0, 2.0) == pytest.approx(1.5)
    assert brush.source_radius(0.0, 0.5) == pytest.approx(6.0)


@pytest.mark.parametrize("rossz", [0.0, -1.0, math.nan, math.inf, -math.inf])
def test_ervenytelen_nagyitas_az_egyre_esik_vissza(rossz: float) -> None:
    assert brush.sanitize_zoom(rossz) == 1.0
    assert brush.sanitize_zoom(0.97) == 0.97


def test_a_relativ_sugar_a_rovidebb_oldalhoz_mert_forrasradius() -> None:
    assert brush.relative_radius(25.0, 1024) == pytest.approx(25 / 1024)
    assert brush.relative_radius(25.0, 256) == pytest.approx(25 / 256)
    # a körnél nagyobb sugár a képre vágva (az ini 16 bites kódolása 1,0 alatt marad)
    assert brush.relative_radius(500.0, 100) == 1.0


def test_a_relativ_sugar_ervenytelen_rovidebb_oldalnal_hiba() -> None:
    with pytest.raises(ValueError):
        brush.relative_radius(10.0, 0)


# --- a vezérlő ---------------------------------------------------------------------------


def _foltok(controller) -> tuple:
    return controller._retouch_patches


def test_a_vezerlo_alapallasa_a_csuszka_kozepen_es_az_indulo_sugar(controller, photo) -> None:
    """A csúszka fogantyúja középen áll, a sugár az induló s = 0,25-ből jön: 25 forrásképpont (z = 1)."""
    controller.beginEdit("1", str(photo))
    assert abs(brush.slider_position(controller.brushSize) - 0.5) <= 0.01
    assert controller.retouchBrushSourceRadius == pytest.approx(25.0)


def test_a_csuszka_megerintese_utan_s_egyenlo_t(controller, photo) -> None:
    controller.beginEdit("1", str(photo))
    controller.setBrushSize(100)
    assert controller.retouchBrushSourceRadius == pytest.approx(100.0)
    controller.setBrushSize(1)
    # a bal végen a 3 képpontos minimum dominál: z = 1-nél 3 forrásképpont
    assert controller.retouchBrushSourceRadius == pytest.approx(3.0)
    controller.setBrushSize(74)
    assert controller.retouchBrushSourceRadius == pytest.approx(100 * 73 / 99)


def test_a_nagyitas_a_forrasradiust_csak_a_minimumnal_modositja(controller, photo) -> None:
    controller.beginEdit("1", str(photo))
    controller.setBrushSize(100)
    controller.setRetouchViewZoom(0.5)
    assert controller.retouchBrushSourceRadius == pytest.approx(100.0)
    controller.setBrushSize(1)
    assert controller.retouchBrushSourceRadius == pytest.approx(6.0)
    controller.setRetouchViewZoom(3.0)
    assert controller.retouchBrushSourceRadius == pytest.approx(1.0)


def test_a_nagyitas_valtozasa_jelzest_kuld(controller, photo) -> None:
    controller.beginEdit("1", str(photo))
    jelzesek: list[int] = []
    controller.retouchBrushSourceRadiusChanged.connect(lambda: jelzesek.append(1))
    controller.setRetouchViewZoom(0.5)
    assert len(jelzesek) == 1
    controller.setRetouchViewZoom(0.5)
    assert len(jelzesek) == 1, "változatlan nagyításra nincs új jelzés"


def test_az_ecsetallapot_uj_szerkesztesnel_alapra_all(controller, photo) -> None:
    controller.beginEdit("1", str(photo))
    controller.setBrushSize(100)
    controller.endEdit()
    controller.beginEdit("1", str(photo))
    assert controller.retouchBrushSourceRadius == pytest.approx(25.0)
    assert abs(brush.slider_position(controller.brushSize) - 0.5) <= 0.01


def _folt_sugara_pixelben(controller, kep_rovidebb_oldal: int) -> float:
    controller.enterRetouchTool()
    controller.beginRetouchPatch(0.3, 0.3)
    controller.commitRetouchPatch(0.6, 0.6)
    (folt,) = _foltok(controller)
    return folt.radius * kep_rovidebb_oldal


def test_a_folt_kepponstsugara_az_elonezeti_gyuru_forrassugaraval_egyezik(controller, photo) -> None:
    """A mentett folt relatív sugara a forrásképi sugár osztva a kép rövidebb oldalával."""
    controller.beginEdit("1", str(photo))
    rovidebb = min(controller._image_size)
    controller.setBrushSize(74)
    elvart = controller.retouchBrushSourceRadius
    assert _folt_sugara_pixelben(controller, rovidebb) == pytest.approx(elvart)


def test_a_folt_relativ_sugara_a_kep_meretetol_fugg_a_kepponstsugar_nem(
    controller, tmp_path
) -> None:
    """Két eltérő képméreten ugyanaz a csúszkaérték ugyanazt a forrásképi sugarat adja (a relatív
    sugár a képméretet követi, hogy a `retouch=2` formátum ne változzon)."""
    kicsi = make_jpeg(tmp_path / "kicsi.jpg", size=(192, 128))
    nagy = make_jpeg(tmp_path / "nagy.jpg", size=(640, 480))
    eredmenyek = []
    for fajl in (kicsi, nagy):
        controller.beginEdit("1", str(fajl))
        controller.setBrushSize(50)
        rovidebb = min(controller._image_size)
        eredmenyek.append(
            (_folt_sugara_pixelben(controller, rovidebb), controller._retouch_patches[0].radius)
        )
        controller.exitRetouchTool()
        controller.endEdit()
    (kicsi_px, kicsi_rel), (nagy_px, nagy_rel) = eredmenyek
    assert kicsi_px == pytest.approx(nagy_px)
    assert kicsi_rel != pytest.approx(nagy_rel)
    assert kicsi_rel == pytest.approx(brush.source_radius(49 / 99, 1.0) / 128)
    assert nagy_rel == pytest.approx(brush.source_radius(49 / 99, 1.0) / 480)


def test_a_mentett_folt_ini_kodolasa_a_relativ_sugarat_orzi() -> None:
    folt = RetouchPatch(target_x=0.3, target_y=0.3, source_x=0.6, source_y=0.6, radius=25 / 1024)
    visszaolvasott = decode_patch(encode_patch(folt))
    assert abs(visszaolvasott.radius * 1024 - 25.0) <= 0.1
