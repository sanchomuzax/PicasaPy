"""A `Színkezelés használata` kapcsoló (#1725).

A viselkedés a `docs/specs/picasa-megjelenitesi-modok.md` 5.12 szakaszából
jön, MÉRVE az eredeti binárison:

* a kapcsoló a `Preferences\\EnableColorManagement`-en tárolódik, **alap 0**
  (`0x005c95bf`), tehát nálunk is perzisztens és alapból kikapcsolt;
* a kezelő a színkezelés-objektum `+0x5c` bájtjába ír, és **minden**
  színkezelő hívás ezen a bájton áll vagy bukik (`0x00a3e3bd`,
  `0x00a3e591`) — kikapcsolva no-op;
* a motor **littleCMS** (`"not an ICC profile, invalid signature"`,
  `"cmsWhitePointFromTemp"`), tehát a hatás a beágyazott ICC-profil
  SZABVÁNYOS átalakítása, nem saját színtan;
* bekapcsoláskor a szerkesztő-előnézet **újraépül** (`0x005c966a`).

⚠️ Az `icc_camera_to_tone_matrix` (3×3) a nyers kamerakép külön útja; a
beszorzás helye NINCS kimérve, ezért ez a jegy nem is állít róla semmit.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QSettings
from PySide6.QtGui import QColorSpace, QImage

from picasapy.app.color_management_controller import (
    COLOR_MANAGEMENT_KEY,
    ColorManagementMixin,
    coerce_color_management_flag,
    wire_color_management,
)
from picasapy.app.edit_preview import _decode_source

_NEVEZETT = QColorSpace.NamedColorSpace


def _adobergb_kep(utvonal) -> None:
    """Négy képpont AdobeRGB-profillal — a beágyazott profil hordozója."""
    kep = QImage(4, 4, QImage.Format.Format_RGB32)
    kep.fill(0xFF804020)
    kep.setColorSpace(QColorSpace(_NEVEZETT.AdobeRgb))
    assert kep.save(str(utvonal))


class TestCoerce:
    @pytest.mark.parametrize("ertek", [True, "true", "1", "TRUE", " true "])
    def test_igaz_ertekek(self, ertek):
        assert coerce_color_management_flag(ertek) is True

    @pytest.mark.parametrize("ertek", [None, False, "false", "0", "", "hupak", 3.5])
    def test_hamis_vagy_ertelmezhetetlen(self, ertek):
        assert coerce_color_management_flag(ertek) is False


class TestMixin:
    @pytest.fixture
    def controller(self, qt_app, tmp_path):
        class _Proba(ColorManagementMixin, QObject):
            def __init__(self, settings):
                super().__init__()
                self._settings = settings
                self._init_color_management()

            def _get_settings(self):
                return self._settings

        return _Proba(
            QSettings(str(tmp_path / "b.ini"), QSettings.Format.IniFormat)
        )

    def test_alapbol_kikapcsolt(self, controller):
        """MÉRVE: a GetPreference alapértéke 0 (`0x005c95bf`)."""
        assert controller.colorManagement is False

    def test_bekapcsolas_megmarad(self, controller):
        controller.setColorManagement(True)
        assert controller.colorManagement is True
        assert coerce_color_management_flag(
            controller._get_settings().value(COLOR_MANAGEMENT_KEY)
        )

    def test_valtas_mindket_iranyba(self, controller):
        controller.toggleColorManagement()
        assert controller.colorManagement is True
        controller.toggleColorManagement()
        assert controller.colorManagement is False

    def test_azonos_erteknel_nincs_jelzes(self, controller):
        """A pipa-kötés miatt fontos: azonos értéknél nincs jelzés (#1468)."""
        hivasok = []
        controller.colorManagementChanged.connect(lambda: hivasok.append(1))
        controller.setColorManagement(False)
        assert hivasok == []
        controller.setColorManagement(True)
        assert len(hivasok) == 1


class TestDekodolas:
    def test_kikapcsolva_a_keppont_valtozatlan(self, qt_app, tmp_path):
        utvonal = tmp_path / "a.png"
        _adobergb_kep(utvonal)
        tomb = _decode_source(utvonal, color_managed=False)
        assert tomb is not None
        assert tuple(int(x) for x in tomb[0, 0][:3]) == (0x80, 0x40, 0x20)

    def test_bekapcsolva_srgb_be_alakul(self, qt_app, tmp_path):
        utvonal = tmp_path / "a.png"
        _adobergb_kep(utvonal)
        tomb = _decode_source(utvonal, color_managed=True)
        assert tomb is not None
        keppont = tuple(int(x) for x in tomb[0, 0][:3])
        assert keppont != (0x80, 0x40, 0x20), (
            "a beágyazott AdobeRGB-profil átalakítása nem futott le"
        )

    def test_profil_nelkuli_kep_valtozatlan(self, qt_app, tmp_path):
        """Profil nélküli képen a bekapcsolt színkezelés sem változtat."""
        utvonal = tmp_path / "b.png"
        kep = QImage(4, 4, QImage.Format.Format_RGB32)
        kep.fill(0xFF804020)
        assert kep.save(str(utvonal))
        be = _decode_source(utvonal, color_managed=True)
        ki = _decode_source(utvonal, color_managed=False)
        assert be is not None and ki is not None
        assert tuple(be[0, 0][:3]) == tuple(ki[0, 0][:3])


class TestBekotes:
    def test_az_atvezeto_a_kezdo_allapotot_is_atviszi(self, qt_app, tmp_path):
        """A `wire_display_mode` mintája: a bekötés azonnal is átvezet."""

        class _Ctl(ColorManagementMixin, QObject):
            def __init__(self, settings):
                super().__init__()
                self._settings = settings
                self._init_color_management()

            def _get_settings(self):
                return self._settings

        class _Provider:
            def __init__(self):
                self.kapott = []

            def set_color_management(self, be):
                self.kapott.append(bool(be))

        class _Edit:
            def __init__(self):
                self.frissitesek = 0

            def refresh_displayed_image(self):
                self.frissitesek += 1

        beallitasok = QSettings(
            str(tmp_path / "c.ini"), QSettings.Format.IniFormat
        )
        beallitasok.setValue(COLOR_MANAGEMENT_KEY, "true")
        ctl, provider, edit = _Ctl(beallitasok), _Provider(), _Edit()

        wire_color_management(ctl, edit, provider)
        assert provider.kapott == [True], "a kezdő állapot nem ment át"
        assert edit.frissitesek == 1

        ctl.setColorManagement(False)
        assert provider.kapott == [True, False]
        assert edit.frissitesek == 2
