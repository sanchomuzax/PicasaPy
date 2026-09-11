"""#3023: a kimenő dia ÁTVESZI a bejövő geometriáját.

A tulajdonos élesben jelentette: *„A diavetítésnél az éppen eltűnő kép egy
picit kisebb lesz, emiatt ugrálás hatás van."*

## A mérés, ami az okot adta

Az áttűnés alatt két elem van a képernyőn: a bejövő dia
(`slideshowImage`) és a kimenő másolata (`slideshowPrevImage`). A másolat
NEM vette át a bejövő geometriáját:

| tulajdonság | a bejövő dia | a kimenő másolat (a hiba előtt) |
|---|---|---|
| `scale` | „Pásztázás és nagyítás" alatt 1,0 → 1,08 | mindig 1,0 |
| `rotation` | az ini `rotate(N)` szerint | nincs |
| szélesség/magasság | álló elforgatásnál felcserélve | a nézet mérete |

A váltás pillanatában tehát a látott kép **visszaugrott** alapméretre —
ez a jelentett ugrálás.

## Miért viselkedési próba

A #433 és a #3018 őrei a forrásokat és a QML szövegét nézik; a geometria
mindkettőben rendben volt. Ez a próba a két elem tulajdonságait a váltás
UTÁN **összehasonlítja**, tehát a méret-visszaugrást méri, nem számolja.

⚠️ A vetítő `QQuickView`-ban fut: szülő nélküli elemként a `visible`
effektív értéke hamis marad, és a dia-URL kötése üresen állna.
"""


from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import (
    Property,
    Q_ARG,
    QMetaObject,
    QObject,
    Qt,
    QUrl,
    Signal,
    Slot,
)
from PySide6.QtQuick import QQuickView

_QML = Path(picasapy.app.__file__).parent / "qml"


class _Modell(QObject):
    """Három fotó — a vetítőnek ennyi kell."""

    revisionChanged = Signal()

    def __init__(self, utak, forgatas: int = 0):
        super().__init__()
        self._utak = list(utak)
        self.forgatas = int(forgatas)

    @Property(int, notify=revisionChanged)
    def revision(self):
        return 0

    @Slot(result=int)
    def rowCount(self):
        return len(self._utak)

    @Slot(int, result=bool)
    def isVideoAt(self, index):
        return False

    @Slot(int, str, result=str)
    def displayUrlAt(self, index, mod):
        return "file://" + self._utak[index] if 0 <= index < len(self._utak) else ""

    #: #3023: a próba beállíthatja, hogy a modell forgatást jelentsen —
    #: az elforgatott dia geometriáját külön mérjük
    @Slot(int, result=int)
    def rotateAt(self, index):
        return self.forgatas

    @Slot(int, result=bool)
    def starAt(self, index):
        return False

    @Slot(int, result=str)
    def filePathAt(self, index):
        return self._utak[index] if 0 <= index < len(self._utak) else ""

    @Slot(int, result=str)
    def captionAt(self, index):
        return ""


@pytest.fixture
def vetito(qt_app):
    nezet = QQuickView()
    nezet.engine().addImportPath(str(_QML))
    nezet.setSource(
        QUrl.fromLocalFile(str(_QML / "PicasaPy" / "SlideshowView.qml"))
    )
    assert nezet.status() == QQuickView.Status.Ready, [
        hiba.toString() for hiba in nezet.errors()
    ]
    gyoker = nezet.rootObject()
    nezet.show()
    qt_app.processEvents()
    #: a modellt a PRÓBA tartja életben — referencia nélkül a QML-ből
    #: „nem függvény" hibával esne ki (mérve)
    modell = _Modell(["/k/a.jpg", "/k/b.jpg", "/k/c.jpg"])
    gyoker.setProperty("photosModel", modell)
    gyoker.setProperty("transitionKind", "dissolve")
    QMetaObject.invokeMethod(
        gyoker, "start", Qt.ConnectionType.DirectConnection, Q_ARG("QVariant", 0)
    )
    qt_app.processEvents()
    assert gyoker.property("visible") is True, "a vetítő nem indult el"
    yield gyoker, modell, qt_app
    nezet.deleteLater()


def _elem(gyoker, nev: str):
    for gyerek in gyoker.children():
        if (gyerek.objectName() or "") == nev:
            return gyerek
    raise AssertionError(f"nincs meg: {nev}")


def _lep(gyoker, qt_app):
    QMetaObject.invokeMethod(gyoker, "advance", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


class TestAKimenoGeometria:
    """A kimenő másolat ugyanúgy álljon, ahogy a néző az előbb látta."""

    def test_a_NAGYITAS_atkerul_a_kimeno_masolatra(self, vetito):
        """A „Pásztázás és nagyítás" magja: a másolat ne 1,0-n induljon."""
        gyoker, _modell, qt_app = vetito
        gyoker.setProperty("transitionKind", "kenburns")
        dia = _elem(gyoker, "slideshowImage")
        dia.setProperty("scale", 1.08)
        qt_app.processEvents()
        _lep(gyoker, qt_app)
        kimeno = _elem(gyoker, "slideshowPrevImage")
        assert abs(kimeno.property("scale") - 1.08) < 1e-6, (
            "a kimenő másolat alapméretre ugrott vissza: "
            f"scale={kimeno.property('scale')} a látott 1,08 helyett"
        )

    def test_a_BEJOVO_dia_a_nagyitas_elejerol_indul(self, vetito):
        """Különben a következő dián nincs pásztázás, csak a maradék méret."""
        gyoker, _modell, qt_app = vetito
        gyoker.setProperty("transitionKind", "kenburns")
        dia = _elem(gyoker, "slideshowImage")
        dia.setProperty("scale", 1.08)
        qt_app.processEvents()
        _lep(gyoker, qt_app)
        assert abs(dia.property("scale") - 1.0) < 1e-3, (
            f"a bejövő dia nagyítása beragadt: {dia.property('scale')}"
        )

    def test_az_ELFORGATAS_atkerul(self, vetito):
        gyoker, modell, qt_app = vetito
        modell.forgatas = 1
        modell.revisionChanged.emit()
        qt_app.processEvents()
        _lep(gyoker, qt_app)
        dia = _elem(gyoker, "slideshowImage")
        kimeno = _elem(gyoker, "slideshowPrevImage")
        assert dia.property("rotation") == 90, "a próba elrontotta a beállítást"
        assert kimeno.property("rotation") == 90, (
            "a kimenő másolat elfordulás nélkül jelenik meg: "
            f"{kimeno.property('rotation')}°"
        )

    def test_az_elforgatott_dia_MERETE_is_atkerul(self, vetito):
        """Álló elforgatásnál a szélesség/magasság fel van cserélve.

        A nézetnek MÉRETET adunk: nulla méretű szülő mellett mindkét elem
        0×0 volna, és a próba akkor semmit nem mérne."""
        gyoker, modell, qt_app = vetito
        gyoker.setProperty("width", 800)
        gyoker.setProperty("height", 600)
        modell.forgatas = 1
        modell.revisionChanged.emit()
        qt_app.processEvents()
        _lep(gyoker, qt_app)
        dia = _elem(gyoker, "slideshowImage")
        kimeno = _elem(gyoker, "slideshowPrevImage")
        assert (dia.property("width"), dia.property("height")) == (600, 800), (
            "a próba nem mér: a dia nem cserélte fel a méretét"
        )
        assert (kimeno.property("width"), kimeno.property("height")) == (
            dia.property("width"), dia.property("height")
        ), "a kimenő másolat mérete eltér a látott diától"

    def test_forgatas_NELKUL_is_egyezik_a_ket_elem(self, vetito):
        """Regresszió: a sima eset se boruljon fel."""
        gyoker, _modell, qt_app = vetito
        _lep(gyoker, qt_app)
        dia = _elem(gyoker, "slideshowImage")
        kimeno = _elem(gyoker, "slideshowPrevImage")
        assert (kimeno.property("width"), kimeno.property("height"),
                kimeno.property("rotation"), kimeno.property("scale")) == (
            dia.property("width"), dia.property("height"),
            dia.property("rotation"), dia.property("scale"))
