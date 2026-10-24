"""A Film készítése diaidejének natív alapértéke, határai és mentése (#5675)."""

from PySide6.QtCore import QMetaObject, QObject, QSettings
import pytest
from support.qt_wait import varj_feltetelre


def _obj(window, name: str):
    result = window.findChild(QObject, name)
    assert result is not None, f"hiányzik a QML-objektum: {name}"
    return result


@pytest.mark.parametrize("magassag_eltolas", (-5, 0, 5))
def test_diaidő_alapérték_határok_és_beállításmentés(
    qml_app, qt_app, tmp_path, magassag_eltolas
):
    window, controller, _engine = qml_app
    window.resize(window.width(), window.height() + magassag_eltolas)
    window.show()
    window.openMovieFromRows([0])
    assert varj_feltetelre(
        qt_app,
        lambda: window.findChild(QObject, "movieDialog") is not None
        and window.findChild(QObject, "movieDialog").property("visible"),
        3.0,
    ), "a Film készítése panel nem nyílt meg"

    diaido = _obj(window, "movieSeconds")
    assert diaido.property("value") == 40, "az új diaidő nem 4,0 másodperc"
    assert diaido.property("from") == 10, "a diaidő alsó határa nem 1,0 s"
    assert diaido.property("to") == 3000, "a diaidő felső határa nem 300,0 s"
    diaido.setProperty("value", 0)
    assert diaido.property("value") == 10, "a diaidő 1,0 másodperc alá állítható"
    diaido.setProperty("value", 3000)
    assert diaido.property("value") == 3000, "a 300,0 másodperc nem érhető el"

    diaido.setProperty("value", 3010)
    assert diaido.property("value") == 3000, "a diaidő 301 másodpercig állítható"
    diaido.setProperty("value", 55)
    assert QMetaObject.invokeMethod(diaido, "moved")

    atmenet = _obj(window, "movieTransitionBox")
    assert controller.movieTransition == "dissolve"
    assert atmenet.property("currentIndex") == 1
    atmenet.setProperty("currentIndex", 3)

    controller._get_settings().sync()
    fajl = tmp_path / "settings.ini"
    mentett = QSettings(str(fajl), QSettings.Format.IniFormat)
    mentett.sync()
    friss_beallitas = QSettings(str(fajl), QSettings.Format.IniFormat)
    assert float(friss_beallitas.value("slideduration")) == 5.5
    assert friss_beallitas.value("makemovietransition") == "dissolvewhite"
    from picasapy.app.controller import AppController

    ujrainditott = AppController(
        controller._db_path,
        tuple(controller._roots),
        controller._provider,
        parent=controller,
        settings=friss_beallitas,
    )
    assert ujrainditott.movieSlideDuration == 5.5
    assert ujrainditott.movieTransition == "dissolvewhite"
