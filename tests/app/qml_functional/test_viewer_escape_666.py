"""#666: az Esc az AKTÍV mód-eszközt szakítsa meg, ne a nézőt zárja be.

A vágó-eszköz bekapcsolt állapotában az Esc korábban a **teljes fotónézőt**
bezárta, és a megkezdett vágás elveszett. Az eredetiben az Esc a vágást
vonja vissza (a panel Mégse gombjával azonos hatás), a néző pedig nyitva
marad — a retusálásnál ez a minta már működött (#445).

A logika a `PhotoViewer.handleEscape()` függvényben él, hogy hívható és
mérhető legyen; a billentyű-kötés csak továbbhív. **Mindkettőt őrizzük:** a
viselkedést a valódi ablakon (a néző nyitva marad-e), a kötést a QML forrás
olvasásával — enélkül a függvény helyes maradhatna úgy is, hogy az Esc
közben már nem is hívja meg.
"""

import re
from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, Qt

_QML_PATH = (
    Path(__file__).resolve().parents[3]
    / "src/picasapy/app/qml/PicasaPy/PhotoViewer.qml"
)


def _open_viewer(window, qt_app):
    """Néző megnyitása az első képen; visszaadja a nézőt és a szerkesztőt."""
    window.setProperty("viewerOpen", True)
    viewer = window.findChild(QObject, "photoViewer")
    assert viewer is not None, "photoViewer nem található"
    viewer.setProperty("currentIndex", 0)
    qt_app.processEvents()
    panel = window.findChild(QObject, "viewerEditorPanel")
    assert panel is not None, "viewerEditorPanel nem található"
    return viewer, panel


def _escape(viewer, qt_app):
    """A billentyű-kötés által hívott függvény meghívása."""
    QMetaObject.invokeMethod(viewer, "handleEscape", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


class TestEscapeWithCropActive:
    def test_aktiv_vagasnal_a_nezo_nyitva_marad(self, qml_app, qt_app):
        """Esc aktív vágásnál: a vágás szakad meg, nem a néző zárul be."""
        window, _controller, _engine = qml_app
        viewer, panel = _open_viewer(window, qt_app)
        panel.setProperty("cropActive", True)
        qt_app.processEvents()
        assert panel.property("cropActive") is True

        _escape(viewer, qt_app)

        assert panel.property("cropActive") is False, (
            "az Esc-nek meg kell szakítania a vágást"
        )
        assert window.property("viewerOpen") is True, (
            "a nézőnek NYITVA kell maradnia — a vágás megszakítása nem "
            "jelenti a néző bezárását"
        )

    def test_mod_eszkoz_nelkul_az_esc_bezarja_a_nezot(self, qml_app, qt_app):
        """A korábbi, egyértelmű viselkedés nem romolhat el."""
        window, _controller, _engine = qml_app
        viewer, panel = _open_viewer(window, qt_app)
        assert panel.property("cropActive") is False

        _escape(viewer, qt_app)

        assert window.property("viewerOpen") is False


class TestEscapeBinding:
    def test_a_billentyu_kotes_a_kozos_fuggvenyt_hivja(self):
        """A kötés nem szakadhat el a logikától.

        Ha valaki visszaírja a törzset a `Keys.onEscapePressed`-be, a fenti
        viselkedés-tesztek attól még zöldek maradnának — ezért olvassuk a
        VALÓDI forrást.
        """
        # #6234: a billentyűkezelés a PhotoViewerKeyboard.qml-be költözött, a
        # gazdát `keyboard.hostViewer` néven éri el; a kötés tartalma ugyanaz.
        forras = "\n".join(
            (_QML_PATH.parent / nev).read_text(encoding="utf-8")
            for nev in ("PhotoViewer.qml", "PhotoViewerKeyboard.qml")
        )
        assert re.search(
            r"Keys\.onEscapePressed:\s*\{?\s*if \(!(?:viewer|keyboard\.hostViewer)"
            r"\.textEntryHasFocus\)\s*(?:viewer|keyboard\.hostViewer)\.handleEscape\(\)",
            forras,
        )
        assert "function handleEscape()" in forras
