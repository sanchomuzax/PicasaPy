"""Az Opciók ablak a legutóbb használt fülre nyílik (#7328), valódi kattintással.

Az eredeti `COptionsDialog` destruktora MINDEN lezáráskor kiírja a fül
indexét a `Preferences\\LastUsedOptionsPage` kulcsba (`0x006e373d`-
`0x006e3767`), az OK-n és a Mégse-n kívül az ablakbezárásnál is; a menü
`-1`-gyel hívja, ami a kulcs értékére (alapérték 0) nyit.

Az „újraindított alkalmazás" a mentett `settings.ini`-vel épített ÚJ app:
a második próba előre beírt beállításfájllal indul, mint egy valódi
újraindítás után.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, QSettings, Qt
from PySide6.QtTest import QTest

from conftest import _build_qml_app
from picasapy.app.option_settings import LAST_OPTIONS_TAB_KEY
from support.varakozas import var_feltetelre
from tests.app.qml_functional.test_menu_talca_egyeb_valodi_5135_b import (
    _elokeszit,
)
from tests.app.qml_functional.test_menu_talca_egyeb_valodi_5135_d import (
    _beallitasok_megnyit,
    _vizualis_keres,
)

#: a fülsor 0 alapú sorrendje (OptionsDialog.qml)
FUL_ALTALANOS = 0
FUL_NEVCIMKEK = 7
FUL_GOOGLE_FOTOK = 8


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, feltetel, masodperc)


def _gyerek(szulo, nev: str):
    gyerek = szulo.findChild(QObject, nev)
    assert gyerek is not None, f"{nev} nem található"
    return gyerek


def _kattints(qt_app, ablak, elem) -> None:
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        pos=QPoint(round(pont.x()), round(pont.y())),
    )
    qt_app.processEvents()


def _aktualis_ful(dialog) -> int:
    return _gyerek(dialog, "optionsTabBar").property("currentIndex")


def _ful_gombja(dialog, nev: str):
    return _vizualis_keres(dialog, nev)


def _mentett_ful(controller):
    controller._get_settings().sync()
    return controller._get_settings().value(LAST_OPTIONS_TAB_KEY)


def _bezar(qt_app, dialog) -> None:
    assert _varj(qt_app, lambda: dialog.property("visible") is False), (
        "az Opciók ablaka nem záródott be"
    )


@pytest.fixture
def opciok_app(qt_app, tmp_path):
    yield from _build_qml_app(qt_app, tmp_path)


@pytest.fixture
def ujraindult_app(qt_app, tmp_path, request):
    """Az alkalmazás egy korábbi futás által mentett fül-indexszel indul."""
    mentett = request.param
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    settings.setValue(LAST_OPTIONS_TAB_KEY, mentett)
    settings.sync()
    del settings
    yield from _build_qml_app(qt_app, tmp_path)


def test_uj_profilon_az_elso_megnyitas_az_altalanos_fulre_nyit(
    opciok_app, qt_app
):
    window, controller, _engine = opciok_app
    _elokeszit(window, qt_app, controller)
    assert controller._get_settings().value(LAST_OPTIONS_TAB_KEY) is None

    dialog = _beallitasok_megnyit(window, qt_app, window.property("menuBar"))

    assert _aktualis_ful(dialog) == FUL_ALTALANOS


@pytest.mark.parametrize(
    "lezaras", ["optionsOkButton", "optionsCancelButton", "ablakbezaras"]
)
def test_lezaras_utan_a_kovetkezo_megnyitas_ugyanarra_a_fulre_nyit(
    opciok_app, qt_app, lezaras
):
    window, controller, _engine = opciok_app
    _elokeszit(window, qt_app, controller)
    dialog = _beallitasok_megnyit(window, qt_app, window.property("menuBar"))

    _kattints(qt_app, dialog, _ful_gombja(dialog, "optionsTabNameTags"))
    assert _aktualis_ful(dialog) == FUL_NEVCIMKEK
    if lezaras == "ablakbezaras":
        assert dialog.close()
    else:
        _kattints(qt_app, dialog, _gyerek(dialog, "optionsOkButton" if lezaras == "optionsOkButton" else "optionsCancelButton"))
    _bezar(qt_app, dialog)

    assert int(_mentett_ful(controller)) == FUL_NEVCIMKEK, (
        f"a(z) {lezaras} lezárás nem mentette a fül indexét"
    )
    dialog = _beallitasok_megnyit(window, qt_app, window.property("menuBar"))
    assert _aktualis_ful(dialog) == FUL_NEVCIMKEK


def test_a_megnyitas_nem_ir_amig_az_ablak_nyitva_van(opciok_app, qt_app):
    window, controller, _engine = opciok_app
    _elokeszit(window, qt_app, controller)

    _beallitasok_megnyit(window, qt_app, window.property("menuBar"))

    assert controller._get_settings().value(LAST_OPTIONS_TAB_KEY) is None


def test_a_google_fotok_belepes_a_sajat_fulere_nyit_es_a_fulet_menti(
    opciok_app, qt_app
):
    window, controller, _engine = opciok_app
    _elokeszit(window, qt_app, controller)
    dialog = _beallitasok_megnyit(window, qt_app, window.property("menuBar"))
    _kattints(qt_app, dialog, _ful_gombja(dialog, "optionsTabSlideshow"))
    _kattints(qt_app, dialog, _gyerek(dialog, "optionsCancelButton"))
    _bezar(qt_app, dialog)

    assert QMetaObject.invokeMethod(dialog, "openGooglePhotos")
    assert _varj(qt_app, lambda: dialog.property("visible") is True)
    assert _aktualis_ful(dialog) == FUL_GOOGLE_FOTOK, (
        "a Google Photos belépés nem a saját fülére nyitott"
    )
    _kattints(qt_app, dialog, _gyerek(dialog, "optionsCancelButton"))
    _bezar(qt_app, dialog)

    assert int(_mentett_ful(controller)) == FUL_GOOGLE_FOTOK
    dialog = _beallitasok_megnyit(window, qt_app, window.property("menuBar"))
    assert _aktualis_ful(dialog) == FUL_GOOGLE_FOTOK


@pytest.mark.parametrize("ujraindult_app", [FUL_NEVCIMKEK], indirect=True)
def test_ujraindult_alkalmazas_a_mentett_fulre_nyit(ujraindult_app, qt_app):
    window, controller, _engine = ujraindult_app
    _elokeszit(window, qt_app, controller)

    dialog = _beallitasok_megnyit(window, qt_app, window.property("menuBar"))

    assert _aktualis_ful(dialog) == FUL_NEVCIMKEK


@pytest.mark.parametrize("ujraindult_app", [FUL_GOOGLE_FOTOK], indirect=True)
def test_ujraindult_alkalmazas_a_google_fotok_fulre_is_nyithat(
    ujraindult_app, qt_app
):
    window, controller, _engine = ujraindult_app
    _elokeszit(window, qt_app, controller)

    dialog = _beallitasok_megnyit(window, qt_app, window.property("menuBar"))

    assert _aktualis_ful(dialog) == FUL_GOOGLE_FOTOK


@pytest.mark.parametrize("ujraindult_app", [42, -3, "hibas"], indirect=True)
def test_tartomanyon_kivuli_mentett_ertek_az_elso_fulre_nyit(
    ujraindult_app, qt_app
):
    window, controller, _engine = ujraindult_app
    _elokeszit(window, qt_app, controller)

    dialog = _beallitasok_megnyit(window, qt_app, window.property("menuBar"))

    assert _aktualis_ful(dialog) == FUL_ALTALANOS
