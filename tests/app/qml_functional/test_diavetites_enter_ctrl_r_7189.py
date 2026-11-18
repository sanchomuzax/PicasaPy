"""#7189: a normál diavetítésben az Enter, a Ctrl+R és a Ctrl+Shift+R nem
végez műveletet, mint az eredetiben.

Az eredeti normál vetítésének billentyűútja (`0x00760970`, `0x005e6710`,
`0x005e60d0`) az `Enter`-re és a `Ctrl+R`-re nem hajt végre semmit: a vetítés
nem lép tovább, és a kép nem fordul el. A `Fel`/`Le`, a számjegy, a `Pause`
és a `Play` a #7065 óta az eredeti műveletét végzi (lásd
`test_diavetites_billentyuk_7065.py`), az maradt.

Minden próba valódi billentyűleütéssel (`QTest.keyClick`) fut a teljes
főablakon, tehát a Shortcut- és fókuszútvonalat is méri, nem a metódust hívja.
A forgatás hatását a képen mérjük (`photos.rotateAt`), a háttérmunka
bevárása után, mert a forgatás aszinkron: egy korai olvasás hamis zöldet adna.

A képernyőkímélő (`screensaverMode`) viselkedése nem változik: ott bármely
billentyű kilép, és a próbák ezt is rögzítik.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt
from PySide6.QtGui import QWindow
from PySide6.QtTest import QTest

from support.qt_wait import varj_feltetelre, wait_for_photo_op

CTRL = Qt.KeyboardModifier.ControlModifier
SHIFT = Qt.KeyboardModifier.ShiftModifier


def _child(parent, name):
    obj = parent.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _indit(window, qt_app, index: int, paused: bool):
    window.show()
    window.requestActivate()
    window.setVisibility(QWindow.Visibility.Windowed)
    window.startSlideshow(index, paused)
    show = _child(window, "slideshowView")
    assert varj_feltetelre(
        qt_app, lambda: show.property("visible"), 3.0
    ), "a vetítés nem indult el"
    assert show.property("playing") is (not paused)
    return show


def _kulcs(window, qt_app, kulcs, modosito=Qt.KeyboardModifier.NoModifier):
    QTest.keyClick(window, kulcs, modosito)
    qt_app.processEvents()


def _bevar_hatermunkat(controller, qt_app) -> None:
    """Megvárja az esetleg elindult forgatás háttérmunkáját."""
    wait_for_photo_op(controller, lambda: None, qt_app=qt_app)


def _forgatasok(controller) -> list[int]:
    """Minden sor forgatási állapota: a vetítés bármely sorral indulhat."""
    modell = controller.photos
    return [modell.rotateAt(sor) for sor in range(modell.rowCount())]


def _forgatas_jelzesek(show):
    """A vetítés `rotateRequested` jelzéseit gyűjti: (index, irány) párok."""
    kapott: list[tuple[int, int]] = []
    show.rotateRequested.connect(lambda i, d: kapott.append((i, d)))
    return kapott


class TestEnterNemCsinalSemmit:
    @pytest.mark.parametrize(
        "kulcs", [Qt.Key.Key_Return, Qt.Key.Key_Enter],
        ids=["Return", "Enter_numerikus"],
    )
    def test_enter_szunetelo_vetitesben_nem_lep(
        self, qml_app, qt_app, kulcs
    ):
        window, controller, _engine = qml_app
        controller.setSlideshowLoop(False)
        show = _indit(window, qt_app, 0, paused=True)
        assert show.property("currentIndex") == 0

        _kulcs(window, qt_app, kulcs)

        assert show.property("currentIndex") == 0, "az Enter léptetett"
        assert show.property("playing") is False, "az Enter indított"
        assert show.property("visible") is True, "az Enter bezárta a vetítést"

    @pytest.mark.parametrize(
        "kulcs", [Qt.Key.Key_Return, Qt.Key.Key_Enter],
        ids=["Return", "Enter_numerikus"],
    )
    def test_enter_lejatszas_kozben_nem_lep_es_nem_szuneteltet(
        self, qml_app, qt_app, kulcs
    ):
        window, controller, _engine = qml_app
        controller.setSlideshowLoop(False)
        # Hosszú diaidő, hogy az időzítő ne léptessen a próba alatt.
        controller.setSlideshowSeconds(9)
        show = _indit(window, qt_app, 0, paused=False)
        assert show.property("currentIndex") == 0

        _kulcs(window, qt_app, kulcs)

        assert show.property("currentIndex") == 0, "az Enter léptetett"
        assert show.property("playing") is True, "az Enter szüneteltetett"

    def test_enter_nem_nyitja_meg_a_nezot(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        controller.setSlideshowLoop(False)
        _indit(window, qt_app, 0, paused=True)
        assert window.property("viewerOpen") is False

        _kulcs(window, qt_app, Qt.Key.Key_Return)

        assert window.property("viewerOpen") is False


class TestCtrlRNemForgat:
    @pytest.mark.parametrize(
        "modosito", [CTRL, CTRL | SHIFT], ids=["Ctrl+R", "Ctrl+Shift+R"]
    )
    def test_szunetelo_vetitesben_nem_forgat(
        self, qml_app, qt_app, modosito
    ):
        window, controller, _engine = qml_app
        show = _indit(window, qt_app, 0, paused=True)
        kert = _forgatas_jelzesek(show)
        assert controller.photos.rotateAt(0) == 0

        _kulcs(window, qt_app, Qt.Key.Key_R, modosito)
        _bevar_hatermunkat(controller, qt_app)

        assert kert == [], f"a vetítés forgatást kért: {kert}"
        assert controller.photos.rotateAt(0) == 0, "a kép elfordult"
        assert show.property("playing") is False

    @pytest.mark.parametrize(
        "modosito", [CTRL, CTRL | SHIFT], ids=["Ctrl+R", "Ctrl+Shift+R"]
    )
    def test_lejatszas_kozben_nem_forgat_es_nem_allitja_meg(
        self, qml_app, qt_app, modosito
    ):
        window, controller, _engine = qml_app
        controller.setSlideshowSeconds(9)
        show = _indit(window, qt_app, 0, paused=False)
        kert = _forgatas_jelzesek(show)

        _kulcs(window, qt_app, Qt.Key.Key_R, modosito)
        _bevar_hatermunkat(controller, qt_app)

        assert kert == [], f"a vetítés forgatást kért: {kert}"
        assert controller.photos.rotateAt(0) == 0, "a kép elfordult"
        assert show.property("playing") is True
        assert show.property("currentIndex") == 0

    def test_mero_kontroll_a_forgatas_a_vezerlosavbol_meg_mukodik(
        self, qml_app, qt_app
    ):
        """A mérő kontrollja: ha a vetítés forgatást kér, a próba látja.

        A vezérlősáv ↺/↻ gombja ugyanazt a `rotateCurrent`-et hívja, mint
        amit a billentyű hívott; az eredeti vetítősávjában a gombok
        megvannak, ezért ez az út marad. Enélkül a fenti negatív próbák
        akkor is zöldek volnának, ha a `rotateAt` olvasása vagy a bevárás
        hibás.
        """
        window, controller, _engine = qml_app
        show = _indit(window, qt_app, 0, paused=True)
        kert = _forgatas_jelzesek(show)

        wait_for_photo_op(
            controller,
            lambda: QMetaObject.invokeMethod(
                show, "rotateCurrent", Qt.ConnectionType.DirectConnection,
                Q_ARG("QVariant", 1),
            ),
            qt_app=qt_app,
        )

        assert kert == [(0, 1)]
        assert controller.photos.rotateAt(0) == 1


class TestSzomszedBillentyukMegmaradnak:
    """A Fel/Le, a számjegy, a Pause és a Play a javítás után is működik."""

    def test_le_fel_lep(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        controller.setSlideshowLoop(False)
        show = _indit(window, qt_app, 0, paused=True)

        _kulcs(window, qt_app, Qt.Key.Key_Down)
        assert show.property("currentIndex") == 1
        _kulcs(window, qt_app, Qt.Key.Key_Up)
        assert show.property("currentIndex") == 0

    def test_szamjegy_a_diaidot_allitja(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        controller.setSlideshowSeconds(10)
        _indit(window, qt_app, 0, paused=True)

        _kulcs(window, qt_app, Qt.Key.Key_4)

        assert controller.slideshowSeconds == 4

    def test_pause_szuneteltet_es_media_play_folytat(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        controller.setSlideshowSeconds(9)
        show = _indit(window, qt_app, 0, paused=False)

        _kulcs(window, qt_app, Qt.Key.Key_Pause)
        assert show.property("playing") is False
        _kulcs(window, qt_app, Qt.Key.Key_MediaPlay)
        assert show.property("playing") is True

    def test_r_modosito_nelkul_nem_forgat_es_nem_lep(self, qml_app, qt_app):
        """A sima `R` sosem volt vetítésbillentyű: a próba a Ctrl-os
        kombináció és a sima betű közti különbséget is rögzíti."""
        window, controller, _engine = qml_app
        controller.setSlideshowLoop(False)
        show = _indit(window, qt_app, 0, paused=True)
        kert = _forgatas_jelzesek(show)

        _kulcs(window, qt_app, Qt.Key.Key_R)
        _bevar_hatermunkat(controller, qt_app)

        assert kert == []
        assert controller.photos.rotateAt(0) == 0
        assert show.property("currentIndex") == 0


class TestKepernyovedoNemValtozik:
    """A képernyőkímélőben bármely billentyű kilép, a kép nem fordul."""

    @pytest.mark.parametrize(
        ("kulcs", "modosito"),
        [
            (Qt.Key.Key_Return, Qt.KeyboardModifier.NoModifier),
            (Qt.Key.Key_Enter, Qt.KeyboardModifier.NoModifier),
            (Qt.Key.Key_R, CTRL),
            (Qt.Key.Key_R, CTRL | SHIFT),
        ],
        ids=["Return", "Enter_numerikus", "Ctrl+R", "Ctrl+Shift+R"],
    )
    def test_billentyu_kilep_es_nem_forgat(
        self, qml_app, qt_app, kulcs, modosito
    ):
        window, controller, _engine = qml_app
        controller.setScreensaverSources(
            [f"folder:{Path(controller._roots[0])}"]
        )
        window.show()
        window.requestActivate()
        window.startScreensaverPreview()
        show = _child(window, "slideshowView")
        assert show.property("screensaverMode") is True
        assert varj_feltetelre(
            qt_app, lambda: show.property("screensaverInputArmed"), 3.0
        ), "a képernyővédő nem fogadja a billentyűt"
        kert = _forgatas_jelzesek(show)
        elotte = _forgatasok(controller)
        assert len(elotte) >= 2

        _kulcs(window, qt_app, kulcs, modosito)
        _bevar_hatermunkat(controller, qt_app)

        assert show.property("visible") is False, "a billentyű nem lépett ki"
        assert kert == []
        assert _forgatasok(controller) == elotte, "egy kép elfordult"
