"""#2992: a diaidő a vetítő sávjáról állítható.

Az eredeti sávján (`oneup`) a 11–14. vezérlő a diaidő-blokk:
`tpslabel` („Display Time") · `minusone` · `tps` (a szám) · `plusone`.
A `SlideshowEffectTime` alapértéke **3** másodperc.

Nálunk az átmenet-választó és a feliratmód-gomb már megvolt (#433), a
diaidő viszont csak tulajdonságként létezett — a tulajdonos jelezte, hogy
nem tudja állítani.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

_QML = Path(picasapy.app.__file__).parent / "qml"


def _nevvel(gyoker, nev: str):
    """A `QObject.children()` a QML-fát is bejárja (nem csak a vizuálisat)."""

    def walk(item):
        for gy in item.children():
            yield gy
            yield from walk(gy)

    for it in walk(gyoker):
        if (it.objectName() or "") == nev:
            return it
    return None


@pytest.fixture
def vetito(qt_app):
    motor = QQmlEngine()
    motor.addImportPath(str(_QML))
    komponens = QQmlComponent(
        motor, QUrl.fromLocalFile(str(_QML / "PicasaPy" / "SlideshowView.qml"))
    )
    elem = komponens.create()
    assert elem is not None, komponens.errorString()
    yield elem
    elem.deleteLater()


class TestADiaidoBlokk:
    def test_a_NEGY_elem_ott_van(self, vetito):
        for nev in (
            "slideshowTimeBlock",
            "slideshowTimeMinus",
            "slideshowTimeValue",
            "slideshowTimePlus",
        ):
            assert _nevvel(vetito, nev) is not None, f"hiányzik: {nev}"

    def test_az_alapertek_HAROM(self, vetito):
        assert vetito.property("seconds") == 3

    def test_a_szam_a_savon_LATSZIK(self, vetito):
        ertek = _nevvel(vetito, "slideshowTimeValue")
        assert "3" in ertek.property("text")

    def test_a_PLUSZ_a_hivonak_szol(self, vetito, qt_app):
        """A vetítő nem ír beállítást — a hívó (Main.qml) teszi."""
        kapott = []
        vetito.secondsChosen.connect(kapott.append)
        _nevvel(vetito, "slideshowTimePlus").clicked.emit()
        assert kapott == [4]

    def test_a_MINUSZ_a_hivonak_szol(self, vetito):
        kapott = []
        vetito.secondsChosen.connect(kapott.append)
        _nevvel(vetito, "slideshowTimeMinus").clicked.emit()
        assert kapott == [2]

    def test_az_ALSO_hataron_a_minusz_tiltott(self, vetito):
        vetito.setProperty("seconds", 1)
        assert _nevvel(vetito, "slideshowTimeMinus").property("enabled") is False

    def test_a_FELSO_hataron_a_plusz_tiltott(self, vetito):
        vetito.setProperty("seconds", 30)
        assert _nevvel(vetito, "slideshowTimePlus").property("enabled") is False

    def test_a_diaido_a_TEMPOT_is_allitja(self, vetito):
        """A másodperc a lépegető időzítő intervalluma is."""
        vetito.setProperty("seconds", 7)
        assert vetito.property("intervalMs") == 7000


class TestAMarMeglevoVezerlok:
    """A #433 óta meglévő kettő — ne veszítsük el őket (#2992)."""

    def test_az_atmenet_valaszto_megvan(self, vetito):
        assert _nevvel(vetito, "slideshowTransitionBox") is not None

    def test_a_feliratmod_gomb_megvan(self, vetito):
        assert _nevvel(vetito, "slideshowCaptionModeButton") is not None
