"""#2987: a diavetítés a TELJES ablakot töltse ki, ne csak a közepét.

## A mérés, ami az okot adta

A tulajdonos jelentette, hogy a vetítés nem teljesképernyős. A kód
szándéka megvan (`Main.qml` `startSlideshow`: `Window.FullScreen`), tehát
nem az hiányzik. Az ablak `ApplicationWindow`, és három sávot definiál:

| sáv | |
|---|---|
| `menuBar` | `PicasaMenuBar` |
| `header` | `MainToolbar` |
| `footer` | `TrayBar` |

A `SlideshowView` az ablak közvetlen gyermeke, `anchors.fill: parent` —
`ApplicationWindow`-ban ez a **contentItem**-et tölti ki, vagyis a
fejléc ÉS a lábléc KÖZÖTTI sávot, a menüsáv nélkül. Az ablak tehát
teljes képernyőre vált, a vetítés mégis dobozban marad.

⚠️ Ez **platformfüggetlen** — a windowsos megfigyelést is magyarázza.

## Miért nem a `visibility`-t nézi az őr

A jegy külön kimondja: a `window.visibility === FullScreen` állítás
IGAZ volna, miközben a hiba fennáll. Ez a próba ezért a vetítő
MAGASSÁGÁT hasonlítja az ablakéhoz, és a három sáv láthatóságát nézi.
"""

from __future__ import annotations

import numpy as np
import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, Qt

import cv2


def _child(window, nev):
    def walk(item):
        for gy in item.childItems():
            yield gy
            yield from walk(gy)

    for it in walk(window.contentItem()):
        if (it.objectName() or "") == nev:
            return it
    return None


@pytest.fixture
def futo_vetites(qml_app, qt_app, tmp_path):
    window, _controller, _engine = qml_app
    kep = np.full((160, 320, 3), 200, dtype=np.uint8)
    assert cv2.imwrite(str(tmp_path / "kepek" / "a.jpg"), kep)
    window.setProperty("selectedIndex", 0)
    QMetaObject.invokeMethod(
        window,
        "startSlideshow",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", -1),
    )
    qt_app.processEvents()
    vetito = _child(window, "slideshowView")
    assert vetito is not None and vetito.property("visible") is True, (
        "a diavetítés nem indult el"
    )
    yield window, vetito
    # a VALÓDI kilépés útja: a vetítő `stop()`-ja zárja le magát, és a
    # `closed` jelzésre fut az ablak `exitSlideshow`-ja
    QMetaObject.invokeMethod(vetito, "stop", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


class TestATeljesKitoltes:
    def test_a_vetito_MAGASSAGA_az_ablake(self, futo_vetites, qt_app):
        window, vetito = futo_vetites
        qt_app.processEvents()
        assert vetito.height() == window.property("height"), (
            "a vetítés nem tölti ki az ablakot: "
            f"{vetito.height()} px a(z) {window.property('height')} px-ből — "
            "a menüsáv/fejléc/lábléc elveszi a helyet"
        )

    def test_a_HAROM_sav_eltunik(self, futo_vetites, qt_app):
        """Az eredetiben a vetítés alatt semmi más nem látszik (#1903)."""
        window, _vetito = futo_vetites
        qt_app.processEvents()
        latszo = [
            nev
            for nev in ("mainToolbar", "trayBar")
            if (_child(window, nev) is not None
                and _child(window, nev).property("visible") is True)
        ]
        menusav = window.property("menuBar")
        if menusav is not None and menusav.property("visible") is True:
            latszo.append("menuBar")
        assert not latszo, f"a vetítés alatt is látszik: {latszo}"


class TestAVisszaallas:
    def test_kilepes_utan_VISSZAJON_a_harom_sav(self, qml_app, qt_app, tmp_path):
        window, _controller, _engine = qml_app
        kep = np.full((160, 320, 3), 200, dtype=np.uint8)
        assert cv2.imwrite(str(tmp_path / "kepek" / "a.jpg"), kep)
        window.setProperty("selectedIndex", 0)
        QMetaObject.invokeMethod(
            window, "startSlideshow", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", -1),
        )
        qt_app.processEvents()
        #: A vetítő `stop()`-ja a valódi kilépés útja — az ablak
        #: `exitSlideshow`-ja a `closed` jelzésre fut le. (Közvetlenül
        #: hívva a vetítő LÁTHATÓ maradna, és a sávok sem jönnének vissza:
        #: ez nem a termék hibája, hanem rossz próba volna.)
        vetito = _child(window, "slideshowView")
        QMetaObject.invokeMethod(
            vetito, "stop", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        hianyzo = [
            nev
            for nev in ("mainToolbar", "trayBar")
            if (_child(window, nev) is None
                or _child(window, nev).property("visible") is not True)
        ]
        menusav = window.property("menuBar")
        if menusav is None or menusav.property("visible") is not True:
            hianyzo.append("menuBar")
        assert not hianyzo, (
            f"a vetítés után nem jött vissza: {hianyzo}"
        )
