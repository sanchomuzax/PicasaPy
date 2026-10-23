"""#4856: a diavetítés átmenet-választója az eredeti hét átmenetét kínálja.

A `docs/specs/picasa-create-features.md` 4.3 szerint a diavetítés
átmenet-listája hét tétel, ebben a sorrendben: Cut, Pan and Zoom, Dissolve,
Wipe, Circle, Push, Rectangle. A 22 tételes készlet a filmkészítőé
(`CreateDialogs.qml`, `transitionKeys`); az változatlan marad.

A legördülőt valódi egérkattintással nyitjuk meg, és a látható sorokból
olvassuk ki a listát.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QPoint, QPointF, QSettings, Qt
from PySide6.QtTest import QTest
import pytest

from support.qt_wait import varj_feltetelre

# A 4.3 szerinti sorrend: (kulcs, felirat). A feliratok a meglévő
# `SlideshowView.qml`-beli `qsTr` szövegek, új felirat nincs.
_DIAVETITES_ATMENETEK = (
    ("cut", "Cut"),
    ("kenburns", "Pan and Zoom"),
    ("dissolve", "Dissolve"),
    ("wiperight", "Wipe"),
    ("circleout", "Circle"),
    ("pushright", "Push"),
    ("rect", "Rectangle"),
)
_FILMKESZITO_KENBURNSAOI_SORSZAM = 19


def _gyerek(gyoker, nev):
    obj = gyoker.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def _atmenetvalasztot_engedelyez(controller):
    """Az átmenet-listát tesztelő próbáknál kapcsoljuk ki a BigSlideshow2-t."""
    controller._get_settings().setValue("Preferences/BigSlideshow2", False)
    controller.statusChanged.emit()


def _kozep(item):
    return item.mapToScene(QPointF(item.width() / 2, item.height() / 2))


def _egerrel_kattint(window, item):
    pont = _kozep(item)
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )


def _valaszto_megnyitasa(window, qt_app, show, combo, controls, popup):
    show.setProperty("currentIndex", 0)
    show.setProperty("visible", True)
    assert varj_feltetelre(
        qt_app, lambda: show.property("visible"), masodperc=10.0
    ), "a diavetítés nem vált láthatóvá"
    show.setProperty("playing", False)
    QTest.mouseMove(window, QPoint(1, 1))
    qt_app.processEvents()
    pont = _kozep(combo)
    QTest.mouseMove(window, QPoint(round(pont.x()), round(pont.y())))
    assert varj_feltetelre(
        qt_app, lambda: controls.property("opacity") > 0, masodperc=10.0
    ), "az egérmozgatás nem jelenítette meg a vezérlősávot"
    _egerrel_kattint(window, combo)
    assert varj_feltetelre(
        qt_app, lambda: popup.property("visible"), masodperc=10.0
    ), "az átmenetválasztó nem nyílt ki"


def _lathato_sorok(lista):
    """A legördülő látható sorainak feliratai, a sorindex szerint."""
    sorok = {}
    for item in lista.property("contentItem").childItems():
        index = item.property("index")
        szoveg = item.property("modelData")
        if index is not None and szoveg is not None and item.isVisible():
            sorok[int(index)] = str(szoveg)
    return [sorok[index] for index in sorted(sorok)]


@pytest.fixture
def mentett_kenburnsaoi(tmp_path):
    """A mentett beállítás a `qml_app` felállása ELŐTT kerül a tárolóba.

    A fixture-sorrend a szignatúrán múlik: ez a fixture előbb szerepel,
    mint a `qml_app`, így a vetítő már a mentett értékkel indul.
    """
    beallitasok = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    beallitasok.setValue("view/slideshowTransition", "kenburnsaoi")
    beallitasok.sync()


def test_a_valaszto_pontosan_a_het_eredeti_atmenetet_mutatja(qml_app, qt_app):
    window, controller, _engine = qml_app
    _atmenetvalasztot_engedelyez(controller)
    show = _gyerek(window, "slideshowView")
    combo = _gyerek(window, "slideshowTransitionBox")
    popup = _gyerek(window, "picasaComboPopup")
    lista = _gyerek(window, "picasaComboList")
    controls = _gyerek(window, "slideshowControls")
    _valaszto_megnyitasa(window, qt_app, show, combo, controls, popup)

    assert combo.property("count") == len(_DIAVETITES_ATMENETEK), (
        "a diavetítés átmenet-választója nem hét tételt tartalmaz"
    )
    assert _lathato_sorok(lista) == [
        nev for _kulcs, nev in _DIAVETITES_ATMENETEK
    ], "a legördülő látható sorai nem a 4.3 szerinti hét elem"


def test_az_alapertek_dissolve(qml_app, qt_app):
    window, controller, _engine = qml_app
    _atmenetvalasztot_engedelyez(controller)
    show = _gyerek(window, "slideshowView")
    combo = _gyerek(window, "slideshowTransitionBox")

    assert show.property("transitionKind") == "dissolve"
    assert combo.property("currentText") == "Dissolve"


def test_mentett_kenburnsaoi_betoltesekor_dissolve_lesz(
    mentett_kenburnsaoi, qml_app, qt_app
):
    window, controller, _engine = qml_app
    _atmenetvalasztot_engedelyez(controller)
    show = _gyerek(window, "slideshowView")
    combo = _gyerek(window, "slideshowTransitionBox")

    assert controller.property("slideshowTransition") == "dissolve"
    assert show.property("transitionKind") == "dissolve"
    assert combo.property("currentText") == "Dissolve"


def test_a_filmkeszito_listaja_megtartja_a_kenburnsaoi_t(qml_app, qt_app):
    window, _controller, _engine = qml_app
    # a filmpanel csak a megnyitáskor jön létre: két kijelölt képpel,
    # a főablak film gombjára kattintva (mint a `test_film_panel_4125.py`)
    window.setProperty("selectedIndexes", [0, 1])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    _egerrel_kattint(window, _gyerek(window, "trayMovieButton"))
    film = _gyerek(window, "movieDialog")
    assert varj_feltetelre(
        qt_app, lambda: film.property("visible"), masodperc=10.0
    ), "a főablak film gombja nem nyitotta meg a filmpanelt"
    kulcsok = film.property("transitionKeys").toVariant()
    atmenet_valaszto = _gyerek(window, "movieTransitionBox")
    feliratok = list(atmenet_valaszto.property("model") or [])

    assert kulcsok[_FILMKESZITO_KENBURNSAOI_SORSZAM] == "kenburnsaoi"
    assert len(kulcsok) == 22
    assert feliratok[_FILMKESZITO_KENBURNSAOI_SORSZAM] == "Pan and Zoom - face"
