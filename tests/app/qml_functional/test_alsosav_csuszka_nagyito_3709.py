"""#3709 — a #3602 (PR #3703) UTÁN maradt két eltérés a tulajdonos
1917 px-es képernyőképéhez (`research/testdata/screenshot/Képernyőkép
2026-07-18 150933.png`) képest:

- a nagyítás-csúszka **rajzolt** sávja nálunk kitölti a 127 px-es
  foglalatot, az eredetiben ~6 px belső behúzással rajzolódik
  (`traySizeSlider` bal széle x 1515, a sáv x 1521-től indul);
- a nagyító nálunk keretes gomb (a `PicasaButton` mindig rajzolt
  szegélye/gradiense), az eredetiben keret nélküli ikon.

A kapcsolócsoport (`trayMetadataGroup`) ~3–4 px-es szélesség-eltérése
NEM része ennek a fájlnak: a pontos célérték a hivatkozott
képernyőkép nélkül nem vezethető le megbízhatóan (nincs elérhető
mérőkép ebben a körben) — ld. a jegy #3709 kommentjét.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPointF

#: Fél képpont tűrés: a QML geometriája tört szám lehet.
TURES = 0.5

#: Mennyivel kell eltérnie egy képpontnak (a három csatorna összegében) a
#: háttértől, hogy szegélynek/kitöltésnek számítson — a #3603 mércéje.
ELKULONBSEG = 30


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
    elem = _elem(window, nev)
    return elem.mapToItem(sav, QPointF(0, 0)).x()


class TestACsuszkaSavBehuzasa:
    """A `traySizeSlider` RAJZOLT sávja MÉRT 6 képpont belső behúzással
    indul — a foglalat (127 px) maga nem szűkül, csak a rajz."""

    def test_a_rajzolt_sav_6_kepponttal_beljebb_kezdodik(
        self, qml_app_module, qt_app
    ):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, 1280)
        csuszka = _elem(window, "traySizeSlider")
        sav = csuszka.property("background")
        assert sav is not None, "a csúszkának nincs `background`-eleme"
        assert sav.x() == pytest.approx(6, abs=TURES)

    def test_a_rajzolt_sav_jobb_szele_valtozatlan(self, qml_app_module, qt_app):
        """A behúzás csak BALRÓL jön — a sáv jobb széle a foglalat jobb
        szélén marad (127 − 6 = 121 képpont széles rajz)."""
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, 1280)
        csuszka = _elem(window, "traySizeSlider")
        sav = csuszka.property("background")
        assert sav.x() + sav.width() == pytest.approx(csuszka.width(), abs=TURES)
        assert sav.width() == pytest.approx(121, abs=TURES)

    def test_a_foglalat_merete_valtozatlan_marad(self, qml_app_module, qt_app):
        """A behúzás NEM a csúszka interaktív területét szűkíti — a #3602
        7 képpontos nagyító-csúszka rése ettől nem mozdulhat."""
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, 1280)
        csuszka = _elem(window, "traySizeSlider")
        assert csuszka.width() == 127
        nagyito = _elem(window, "trayLoupeButton")
        nagyito_jobb = _x_a_savban(window, "trayLoupeButton") + nagyito.width()
        csuszka_bal = _x_a_savban(window, "traySizeSlider")
        assert csuszka_bal - nagyito_jobb == pytest.approx(7, abs=TURES)


class TestANagyitoKeretNelkuli:
    """A nagyító gombja KERET NÉLKÜLI ikon — a `PicasaButton` szegélye/
    gradiense eddig mindig kirajzolódott, függetlenül az állapottól."""

    def _kep_es_hatarok(self, qml_app_module, qt_app):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, 1280)
        window.setProperty("height", 700)
        for _ in range(4):
            qt_app.processEvents()
        gomb = _elem(window, "trayLoupeButton")
        bal_felso = gomb.mapToScene(QPointF(0, 0))
        kep = window.grabWindow()
        return kep, bal_felso, gomb.width(), gomb.height()

    def _osszeg(self, kep, x: int, y: int) -> int:
        szin = kep.pixelColor(round(x), round(y))
        return szin.red() + szin.green() + szin.blue()

    def test_nincs_lathato_keret_a_gomb_szelen(self, qml_app_module, qt_app):
        kep, bf, szeles, magas = self._kep_es_hatarok(qml_app_module, qt_app)
        # a háttér-referencia: a nagyító és a csúszka közötti MÉRT 7
        # képpontos résben — ott biztosan a sáv krómja látszik, semmi más
        hatter_x = bf.x() + szeles + 3
        hatter = self._osszeg(kep, hatter_x, bf.y() + magas / 2)

        # a gomb négy szélének KÖZEPE — a korábbi PicasaButton szegélye itt
        # egy teljes, folytonos vonalként rajzolódott ki
        elek = [
            (bf.x() + szeles / 2, bf.y()),  # felső él közepe
            (bf.x() + szeles / 2, bf.y() + magas - 1),  # alsó él közepe
            (bf.x(), bf.y() + magas / 2),  # bal él közepe
            (bf.x() + szeles - 1, bf.y() + magas / 2),  # jobb él közepe
        ]
        for x, y in elek:
            elteres = abs(self._osszeg(kep, x, y) - hatter)
            assert elteres <= ELKULONBSEG, (
                f"a gomb szélén ({x:.0f}, {y:.0f}) szegély/kitöltés "
                f"látszik a háttérhez ({hatter}) képest (különbség "
                f"{elteres}) — az eredetiben a nagyító keret nélküli ikon"
            )


class TestANagyitoKattinthatosagaMegmarad:
    """A keret eltűnése nem veheti el a kattinthatóságot (#1911 láncát)."""

    def test_a_gomb_meg_mindig_25x19(self, qml_app_module, qt_app):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, 1280)
        gomb = _elem(window, "trayLoupeButton")
        assert (gomb.width(), gomb.height()) == (25.0, 19.0)

    def test_a_gombnak_van_tooltip_szovege(self, qml_app_module, qt_app):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, 1280)
        gomb = _elem(window, "trayLoupeButton")
        szoveg = gomb.property("ToolTip.text") or ""
        if not szoveg:
            # az attached property nem mindig olvasható property-ként (a
            # #1911 mintája) — ilyenkor a forrás a hiteles hely
            import picasapy.app as app_csomag
            from pathlib import Path

            forras = (
                Path(app_csomag.__file__).parent / "qml" / "PicasaPy"
                / "TrayBar.qml"
            ).read_text(encoding="utf-8")
            assert (
                'ToolTip.text: qsTr("Click and drag over photos'
                in forras
            )
        else:
            assert szoveg == "Click and drag over photos to magnify them"
