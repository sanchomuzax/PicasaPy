"""A megjelenítési mód vezérlő-szeletének tesztjei — #1575.

A `Nézet ▸ Megjelenítési mód` almenü **tizenegy tagú, egyetlen kizáró
csoport** (mérve: `0x00575670`, ld. `docs/specs/picasa-megjelenitesi-modok.md`
1–2. szakasz). Ez a fájl a szelet három szerződését állítja:

* a tizenegy mód azonosítója és **sorrendje** a spec szerinti,
* az alapértelmezés az `auto` (`ID_VIEW_AUTO`, mérve: `0x0040bd90`),
* az érték **NEM tárolódik el** — se QSettings, se fájl (mérve: a beállító
  semmit nem ír, 6. szakasz). Minden indulás alaphelyzetből kezd.

A negyedik szerződés — „azonos értékre állítva NE jelezzen" — nem
kényelmi optimalizáció, hanem a QML-oldali **rádió-csapda őrének foga**:
ha a beállító feltétel nélkül jelezne, a menü pipája a hibás
(visszakötés nélküli) QML mellett is helyreállna, és a
`test_megjelenitesi_mod_menu_1575.py` funkcionális tesztje semmit nem
bizonyítana (ld. a #1468 „őszinte címke" bekezdéseit).
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QSettings

from picasapy.app.display_mode_controller import (
    DEFAULT_DISPLAY_MODE,
    DISPLAY_MODES,
    DisplayModeMixin,
)


class _Proba(DisplayModeMixin, QObject):
    """A mixin önmagában — csak a `_get_settings()`-re támaszkodik."""

    def __init__(self, settings):
        super().__init__()
        self._settings = settings
        self._init_display_mode()

    def _get_settings(self):
        return self._settings


@pytest.fixture
def settings(tmp_path):
    return QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)


@pytest.fixture
def controller(qt_app, settings):
    return _Proba(settings)


class TestModLista:
    """A tizenegy mód és a sorrendjük — a spec 1. szakasza."""

    def test_pontosan_tizenegy_mod(self):
        assert len(DISPLAY_MODES) == 11
        assert len(set(DISPLAY_MODES)) == 11, "ismétlődő módazonosító"

    def test_a_sorrend_a_specet_koveti(self):
        assert DISPLAY_MODES == (
            "auto",
            "normal",
            "dither16",
            "rdesk",
            "lcd",
            "projector",
            "overflow",
            "mac",
            "linear",
            "sepia",
            "bw",
        )

    def test_az_alapertelmezes_az_automatikus(self):
        assert DEFAULT_DISPLAY_MODE == "auto"
        assert DEFAULT_DISPLAY_MODE in DISPLAY_MODES


class TestBeallitas:
    def test_indulaskor_az_alapertelmezes_all(self, controller):
        assert controller.displayMode == DEFAULT_DISPLAY_MODE

    @pytest.mark.parametrize("mode", DISPLAY_MODES)
    def test_mind_a_tizenegy_beallithato(self, controller, mode):
        controller.setDisplayMode(mode)
        assert controller.displayMode == mode

    @pytest.mark.parametrize("rossz", ["", "nincs-ilyen", "AUTO", None, 7, b"auto"])
    def test_ismeretlen_erteket_kihagy(self, controller, rossz):
        controller.setDisplayMode("sepia")
        controller.setDisplayMode(rossz)
        assert controller.displayMode == "sepia"


class TestNemTarolodikEl:
    """MÉRVE: a beállító semmit nem ír — minden indítás alaphelyzet.

    Ez nem hiányosság, hanem az eredeti viselkedés; bevezetni TILOS.
    """

    def test_a_beallitas_nem_ir_a_qsettingsbe(self, controller, settings):
        elotte = set(settings.allKeys())
        controller.setDisplayMode("projector")
        settings.sync()
        assert set(settings.allKeys()) == elotte

    def test_uj_peldany_alaphelyzetbol_indul(self, qt_app, settings):
        elso = _Proba(settings)
        elso.setDisplayMode("bw")
        assert elso.displayMode == "bw"

        masodik = _Proba(settings)
        assert masodik.displayMode == DEFAULT_DISPLAY_MODE


class TestJelzes:
    """A jelzés a rádió-csapda őrének foga — ld. a modul-docstringet."""

    @staticmethod
    def _szamlalo(controller):
        jelzesek = []
        controller.displayModeChanged.connect(lambda: jelzesek.append(1))
        return jelzesek

    def test_valodi_valtasnal_jelez(self, controller):
        jelzesek = self._szamlalo(controller)
        controller.setDisplayMode("lcd")
        assert len(jelzesek) == 1

    def test_azonos_ertekre_allitva_NEM_jelez(self, controller):
        controller.setDisplayMode("lcd")
        jelzesek = self._szamlalo(controller)
        controller.setDisplayMode("lcd")
        assert jelzesek == [], (
            "a beállító azonos értéknél is jelzett — ettől a menü pipája a "
            "HIBÁS (visszakötés nélküli) QML mellett is helyreállna, és a "
            "rádió-csapda funkcionális tesztje elveszítené a fogát"
        )

    def test_ismeretlen_erteknel_NEM_jelez(self, controller):
        jelzesek = self._szamlalo(controller)
        controller.setDisplayMode("nincs-ilyen")
        assert jelzesek == []


class TestAppControllerbeKeverve:
    """A szelet tényleg az `AppController` része — nem árva modul."""

    def test_az_appcontroller_orokli(self):
        from picasapy.app.controller import AppController

        assert issubclass(AppController, DisplayModeMixin)
