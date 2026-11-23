"""#7380: a szöveg KÖZVETLENÜL a képre gépelhető, mint az eredeti Picasában.

Az eredeti Szöveg eszközben nincs szövegmező a panelben (job-839 `__10`): a
kép közepén a „Type anywhere to add text” hint áll, a kattintás (`__12`)
után a hely jelölt (a szövegkurzor a ponton), a gépelt szöveg (`__14`) a
képen jelenik meg egy lekerekített, vastag világos keretű dobozban, és az
Alkalmaz csak ekkor aktív. A kész szöveg (`__26`) a kattintott pont ALATT áll.

A próbák a VALÓDI, kirajzolt ablakot mérik (nem a számolt geometriát):
a keret képpontprofilját a `__14` képkockából mért értékekhez hasonlítják.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest

import picasapy.app
from tests.app.qml_functional._editor_test_helpers import EditorTestHelpers
from tests.support.varakozas import var_feltetelre

# a job-839 `__14` mérése (képernyőképpont, a kattintott (600,400) ponthoz)
_KERET_KULSO_BAL = -33  # a külső keret bal széle a ponthoz képest
_KERET_KULSO_FELSO = -32
_KERET_SAV_SOTET = 46  # a külső/belső sötét sáv szürkeértéke
_KERET_SAV_VILAGOS = 172  # a vastag világos sáv szürkeértéke
# a futó próba-app a forrásnyelvet (angol) mutatja; a fordításokat a
# `TestFordítasok` a `.ts` fájlokból ellenőrzi
_HINT = "Type anywhere to add text"
_CLEAR_ALL = "Clear All"
_CLEAR_ALL_TOOLTIP = "Remove all existing text"
_I18N = Path(picasapy.app.__file__).parent / "i18n"


def _elem(window, nev: str):
    item = window.findChild(QObject, nev)
    assert item is not None, f"{nev} nem található"
    return item


def _var(qt_app, feltetel, uzenet: str, masodperc: float = 10.0) -> None:
    assert var_feltetelre(qt_app, feltetel, masodperc), uzenet


def _kattint(window, item, x: float, y: float) -> QPoint:
    pont = item.mapToScene(QPointF(x, y))
    kepernyo = QPoint(round(pont.x()), round(pont.y()))
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, kepernyo
    )
    return kepernyo


def _gepel(window, qt_app, szoveg: str) -> None:
    """Karakterenkénti valódi billentyűleütés az ablak fókuszába."""
    for karakter in szoveg:
        QTest.keyClick(window, karakter)
        qt_app.processEvents()


def _szurke(kep: QImage, x: int, y: int) -> int:
    szin = kep.pixelColor(x, y)
    return round((szin.red() + szin.green() + szin.blue()) / 3)


def _feltoltott(qml_app, qt_app):
    """Megnyitja a nézőt és a Szöveg eszközt; visszaadja a fontos elemeket."""
    window, _, engine = qml_app
    EditorTestHelpers()._open_viewer(window, qt_app)
    panel = _elem(window, "viewerEditorPanel")
    panel.setProperty("textActive", True)
    qt_app.processEvents()
    terulet = _elem(window, "textClickArea")
    _var(qt_app, lambda: terulet.width() > 0, "a szövegkattintás területe üres")
    edit = engine.rootContext().contextProperty("editController")
    return window, panel, terulet, edit


class TestPanelSzovegmezoNelkul:
    def test_a_panelben_nincs_szovegmezo_es_nincs_magyarazo_sor(
        self, qml_app, qt_app
    ):
        window, panel, _terulet, _edit = _feltoltott(qml_app, qt_app)
        oszlop = _elem(window, "textColumn")
        assert oszlop.findChild(QObject, "textContentField") is None, (
            "a panelben nem lehet szövegmező: a szöveg a képre gépelhető"
        )
        leiro = oszlop.findChild(QObject, "textPanelInstruction")
        assert leiro is None, "a magyarázó sor kikerült a panelből"

    def test_clear_all_a_gomb_felirata_es_a_regi_felirat_a_tooltip(
        self, qml_app, qt_app
    ):
        window, _panel, _terulet, _edit = _feltoltott(qml_app, qt_app)
        gomb = _elem(window, "textRemoveAllButton")
        assert gomb.property("label") == _CLEAR_ALL
        assert gomb.property("tooltip") == _CLEAR_ALL_TOOLTIP


class TestHint:
    def test_a_hint_a_kep_kozepen_all_kattintasig(self, qml_app, qt_app):
        window, _panel, terulet, _edit = _feltoltott(qml_app, qt_app)
        hint = _elem(window, "textHint")
        assert hint.property("visible") is True
        assert hint.property("text") == _HINT
        kozep = hint.mapToScene(
            QPointF(hint.width() / 2, hint.height() / 2)
        )
        kep_kozep = terulet.mapToScene(
            QPointF(terulet.width() / 2, terulet.height() / 2)
        )
        assert abs(kozep.x() - kep_kozep.x()) <= 2
        assert abs(kozep.y() - kep_kozep.y()) <= 2

    def test_kattintas_utan_a_hint_eltunik(self, qml_app, qt_app):
        window, _panel, terulet, _edit = _feltoltott(qml_app, qt_app)
        hint = _elem(window, "textHint")
        _kattint(window, terulet, terulet.width() * 0.3, terulet.height() * 0.4)
        _var(
            qt_app, lambda: hint.property("visible") is False,
            "a hint a kattintás után is látszik",
        )

    def test_clear_all_kattintas_elott_tiltott_utana_aktiv(self, qml_app, qt_app):
        window, _panel, terulet, _edit = _feltoltott(qml_app, qt_app)
        gomb = _elem(window, "textRemoveAllButton")
        assert gomb.property("enabled") is False, "job-839 __10: tiltott"
        _kattint(window, terulet, terulet.width() * 0.3, terulet.height() * 0.4)
        _var(
            qt_app, lambda: gomb.property("enabled") is True,
            "job-839 __12: a kattintás után a Clear All aktív",
        )


class TestKozvetlenGepeles:
    def test_kattintas_utan_a_hely_jelolt_a_szovegkurzor_a_ponton(
        self, qml_app, qt_app
    ):
        window, _panel, terulet, edit = _feltoltott(qml_app, qt_app)
        mezo = _elem(window, "textContentField")
        assert mezo.property("visible") is False
        pont = _kattint(window, terulet, terulet.width() * 0.3, terulet.height() * 0.4)
        _var(qt_app, lambda: mezo.property("visible") is True, "nincs bevitel")
        _var(
            qt_app, lambda: mezo.property("activeFocus") is True,
            "a bevitel nem kapott fókuszt a kattintás után",
        )
        bal_felso = mezo.mapToScene(QPointF(0, 0))
        assert abs(bal_felso.x() - pont.x()) <= 1, "a bal szél nem a ponton áll"
        assert abs(bal_felso.y() - pont.y()) <= 1, "a sor teteje nem a ponton áll"
        hely = edit.property("textEditPlacement")
        assert hely["x"] == pytest.approx(0.3, abs=0.01)
        assert hely["y"] == pytest.approx(0.4, abs=0.01)

    def test_valodi_billentyuzettel_a_szoveg_a_piszkozatba_kerul_es_az_alkalmaz_aktiv(
        self, qml_app, qt_app
    ):
        window, panel, terulet, edit = _feltoltott(qml_app, qt_app)
        alkalmaz = _elem(window, "textApplyButton")
        assert alkalmaz.property("enabled") is False
        _kattint(window, terulet, terulet.width() * 0.3, terulet.height() * 0.4)
        mezo = _elem(window, "textContentField")
        _var(qt_app, lambda: mezo.property("activeFocus") is True, "nincs fókusz")
        assert alkalmaz.property("enabled") is False, (
            "szöveg nélkül az Alkalmaz nem lehet aktív"
        )
        _gepel(window, qt_app, "Proba")
        _var(
            qt_app, lambda: edit.property("textDraft") == "Proba",
            "a gépelt szöveg nem jutott a piszkozatba",
        )
        assert panel.property("textDraftContent") == "Proba"
        _var(
            qt_app, lambda: alkalmaz.property("enabled") is True,
            "szöveg után az Alkalmaz nem aktív",
        )

    def test_a_szovegmezo_programozott_ertekadasa_is_a_piszkozatot_viszi(
        self, qml_app, qt_app
    ):
        """A régi próbák ezen az úton írtak a mezőbe; a viselkedés marad."""
        window, panel, _terulet, edit = _feltoltott(qml_app, qt_app)
        mezo = _elem(window, "textContentField")
        mezo.setProperty("text", "Nyaralás")
        qt_app.processEvents()
        assert edit.property("textDraft") == "Nyaralás"
        assert panel.property("textDraftContent") == "Nyaralás"

    def test_a_doboz_csak_szoveggel_latszik_es_a_keret_a_mert_profil(
        self, qml_app, qt_app
    ):
        window, _panel, terulet, _edit = _feltoltott(qml_app, qt_app)
        keret = _elem(window, "textBoxFrame")
        assert keret.property("visible") is False, "üres szövegnél csak a kurzor áll"
        pont = _kattint(window, terulet, terulet.width() * 0.3, terulet.height() * 0.4)
        mezo = _elem(window, "textContentField")
        _var(qt_app, lambda: mezo.property("activeFocus") is True, "nincs fókusz")
        _gepel(window, qt_app, "PicasaProba")
        _var(
            qt_app, lambda: keret.property("visible") is True,
            "a begépelt szöveg körül nem jelent meg a doboz",
        )
        qt_app.processEvents()
        kep = window.grabWindow()
        bal = keret.mapToScene(QPointF(0, 0))
        # a keret külső bal széle a mért helyen: a ponttól -32/-33 képpontra
        assert abs(bal.x() - (pont.x() + _KERET_KULSO_BAL)) <= 2
        assert abs(bal.y() - (pont.y() + _KERET_KULSO_FELSO)) <= 2
        # a profil a keret bal szélétől, a doboz FÜGGŐLEGES közepén:
        # sötét sáv · vastag világos sáv · sötét sáv (job-839 `__14`: x 567..581)
        y = round(bal.y() + keret.property("height") / 2)
        x0 = round(bal.x())
        sotet_kulso = _szurke(kep, x0 + 1, y)
        vilagos = _szurke(kep, x0 + 7, y)
        sotet_belso = _szurke(kep, x0 + 13, y)
        assert abs(sotet_kulso - _KERET_SAV_SOTET) <= 25, sotet_kulso
        assert abs(vilagos - _KERET_SAV_VILAGOS) <= 25, vilagos
        assert abs(sotet_belso - _KERET_SAV_SOTET) <= 25, sotet_belso

    def test_a_doboz_belseje_atlatszo_a_kep_latszik_benne(self, qml_app, qt_app):
        """job-839 `__14`: a keret belseje a képpel azonos (arány 1,00)."""
        window, _panel, terulet, _edit = _feltoltott(qml_app, qt_app)
        pont = _kattint(window, terulet, terulet.width() * 0.3, terulet.height() * 0.4)
        mezo = _elem(window, "textContentField")
        _var(qt_app, lambda: mezo.property("activeFocus") is True, "nincs fókusz")
        qt_app.processEvents()
        elotte = window.grabWindow()
        _gepel(window, qt_app, "PicasaProba")
        keret = _elem(window, "textBoxFrame")
        _var(qt_app, lambda: keret.property("visible") is True, "nincs doboz")
        qt_app.processEvents()
        utana = window.grabWindow()
        # a belső terület: a ponttól balra/fent 10 képpontra (a szöveg és a
        # keret közti átlátszó sávban), a szöveg nélküli részen
        x, y = pont.x() - 8, pont.y() - 8
        assert _szurke(utana, x, y) == _szurke(elotte, x, y), (
            "a doboz belseje elfedi a képet"
        )


class TestAlkalmazUtan:
    def test_a_kesz_szoveg_a_kattintott_pont_alatt_all(self, qml_app, qt_app):
        """job-839 `__26`: a betűk a kattintott pont ALATT, a bal szél a ponton."""
        window, panel, terulet, _edit = _feltoltott(qml_app, qt_app)
        pont = _kattint(window, terulet, terulet.width() * 0.3, terulet.height() * 0.4)
        mezo = _elem(window, "textContentField")
        _var(qt_app, lambda: mezo.property("activeFocus") is True, "nincs fókusz")
        qt_app.processEvents()
        elotte = _kep_tomb(window.grabWindow())
        _gepel(window, qt_app, "PicasaProba")
        alkalmaz = _elem(window, "textApplyButton")
        _var(qt_app, lambda: alkalmaz.property("enabled") is True, "Alkalmaz tiltott")
        _kattint(window, alkalmaz, alkalmaz.width() / 2, alkalmaz.height() / 2)
        _var(
            qt_app, lambda: panel.property("textActive") is False,
            "az Alkalmaz nem zárta az eszközt",
        )

        def _van_szoveg() -> bool:
            return _szoveg_befoglalo(
                _kep_tomb(window.grabWindow()), elotte, pont
            ) is not None

        _var(qt_app, _van_szoveg, "a kész szöveg nem jelent meg a képen", 15.0)
        felso, also, bal, jobb = _szoveg_befoglalo(
            _kep_tomb(window.grabWindow()), elotte, pont
        )
        # job-839 `__26`: x 601-651, y 402-407 a (600,400) pontnál
        assert felso >= pont.y() - 1, f"a betűk a pont FÖLÖTT állnak ({felso})"
        assert felso <= pont.y() + 6, f"a betűk túl messze a pont alatt ({felso})"
        assert abs(bal - pont.x()) <= 3, f"a bal szél nem a ponton áll ({bal})"


def _kep_tomb(kep: QImage) -> np.ndarray:
    kep = kep.convertToFormat(QImage.Format.Format_RGB888)
    ptr = kep.constBits()
    tomb = np.frombuffer(ptr, dtype=np.uint8, count=kep.sizeInBytes())
    return tomb.reshape(kep.height(), kep.bytesPerLine())[
        :, : kep.width() * 3
    ].reshape(kep.height(), kep.width(), 3).astype(int)


def _szoveg_befoglalo(utana: np.ndarray, elotte: np.ndarray, pont: QPoint):
    """A pont körüli ablakban változott képpontok befoglalója, vagy None."""
    y0, y1 = pont.y() - 40, pont.y() + 60
    x0, x1 = pont.x() - 40, pont.x() + 200
    kulonbseg = np.abs(utana[y0:y1, x0:x1] - elotte[y0:y1, x0:x1]).sum(axis=-1) > 60
    sorok = np.nonzero(kulonbseg.any(axis=1))[0]
    oszlopok = np.nonzero(kulonbseg.any(axis=0))[0]
    if sorok.size == 0:
        return None
    return (
        int(sorok.min()) + y0, int(sorok.max()) + y0,
        int(oszlopok.min()) + x0, int(oszlopok.max()) + x0,
    )
