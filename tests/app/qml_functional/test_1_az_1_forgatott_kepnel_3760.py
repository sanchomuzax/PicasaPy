"""#3760: az 1:1 nagyítás elforgatott képnél túlnagyít.

## A hiba

`PhotoViewer.qml` `actualZoomFactor()`-a a `kep.paintedWidth`-et (a kép
elemének forgatás ELŐTTI, tehát a `rotation:`-transzformáció alatti
koordinátájában értendő festett szélessége) forgatott képnél
(`iniSteps % 2`) a fájl MAGASSÁGÁVAL osztotta — holott a
`Image.PreserveAspectFit` illesztés a betöltött (forgatatlan) kép saját
arányát követi, tehát a `paintedWidth` a forgatástól FÜGGETLENÜL a fájl
SZÉLESSÉGÉVEL arányos. Egy 300×500-as, 90°-kal elforgatott képnél az
„1:1" a valós 1,04-szeres helyett 1,73-szorosra nagyított.

## Miért mérünk KÜLÖN a #2492 és #3741 próbáitól

A #2563 leképezés-őrei (`test_nagyitas_lekepezes_2492.py`) az `r`-t a FUTÓ
kódtól kérdezik — egy rossz `r` mellett is zöldek maradnának, ahogy a #2492
esetében is történt. Ez az őr a MODELLBŐL ismert fájlméretet (nem a
futó `actualZoomFactor()`-t) veti össze a jelenet-koordinátában, forgatás
UTÁN mért képpontokkal — tehát a rossz képlet itt NEM tudja önmagát
igazolni.
"""

from __future__ import annotations

import cv2
import numpy as np
import pytest
from PySide6.QtCore import QMetaObject, QObject, QPointF, Q_ARG, Qt
from PySide6.QtTest import QTest

from tests.app.qml_functional.conftest import _build_qml_app

#: portrét kép, jól megkülönböztethető szélesség/magasság — a próba épp
#: azt méri, hogy a kettő ne cserélődjön fel rosszul
FAJL_SZELESSEG = 300
FAJL_MAGASSAG = 500


def _kep_keszit(lib, *, forgatas_lepes: int) -> None:
    kep = np.full((FAJL_MAGASSAG, FAJL_SZELESSEG, 3), (60, 120, 200), np.uint8)
    cv2.imwrite(str(lib / "a.jpg"), kep, [cv2.IMWRITE_JPEG_QUALITY, 95])
    (lib / ".picasa.ini").write_text(
        f"[a.jpg]\nrotate=rotate({forgatas_lepes})\n", encoding="utf-8"
    )


@pytest.fixture(params=[1, 3], ids=["90fok", "270fok"])
def forgatott_nezo(request, qt_app, tmp_path):
    lepes = request.param
    gen = _build_qml_app(
        qt_app, tmp_path,
        kepeket_keszit=lambda lib: _kep_keszit(lib, forgatas_lepes=lepes),
    )
    window, _controller, _engine = next(gen)
    window.resize(1280, 1024)
    window.show()
    for _ in range(20):
        qt_app.processEvents()
    window.setProperty("viewerOpen", True)
    qt_app.processEvents()
    nezo = window.findChild(QObject, "photoViewer")
    assert nezo is not None
    QMetaObject.invokeMethod(
        nezo, "show", Qt.ConnectionType.DirectConnection, Q_ARG("QVariant", 0)
    )
    QTest.qWait(300)
    yield window, nezo, lepes
    try:
        next(gen)
    except StopIteration:
        pass


def _hivd(qt_app, obj, nev, *args):
    QMetaObject.invokeMethod(
        obj, nev, Qt.ConnectionType.DirectConnection,
        *[Q_ARG("QVariant", a) for a in args],
    )
    qt_app.processEvents()


def _kirajzolt_meret_jelenetben(kep) -> tuple[float, float]:
    """A ténylegesen kirajzolt kép (letterboxolt, elforgatott, nagyított)
    befoglaló mérete JELENET-koordinátában — a `mapToScene` a `rotation:`
    és a `scale:` transzformációt is követi, tehát ez a KÉPERNYŐN valóban
    elfoglalt terület, nem egy újraszámolt képlet."""
    szel = kep.property("width")
    mag = kep.property("height")
    pszel = kep.property("paintedWidth")
    pmag = kep.property("paintedHeight")
    bal_felso = kep.mapToScene(
        QPointF((szel - pszel) / 2, (mag - pmag) / 2)
    )
    jobb_also = kep.mapToScene(
        QPointF((szel - pszel) / 2 + pszel, (mag - pmag) / 2 + pmag)
    )
    return (
        abs(jobb_also.x() - bal_felso.x()),
        abs(jobb_also.y() - bal_felso.y()),
    )


class TestAzEgyAzEgyForgatottKepen:
    def test_1_1_nel_a_kirajzolt_terulet_a_valodi_keppontszam(
        self, forgatott_nezo, qt_app
    ):
        """Kész-ha #1: 1:1-nél elforgatott képen is egy fájlképpont = egy
        képernyőképpont. `iniSteps % 2` esetén a doboz oldalai
        felcserélődnek, tehát a KÉPERNYŐN a szélesség a fájl
        MAGASSÁGÁNAK, a magasság a fájl SZÉLESSÉGÉNEK felel meg."""
        window, nezo, _lepes = forgatott_nezo
        kep = window.findChild(QObject, "viewerImage")
        assert kep is not None
        assert kep.property("rotation") in (90, 270)

        _hivd(qt_app, nezo, "zoomActual")

        szel, mag = _kirajzolt_meret_jelenetben(kep)
        assert szel == pytest.approx(FAJL_MAGASSAG, abs=2.0), (
            f"a kirajzolt szélesség {szel:.1f}, a fájl magassága "
            f"({FAJL_MAGASSAG}) helyett"
        )
        assert mag == pytest.approx(FAJL_SZELESSEG, abs=2.0), (
            f"a kirajzolt magasság {mag:.1f}, a fájl szélessége "
            f"({FAJL_SZELESSEG}) helyett"
        )

    def test_a_400_szazalek_is_a_valodi_meret_negyszerese(
        self, forgatott_nezo, qt_app
    ):
        """Regresszió-őr a csúszka felső végére — ugyanaz a `r`-hiba a
        400 %-os végállást is elrontaná."""
        window, nezo, _lepes = forgatott_nezo
        kep = window.findChild(QObject, "viewerImage")

        _hivd(qt_app, nezo, "setZoomValue", 1.0)

        szel, mag = _kirajzolt_meret_jelenetben(kep)
        assert szel == pytest.approx(4 * FAJL_MAGASSAG, rel=0.02)
        assert mag == pytest.approx(4 * FAJL_SZELESSEG, rel=0.02)


class TestForgatasNelkulValtozatlan:
    def test_forgatas_nelkul_a_kepponthoz_valtozatlan(self, qt_app, tmp_path):
        """Kész-ha #2: forgatás nélkül a régóta zöld #2492-viselkedés nem
        romolhat el."""
        gen = _build_qml_app(
            qt_app, tmp_path,
            kepeket_keszit=lambda lib: _kep_keszit(lib, forgatas_lepes=0),
        )
        window, _controller, _engine = next(gen)
        window.resize(1280, 1024)
        window.show()
        for _ in range(20):
            qt_app.processEvents()
        window.setProperty("viewerOpen", True)
        qt_app.processEvents()
        nezo = window.findChild(QObject, "photoViewer")
        QMetaObject.invokeMethod(
            nezo, "show", Qt.ConnectionType.DirectConnection, Q_ARG("QVariant", 0)
        )
        QTest.qWait(300)
        kep = window.findChild(QObject, "viewerImage")
        assert kep.property("rotation") == 0

        _hivd(qt_app, nezo, "zoomActual")

        szel, mag = _kirajzolt_meret_jelenetben(kep)
        assert szel == pytest.approx(FAJL_SZELESSEG, abs=2.0)
        assert mag == pytest.approx(FAJL_MAGASSAG, abs=2.0)
        try:
            next(gen)
        except StopIteration:
            pass
