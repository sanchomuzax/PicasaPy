"""A „Rács" táblázat maradék vezérlői VALÓDI kattintással (#5135, 3. rész).

Lefedve:
- `timelineThumbMouseArea` - az idővonal bélyegképe megnyitja a nézetet;
- a `moreSuggestionsButton` hiányzik a Név nélküliek albumából, mert a #5183
  eltávolította a közös névsor műveleteit ebből a nézetből.

Kimaradt tételek, ezért NINCS itt teszt (a jegy szerint leírva):
- `faceRegionArea_` (FacesOverlay): csak észlelt arcon él, a teszthez
  arcdetektálás és arc-adat kellene;
- `peoplePanelIgnoreDontAskCheck` (PeoplePanel): a jelölő a „Személy
  figyelmen kívül hagyása" párbeszédben van, amit csak az arc-javaslatok
  teljes fixture-je nyit (a 4573-as teszt egy hosszú függvényben építi);
- `dropGeotagCancelButton` (Main.qml): a párbeszédet térkép-húzás nyitja,
  amihez a 4583-as teszt helyi próba-térképet épít.
"""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, Qt, Slot
from PySide6.QtQuick import QQuickWindow

from test_racs_vezerlok_valodi_5135 import _kattints_elemre, _varj, _vizualis
from test_unnamed_faces_view import _StubFaceScanController, _make_view


class _Keresoes(_StubFaceScanController):
    """A stub kiegészítve a „További javaslatok" hívásával."""

    @Slot()
    def moreSuggestions(self):
        self.calls.append(("moreSuggestions",))


class TestIdovonalBelyeg:
    def test_a_belyegkep_valodi_kattintasra_megnyitja_a_nezot(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        window.show()
        window.requestActivate()
        QMetaObject.invokeMethod(window, "toggleTimeline", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        assert _varj(qt_app, lambda: window.property("timelineOpen") is True)
        assert _varj(qt_app, lambda: _vizualis(window, "timelineThumbMouseArea") is not None)
        belyeg = _vizualis(window, "timelineThumbMouseArea")

        _kattints_elemre(qt_app, window, belyeg)

        assert _varj(qt_app, lambda: window.property("viewerOpen") is True), (
            "a bélyegkép kattintás nem nyitotta meg a nézetet"
        )
        assert window.property("timelineOpen") is False
        assert controller.currentFolder != ""


class TestTovabbiJavaslatok:
    def test_a_kozos_javaslatgomb_nem_latszik_a_nevnelkuliek_albumaban(
        self, qt_app
    ):
        keresoes = _Keresoes()
        view = _make_view(qt_app, controller=keresoes)
        ablak = QQuickWindow()
        ablak.resize(480, 360)
        view.setParentItem(ablak.contentItem())
        view.setWidth(480)
        view.setHeight(360)
        ablak.show()
        ablak.requestActivate()
        qt_app.processEvents()

        gomb = _vizualis(ablak, "moreSuggestionsButton")
        assert gomb is not None and not gomb.isVisible(), (
            "a közös További javaslatok gomb még látszik a Név nélküliek albumában"
        )
        ablak.close()
