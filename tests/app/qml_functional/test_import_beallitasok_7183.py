"""Az importablak megjegyzi az almappa-módot, a törlési módot és a célmappát,
a törlési mód pedig csak DCIM-es kártyánál él - #7183.

Valódi kattintással futnak: az Import gomb, a forrás-legördülők, a rádiók,
az Import All és a megerősítő ablak gombjai. A csatolt meghajtót a
platformhatáron helyettesítő ideiglenes mappa adja (valódi meghajtóhoz nem
nyúlunk); a natív mappaválasztót a tesztek nem tudják kattintani, ezért a
mappa-forrást a választó `onAccepted` ágával azonos `useSourceFolder`
függvény adja.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, Qt

from support.import_kartya_7183 import (
    csatolt_kartya_kivalasztasa,
    elem,
    elozmeny_forras_kivalasztasa,
    kattint,
    kattint_letiltottra,
    varj,
)
from support.jpeg_factory import make_jpeg

_TORLESI_RADIOK = (
    "importSourceAfterDeleteCopiedRadio",
    "importSourceAfterDeleteAllRadio",
)
_MIND_A_HAROM = ("importSourceAfterLeaveRadio",) + _TORLESI_RADIOK


def _utvonalak(elemek) -> list[Path]:
    """A felületen látszó útvonalak, `Path`-ként (platformfüggetlen összevetés)."""
    return [Path(str(elem)) for elem in elemek]


def _megnyit(fo, qt_app):
    """Az Import gomb valódi kattintása; visszaadja az ablakot."""
    fo.resize(1280, 800)
    fo.show()
    qt_app.processEvents()
    kattint(fo, elem(fo, "toolbarImportButton"), qt_app)
    ablak = elem(fo, "importSourceDialog")
    varj(qt_app, lambda: ablak.property("visible") is True, "nem nyílt meg")
    return ablak


def _bezar(ablak, qt_app) -> None:
    kattint(ablak, elem(ablak, "importSourceCloseButton"), qt_app)
    varj(qt_app, lambda: ablak.property("visible") is False, "nem zárult be")


def _ujranyit(fo, ablak, qt_app) -> None:
    _bezar(ablak, qt_app)
    kattint(fo, elem(fo, "toolbarImportButton"), qt_app)
    varj(qt_app, lambda: ablak.property("visible") is True, "nem nyílt újra")
    qt_app.processEvents()


def _kartya(gyoker: Path, nev: str, *, dcim: str | None, darab: int = 1) -> Path:
    """Kártya-mappa; a képek a `DCIM` alatt (vagy anélkül) vannak."""
    kartya = gyoker / nev
    kepek = kartya / dcim / "100CANON" if dcim else kartya / "kepek"
    kepek.mkdir(parents=True)
    for index in range(darab):
        make_jpeg(
            kepek / f"kep-{index}.jpg",
            taken_at=f"2024:03:{5 + index:02d} 10:00:00",
        )
    return kartya


def _beallit_mappa_forrast(ablak, qt_app, mappa: Path, darab: int) -> None:
    """A mappaválasztó `onAccepted` ágával azonos függvény (natív
    választót tesztből nem lehet kattintani)."""
    assert QMetaObject.invokeMethod(
        ablak,
        "useSourceFolder",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", mappa.as_uri()),
        Q_ARG("QVariant", False),
    )
    varj(
        qt_app,
        lambda: not ablak.property("scanning")
        and int(ablak.property("previewCount")) == darab,
        "a mappa beolvasása nem fejeződött be",
    )
    qt_app.processEvents()


def _radiok_tiltottak_es_leave(ablak) -> None:
    for nev in _MIND_A_HAROM:
        assert elem(ablak, nev).property("enabled") is False, nev
    assert elem(ablak, "importSourceAfterLeaveRadio").property("checked") is True
    for nev in _TORLESI_RADIOK:
        assert elem(ablak, nev).property("checked") is False, nev
    assert ablak.property("effectiveAfterCopying") == "leave"


def _radiok_aktivak(ablak) -> None:
    for nev in _MIND_A_HAROM:
        assert elem(ablak, nev).property("enabled") is True, nev


@pytest.fixture
def app(qml_app, qt_app):
    fo, _vezerlo, engine = qml_app
    importvezerlo = engine.rootContext().contextProperty("importSourceController")
    assert importvezerlo is not None
    return fo, importvezerlo, qt_app


class TestUresProfil:
    def test_kezi_cimmel_es_leave_allassal_nyilik(self, app):
        fo, _vezerlo, qt_app = app
        ablak = _megnyit(fo, qt_app)

        assert ablak.property("namingMode") == "manual"
        assert ablak.property("afterCopying") == "leave"
        assert elem(ablak, "importSourceNamingManualRadio").property("checked") is True
        assert elem(ablak, "importSourceNamingByDateRadio").property("checked") is False
        assert elem(ablak, "importSourceNamingTodayRadio").property("checked") is False
        assert elem(ablak, "importSourceAfterLeaveRadio").property("checked") is True

    def test_forras_nelkul_a_torlesi_radiok_tiltottak(self, app):
        fo, _vezerlo, qt_app = app
        ablak = _megnyit(fo, qt_app)

        _radiok_tiltottak_es_leave(ablak)


class TestATorolhetoForras:
    def test_dcim_mappas_kartyanal_mind_a_harom_mod_aktiv(
        self, app, tmp_path, monkeypatch
    ):
        fo, vezerlo, qt_app = app
        ablak = _megnyit(fo, qt_app)
        kartya = _kartya(tmp_path, "kartya", dcim="DCIM")

        csatolt_kartya_kivalasztasa(ablak, vezerlo, qt_app, monkeypatch, kartya, darab=1)

        _radiok_aktivak(ablak)
        kattint(ablak, elem(ablak, "importSourceAfterDeleteCopiedRadio"), qt_app)
        assert ablak.property("afterCopying") == "delete_copied"
        assert ablak.property("effectiveAfterCopying") == "delete_copied"
        kattint(ablak, elem(ablak, "importSourceAfterDeleteAllRadio"), qt_app)
        assert ablak.property("afterCopying") == "delete_all"
        kattint(ablak, elem(ablak, "importSourceAfterLeaveRadio"), qt_app)
        assert ablak.property("afterCopying") == "leave"

    def test_kisbetus_dcim_mappa_is_torolhetove_teszi(
        self, app, tmp_path, monkeypatch
    ):
        fo, vezerlo, qt_app = app
        ablak = _megnyit(fo, qt_app)
        kartya = _kartya(tmp_path, "kartya", dcim="dcim")

        csatolt_kartya_kivalasztasa(ablak, vezerlo, qt_app, monkeypatch, kartya, darab=1)

        _radiok_aktivak(ablak)

    def test_dcim_nelkuli_meghajtonal_a_radiok_tiltottak_es_leave_all(
        self, app, tmp_path, monkeypatch
    ):
        fo, vezerlo, qt_app = app
        ablak = _megnyit(fo, qt_app)
        meghajto = _kartya(tmp_path, "usb", dcim=None)

        csatolt_kartya_kivalasztasa(ablak, vezerlo, qt_app, monkeypatch, meghajto, darab=1)

        _radiok_tiltottak_es_leave(ablak)
        kattint_letiltottra(
            ablak, elem(ablak, "importSourceAfterDeleteAllRadio"), qt_app
        )
        assert ablak.property("effectiveAfterCopying") == "leave"
        assert elem(ablak, "importSourceAfterLeaveRadio").property("checked") is True

    def test_mappa_forrasnal_a_radiok_tiltottak_es_leave_all(
        self, app, tmp_path
    ):
        """`Folder on Disk`: még DCIM mappás gyökérnél sem törölhető."""
        fo, _vezerlo, qt_app = app
        ablak = _megnyit(fo, qt_app)
        kartya = _kartya(tmp_path, "mappa", dcim="DCIM")

        _beallit_mappa_forrast(ablak, qt_app, kartya, 1)

        _radiok_tiltottak_es_leave(ablak)

    def test_fajl_forrasnal_a_radiok_tiltottak_es_leave_all(
        self, app, tmp_path
    ):
        fo, _vezerlo, qt_app = app
        ablak = _megnyit(fo, qt_app)
        kartya = _kartya(tmp_path, "fajlok", dcim="DCIM")
        fajl = kartya / "DCIM" / "100CANON" / "kep-0.jpg"

        assert QMetaObject.invokeMethod(
            ablak,
            "useSelectedFiles",
            Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", [fajl.as_uri()]),
        )
        varj(
            qt_app,
            lambda: not ablak.property("scanning")
            and int(ablak.property("previewCount")) == 1,
            "a fájl beolvasása nem fejeződött be",
        )

        _radiok_tiltottak_es_leave(ablak)

    def test_elozmeny_forrasnal_meg_dcim_mappas_gyokernel_is_tiltottak(
        self, app, tmp_path
    ):
        fo, vezerlo, qt_app = app
        ablak = _megnyit(fo, qt_app)
        kartya = _kartya(tmp_path, "elozmeny", dcim="DCIM")

        elozmeny_forras_kivalasztasa(ablak, vezerlo, qt_app, kartya, darab=1)

        _radiok_tiltottak_es_leave(ablak)

    def test_torolheto_forrasra_visszavaltva_a_tarolt_ertek_ter_vissza(
        self, app, tmp_path, monkeypatch
    ):
        fo, vezerlo, qt_app = app
        ablak = _megnyit(fo, qt_app)
        kartya = _kartya(tmp_path, "kartya", dcim="DCIM")
        mappa = _kartya(tmp_path, "mappa", dcim="DCIM")

        csatolt_kartya_kivalasztasa(ablak, vezerlo, qt_app, monkeypatch, kartya, darab=1)
        kattint(ablak, elem(ablak, "importSourceAfterDeleteCopiedRadio"), qt_app)
        assert elem(
            ablak, "importSourceAfterDeleteCopiedRadio"
        ).property("checked") is True

        _beallit_mappa_forrast(ablak, qt_app, mappa, 1)
        _radiok_tiltottak_es_leave(ablak)

        csatolt_kartya_kivalasztasa(ablak, vezerlo, qt_app, monkeypatch, kartya, darab=1)
        _radiok_aktivak(ablak)
        assert elem(
            ablak, "importSourceAfterDeleteCopiedRadio"
        ).property("checked") is True
        assert elem(ablak, "importSourceAfterLeaveRadio").property("checked") is False
        assert ablak.property("effectiveAfterCopying") == "delete_copied"


def _forras_es_cel(ablak, tmp_path, qt_app, monkeypatch, vezerlo, *, darab=1):
    """DCIM-es csatolt kártya beolvasva; visszaadja (kártya, cél)."""
    kartya = _kartya(tmp_path, "kartya", dcim="DCIM", darab=darab)
    cel = tmp_path / "cel"
    cel.mkdir()
    csatolt_kartya_kivalasztasa(
        ablak, vezerlo, qt_app, monkeypatch, kartya, darab=darab
    )
    ablak.setProperty("destFolder", str(cel))
    qt_app.processEvents()
    return kartya, cel


def _importal_megerositessel(ablak, vezerlo, qt_app, fo) -> None:
    """Import All kattintás, a törlés-megerősítés igenje, import vége."""
    vegek = []
    vezerlo.importFinished.connect(lambda ok, hiba: vegek.append((ok, hiba)))
    kattint(ablak, elem(ablak, "importSourceStartButton"), qt_app)
    kerdes = elem(fo, "importSourceConfirmRemoveDialog")
    varj(qt_app, lambda: kerdes.property("visible") is True, "nincs megerősítés")
    kattint(ablak, elem(fo, "importSourceConfirmRemoveYesButton"), qt_app)
    varj(qt_app, lambda: bool(vegek), "az import nem fejeződött be")
    assert vegek[-1][1] == 0, f"hibás import: {vegek[-1]}"


class TestUjranyitas:
    def test_az_import_inditasa_utan_ujranyitva_a_valasztott_modok_latszanak(
        self, app, tmp_path, monkeypatch
    ):
        fo, vezerlo, qt_app = app
        ablak = _megnyit(fo, qt_app)
        kartya, cel = _forras_es_cel(ablak, tmp_path, qt_app, monkeypatch, vezerlo)
        kattint(ablak, elem(ablak, "importSourceNamingTodayRadio"), qt_app)
        kattint(ablak, elem(ablak, "importSourceAfterDeleteCopiedRadio"), qt_app)

        _importal_megerositessel(ablak, vezerlo, qt_app, fo)

        # az import megtörtént és törölt a kártyáról
        assert list(cel.rglob("kep-0.jpg"))
        assert not (kartya / "DCIM" / "100CANON" / "kep-0.jpg").exists()

        # a tárolt értéktől eltérő állás az ablakban, hogy a visszatöltés látszódjon
        kattint(ablak, elem(ablak, "importSourceNamingManualRadio"), qt_app)
        kattint(ablak, elem(ablak, "importSourceAfterLeaveRadio"), qt_app)
        assert ablak.property("namingMode") == "manual"
        assert ablak.property("afterCopying") == "leave"

        _ujranyit(fo, ablak, qt_app)

        assert ablak.property("namingMode") == "today"
        assert elem(ablak, "importSourceNamingTodayRadio").property("checked") is True
        assert elem(ablak, "importSourceNamingManualRadio").property("checked") is False
        assert ablak.property("afterCopying") == "delete_copied"
        assert elem(
            ablak, "importSourceAfterDeleteCopiedRadio"
        ).property("checked") is True
        assert elem(ablak, "importSourceAfterLeaveRadio").property("checked") is False

    def test_a_mentett_delete_all_ujranyitaskor_delete_copied(
        self, app, tmp_path, monkeypatch
    ):
        fo, vezerlo, qt_app = app
        ablak = _megnyit(fo, qt_app)
        _kartya_, _cel = _forras_es_cel(ablak, tmp_path, qt_app, monkeypatch, vezerlo)
        kattint(ablak, elem(ablak, "importSourceNamingByDateRadio"), qt_app)
        kattint(ablak, elem(ablak, "importSourceAfterDeleteAllRadio"), qt_app)

        _importal_megerositessel(ablak, vezerlo, qt_app, fo)
        _ujranyit(fo, ablak, qt_app)

        assert ablak.property("afterCopying") == "delete_copied"
        assert elem(
            ablak, "importSourceAfterDeleteCopiedRadio"
        ).property("checked") is True
        assert elem(
            ablak, "importSourceAfterDeleteAllRadio"
        ).property("checked") is False

    def test_bezaras_import_nelkul_nem_ment(self, app, tmp_path, monkeypatch):
        """A mentés az import INDÍTÁSAKOR történik: a csak átállított, de el
        nem indított választás újranyitáskor a korábbi tárolt értékre áll."""
        fo, vezerlo, qt_app = app
        ablak = _megnyit(fo, qt_app)
        _forras_es_cel(ablak, tmp_path, qt_app, monkeypatch, vezerlo)
        kattint(ablak, elem(ablak, "importSourceNamingTodayRadio"), qt_app)
        kattint(ablak, elem(ablak, "importSourceAfterDeleteAllRadio"), qt_app)

        _ujranyit(fo, ablak, qt_app)

        assert ablak.property("namingMode") == "manual"
        assert ablak.property("afterCopying") == "leave"
        assert elem(ablak, "importSourceNamingManualRadio").property("checked") is True
        assert elem(ablak, "importSourceAfterLeaveRadio").property("checked") is True


class TestCelmappa:
    def test_a_cel_hibas_futasnal_is_bekerul_az_elozmenybe(
        self, app, tmp_path, monkeypatch
    ):
        import picasapy.app.import_source_controller as modul

        fo, vezerlo, qt_app = app
        ablak = _megnyit(fo, qt_app)
        _kartya_, cel = _forras_es_cel(ablak, tmp_path, qt_app, monkeypatch, vezerlo)
        kattint(ablak, elem(ablak, "importSourceNamingByDateRadio"), qt_app)

        def hibas_masolas(*_args, **_kwargs):
            raise OSError("a cél írásvédett")

        monkeypatch.setattr(modul, "copy_photo", hibas_masolas)
        vegek = []
        vezerlo.importFinished.connect(lambda ok, hiba: vegek.append((ok, hiba)))
        kattint(ablak, elem(ablak, "importSourceStartButton"), qt_app)
        varj(qt_app, lambda: bool(vegek), "az import nem fejeződött be")

        assert vegek[-1] == (0, 1)
        assert _utvonalak(vezerlo.recentDestinations) == [cel]

    def test_az_elozmenylista_legfeljebb_ot_elemu(
        self, app, tmp_path, monkeypatch
    ):
        fo, vezerlo, qt_app = app
        ablak = _megnyit(fo, qt_app)
        kartya = _kartya(tmp_path, "kartya", dcim="DCIM")
        csatolt_kartya_kivalasztasa(
            ablak, vezerlo, qt_app, monkeypatch, kartya, darab=1
        )
        kattint(ablak, elem(ablak, "importSourceNamingByDateRadio"), qt_app)
        vegek = []
        vezerlo.importFinished.connect(lambda ok, hiba: vegek.append((ok, hiba)))
        celok = []
        for index in range(6):
            cel = tmp_path / f"cel-{index}"
            cel.mkdir()
            celok.append(cel)
            ablak.setProperty("destFolder", str(cel))
            qt_app.processEvents()
            kattint(ablak, elem(ablak, "importSourceStartButton"), qt_app)
            varj(
                qt_app,
                lambda szam=index + 1: len(vegek) >= szam,
                "az import nem fejeződött be",
            )

        assert _utvonalak(vezerlo.recentDestinations) == list(reversed(celok[1:]))
        legordulo = elem(ablak, "importSourceRecentDestBox")
        # az alapértelmezett hely a lista végén külön tétel, ezért legfeljebb 6
        assert int(legordulo.property("count")) <= 6
