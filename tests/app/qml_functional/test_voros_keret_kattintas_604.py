"""#604: VALÓDI kattintás a vörösszem-kereten — nem a metódus hívása.

A jegy 5. pontja szó szerint ezt kéri: két régió felvétele → kattintás az
elsőre → a régiószám 1-re csökken, és a megmaradt a második.

Miért így: a `removeRedeyeRegionAt` közvetlen hívása azt mérné, hogy a
vezérlő jól számol — azt a `tests/app/test_voros_keret_torles_604.py` már
méri. Ez a lap a **bekötést** méri: hogy a húzó-terület a puszta kattintást
tényleg törlésnek adja tovább, a helyes normált koordinátákkal.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QEvent, QObject, QPointF, Qt
from PySide6.QtGui import QMouseEvent


def _kattints(qt_app, ablak, elem, x: float, y: float) -> None:
    """Valódi egérkattintás az `elem` LOKÁLIS (x, y) pontján."""
    globalis = elem.mapToScene(QPointF(x, y))
    for tipus in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease):
        qt_app.sendEvent(
            ablak,
            QMouseEvent(
                tipus,
                globalis,
                globalis,
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton
                if tipus == QEvent.Type.MouseButtonPress
                else Qt.MouseButton.NoButton,
                Qt.KeyboardModifier.NoModifier,
            ),
        )
    qt_app.processEvents()


class TestAKeretreKattintas:
    def _elofeltetelek(self, viewer, terulet):
        """A kattintás előfeltételei — ÁLLÍTVA, nem `skip`-pel kihagyva.

        ⚠️ A környezetfüggő `skip` nem őr: az `offscreen` platformon (ezen
        futnak a tesztek helyben ÉS a CI-n is, ld. `tests/app/conftest.py`) a
        húzó-terület mérete és a vezérlő is megvan. Ha valamelyik eltűnik, az
        nem „más környezet", hanem elromlott bekötés — akkor ez a lap
        elbukik, nem hallgat."""
        ctl = viewer.property("editCtl")
        assert ctl is not None, "a szerkesztő-vezérlő nincs bekötve a nézőhöz"
        szel = terulet.property("width")
        mag = terulet.property("height")
        assert szel and mag, (
            f"a húzó-terület mérete {szel}×{mag} — nincs mire kattintani"
        )
        return ctl, szel, mag

    def _eszkoz(self, window, qt_app):
        """Nyitott néző + aktív vörösszem-eszköz, két felvett kerettel."""
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("redeyeActive", True)
        qt_app.processEvents()
        terulet = window.findChild(QObject, "redeyeDragArea")
        assert terulet is not None, "a húzó-terület nincs a fában"
        return viewer, terulet

    def test_a_kattintas_TORLI_a_keretet(self, qml_app, qt_app):
        window, controller, _ = qml_app
        viewer, terulet = self._eszkoz(window, qt_app)
        ctl, szel, mag = self._elofeltetelek(viewer, terulet)
        # két régió a puffer két SARKÁBAN, hogy a kattintás egyértelmű legyen
        ctl.addRedeyeRegion(0.05, 0.05, 0.2, 0.2)
        ctl.addRedeyeRegion(0.70, 0.70, 0.2, 0.2)
        qt_app.processEvents()
        assert ctl.property("redeyeRegionCount") == 2

        _kattints(qt_app, window, terulet, 0.15 * szel, 0.15 * mag)

        assert ctl.property("redeyeRegionCount") == 1
        megmaradt = ctl.property("redeyeRegions")[0]
        assert megmaradt["x"] == pytest.approx(0.70, abs=0.01)

    def test_a_kereten_KIVULI_kattintas_nem_torol(self, qml_app, qt_app):
        window, controller, _ = qml_app
        viewer, terulet = self._eszkoz(window, qt_app)
        ctl, szel, mag = self._elofeltetelek(viewer, terulet)
        ctl.addRedeyeRegion(0.05, 0.05, 0.2, 0.2)
        qt_app.processEvents()

        _kattints(qt_app, window, terulet, 0.9 * szel, 0.9 * mag)

        assert ctl.property("redeyeRegionCount") == 1
