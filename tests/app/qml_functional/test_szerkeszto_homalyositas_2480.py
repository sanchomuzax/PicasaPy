"""#2480 — a szerkesztő modális párbeszédei mögött elhomályosító réteg áll.

Az eredetiben erre külön réteg van: `editpanel/modaldialogblur`
(`editpanel.tre:1362`) — a `root` közvetlen gyereke (tehát a TELJES
szerkesztő fölé kerül, nem a bal panelen belülre), `m_scaleXY` (a teljes
vászonra feszül) és `m_hidden` (alapból rejtett).

⚠️ **Mérve (2026-09-11), mielőtt bármit építettem:** a Qt Quick Controls
`Fusion` stílusa nálunk NEM ad elhomályosítást a modális párbeszéd mögé — a
felépült fában a `QQuickOverlay` alatt csak a párbeszéd `QQuickPopupItem`-je
áll, homályosító réteg nincs. A jegy grep-alapú állítása tehát a rajzolt fán
is igaz.

⚠️ Amit ez az őr NEM mér: a homályosítás MÉRTÉKÉT és SZÍNÉT. Azt a
`respack.yt` rétege adná meg, ami nincs kimérve — a választott érték a mi
döntésünk, és a `PhotoViewer.qml` kommentje kimondja.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject

import picasapy.app

def _nyisd_meg_a_nezot(window, qt_app):
    """A nézőt TÉNYLEGESEN megnyitja.

    ⚠️ Zárt nézőben a réteg `visible`-je kötéstől függetlenül hamis: a Qt a
    TÉNYLEGES láthatóságot adja vissza, és egy rejtett ős minden gyerekét
    rejtettnek jelenti (a `test_viewer_context_menu.py` ugyanezt a csapdát
    kerüli meg). Enélkül az őr a saját vakságát mérné."""
    window.setProperty("viewerOpen", True)
    qt_app.processEvents()


_VIEWER = (
    Path(picasapy.app.__file__).parent
    / "qml" / "PicasaPy" / "PhotoViewer.qml"
).read_text(encoding="utf-8")


class TestARetegMegvan:
    def test_a_reteg_ott_van_a_faban(self, qml_app, qt_app):
        window, _c, _e = qml_app
        assert window.findChild(QObject, "editorModalDialogBlur") is not None, (
            "nincs elhomályosító réteg a szerkesztőben (#2480)"
        )

    def test_alapbol_REJTETT(self, qml_app, qt_app):
        """`m_hidden`: a réteget a modális párbeszéd kapcsolja be. A NYITOTT
        nézőben mérjük, különben a rejtett ős miatt lenne hamis."""
        window, _c, _e = qml_app
        _nyisd_meg_a_nezot(window, qt_app)
        reteg = window.findChild(QObject, "editorModalDialogBlur")
        assert reteg.property("visible") is False

    def test_a_TELJES_nezore_feszul(self, qml_app, qt_app):
        """`m_scaleXY` + a `root` gyereke: a bal panel ÉS az előnézet is alá
        esik, nem csak a panel."""
        window, _c, _e = qml_app
        reteg = window.findChild(QObject, "editorModalDialogBlur")
        nezo = window.findChild(QObject, "photoViewer")
        assert nezo is not None
        assert reteg.property("width") == nezo.property("width")
        assert reteg.property("height") == nezo.property("height")

    def test_NEM_nyel_el_esemenyt(self):
        """A modalitást a Qt adja (`modal: true`); egy eseményt elnyelő réteg
        a párbeszéd bezárása utáni első kattintást is elvinné."""
        kezd = _VIEWER.index('objectName: "editorModalDialogBlur"')
        assert "enabled: false" in _VIEWER[kezd : kezd + 400]


class TestAKapcsolas:
    def test_a_lathatosag_a_parbeszed_nyitottsagat_koveti(self, qml_app, qt_app):
        window, _c, _e = qml_app
        _nyisd_meg_a_nezot(window, qt_app)
        reteg = window.findChild(QObject, "editorModalDialogBlur")
        panel = window.findChild(QObject, "viewerEditorPanel")
        assert panel is not None

        assert reteg.property("visible") is False
        parbeszed = window.findChild(QObject, "deleteCustomAspectConfirmDialog")
        assert parbeszed is not None, "nincs meg a szerkesztő megerősítő párbeszéde"
        parbeszed.setProperty("visible", True)
        qt_app.processEvents()

        assert panel.property("modalDialogOpen") is True
        assert reteg.property("visible") is True, (
            "a párbeszéd nyitva, a réteg mégsem látszik (#2480)"
        )

        parbeszed.setProperty("visible", False)
        qt_app.processEvents()
        assert reteg.property("visible") is False, (
            "a réteg a párbeszéd bezárása után is ott maradt"
        )

    def test_a_forrasban_a_MERT_elem_van_megnevezve(self):
        """A komment sem hazudhat: a réteg eredete nevesítve áll."""
        kezd = _VIEWER.index('objectName: "editorModalDialogBlur"')
        blokk = _VIEWER[max(0, kezd - 1600) : kezd]
        assert "editpanel/modaldialogblur" in blokk
        assert "m_scaleXY" in blokk
        assert "m_hidden" in blokk
