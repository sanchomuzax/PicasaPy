"""#7065: a normál diavetítés Fel/Le, számjegy és Pause/Play billentyűi.

Az eredeti `editoneup` billentyűkezelő (`0x00760970`) a `Fel` (`0x26`)
billentyűre hátra, a `Le` (`0x28`) billentyűre előre lép; a számjegy a
`SlideshowEffectTime` értéke (nulla helyett 1); a `Pause` (`0x13`) lejátszás
közben, a `Play` (`0xfa`) szünetben kapcsolja az `auto`-t.

Minden próba valódi billentyűleütéssel (`QTest.keyClick`) fut a teljes
főablakon, tehát a kattintás-/fókuszútvonalat is méri, nem a metódust hívja.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QGuiApplication, QKeyEvent, QWindow
from PySide6.QtTest import QTest

from support.qt_wait import varj_feltetelre


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


def _kulcs_esemennyel(window, qt_app, kulcs):
    """Billentyűleütés közvetlen `QKeyEvent`-tel az ablaknak.

    A `QTest.keyClick` a `Key_Play`-nél a QtTest saját ASCII-táblája miatt
    elszáll (`qasciikey.cpp`, ASSERT), ezért ennél a billentyűnél a lenyomást
    és az elengedést mi küldjük: ugyanaz az esemény, ugyanazon az úton
    (ablak, aktív fókuszelem), csak a QtTest leképezése nélkül."""
    for tipus in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
        esemeny = QKeyEvent(tipus, kulcs, Qt.KeyboardModifier.NoModifier)
        QGuiApplication.sendEvent(window, esemeny)
    qt_app.processEvents()


def _cimke(window) -> str:
    return str(_child(window, "slideshowTimeValue").property("text"))


class TestFelLe:
    def test_le_elore_lep_mint_a_jobb_nyil(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        controller.setSlideshowLoop(False)
        show = _indit(window, qt_app, 0, paused=True)
        assert show.property("currentIndex") == 0

        _kulcs(window, qt_app, Qt.Key.Key_Down)

        assert show.property("currentIndex") == 1, "a Le nem lépett előre"

    def test_fel_hatra_lep_mint_a_bal_nyil(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        controller.setSlideshowLoop(False)
        show = _indit(window, qt_app, 1, paused=True)
        assert show.property("currentIndex") == 1

        _kulcs(window, qt_app, Qt.Key.Key_Up)

        assert show.property("currentIndex") == 0, "a Fel nem lépett hátra"

    def test_fel_es_le_iranya_megegyezik_a_bal_jobb_nyilakkal(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        controller.setSlideshowLoop(False)
        show = _indit(window, qt_app, 0, paused=True)

        _kulcs(window, qt_app, Qt.Key.Key_Right)
        jobb = show.property("currentIndex")
        _kulcs(window, qt_app, Qt.Key.Key_Left)
        bal = show.property("currentIndex")
        assert (jobb, bal) == (1, 0)

        _kulcs(window, qt_app, Qt.Key.Key_Down)
        assert show.property("currentIndex") == jobb
        _kulcs(window, qt_app, Qt.Key.Key_Up)
        assert show.property("currentIndex") == bal

    def test_fel_az_elso_kepen_nem_lep_ki_a_listabol(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        controller.setSlideshowLoop(False)
        show = _indit(window, qt_app, 0, paused=True)

        _kulcs(window, qt_app, Qt.Key.Key_Up)

        assert show.property("currentIndex") == 0
        assert show.property("visible") is True


class TestSzamjegy:
    @pytest.mark.parametrize("szamjegy", range(1, 10))
    def test_szamjegy_a_diaidot_allitja(self, qml_app, qt_app, szamjegy):
        window, controller, _engine = qml_app
        # A kiinduló érték (10) a számjegyektől különbözik, különben a próba
        # nem tudná megkülönböztetni a hatást a változatlanságtól.
        controller.setSlideshowSeconds(10)
        show = _indit(window, qt_app, 0, paused=False)
        assert controller.slideshowSeconds == 10

        kulcs = getattr(Qt.Key, f"Key_{szamjegy}")
        _kulcs(window, qt_app, kulcs)

        assert controller.slideshowSeconds == szamjegy
        assert show.property("seconds") == szamjegy

    def test_nulla_nem_ir_nullat_hanem_egyet(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        controller.setSlideshowSeconds(7)
        show = _indit(window, qt_app, 0, paused=False)
        assert controller.slideshowSeconds == 7

        _kulcs(window, qt_app, Qt.Key.Key_0)

        assert controller.slideshowSeconds == 1, (
            "a 0 nem 1-et írt, hanem "
            f"{controller.slideshowSeconds}-t"
        )
        assert show.property("seconds") == 1

    def test_szamjegy_szunetben_a_cimke_is_frissul(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        controller.setSlideshowSeconds(3)
        show = _indit(window, qt_app, 0, paused=True)
        assert _cimke(window) == "3 seconds"

        _kulcs(window, qt_app, Qt.Key.Key_5)

        assert show.property("playing") is False, "a számjegy nem indíthat"
        assert controller.slideshowSeconds == 5
        assert _cimke(window) == "5 seconds"

        _kulcs(window, qt_app, Qt.Key.Key_1)
        assert _cimke(window) == "1 second"

    def test_numerikus_billentyuzet_szamjegye_is_ker(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        controller.setSlideshowSeconds(3)
        _indit(window, qt_app, 0, paused=True)

        _kulcs(window, qt_app, Qt.Key.Key_8, Qt.KeyboardModifier.KeypadModifier)

        assert controller.slideshowSeconds == 8

    def test_ctrl_szamjegy_nem_allitja_a_diaidot(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        controller.setSlideshowSeconds(3)
        _indit(window, qt_app, 0, paused=True)

        _kulcs(
            window, qt_app, Qt.Key.Key_6, Qt.KeyboardModifier.ControlModifier
        )

        assert controller.slideshowSeconds == 3


class TestPauseEsPlay:
    def test_pause_lejatszas_kozben_szuneteltet(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        show = _indit(window, qt_app, 0, paused=False)

        _kulcs(window, qt_app, Qt.Key.Key_Pause)

        assert show.property("playing") is False

    def test_pause_szunetben_nem_folytatja(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        show = _indit(window, qt_app, 0, paused=True)

        _kulcs(window, qt_app, Qt.Key.Key_Pause)

        assert show.property("playing") is False

    def test_play_szunetben_folytatja(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        show = _indit(window, qt_app, 0, paused=False)
        _kulcs(window, qt_app, Qt.Key.Key_Pause)
        assert show.property("playing") is False

        _kulcs_esemennyel(window, qt_app, Qt.Key.Key_Play)

        assert show.property("playing") is True

    def test_play_lejatszas_kozben_nem_szuneteltet(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        show = _indit(window, qt_app, 0, paused=False)

        _kulcs_esemennyel(window, qt_app, Qt.Key.Key_Play)

        assert show.property("playing") is True

    def test_linuxos_media_play_billentyu_is_folytat(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        show = _indit(window, qt_app, 0, paused=True)

        _kulcs(window, qt_app, Qt.Key.Key_MediaPlay)

        assert show.property("playing") is True


class TestMeglevoBillentyukValtozatlanok:
    def test_space_valt_szunet_es_folytatas_kozott(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        show = _indit(window, qt_app, 0, paused=False)

        _kulcs(window, qt_app, Qt.Key.Key_Space)
        assert show.property("playing") is False
        _kulcs(window, qt_app, Qt.Key.Key_Space)
        assert show.property("playing") is True

    def test_bal_jobb_nyil_lep(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        controller.setSlideshowLoop(False)
        show = _indit(window, qt_app, 0, paused=True)

        _kulcs(window, qt_app, Qt.Key.Key_Right)
        assert show.property("currentIndex") == 1
        _kulcs(window, qt_app, Qt.Key.Key_Left)
        assert show.property("currentIndex") == 0

    def test_enter_tovabbra_elore_lep(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        controller.setSlideshowLoop(False)
        show = _indit(window, qt_app, 0, paused=True)

        _kulcs(window, qt_app, Qt.Key.Key_Return)

        assert show.property("currentIndex") == 1

    def test_escape_bezarja_a_vetitest(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        show = _indit(window, qt_app, 0, paused=False)

        _kulcs(window, qt_app, Qt.Key.Key_Escape)

        assert show.property("visible") is False

    def test_billentyuk_nem_valtoztatjak_a_diaidot_tevesen(
        self, qml_app, qt_app
    ):
        """A nyilak és a Space nem érintik a diaidő beállítását."""
        window, controller, _engine = qml_app
        controller.setSlideshowSeconds(4)
        controller.setSlideshowLoop(False)
        _indit(window, qt_app, 0, paused=True)

        for kulcs in (
            Qt.Key.Key_Right, Qt.Key.Key_Left, Qt.Key.Key_Down,
            Qt.Key.Key_Up, Qt.Key.Key_Space, Qt.Key.Key_Space,
        ):
            _kulcs(window, qt_app, kulcs)

        assert controller.slideshowSeconds == 4


class TestKepernyovedoNemValtozik:
    """A képernyővédőben minden billentyű csak kilép, a diaidőt nem írja."""

    @pytest.mark.parametrize(
        "kulcs",
        [Qt.Key.Key_5, Qt.Key.Key_0, Qt.Key.Key_Up, Qt.Key.Key_Down,
         Qt.Key.Key_Pause],
    )
    def test_billentyu_csak_kilep_es_nem_irja_a_normal_diaidot(
        self, qml_app, qt_app, kulcs
    ):
        window, controller, _engine = qml_app
        controller.setSlideshowSeconds(4)
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

        _kulcs(window, qt_app, kulcs)

        assert show.property("visible") is False
        assert controller.slideshowSeconds == 4
