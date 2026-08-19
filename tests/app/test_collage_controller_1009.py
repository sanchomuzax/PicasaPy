"""#1009: a „Kép használata" TÉNYLEGES háttérképet választ.

A v0.8.1-ben a módváltás csak a rádiógombot mozdította el: a
`_collage_panel_bg_image` mezőt egyetlen hely írta, a
`setBackgroundFromSelection()`. Kijelölés nélkül tehát a mód átbillent
„Kép használata"-ra, de háttérkép nem lett, és a 37 × 37-es előnézet üres
maradt — a felhasználónak nem volt visszajelzése arról, mi a háttér.

**Amit az eredetiről tudunk.** A háttérkép a kollázs SAJÁT képeinek egyike,
**indexszel** hivatkozva (`0x00830a00(this, index)` tölti az előnézetet, és
`index == -1` esetén kilép — `0x00830a8b`). Ez *megerősített*.

**Amit következtetünk.** Hogy módváltáskor az ELSŐ kép lesz a háttér, az
*erős, de nem megerősített*: a golden-anyag két képhátteres mintájában
(`AI2.cxf`, `AI5.cxf`) a `<background><src>` mindkétszer a csomópontlista
első eleme, de nem zárható ki, hogy azt a felhasználó választotta. Ez tehát
**alapértelmezés**, nem törvény — a kijelöléssel bármikor felülírható, és
mindenképpen jobb a mai üres állapotnál.

A fájl állításai az ÁLLAPOTRÓL szólnak; hogy a felület ki is rajzolja, azt a
`qml_functional/test_collage_background_1009.py` dönti el.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QSettings

from picasapy.collage.autosave import AUTOSAVE_NAME
from picasapy.collage.cxf import loads

from support.jpeg_factory import make_jpeg


class _Photo:
    def __init__(self, folder_path, name, caption=None, width=400, height=300):
        self.folder_path = folder_path
        self.name = name
        self.caption = caption
        self.width = width
        self.height = height


class _Photos:
    def __init__(self, photos):
        self.photos = list(photos)


@pytest.fixture
def library(tmp_path):
    """Ékezetes mappa szándékosan: a kimenet is ilyenbe megy (#190)."""
    root = tmp_path / "Nyaralás 2026"
    root.mkdir()
    for name in ("a.jpg", "b.jpg", "c.jpg"):
        make_jpeg(root / name, size=(80, 60))
    return root


@pytest.fixture
def host(qt_app, tmp_path, library):
    from picasapy.app.collage_controller import COLLAGE_OUTPUT_DIR_KEY, CollageMixin

    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    settings.setValue(COLLAGE_OUTPUT_DIR_KEY, str(tmp_path / "Kollázsok"))

    class _Host(CollageMixin, QObject):
        def __init__(self):
            super().__init__()
            self._settings = settings
            self._photos = _Photos(
                [
                    _Photo(str(library), "a.jpg", "Alma"),
                    _Photo(str(library), "b.jpg"),
                    _Photo(str(library), "c.jpg", "Cica"),
                ]
            )

        def _get_settings(self):
            return self._settings

        def _screen_ratio(self):
            return 9 / 16

    instance = _Host()
    yield instance
    assert instance.waitForBackgroundWorkers(30.0), "a kollázs-szál nem állt le"


@pytest.fixture
def nyitott(host):
    host.openCollage([0, 1, 2])
    return host


def _utak(vezerlo) -> list[str]:
    return [csomopont.path for csomopont in vezerlo.collageNodes.nodes]


class TestModvaltas:
    def test_a_kep_hasznalata_TENYLEG_valaszt_kepet(self, nyitott):
        """A jegy lényege: a módváltás után van háttérkép."""
        nyitott.setCollageBackgroundMode("image")
        assert nyitott.collageBackgroundImage != ""

    def test_a_valasztott_kep_a_kollazs_SAJAT_kepe(self, nyitott):
        nyitott.setCollageBackgroundMode("image")
        assert nyitott.collageBackgroundImage in _utak(nyitott)

    def test_alapertelmezesben_az_ELSO_kep(self, nyitott):
        """Erős következtetés a golden két mintájából — alapértelmezés."""
        nyitott.setCollageBackgroundMode("image")
        assert nyitott.collageBackgroundImage == _utak(nyitott)[0]

    def test_a_modvaltas_jelzi_a_kepvaltast(self, nyitott):
        """Jelzés nélkül a QML-kötés nem frissül: az előnézet üres maradna."""
        kaptunk: list[int] = []
        nyitott.collageBackgroundImageChanged.connect(lambda: kaptunk.append(1))
        nyitott.setCollageBackgroundMode("image")
        assert kaptunk, "elmaradt a collageBackgroundImageChanged"

    def test_egyszinu_modban_nincs_hatterkep(self, nyitott):
        assert nyitott.collageBackgroundMode == "solid"
        assert nyitott.collageBackgroundImage == ""

    def test_kep_nelkuli_kollazsban_sem_omlik_ossze(self, host):
        host.setCollageBackgroundMode("image")
        assert host.collageBackgroundImage == ""

    def test_a_visszavaltas_nem_felejti_el_a_valasztast(self, nyitott):
        nyitott.setCollageSelection([2])
        nyitott.setBackgroundFromSelection()
        valasztott = nyitott.collageBackgroundImage
        nyitott.setCollageBackgroundMode("solid")
        nyitott.setCollageBackgroundMode("image")
        assert nyitott.collageBackgroundImage == valasztott


class TestKijelolesFelulirja:
    def test_a_kijeloles_felulirja_az_alapertelmezest(self, nyitott):
        nyitott.setCollageBackgroundMode("image")
        nyitott.setCollageSelection([2])
        nyitott.setBackgroundFromSelection()
        assert Path(nyitott.collageBackgroundImage).name == "c.jpg"
        assert nyitott.collageBackgroundMode == "image"

    def test_kijeloles_nelkul_marad_a_regi_hatter(self, nyitott):
        nyitott.setCollageSelection([2])
        nyitott.setBackgroundFromSelection()
        nyitott.setCollageSelection([0, 1])
        nyitott.setBackgroundFromSelection()
        assert Path(nyitott.collageBackgroundImage).name == "c.jpg"


class TestTorottHivatkozas:
    def test_a_hatterkep_eltavolitasa_nem_hagy_torott_hivatkozast(self, nyitott):
        nyitott.setCollageBackgroundMode("image")
        eltavolitando = nyitott.collageBackgroundImage
        nyitott.setCollageSelection([_utak(nyitott).index(eltavolitando)])
        nyitott.removeSelectedNodes()
        assert nyitott.collageBackgroundImage != eltavolitando
        assert nyitott.collageBackgroundImage in _utak(nyitott)

    def test_az_utolso_kep_utan_ures_a_hatter(self, nyitott):
        nyitott.setCollageBackgroundMode("image")
        nyitott.selectAllNodes()
        nyitott.removeSelectedNodes()
        assert nyitott.collageBackgroundImage == ""

    def test_a_hatter_a_KEPET_koveti_nem_a_rest(self, nyitott):
        """Keverés után is ugyanaz a KÉP a háttér, nem ami a helyére csúszott."""
        nyitott.setCollageSelection([2])
        nyitott.setBackgroundFromSelection()
        valasztott = nyitott.collageBackgroundImage
        nyitott.swapNodes(0, 2)
        assert nyitott.collageBackgroundImage == valasztott

    def test_a_bezaras_utan_nem_marad_hatterkep(self, nyitott):
        nyitott.setCollageBackgroundMode("image")
        nyitott.closeCollage()
        assert nyitott.collageBackgroundImage == ""


class TestCxf:
    """A mentett projektfájl ugyanazt a hátteret mutassa, mint a panel."""

    def _piszkozat(self, vezerlo, tmp_path):
        vezerlo.saveCollageDraft()
        ut = tmp_path / "Kollázsok" / AUTOSAVE_NAME
        assert ut.exists(), "nem született piszkozat"
        return loads(ut.read_bytes())

    def test_a_kephatter_kimegy_a_cxf_be(self, nyitott, tmp_path):
        nyitott.setCollageBackgroundMode("image")
        projekt = self._piszkozat(nyitott, tmp_path)
        assert projekt.background.type == "image"
        assert projekt.background.src == nyitott.collageBackgroundImage

    def test_a_cxf_hattere_a_kollazs_egyik_kepe(self, nyitott, tmp_path):
        nyitott.setCollageBackgroundMode("image")
        projekt = self._piszkozat(nyitott, tmp_path)
        assert projekt.background.src in [csomo.src for csomo in projekt.nodes]

    def test_a_kijelolt_hatter_megy_ki_nem_az_elso(self, nyitott, tmp_path):
        nyitott.setCollageSelection([2])
        nyitott.setBackgroundFromSelection()
        projekt = self._piszkozat(nyitott, tmp_path)
        assert Path(projekt.background.src).name == "c.jpg"

    def test_egyszinu_modban_marad_a_solid(self, nyitott, tmp_path):
        projekt = self._piszkozat(nyitott, tmp_path)
        assert projekt.background.type == "solid"
        assert projekt.background.src == ""
