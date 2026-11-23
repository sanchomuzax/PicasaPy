"""#7393 - a Kiegyenesítés újranyitáskor 0-ról indul, az Apply új `tilt` tagot fűz,
és a csúszka fogantyújának KÖZEPE a foglalat teljes 253 képpontját bejárja.

Mérce: picasa-colab-jobs job-913 (gray_ramp.jpg, 1024x256). A PNG-k nincsenek a
repóban; az alábbi számok a képkockákból mért értékek:

* `__16`: az újranyitott eszköz (az alapkép a már kiegyenesített kép), a
  fogantyú közepe 689,5 (a rajz 14 px széles a 16 px-es rétegben: a rajzolt
  közép a logikai közép -1 px-én áll), a foglalat 564..817.
* `__18`: a második húzás (egér x = 640), a fogantyú 638,5-ön; a csúszka
  értéke `(x - 690,5) / 126,5`.
* a záró ini: `filters=tilt=1,0.391249,0.000000;tilt=1,-0.399233,0.000000;`.

A képminták a kép kirajzolt téglalapjának (987 x 247 px) 10 oszlopa x 3 sora
(az oszlopok a szélesség (c + 0,5) / 10-énél, a sorok a magasság 20, 50, 80
%-ánál), mindegyik egy 7 x 7-es blokk mediánja (a szaggatott rács 1 px-es
vonalait a medián elnyeli). A `__8` a kiegyenesítetlen rámpa: kontroll arra,
hogy a próbakép ugyanaz a rámpa, mint a felvételen.

Nincs mérve (nyitott kérdés): a nulla értékű Alkalmaz mit ír az eredetiben. A
jegy szerint ezt nem szabad általánosítani; ez a próba csak a MAI viselkedést
rögzíti (változatlan, 0 értéknél nem keletkezik új tag).
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QSignalSpy, QTest

from tests.app.qml_functional._kiegyenesites_helpers_4058 import (
    _forrasra_var,
    _kep_betoltve,
    _pont,
)
from tests.support.varakozas import var_feltetelre

ABLAK = (1280, 1005)

#: A job-913 foglalata: 253 px, a fogantyú KÖZEPE járja végig; az érték
#: `(x - 690,5) / 126,5`, tehát a helyi x-re `(x - 126,5) / 126,5`.
FOGLALAT = 253
FELE = FOGLALAT / 2
#: A 740-es és a 640-es egérpozíció a foglalat 564-es bal szélétől mérve.
HELYI_740 = 740 - 564
HELYI_640 = 640 - 564
ERTEK_740 = 0.391249
ERTEK_640 = -0.399233

JOB913_MINTA = {
    8: [
        [12, 37, 63, 88, 114, 139, 165, 190, 216, 241],
        [12, 37, 63, 88, 114, 139, 165, 190, 216, 241],
        [12, 37, 63, 88, 114, 139, 165, 190, 216, 241],
    ],
    16: [
        [40, 60, 79, 98, 118, 137, 156, 176, 195, 215],
        [39, 58, 78, 97, 116, 136, 156, 175, 194, 214],
        [38, 57, 77, 96, 116, 135, 154, 173, 193, 212],
    ],
    18: [
        [59, 75, 89, 104, 119, 133, 148, 163, 177, 193],
        [59, 75, 89, 104, 118, 133, 148, 163, 177, 193],
        [59, 75, 89, 104, 119, 133, 148, 163, 177, 193],
    ],
}
OSZLOPOK = [(c + 0.5) / 10 for c in range(10)]
SOROK = [0.2, 0.5, 0.8]
#: A mért legnagyobb eltérés (2 szürkeszint: JPEG-kerekítés és a 0,391304 /
#: 0,391249 szögkülönbség) fölé 1, szándékosan szűken. A "csak az egyik tilt"
#: hibás kép a `__18`-tól 20 szint fölött tér el, a nélküle készült a `__16`-tól
#: 60 fölött.
MINTA_TURES = 3


def _item(gyoker, nev: str):
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található a kirajzolt fában"
    return elem


def _rampa_mentese(utvonal: Path) -> None:
    """A job-913 `gray_ramp.jpg`-je: 1024 x 256, balról jobbra feketéből fehérbe."""
    oszlopok = np.linspace(0, 255, 1024).round().astype(np.uint8)
    kep = np.tile(oszlopok, (256, 1))
    assert cv2.imwrite(str(utvonal), kep, [cv2.IMWRITE_JPEG_QUALITY, 100])


def _feldolgoz(qt_app, darab: int = 5) -> None:
    for _ in range(darab):
        qt_app.processEvents()


def _kattint(window, elem, qt_app) -> None:
    assert elem.width() > 0 and elem.height() > 0, "a vezérlő nem látható"
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _pont(elem, elem.width() / 2, elem.height() / 2),
    )
    _feldolgoz(qt_app)


class Nezo:
    """A megnyitott néző a rámpaképpel: a valódi vezérlőkre kattint."""

    def __init__(self, window, controller, qt_app, tmp_path: Path) -> None:
        self.window = window
        self.qt_app = qt_app
        self.ini = tmp_path / "kepek" / ".picasa.ini"
        _rampa_mentese(Path(str(controller.photos.filePathAt(0))))
        window.setProperty("width", ABLAK[0])
        window.setProperty("height", ABLAK[1])
        _feldolgoz(qt_app)
        window.setProperty("viewerOpen", True)
        self.viewer = _item(window, "photoViewer")
        self.viewer.setProperty("currentIndex", 0)
        _feldolgoz(qt_app, 8)
        self.edit = self.viewer.property("editCtl")
        self.image = _item(window, "viewerImage")
        assert var_feltetelre(qt_app, lambda: _kep_betoltve(self.image), 10.0), (
            "a szerkesztő főképe nem töltődött be"
        )

    # -- az eszköz ----------------------------------------------------------
    def eszkoz_nyit(self) -> None:
        _kattint(self.window, _item(self.window, "editToolTilt"), self.qt_app)
        assert _item(self.window, "viewerEditorPanel").property("tiltActive") is True
        self.slider = _item(self.window, "tiltSlider")
        _feldolgoz(self.qt_app)
        self._helyzet_nyugalomra()

    def _helyzet_nyugalomra(self) -> None:
        """Az eszköztár animálva csúszik be: a lassabb (CI) gépen a csúszka még
        mozog, amikor a próba lenyomná az egeret. Addig várunk, amíg a csúszka
        jelenetbeli helyzete tíz egymás utáni körben nem változik."""
        elozo, nyugodt = None, 0
        for _ in range(400):
            hely = self.slider.mapToScene(QPointF(0, 0))
            most = (round(hely.x(), 1), round(hely.y(), 1))
            nyugodt = nyugodt + 1 if most == elozo else 0
            if nyugodt >= 10:
                return
            elozo = most
            QTest.qWait(10)
        raise AssertionError("a Kiegyenesítés eszköztára nem állt meg")

    def alkalmaz(self) -> None:
        elotte = str(self.edit.property("previewSource"))
        _kattint(self.window, _item(self.window, "tiltApplyButton"), self.qt_app)
        assert self.edit.waitForBackgroundWorkers(10.0)
        _feldolgoz(self.qt_app)
        self.kep_frissul(elotte)

    # -- a csúszka ----------------------------------------------------------
    def foglalat_x(self, helyi_x: float) -> QPoint:
        return _pont(self.slider, helyi_x, self.slider.height() / 2)

    def fogantyu_kozepe(self) -> float:
        """A fogantyú LOGIKAI közepe a csúszka bal szélétől (helyi x)."""
        fogantyu = self.slider.property("handle")
        return float(fogantyu.property("x")) + float(fogantyu.property("width")) / 2

    def ertek(self) -> float:
        return float(self.slider.property("value"))

    def huzas(self, cel_helyi_x: int) -> None:
        """Valódi egéresemény: a fogantyú közepén lenyom, a célig húz, elenged."""
        kezdo = self.foglalat_x(self.fogantyu_kozepe())
        cel = self.foglalat_x(cel_helyi_x)
        elotte = str(self.edit.property("previewSource"))
        QTest.mouseMove(self.window, kezdo, 10)
        QTest.mousePress(
            self.window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, kezdo
        )
        assert var_feltetelre(
            self.qt_app, lambda: self.slider.property("pressed") is True, 3.0
        ), "az egérlenyomás nem érte el a csúszkát"
        lepes = 1 if cel.x() > kezdo.x() else -1
        for x in range(kezdo.x() + lepes, cel.x() + lepes, lepes * 8):
            QTest.mouseMove(self.window, QPoint(x, cel.y()), 5)
        QTest.mouseMove(self.window, cel, 10)
        QTest.mouseRelease(
            self.window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, cel
        )
        assert var_feltetelre(
            self.qt_app, lambda: self.slider.property("pressed") is False, 3.0
        ), "a csúszka nem engedte el az egeret"
        assert self.edit.waitForBackgroundWorkers(10.0)
        _feldolgoz(self.qt_app)
        self.kep_frissul(elotte)

    # -- a kép --------------------------------------------------------------
    def kep_frissul(self, forras_elotte: str) -> None:
        forras = str(self.edit.property("previewSource"))
        if forras != forras_elotte:
            _forrasra_var(self.image, self.qt_app, forras_elotte, forras, "az előnézet")
        frames = QSignalSpy(self.window.frameSwapped)
        self.window.update()
        assert var_feltetelre(self.qt_app, lambda: frames.count() > 0, 3.0), (
            "az új képkocka nem rajzolódott ki"
        )

    def ini_lanc(self) -> str:
        if not self.ini.exists():
            return ""
        for sor in self.ini.read_text(encoding="utf-8").splitlines():
            if sor.startswith("filters="):
                return sor
        return ""

    def tilt_ertekek(self) -> list[float]:
        lanc = self.ini_lanc()[len("filters="):]
        return [
            float(resz.split("=")[1].split(",")[1])
            for resz in lanc.split(";")
            if resz.startswith("tilt=")
        ]

    def kep_minta(self) -> list[list[int]]:
        """A kirajzolt kép 10 x 3-as mintája a felvételek módszerével."""
        kep = self.window.grabWindow()
        assert not kep.isNull()
        szeles = float(self.image.property("paintedWidth"))
        magas = float(self.image.property("paintedHeight"))
        bal = (self.image.width() - szeles) / 2
        felso = (self.image.height() - magas) / 2
        sarok = self.image.mapToScene(QPointF(bal, felso))
        minta = []
        for sor_arany in SOROK:
            sor = []
            for oszlop_arany in OSZLOPOK:
                x = int(sarok.x() + oszlop_arany * szeles)
                y = int(sarok.y() + sor_arany * magas)
                blokk = [
                    kep.pixelColor(xx, yy).red()
                    for yy in range(y - 3, y + 4)
                    for xx in range(x - 3, x + 4)
                ]
                sor.append(int(np.median(blokk)))
            minta.append(sor)
        return minta


@pytest.fixture
def nezo(qml_app_negyzet_kepek, qt_app, tmp_path):
    window, controller, _ = qml_app_negyzet_kepek
    return Nezo(window, controller, qt_app, tmp_path)


def _elteres(minta, referencia) -> int:
    return int(np.max(np.abs(np.asarray(minta) - np.asarray(referencia))))


def test_a_fogantyu_kozepe_a_teljes_253_pixeles_foglalatot_bejarja(nezo):
    """Kész, ha (3), geometria: a fogantyú KÖZEPE a foglalat két szélén áll
    (eddig csak 237 képpontot futott be: a 16 px-es fogantyú fél-fél szélességét
    elvesztette)."""
    nezo.eszkoz_nyit()
    assert nezo.slider.property("width") == FOGLALAT

    nezo.slider.setProperty("value", -1.0)
    _feldolgoz(nezo.qt_app)
    bal = nezo.fogantyu_kozepe()
    nezo.slider.setProperty("value", 1.0)
    _feldolgoz(nezo.qt_app)
    jobb = nezo.fogantyu_kozepe()

    assert bal == pytest.approx(0.0, abs=0.5)
    assert jobb == pytest.approx(FOGLALAT, abs=0.5)
    assert jobb - bal == pytest.approx(FOGLALAT, abs=1.0), (
        f"a fogantyú közepe {jobb - bal} képpontot fut be, a mért 253 helyett"
    )


def test_az_egerrel_a_740_es_x_re_huzva_a_csuszka_erteke_0_3913(nezo):
    """Kész, ha (3): `(x - 690,5) / 126,5`, valódi egéreseménnyel."""
    nezo.eszkoz_nyit()
    assert _item(nezo.window, "editorToolBar").property("scale") == 1.0, (
        "az eszközsáv skálája nem 1: a helyi képpont nem egyezik a felvételével"
    )

    nezo.huzas(HELYI_740)

    assert nezo.ertek() == pytest.approx(0.3913, abs=0.001)
    assert nezo.ertek() == pytest.approx(ERTEK_740, abs=0.001)


def test_a_640_es_x_re_huzva_a_csuszka_erteke_minusz_0_3992(nezo):
    nezo.eszkoz_nyit()

    nezo.huzas(HELYI_640)

    assert nezo.ertek() == pytest.approx(ERTEK_640, abs=0.001)


def test_a_kiegyenesitett_kepen_az_ujranyitott_eszkoz_fogantyuja_kozepen_all(nezo):
    """Kész, ha (1): az Alkalmaz után újranyitva a csúszka 0-n áll, és a
    fogantyú a foglalat közepén (job-913 `__16`: 689,5 a 690,5-ös közép mellett,
    a rajz és a logikai közép 1 px-es különbségével)."""
    nezo.eszkoz_nyit()
    nezo.huzas(HELYI_740)
    nezo.alkalmaz()
    assert nezo.tilt_ertekek() == [pytest.approx(ERTEK_740, abs=0.001)]

    nezo.eszkoz_nyit()

    assert nezo.ertek() == 0.0
    assert nezo.fogantyu_kozepe() == pytest.approx(FELE, abs=1.0)


def test_ket_alkalmaz_utan_ket_tilt_tag_van_az_iniben(nezo):
    """Kész, ha (2): a job-913 mozdulataival (740, majd 640) két tag."""
    nezo.eszkoz_nyit()
    nezo.huzas(HELYI_740)
    nezo.alkalmaz()
    nezo.eszkoz_nyit()
    nezo.huzas(HELYI_640)
    nezo.alkalmaz()

    ertekek = nezo.tilt_ertekek()

    assert ertekek == [
        pytest.approx(ERTEK_740, abs=0.001),
        pytest.approx(ERTEK_640, abs=0.001),
    ], f"a lánc: {nezo.ini_lanc()}"


def test_a_nulla_erteku_alkalmaz_nem_ir_tagot(nezo):
    """Csak a mai viselkedés: változatlan (0) értéknél nincs új tag és új
    Visszavonás-lépés. Az eredeti viselkedése nincs mérve (nyitott kérdés)."""
    nezo.eszkoz_nyit()
    nezo.huzas(HELYI_740)
    nezo.alkalmaz()
    nezo.eszkoz_nyit()
    lanc_elotte = nezo.ini_lanc()

    nezo.alkalmaz()

    assert nezo.ini_lanc() == lanc_elotte
    assert len(nezo.tilt_ertekek()) == 1


def test_a_renderelt_kep_a_job_913_16_es_18_kepkockajaval_egyezik(nezo):
    """Kész, ha (4): az újranyitott eszköz képe a `__16`-tal, a második húzás
    előnézete a `__18`-cal egyezik; a `__8` (a rámpa) a próbakép kontrollja."""
    _feldolgoz(nezo.qt_app, 8)
    kontroll = nezo.kep_minta()
    assert _elteres(kontroll, JOB913_MINTA[8]) <= MINTA_TURES, (
        f"a próbakép nem a felvétel rámpája: {kontroll}"
    )

    nezo.eszkoz_nyit()
    nezo.huzas(HELYI_740)
    nezo.alkalmaz()
    nezo.eszkoz_nyit()
    ujranyitva = nezo.kep_minta()
    nezo.huzas(HELYI_640)
    masodik_huzas = nezo.kep_minta()

    assert _elteres(ujranyitva, JOB913_MINTA[16]) <= MINTA_TURES, (
        f"az újranyitott kép eltér a job-913 __16-tól: {ujranyitva}"
    )
    assert _elteres(masodik_huzas, JOB913_MINTA[18]) <= MINTA_TURES, (
        f"a második húzás előnézete eltér a job-913 __18-tól: {masodik_huzas}"
    )
