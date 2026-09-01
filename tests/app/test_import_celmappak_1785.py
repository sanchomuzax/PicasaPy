"""A korábbi import-CÉLMAPPÁK listája — #1785.

A dialógus a korábbi FORRÁSOKAT eddig is megjegyezte
(`importSourceRecentBox`), a CÉLT viszont nem: minden importálásnál újra
ki kellett tallózni, akkor is, ha ugyanoda ment, mint tegnap.

Az eredeti a célt is megjegyzi — `Preferences\\LastImport%x`, indexelt
kulcsokkal (0x00516180) —, és háromszakaszos menüben kínálja: korábbi
importok · alapértelmezett hely · „Choose…".

## Két döntés, kimondva

* **A nem létező mappa KIMARAD** a felkínált listából (a jegy a
  megvalósítóra bízta). A legördülőben minden tétel egy kattintható cél; egy
  letűnt kártyát felkínálni és hibával elutasítani rosszabb, mint meg sem
  mutatni. A TÁROLT lista nem csonkul: ha a mappa visszakerül, magától újra
  megjelenik — ezt külön teszt állítja.
* **A felső korlát nyolc**, ugyanannyi, mint a forrásoké. Az eredeti
  maximuma nincs kimérve; a jegy is ezt mondja.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import QSettings

from picasapy.app.import_source_controller import (
    MAX_RECENT_DESTINATIONS,
    RECENT_DESTINATIONS_SETTINGS_KEY,
    ImportSourceController,
)

_DIALOG = (
    Path(picasapy.app.__file__).parent
    / "qml" / "PicasaPy" / "ImportSourceDialog.qml"
).read_text(encoding="utf-8")


@pytest.fixture
def ctl(qt_app, tmp_path):
    settings = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    return ImportSourceController(
        provider=None,
        add_folder=lambda _path: None,
        index_path=tmp_path / "index.db",
        settings=settings,
    )


class TestATarolas:
    def test_ures_indulaskor(self, ctl):
        assert list(ctl.recentDestinations) == []

    def test_a_megjegyzett_cel_a_lista_elejere_kerul(self, ctl, tmp_path):
        egy = tmp_path / "egy"
        ketto = tmp_path / "ketto"
        egy.mkdir()
        ketto.mkdir()
        ctl._remember_destination(str(egy))
        ctl._remember_destination(str(ketto))
        assert list(ctl.recentDestinations) == [str(ketto), str(egy)]

    def test_ismetles_nem_duplikal(self, ctl, tmp_path):
        egy = tmp_path / "egy"
        egy.mkdir()
        ctl._remember_destination(str(egy))
        ctl._remember_destination(str(egy))
        assert list(ctl.recentDestinations) == [str(egy)]

    def test_a_lista_VEGES(self, ctl, tmp_path):
        for i in range(MAX_RECENT_DESTINATIONS + 4):
            mappa = tmp_path / f"m{i}"
            mappa.mkdir()
            ctl._remember_destination(str(mappa))
        assert len(ctl.recentDestinations) == MAX_RECENT_DESTINATIONS

    def test_tulELI_az_ujraindiast(self, qt_app, tmp_path):
        settings = QSettings(
            str(tmp_path / "s.ini"), QSettings.Format.IniFormat
        )
        cel = tmp_path / "cel"
        cel.mkdir()

        elso = ImportSourceController(
            provider=None,
            add_folder=lambda _p: None,
            index_path=tmp_path / "index.db",
            settings=settings,
        )
        elso._remember_destination(str(cel))
        settings.sync()

        masodik = ImportSourceController(
            provider=None,
            add_folder=lambda _p: None,
            index_path=tmp_path / "index.db",
            settings=settings,
        )
        assert list(masodik.recentDestinations) == [str(cel)]


class TestANemLetezoMappa:
    def test_KIMARAD_a_felkinalt_listabol(self, ctl, tmp_path):
        letezo = tmp_path / "letezo"
        letezo.mkdir()
        eltunt = tmp_path / "eltunt"
        eltunt.mkdir()
        ctl._remember_destination(str(letezo))
        ctl._remember_destination(str(eltunt))
        eltunt.rmdir()

        assert list(ctl.recentDestinations) == [str(letezo)]

    def test_a_TAROLT_lista_nem_csonkul(self, ctl, tmp_path):
        """Ha a mappa visszakerül (felcsatolt meghajtó), újra megjelenik."""
        eltunt = tmp_path / "eltunt"
        eltunt.mkdir()
        ctl._remember_destination(str(eltunt))
        eltunt.rmdir()
        assert list(ctl.recentDestinations) == []

        eltunt.mkdir()
        assert list(ctl.recentDestinations) == [str(eltunt)]

    def test_a_tarolt_kulcs_valoban_megorzi(self, ctl, tmp_path):
        eltunt = tmp_path / "eltunt"
        eltunt.mkdir()
        ctl._remember_destination(str(eltunt))
        eltunt.rmdir()
        tarolt = ctl._get_settings().value(RECENT_DESTINATIONS_SETTINGS_KEY)
        assert str(eltunt) in [str(x) for x in (tarolt or [])]


class TestAzAlapertelmezettHely:
    def test_van_alapertelmezett(self, ctl):
        assert ctl.defaultDestination

    def test_a_kepek_mappaja_alatti_Picasa_gyujto(self, ctl):
        assert Path(ctl.defaultDestination).name == "Picasa"


class TestAFelulet:
    def test_van_legordulo_a_celhoz(self):
        assert 'objectName: "importSourceRecentDestBox"' in _DIALOG

    def test_a_legordulo_a_vezerlobol_veszi_a_listat(self):
        assert "importSourceController.recentDestinations" in _DIALOG

    def test_az_alapertelmezett_hely_KULON_tetel(self):
        """Az eredeti menü külön szakaszba tette
        (`-seperator-before-default_location-`)."""
        assert "importSourceController.defaultDestination" in _DIALOG

    def test_az_alapertelmezett_nem_ISMETLODIK(self):
        """Ha már a korábbiak közt van, ne kerüljön ki kétszer."""
        kezd = _DIALOG.index('objectName: "importSourceRecentDestBox"')
        blokk = _DIALOG[kezd : kezd + 1400]
        assert "indexOf(" in blokk

    def test_a_valasztas_ATALLITJA_a_celt(self):
        kezd = _DIALOG.index('objectName: "importSourceRecentDestBox"')
        blokk = _DIALOG[kezd : kezd + 1400]
        assert "onActivated: importSourceWindow.destFolder" in blokk

    def test_a_Tallozas_gomb_MEGMARAD(self):
        """A harmadik szakasz (`Acquire::ChooseFolder`) nem tűnhet el."""
        assert 'objectName: "importSourceChooseDestButton"' in _DIALOG
