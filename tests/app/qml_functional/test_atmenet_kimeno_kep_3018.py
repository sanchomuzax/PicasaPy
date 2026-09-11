"""#3018: az áttűnés kimenő képe a KÖZVETLENÜL előző dia.

A tulajdonos élesben jelentette: *„Diavetítésnél mindig a két kép váltása
között valami más kép is mintha bevillanna."*

## A mérés, ami az okot adta

Három kép, két váltás — a kimenő dia (`slideshowPrevImage`) forrása:

| lépés | a képernyőn | a kimenő kép VOLT | helyesen |
|---|---|---|---|
| 0 → 1 | `b.jpg` | *(üres)* | `a.jpg` |
| 1 → 2 | `c.jpg` | **`a.jpg`** | `b.jpg` |

Az áttűnés tehát a **két lépéssel korábbi** képet vegyítette be — ez
villant a felhasználónak. Az ok egy fölösleges kettős tároló (`elozoUrl`),
ami egy lépéssel eltolta az értéket; a váltás pillanatában a
`slide.source` MÉG a kimenő képé (a kötés csak a kezelő után fordul át),
tehát azt kell átadni.

## Miért nem forrás-őr

A #433 próbái a QML szövegét nézik (van-e kimenő elem, fátyol, `cut`-ág) —
mind igaz volt, miközben a hiba fennállt. Ez a próba **végiglépteti** a
vetítést, és a tényleges forrásokat olvassa.

⚠️ A vetítő `QQuickView`-ban fut: szülő nélküli elemként a `visible`
effektív értéke hamis marad, és a dia-URL kötése üresen állna — a próba
akkor semmit nem mérne.
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

    def __init__(self, utak):
        super().__init__()
        self._utak = list(utak)

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

    @Slot(int, result=int)
    def rotateAt(self, index):
        return 0

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


class TestAKimenoKep:
    def test_az_ELSO_valtasnal_az_elso_kep_megy_ki(self, vetito):
        gyoker, _modell, qt_app = vetito
        _lep(gyoker, qt_app)
        assert _elem(gyoker, "slideshowImage").property("source").toString().endswith(
            "/k/b.jpg"
        )
        assert _elem(gyoker, "slideshowPrevImage").property(
            "source"
        ).toString().endswith("/k/a.jpg"), "az első áttűnésnek nincs kimenő képe"

    def test_a_MASODIK_valtasnal_a_kozvetlenul_elozo(self, vetito):
        """Ez a hiba magja: a kimenő kép NEM a két lépéssel korábbi."""
        gyoker, _modell, qt_app = vetito
        _lep(gyoker, qt_app)
        _lep(gyoker, qt_app)
        kimeno = _elem(gyoker, "slideshowPrevImage").property("source").toString()
        assert kimeno.endswith("/k/b.jpg"), (
            "az áttűnés nem a közvetlenül előző képet vegyíti, hanem: "
            f"{kimeno} — ez villan be a felhasználónak"
        )

    def test_a_HARMADIK_valtas_utan_is_egyben_marad(self, vetito):
        """Körbeérve (c → a) is a közvetlenül előző menjen ki."""
        gyoker, _modell, qt_app = vetito
        for _ in range(3):
            _lep(gyoker, qt_app)
        assert _elem(gyoker, "slideshowPrevImage").property(
            "source"
        ).toString().endswith("/k/c.jpg")

    def test_a_kimeno_kep_SOSEM_egyezik_a_bejovovel(self, vetito):
        gyoker, _modell, qt_app = vetito
        for _ in range(4):
            _lep(gyoker, qt_app)
            be = _elem(gyoker, "slideshowImage").property("source").toString()
            ki = _elem(gyoker, "slideshowPrevImage").property("source").toString()
            assert be != ki, f"a kimenő és a bejövő kép azonos: {be}"
