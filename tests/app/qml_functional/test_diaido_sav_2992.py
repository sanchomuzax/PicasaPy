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


def _var(qt_app, ezredmasodperc: int) -> None:
    """Rendes esemenyhurok-fordulo — a `processEvents()` maga nem jaratja
    le az idozitoket (#2992: az elso valtozatom ezen csuszott el)."""
    from PySide6.QtCore import QEventLoop, QTimer

    hurok = QEventLoop()
    QTimer.singleShot(ezredmasodperc, hurok.quit)
    hurok.exec()


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


class TestASavNemTunikELAzEgerAlatt:
    """#2992: a vezérlősáv NE tűnjön el, amíg a mutató rajta van.

    ## A mért hiba

    A sáv egérmozgásra jelenik meg, és 2,5 másodperc után magától eltűnik
    (`hideTimer`). A megjelenítő `MouseArea` viszont a **teljes vetítőt**
    fedi, és a sáv **utána** van deklarálva — tehát a sáv TAKARJA. Amíg a
    mutató a sávon áll (épp a gombot keresi), a `MouseArea` nem kap
    `positionChanged`-et, a `hideTimer` lejár, és a sáv **eltűnik a kéz
    alól**.

    A tulajdonos szava a jegyben: *„egérmozgatásra nem jelenik meg a kis
    lejátszó, ami az eredetiben ott van, fixen."* Az „ott van, fixen" épp
    ezt írja le: az eredetiben a sáv nem szökik el.

    ## Amit ez a lap kiköt

    A sávnak legyen SAJÁT lebegés-figyelője, ami a mutató alatt tartja —
    és amikor a mutató elhagyja, induljon újra az elrejtés.
    """

    def test_a_savnak_van_sajat_lebegesfigyeloje(self, vetito) -> None:
        sav = _nevvel(vetito, "slideshowControls")
        assert sav is not None
        figyelo = _nevvel(vetito, "slideshowControlsHover")
        assert figyelo is not None, (
            "a vezérlősávnak nincs saját lebegés-figyelője — a mutató "
            "alatt el fog tűnni, mert a megjelenítő MouseArea-t maga a "
            "sáv takarja"
        )

    def test_az_elrejto_idozito_a_LEBEGEST_nezi(self, vetito, qt_app) -> None:
        """A kapu VALODI probaja: a sav latszik, az elrejto idozito lejar —
        es mivel a mutato NINCS a savon, a sav eltunik.

        ⚠️ Ez a NEGATIV agat meri (nincs lebeges → eltunik). A POZITIV ag
        (mutato a savon → marad) szintetikus egermozgast kivan egy valodi
        ablakban; azt a `test_a_sav_a_mutato_alatt_MARAD` vegzi.
        """
        sav = _nevvel(vetito, "slideshowControls")
        rejto = _nevvel(vetito, "slideshowHideTimer")
        assert rejto is not None, "az elrejto idozitonek objectName kell"
        sav.setProperty("shown", True)
        rejto.setProperty("interval", 1)
        rejto.setProperty("running", True)
        _var(qt_app, 300)
        assert sav.property("shown") is False


class TestASavAMutatoAlattMarad:
    """A POZITIV ag — es amit rola NEM tudunk gepileg allitani.

    ⛔ **Ket zsakutca, kimondva, hogy a kovetkezo kor ne fussa ujra:**

    1. A `HoverHandler.hovered` **csak olvashato**. Az elso valtozatom
       beirta (`setProperty("hovered", True)`), a PySide elnyelte, a proba
       pedig ZOLDEN atment — ugy, hogy semmit nem mert. Merve: a beiras
       utan a `hovered` tovabbra is `False`.
    2. Szintetikus egermozgas (`QTest.mouseMove`) egy `QQuickView`-ban:
       a koordinatak jok (`SizeRootObjectToView` utan a sav kozepe
       399,556), de a sav `visible`-je **vegig `False` marad** — az
       `opacity`-animaciot (`Behavior on opacity`, 200 ms) az offscreen
       platform nem hajtja, es a `visible: opacity > 0` miatt a lathatatlan
       elem nem kap lebegest. Az `opacity` kezi beirasat a `Behavior`
       elnyeli.

    ⇒ A pozitiv ag (mutato a savon → a sav MARAD) gepileg csak valodi
    ablakkezelovel merheto; a CI-n nincs ilyen. Ezert itt FORRAS-SZINTU
    kikotes all: az elrejto idozito tenylegesen a lebegest nezi. Ez nem
    rajzolast mer — es ezt a lap kimondja, hogy ne olvasodjon tobbnek.
    """

    def test_az_idozito_a_lebegest_KERDEZI(self) -> None:
        forras = (_QML / "PicasaPy" / "SlideshowView.qml").read_text(
            encoding="utf-8"
        )
        sor = [s for s in forras.splitlines() if "onTriggered" in s and "controlsBar.shown = false" in s]
        assert sor, "nem talalom az elrejto idozito agat"
        assert "hovered" in sor[0], (
            f"az elrejtes nem nezi a lebegest: {sor[0].strip()!r} — a sav "
            "igy eltunik a mutato alol"
        )

    def test_a_lebeges_vege_UJRAINDITJA_az_elrejtest(self) -> None:
        """A sav ne maradjon kint orokre, ha a mutato elhagyja."""
        forras = (_QML / "PicasaPy" / "SlideshowView.qml").read_text(
            encoding="utf-8"
        )
        assert "onHoveredChanged" in forras and "hideTimer.restart()" in forras
