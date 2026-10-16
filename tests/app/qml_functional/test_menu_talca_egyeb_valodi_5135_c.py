"""Az „Egyéb" táblázat tételei VALÓDI egérkattintással (#5135, 3. rész, C).

A nyomtatás párbeszéd szegély- és felirat-panelje (`PrintOptionsPanel`).
A panel a „Border and Text Options" gombbal nyílik. A forrás- és
elhelyezés-rádiók a panel `options`-ét írják, a Mégse/Bezár az elvetést,
az OK az elfogadást (`applyChanges`) adja. A mérés ugyanazon a
`options` / `savedOptions` állapoton megy, mint a B-részben.

Ugyanezek a tesztek a `_b` fájl segédeit használják (fixture, megnyitás).
"""

from __future__ import annotations

import pytest

from conftest import _build_qml_app
from tests.app.qml_functional.test_menu_talca_egyeb_valodi_5135_b import (
    _beallitas,
    _elokeszit,
    _gyerek,
    _keszits_konyvtarat,
    _kattints,
    _latszik,
    _nyomtatas_megnyit,
    _nyomtatas_panel_megnyit,
    _varj,
    _zar,
)


@pytest.fixture
def egyeb_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_konyvtarat,
    )


class TestSzegelyPanel:
    def test_szoveg_forras_3_valodi_kattintassal_valtozik(self, egyeb_app, qt_app):
        window, controller, _engine = egyeb_app
        _elokeszit(window, qt_app, controller)
        nyomtatas = _nyomtatas_megnyit(window, qt_app, window.property("menuBar"))
        panel = _nyomtatas_panel_megnyit(window, qt_app)
        elozo = _beallitas(panel, "options", "textSource")
        assert elozo != 3, "a szöveg forrása már 3 volt"

        _kattints(qt_app, _gyerek(window, "printOptionSource3"))
        assert _varj(
            qt_app, lambda: _beallitas(panel, "options", "textSource") == 3
        ), "a 4. forrás (3) rádió kattintás nem állította a szöveg forrását"
        _kattints(qt_app, _gyerek(window, "printOptionsCancelButton"))
        _zar(qt_app, nyomtatas)

    def test_szoveg_elhelyezes_2_valodi_kattintassal_valtozik(
        self, egyeb_app, qt_app
    ):
        window, controller, _engine = egyeb_app
        _elokeszit(window, qt_app, controller)
        nyomtatas = _nyomtatas_megnyit(window, qt_app, window.property("menuBar"))
        panel = _nyomtatas_panel_megnyit(window, qt_app)
        assert _beallitas(panel, "options", "textPlacement") != 2

        _kattints(qt_app, _gyerek(window, "printOptionPlacement2"))
        assert _varj(
            qt_app, lambda: _beallitas(panel, "options", "textPlacement") == 2
        ), "a 2. elhelyezés rádió kattintás nem váltott elhelyezést"
        _kattints(qt_app, _gyerek(window, "printOptionsCancelButton"))
        _zar(qt_app, nyomtatas)

    def test_szoveg_elhelyezes_1_valodi_kattintassal_valtozik(
        self, egyeb_app, qt_app
    ):
        window, controller, _engine = egyeb_app
        _elokeszit(window, qt_app, controller)
        nyomtatas = _nyomtatas_megnyit(window, qt_app, window.property("menuBar"))
        panel = _nyomtatas_panel_megnyit(window, qt_app)
        # előbb máshova, hogy a kattintás valóban váltson
        _kattints(qt_app, _gyerek(window, "printOptionPlacement2"))
        _kattints(qt_app, _gyerek(window, "printOptionPlacement1"))
        assert _varj(
            qt_app, lambda: _beallitas(panel, "options", "textPlacement") == 1
        ), "az 1. elhelyezés rádió kattintás nem váltott elhelyezést"
        _kattints(qt_app, _gyerek(window, "printOptionsCancelButton"))
        _zar(qt_app, nyomtatas)

    def test_szoveg_forras_1_valodi_kattintassal_valtozik(self, egyeb_app, qt_app):
        window, controller, _engine = egyeb_app
        _elokeszit(window, qt_app, controller)
        nyomtatas = _nyomtatas_megnyit(window, qt_app, window.property("menuBar"))
        panel = _nyomtatas_panel_megnyit(window, qt_app)
        _kattints(qt_app, _gyerek(window, "printOptionSource3"))
        _kattints(qt_app, _gyerek(window, "printOptionSource1"))
        assert _varj(
            qt_app, lambda: _beallitas(panel, "options", "textSource") == 1
        ), "a 2. forrás rádió kattintás nem váltotta a szöveg forrását"
        _kattints(qt_app, _gyerek(window, "printOptionsCancelButton"))
        _zar(qt_app, nyomtatas)

    def test_bezaras_elveti_a_valtoztatast(self, egyeb_app, qt_app):
        window, controller, _engine = egyeb_app
        _elokeszit(window, qt_app, controller)
        nyomtatas = _nyomtatas_megnyit(window, qt_app, window.property("menuBar"))
        panel = _nyomtatas_panel_megnyit(window, qt_app)
        elozo = _beallitas(panel, "savedOptions", "textPlacement")
        _kattints(qt_app, _gyerek(window, "printOptionPlacement2"))
        _kattints(qt_app, _gyerek(window, "printOptionsCloseButton"))
        assert _varj(qt_app, lambda: not _latszik(window, "printOptionsPanel")), (
            "a Close gomb nem zárta be a panelt"
        )
        assert _beallitas(panel, "options", "textPlacement") == elozo, (
            "a Close gomb nem vetette el a szegély-változtatást"
        )
        _zar(qt_app, nyomtatas)

    def test_megse_elveti_a_valtoztatast(self, egyeb_app, qt_app):
        window, controller, _engine = egyeb_app
        _elokeszit(window, qt_app, controller)
        nyomtatas = _nyomtatas_megnyit(window, qt_app, window.property("menuBar"))
        panel = _nyomtatas_panel_megnyit(window, qt_app)
        elozo = _beallitas(panel, "savedOptions", "textSource")
        _kattints(qt_app, _gyerek(window, "printOptionSource3"))
        _kattints(qt_app, _gyerek(window, "printOptionsCancelButton"))
        assert _varj(qt_app, lambda: not _latszik(window, "printOptionsPanel")), (
            "a Mégse gomb nem zárta be a panelt"
        )
        assert _beallitas(panel, "options", "textSource") == elozo, (
            "a Mégse gomb nem vetette el a szöveg-forrás változtatását"
        )
        _zar(qt_app, nyomtatas)

    def test_ok_elfogadja_a_valtoztatast(self, egyeb_app, qt_app):
        window, controller, _engine = egyeb_app
        _elokeszit(window, qt_app, controller)
        nyomtatas = _nyomtatas_megnyit(window, qt_app, window.property("menuBar"))
        panel = _nyomtatas_panel_megnyit(window, qt_app)
        _kattints(qt_app, _gyerek(window, "printOptionPlacement2"))
        _kattints(qt_app, _gyerek(window, "printOptionsOkButton"))
        assert _varj(qt_app, lambda: not _latszik(window, "printOptionsPanel")), (
            "az OK gomb nem zárta be a panelt"
        )
        assert _beallitas(panel, "options", "textPlacement") == 2, (
            "az OK gomb nem fogadta el a szegély-változtatást"
        )
        _zar(qt_app, nyomtatas)
