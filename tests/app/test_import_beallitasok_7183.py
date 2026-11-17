"""Az import almappa-módja, törlési módja és célmappa-előzménye - #7183.

Az eredeti Picasa:

* `acquireUseSubFolder` alapja 0 (kézi cím), az import INDÍTÁSAKOR mentődik;
* `acquireCleanCard` alapja 0 (Leave card alone); olvasáskor a 2 (összes
  törlése) 1-re (csak a másolt) esik vissza;
* a legutóbbi célok (`LastImport%x`) az indításkor mentődnek, legfeljebb öt;
* a törlési mód csak olyan forrásnál él, amelynek a gyökerében `DCIM` mappa
  van (kis- és nagybetűre érzéketlenül).

A vezérlő szintjén mérünk, valódi (ideiglenes) mappákkal; a felületi
viselkedés a `qml_functional/test_import_beallitasok_7183.py`-ban él.
"""

from __future__ import annotations

import threading
from pathlib import Path

import pytest
from PySide6.QtCore import QSettings

from picasapy.app.import_source_controller import (
    AFTER_COPY_DELETE_ALL,
    AFTER_COPY_DELETE_COPIED,
    AFTER_COPY_LEAVE,
    MAX_RECENT_DESTINATIONS,
    NAMING_BY_DATE,
    NAMING_MANUAL,
    NAMING_TODAY,
    ImportSourceController,
)
from support.jpeg_factory import make_jpeg


def _vezerlo(qt_app, tmp_path, settings_nev: str = "settings.ini"):
    settings = QSettings(
        str(tmp_path / settings_nev), QSettings.Format.IniFormat
    )
    return ImportSourceController(
        provider=None,
        add_folder=lambda _path: None,
        index_path=tmp_path / "index.db",
        settings=settings,
    )


@pytest.fixture
def ctl(qt_app, tmp_path):
    return _vezerlo(qt_app, tmp_path)


def _utvonalak(elemek) -> list[Path]:
    """A felületen látszó útvonalak, `Path`-ként (platformfüggetlen összevetés)."""
    return [Path(str(elem)) for elem in elemek]


def _forras(tmp_path, nev: str = "kartya", darab: int = 1):
    forras = tmp_path / nev
    forras.mkdir()
    for index in range(darab):
        make_jpeg(
            forras / f"kep-{index}.jpg",
            taken_at=f"2024:03:{5 + index:02d} 10:00:00",
        )
    return forras


def _beolvas(ctl, forras, qt_app) -> None:
    kesz = threading.Event()
    ctl.sourceScanFinished.connect(lambda *_a: kesz.set())
    ctl.scanSource(str(forras))
    while not kesz.is_set():
        qt_app.processEvents()
        kesz.wait(0.01)
    qt_app.processEvents()


def _import(ctl, qt_app, cel, naming, nev, after):
    vege = threading.Event()
    ctl.importFinished.connect(lambda *_a: vege.set())
    ctl.runImport(str(cel), naming, nev, after)
    assert ctl.waitForBackgroundWorkers(30.0), "az import szála nem állt le"
    qt_app.processEvents()
    assert vege.is_set(), "az importFinished nem érkezett meg"


class TestAlapertekek:
    def test_ures_profilban_kezi_cim_az_almappa_mod(self, ctl):
        assert ctl.namingMode == NAMING_MANUAL

    def test_ures_profilban_leave_a_torlesi_mod(self, ctl):
        assert ctl.afterCopying == AFTER_COPY_LEAVE

    def test_ismeretlen_tarolt_almappa_mod_a_kezi_cimre_esik(self, ctl):
        ctl._get_settings().setValue("import/namingmode", "valami-mas")
        assert ctl.namingMode == NAMING_MANUAL

    def test_ismeretlen_tarolt_torlesi_mod_leave(self, ctl):
        ctl._get_settings().setValue("import/aftercopying", "valami-mas")
        assert ctl.afterCopying == AFTER_COPY_LEAVE


class TestMentesAzIndulaskor:
    @pytest.mark.parametrize("mod", [NAMING_MANUAL, NAMING_BY_DATE, NAMING_TODAY])
    def test_az_almappa_mod_az_import_inditasakor_mentodik(
        self, ctl, qt_app, tmp_path, mod
    ):
        forras = _forras(tmp_path)
        cel = tmp_path / "cel"
        cel.mkdir()
        _beolvas(ctl, forras, qt_app)

        _import(ctl, qt_app, cel, mod, "Nyaralas", AFTER_COPY_LEAVE)

        assert ctl.namingMode == mod

    def test_a_torlesi_mod_az_import_inditasakor_mentodik(
        self, ctl, qt_app, tmp_path
    ):
        forras = _forras(tmp_path)
        cel = tmp_path / "cel"
        cel.mkdir()
        _beolvas(ctl, forras, qt_app)

        _import(ctl, qt_app, cel, NAMING_BY_DATE, "", AFTER_COPY_DELETE_COPIED)

        assert ctl.afterCopying == AFTER_COPY_DELETE_COPIED

    def test_a_tarolt_ertek_uj_vezerloben_is_megvan(self, qt_app, tmp_path):
        elso = _vezerlo(qt_app, tmp_path)
        forras = _forras(tmp_path)
        cel = tmp_path / "cel"
        cel.mkdir()
        _beolvas(elso, forras, qt_app)
        _import(elso, qt_app, cel, NAMING_TODAY, "", AFTER_COPY_DELETE_COPIED)
        elso._get_settings().sync()

        masodik = _vezerlo(qt_app, tmp_path)

        assert masodik.namingMode == NAMING_TODAY
        assert masodik.afterCopying == AFTER_COPY_DELETE_COPIED

    def test_a_mentett_delete_all_ujranyitaskor_delete_copied(
        self, qt_app, tmp_path
    ):
        elso = _vezerlo(qt_app, tmp_path)
        forras = _forras(tmp_path)
        cel = tmp_path / "cel"
        cel.mkdir()
        _beolvas(elso, forras, qt_app)
        _import(elso, qt_app, cel, NAMING_BY_DATE, "", AFTER_COPY_DELETE_ALL)
        elso._get_settings().sync()

        masodik = _vezerlo(qt_app, tmp_path)

        assert masodik.afterCopying == AFTER_COPY_DELETE_COPIED

    def test_ervenytelen_kezi_cimnel_nincs_import_es_nincs_mentes(
        self, ctl, qt_app, tmp_path
    ):
        forras = _forras(tmp_path)
        cel = tmp_path / "cel"
        cel.mkdir()
        _beolvas(ctl, forras, qt_app)

        ctl.runImport(str(cel), NAMING_MANUAL, "../x", AFTER_COPY_DELETE_COPIED)
        qt_app.processEvents()

        assert ctl.namingMode == NAMING_MANUAL
        assert ctl.afterCopying == AFTER_COPY_LEAVE
        assert _utvonalak(ctl.recentDestinations) == []


class TestACelmappaElozmeny:
    def test_legfeljebb_ot_elemu_a_lista(self):
        assert MAX_RECENT_DESTINATIONS == 5

    def test_a_cel_az_inditaskor_bekerul_a_listaba(
        self, ctl, qt_app, tmp_path
    ):
        forras = _forras(tmp_path)
        cel = tmp_path / "cel"
        cel.mkdir()
        _beolvas(ctl, forras, qt_app)

        _import(ctl, qt_app, cel, NAMING_BY_DATE, "", AFTER_COPY_LEAVE)

        assert _utvonalak(ctl.recentDestinations) == [cel]

    def test_hibas_futasnal_is_bekerul_a_cel(
        self, ctl, qt_app, tmp_path, monkeypatch
    ):
        """Az eredeti a hibás célt is megjegyzi: a mentés az indításkor
        történik, nem a sikeres másolás után (ez felülírja a #1785
        korábbi, sikeres-másolás utáni mentését)."""
        import picasapy.app.import_source_controller as modul

        forras = _forras(tmp_path)
        cel = tmp_path / "hibas-cel"
        cel.mkdir()
        _beolvas(ctl, forras, qt_app)

        def hibas_masolas(*_args, **_kwargs):
            raise OSError("a cél írásvédett")

        monkeypatch.setattr(modul, "copy_photo", hibas_masolas)
        vege = []
        ctl.importFinished.connect(lambda ok, hiba: vege.append((ok, hiba)))

        ctl.runImport(str(cel), NAMING_BY_DATE, "", AFTER_COPY_LEAVE)
        assert ctl.waitForBackgroundWorkers(30.0)
        qt_app.processEvents()

        assert vege == [(0, 1)]
        assert _utvonalak(ctl.recentDestinations) == [cel]

    def test_nincs_eleg_hely_eseten_is_bekerul_a_cel(
        self, ctl, qt_app, tmp_path, monkeypatch
    ):
        import picasapy.app.import_source_controller as modul

        forras = _forras(tmp_path)
        cel = tmp_path / "tele-cel"
        cel.mkdir()
        _beolvas(ctl, forras, qt_app)
        monkeypatch.setattr(modul, "has_enough_free_space", lambda *_a: False)
        vege = []
        ctl.importFinished.connect(lambda ok, hiba: vege.append((ok, hiba)))

        ctl.runImport(str(cel), NAMING_BY_DATE, "", AFTER_COPY_LEAVE)
        assert ctl.waitForBackgroundWorkers(30.0)
        qt_app.processEvents()

        assert vege == [(0, 1)]
        assert _utvonalak(ctl.recentDestinations) == [cel]

    def test_az_ot_elem_utan_a_legregebbi_kiesik(self, ctl, qt_app, tmp_path):
        forras = _forras(tmp_path)
        _beolvas(ctl, forras, qt_app)
        celok = []
        for index in range(MAX_RECENT_DESTINATIONS + 1):
            cel = tmp_path / f"cel-{index}"
            cel.mkdir()
            celok.append(cel)
            _import(ctl, qt_app, cel, NAMING_BY_DATE, "", AFTER_COPY_LEAVE)

        assert _utvonalak(ctl.recentDestinations) == list(reversed(celok[1:]))

    def test_ugyanaz_a_cel_ketszer_nem_duplikal(
        self, ctl, qt_app, tmp_path
    ):
        forras = _forras(tmp_path)
        cel = tmp_path / "cel"
        cel.mkdir()
        _beolvas(ctl, forras, qt_app)

        _import(ctl, qt_app, cel, NAMING_BY_DATE, "", AFTER_COPY_LEAVE)
        _import(ctl, qt_app, cel, NAMING_BY_DATE, "", AFTER_COPY_LEAVE)

        assert _utvonalak(ctl.recentDestinations) == [cel]


class TestATorolhetoForras:
    def test_dcim_mappas_gyoker_torolheto(self, ctl, tmp_path):
        kartya = tmp_path / "kartya"
        (kartya / "DCIM").mkdir(parents=True)
        assert ctl.isDeletableSource(str(kartya)) is True

    @pytest.mark.parametrize("nev", ["dcim", "Dcim", "DcIm"])
    def test_a_dcim_vizsgalat_kis_nagybetu_erzektelen(self, ctl, tmp_path, nev):
        kartya = tmp_path / "kartya"
        (kartya / nev).mkdir(parents=True)
        assert ctl.isDeletableSource(str(kartya)) is True

    def test_dcim_nelkuli_gyoker_nem_torolheto(self, ctl, tmp_path):
        kartya = tmp_path / "kartya"
        (kartya / "Photos").mkdir(parents=True)
        assert ctl.isDeletableSource(str(kartya)) is False

    def test_a_dcim_nevu_FAJL_nem_mappa(self, ctl, tmp_path):
        kartya = tmp_path / "kartya"
        kartya.mkdir()
        (kartya / "DCIM").write_text("nem mappa", encoding="utf-8")
        assert ctl.isDeletableSource(str(kartya)) is False

    def test_csak_a_gyokerben_szamit_a_dcim(self, ctl, tmp_path):
        kartya = tmp_path / "kartya"
        (kartya / "almappa" / "DCIM").mkdir(parents=True)
        assert ctl.isDeletableSource(str(kartya)) is False

    def test_nem_letezo_vagy_ures_ut_nem_torolheto(self, ctl, tmp_path):
        assert ctl.isDeletableSource(str(tmp_path / "nincs-ilyen")) is False
        assert ctl.isDeletableSource("") is False

    def test_file_url_is_elfogadott(self, ctl, tmp_path):
        kartya = tmp_path / "kartya"
        (kartya / "DCIM").mkdir(parents=True)
        assert ctl.isDeletableSource(kartya.as_uri()) is True
