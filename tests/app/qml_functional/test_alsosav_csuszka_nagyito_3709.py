"""#3709 — az alsó sáv jobb fele képpontra az eredeti szerint.

A mérce a tulajdonos 1920 px-es ablakról készült képernyőképe
(`research/testdata/screenshot/Képernyőkép 2026-07-18 150933.png`, a jobb
szélső 3 oszlop levágva) és a `respack.yt` rétegfejlécei
(`tools/picasa/respack.py`). A képernyőképen mérve (W = 1920):

| elem | eredeti (kép) | `respack.yt` | képlet |
|---|---|---|---|
| nagyítás-csúszka foglalata | 1518 … 1645 | `scalecontainer` 398…525 | `W − 402` … `W − 275` |
| a csúszka RAJZOLT sávja | 1521 … 1641 | `scaleslider/sliderbase` 3…124 a 127-ből | `W − 399` … `W − 279` |
| a négy kapcsoló cellái | 1665 · 1725 · 1785 · 1845 · 1905 | `metadata_group` 545…785, 4 × 60 | `W − 255` … `W − 15` |
| a kapcsolósáv külső keretoszlopai | 1666 és 1903 | `left/right_segment_n`: a keret az 1. és az utolsó előtti oszlopban | `W − 254`, `W − 17` |
| a belső osztók (két sötét oszlop) | 1724/1725 · 1784/1785 · 1844/1845 | a szegmensek a cella szélén | |
| a keret magassága | 22 sor a 24-ből | a keret az 1. és az utolsó előtti sorban | |
| a nagyító ikonja a `loupehit`-ben | x + 2 | `loupe` 368…391 a `loupehit` 366…391-ben | |

A `TestAKirajzoltKep` a `grabWindow()` KÉPÉN, képpont-oszlopok és -sorok
keresésével méri ezeket, két ablakszélességen; property-t csak a keresés
kiinduló sorához olvas.
"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

#: Fél képpont tűrés: a QML geometriája tört szám lehet.
TURES = 0.5

#: Két ablakszélesség: a referenciakép 1920-a és egy keskenyebb.
ABLAKOK = (1280, 1920)

#: Ennyivel kell eltérnie egy képpontnak (a három csatorna összegében) a
#: sáv hátterétől, hogy rajznak számítson — a #3603 mércéje.
ELKULONBSEG = 30

#: A keretvonal a cella kitöltésénél is jóval sötétebb: a háttérhez képest
#: ennyivel (csatornaösszeg) kell sötétebbnek lennie.
KERET_SOTETSEG = 120


def _elem(window, nev: str) -> QObject:
    obj = window.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található a kirajzolt fában"
    return obj


def _szelesseg(window, qt_app, szelesseg: int) -> None:
    window.setProperty("width", szelesseg)
    for _ in range(4):
        qt_app.processEvents()


def _x_a_savban(window, nev: str) -> float:
    """Az elem bal széle a `trayMainBar` koordinátarendszerében."""
    sav = _elem(window, "trayMainBar")
    return _elem(window, nev).mapToItem(sav, QPointF(0, 0)).x()


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        if feltetel():
            return True
        qt_app.processEvents()
        time.sleep(0.005)
    return False


def _kattints(window, elem, qt_app, x: float | None = None) -> None:
    """VALÓDI egérkattintás az elemre (alapból a közepére)."""
    assert elem.width() > 0 and elem.height() > 0, "kattinthatatlan (0 méret)"
    helyi = QPointF(elem.width() / 2 if x is None else x, elem.height() / 2)
    pont = elem.mapToScene(helyi)
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    qt_app.processEvents()


class TestACsuszkaSavja:
    """A `traySizeSlider` RAJZOLT sávja mindkét végén 3 képponttal beljebb
    áll (`scaleslider/sliderbase` 3…124 a 127-es foglalatban)."""

    def test_a_rajzolt_sav_3_kepponttal_beljebb_121_szeles(
        self, qml_app_module, qt_app
    ):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, 1280)
        csuszka = _elem(window, "traySizeSlider")
        sav = csuszka.property("background")
        assert sav is not None, "a csúszkának nincs `background`-eleme"
        assert sav.x() == pytest.approx(3, abs=TURES)
        assert sav.width() == pytest.approx(121, abs=TURES)
        assert csuszka.width() - (sav.x() + sav.width()) == pytest.approx(
            3, abs=TURES
        )

    def test_a_foglalat_merete_valtozatlan_marad(self, qml_app_module, qt_app):
        """A behúzás NEM a kattintható területet szűkíti — a #3602
        7 képpontos nagyító-csúszka rése ettől nem mozdulhat."""
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, 1280)
        csuszka = _elem(window, "traySizeSlider")
        assert csuszka.width() == 127
        nagyito = _elem(window, "trayLoupeButton")
        nagyito_jobb = _x_a_savban(window, "trayLoupeButton") + nagyito.width()
        csuszka_bal = _x_a_savban(window, "traySizeSlider")
        assert csuszka_bal - nagyito_jobb == pytest.approx(7, abs=TURES)


class TestANagyito:
    def test_a_gomb_25x19(self, qml_app_module, qt_app):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, 1280)
        gomb = _elem(window, "trayLoupeButton")
        assert (gomb.width(), gomb.height()) == (25.0, 19.0)

    def test_az_ikon_a_gombon_belul_x2_y1(self, qml_app_module, qt_app):
        """`loupe` 368…391 × 452…468 a `loupehit` 366…391 × 451…470-ben."""
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, 1280)
        gomb = _elem(window, "trayLoupeButton")
        ikon = _elem(window, "trayLoupeIcon")
        hely = ikon.mapToItem(gomb, QPointF(0, 0))
        assert (hely.x(), hely.y()) == (2.0, 1.0)
        assert (ikon.width(), ikon.height()) == (23.0, 16.0)


def _kep(window, qt_app, szelesseg: int):
    _szelesseg(window, qt_app, szelesseg)
    window.setProperty("height", 1030)
    for _ in range(6):
        qt_app.processEvents()
    return window.grabWindow()


def _osszeg(kep, x: int, y: int) -> int:
    szin = kep.pixelColor(x, y)
    return szin.red() + szin.green() + szin.blue()


def _rajzolt_oszlopok(kep, xek, y, hatter) -> list[int]:
    return [x for x in xek if abs(_osszeg(kep, x, y) - hatter) > ELKULONBSEG]


def _keret_oszlopok(kep, xek, y, hatter) -> list[int]:
    return [x for x in xek if hatter - _osszeg(kep, x, y) > KERET_SOTETSEG]


def _keret_sorok(kep, x, yok, hatter) -> list[int]:
    return [y for y in yok if hatter - _osszeg(kep, x, y) > KERET_SOTETSEG]


class TestAKirajzoltKep:
    """A `grabWindow()` képén keresett élek a képernyőkép számaival."""

    @pytest.mark.parametrize("szel", ABLAKOK)
    def test_a_csuszka_rajzolt_sava(self, qml_app_module, qt_app, szel):
        window, _, _ = qml_app_module
        kep = _kep(window, qt_app, szel)
        csuszka = _elem(window, "traySizeSlider")
        bal_felso = csuszka.mapToScene(QPointF(0, 0))
        y = round(bal_felso.y() + csuszka.height() / 2)
        foglalat = round(bal_felso.x())
        assert foglalat == szel - 402, "a foglalat a #3602 szerint W − 402"
        # a háttér a nagyító és a csúszka közti 7 képpontos résből
        hatter = _osszeg(kep, foglalat - 3, y)
        rajz = _rajzolt_oszlopok(kep, range(foglalat - 6, foglalat + 133), y, hatter)
        assert rajz, "a csúszka sávja nem rajzolódott ki"
        assert (rajz[0], rajz[-1]) == (szel - 399, szel - 279), (
            f"a rajzolt sáv {rajz[0]}…{rajz[-1]}, az eredetiben "
            f"{szel - 399}…{szel - 279} (1920-on 1521…1641)"
        )

    @pytest.mark.parametrize("szel", ABLAKOK)
    def test_a_kapcsolosav_keretoszlopai(self, qml_app_module, qt_app, szel):
        window, _, _ = qml_app_module
        kep = _kep(window, qt_app, szel)
        csoport = _elem(window, "trayMetadataGroup")
        teteje = csoport.mapToScene(QPointF(0, 0)).y()
        # a keret alsó sora fölött: a 16 képpontos ikonok (y 4…19) alatt
        y = round(teteje + 21)
        hatter = _osszeg(kep, szel - 262, y)
        keret = _keret_oszlopok(kep, range(szel - 262, szel - 8), y, hatter)
        vart = [
            szel - 254,
            szel - 196, szel - 195,
            szel - 136, szel - 135,
            szel - 76, szel - 75,
            szel - 17,
        ]
        assert keret == vart, (
            f"a kapcsolósáv keretoszlopai {keret}, az eredetiben {vart} "
            "(1920-on 1666 · 1724/1725 · 1784/1785 · 1844/1845 · 1903)"
        )

    @pytest.mark.parametrize("szel", ABLAKOK)
    def test_a_kapcsolosav_kerete_22_sor(self, qml_app_module, qt_app, szel):
        window, _, _ = qml_app_module
        kep = _kep(window, qt_app, szel)
        csoport = _elem(window, "trayMetadataGroup")
        teteje = round(csoport.mapToScene(QPointF(0, 0)).y())
        x = szel - 247
        hatter = _osszeg(kep, x, teteje - 3)
        sorok = _keret_sorok(kep, x, range(teteje - 3, teteje + 28), hatter)
        assert sorok == [teteje + 1, teteje + 22], (
            f"a keret sorai {sorok}, az eredetiben a 24 magas cella 1. és "
            "22. sora"
        )

    @pytest.mark.parametrize("szel", ABLAKOK)
    def test_a_nagyitonak_nincs_kerete(self, qml_app_module, qt_app, szel):
        window, _, _ = qml_app_module
        kep = _kep(window, qt_app, szel)
        gomb = _elem(window, "trayLoupeButton")
        bf = gomb.mapToScene(QPointF(0, 0))
        x0, y0 = round(bf.x()), round(bf.y())
        hatter = _osszeg(kep, x0 + 28, y0 + 9)
        # a bal oszlop és a felső/alsó sor: az ikon (x 2…24, y 1…16) nem
        # ér ide, tehát ami itt rajzolt, az keret volna
        szelek = [(x0, y) for y in range(y0, y0 + 19)]
        szelek += [(x, y0) for x in range(x0, x0 + 25)]
        szelek += [(x, y0 + 18) for x in range(x0, x0 + 25)]
        rajzolt = [
            (x, y) for x, y in szelek
            if abs(_osszeg(kep, x, y) - hatter) > ELKULONBSEG
        ]
        assert not rajzolt, (
            f"a nagyító szélén rajz látszik: {rajzolt[:5]} — az eredetiben "
            "keret nélküli ikon"
        )


class TestAKattintas:
    """Valódi egérkattintással: a keret eltűnése és a behúzás nem veheti
    el a kattinthatóságot. Állapotot ír, ezért saját ablakot kér."""

    def test_a_nagyito_ki_be_kapcsol(self, qml_app, qt_app):
        window, _, _ = qml_app
        _szelesseg(window, qt_app, 1280)
        gomb = _elem(window, "trayLoupeButton")
        assert window.property("loupeActive") is False
        _kattints(window, gomb, qt_app)
        assert _var(qt_app, lambda: window.property("loupeActive") is True)
        _kattints(window, gomb, qt_app)
        assert _var(qt_app, lambda: window.property("loupeActive") is False)

    def test_a_csuszka_a_behuzasban_is_kattinthato(self, qml_app, qt_app):
        window, _, _ = qml_app
        _szelesseg(window, qt_app, 1280)
        csuszka = _elem(window, "traySizeSlider")
        # a jobb végén, a 3 képpontos behúzásban: a rajzon kívül, a
        # foglalaton belül
        _kattints(window, csuszka, qt_app, x=csuszka.width() - 1)
        assert _var(
            qt_app,
            lambda: window.property("thumbSize") >= csuszka.property("to") - 2,
        ), f"thumbSize = {window.property('thumbSize')}"
        _kattints(window, csuszka, qt_app, x=1)
        assert _var(
            qt_app,
            lambda: window.property("thumbSize") <= csuszka.property("from") + 2,
        ), f"thumbSize = {window.property('thumbSize')}"
