"""QML-funkcionális tesztek: #1528 — a vágás „Alaphelyzet” gombja az
ALKALMAZOTT vágást is elveti, nem csak a húzott kijelölést.

**A szemantika bizonyítéka** (nem következtetés): az eredeti Picasa saját
szövegforrása, `referencia/tre-eroforrasok/editpaneltext.tre` 234–235:

    Tooltip editpanel/cropdiscard
    Discards any applied cropping

és a magyar honosítás ugyanerre (`referencia/panel-feliratok-hu.tsv` 4981–
4982): „Alaphelyzet” / „Az összes alkalmazott vágás elvetése". Az eredeti
tehát az ALKALMAZOTT vágást veti el — a mai PicasaPy csak a kijelölést
nullázta.

A kattintás a VEZÉRLŐRE megy (`QTest.mouseClick` az ablakra, a gomb
jelenet-koordinátáin), nem a kezelő közvetlen hívásával: egy közvetlen
hívás akkor is zöld lenne, ha a gomb valójában tiltott vagy takart.

A fájl állapotot (`.picasa.ini`) ír, ezért szándékosan a funkció-szintű
`qml_app` fixture-t használja.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QPoint, QPointF, QRectF, Qt
from PySide6.QtTest import QTest


def _open_viewer(window, qt_app, index=0):
    window.setProperty("viewerOpen", True)
    viewer = window.findChild(QObject, "photoViewer")
    viewer.setProperty("currentIndex", index)
    qt_app.processEvents()
    return viewer


def _child(window, name):
    item = window.findChild(QObject, name)
    assert item is not None, f"{name} nem található"
    return item


def _kozeppont(item) -> QPoint:
    kozep = item.mapToScene(
        QPointF(item.property("width") / 2, item.property("height") / 2)
    )
    return QPoint(round(kozep.x()), round(kozep.y()))


def _kattints(window, item, qt_app) -> None:
    """Valódi egérkattintás a vezérlőre (tiltott gomb nem reagál)."""
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _kozeppont(item),
    )
    qt_app.processEvents()


def _vagas_alkalmazasa(window, qt_app):
    """A vágó-eszköz megnyitása, kijelölés húzása, majd Alkalmaz — a
    `crop64` a mentett láncba kerül."""
    panel = _child(window, "viewerEditorPanel")
    panel.setProperty("cropActive", True)
    qt_app.processEvents()
    overlay = _child(window, "cropOverlay")
    overlay.setProperty("cropRect", QRectF(0.25, 0.25, 0.5, 0.5))
    overlay.setProperty("hasSelection", True)
    qt_app.processEvents()
    # az Alkalmaz gomb (nem az Enter-flow): a néző NEM lép tovább
    _kattints(window, _child(window, "cropApplyButton"), qt_app)
    return panel


def _ini_szoveg(tmp_path) -> str:
    utvonal = tmp_path / "kepek" / ".picasa.ini"
    return utvonal.read_text(encoding="utf-8") if utvonal.exists() else ""


class TestAlaphelyzetElvetiAMentettVagast:
    def test_a_gomb_a_mentett_crop64_et_is_leveszi(self, qml_app, qt_app, tmp_path):
        """A lemezen (`.picasa.ini`) is látszania kell: sem a `filters=`
        láncban `crop64`, sem a Picasa-paritásos `crop=rect64(...)` kulcs."""
        window, _, _ = qml_app
        _open_viewer(window, qt_app)
        panel = _vagas_alkalmazasa(window, qt_app)
        assert "crop64=1," in _ini_szoveg(tmp_path), (
            "az előfeltétel nem áll: az Alkalmaz nem írt crop64-et"
        )

        # a vágó-eszköz újranyitása — a mentett vágás kijelölésként töltődik
        panel.setProperty("cropActive", True)
        qt_app.processEvents()
        _kattints(window, _child(window, "cropResetButton"), qt_app)

        szoveg = _ini_szoveg(tmp_path)
        assert "crop64" not in szoveg, (
            "az „Alaphelyzet” után is maradt crop64 az iniben:\n" + szoveg
        )
        assert "crop=rect64" not in szoveg, (
            "az „Alaphelyzet” után is maradt crop= kulcs az iniben:\n" + szoveg
        )
        assert _child(window, "cropOverlay").property("hasSelection") is False

    def test_alaphelyzet_utan_az_alkalmaz_nem_hozza_vissza(
        self, qml_app, qt_app, tmp_path
    ):
        """Nincs olyan állapot, amelyben az előnézet vágatlan képet mutat,
        de az Alkalmaz meghagyja a vágást."""
        window, _, _ = qml_app
        _open_viewer(window, qt_app)
        panel = _vagas_alkalmazasa(window, qt_app)
        panel.setProperty("cropActive", True)
        qt_app.processEvents()
        _kattints(window, _child(window, "cropResetButton"), qt_app)
        _kattints(window, _child(window, "cropApplyButton"), qt_app)

        assert "crop64" not in _ini_szoveg(tmp_path)
        assert panel.property("cropActive") is False


class TestAGombTiltasa:
    def test_vagatlan_kepen_kijeloles_nelkul_tiltott(self, qml_app, qt_app, tmp_path):
        window, _, engine = qml_app
        _open_viewer(window, qt_app)
        panel = _child(window, "viewerEditorPanel")
        panel.setProperty("cropActive", True)
        qt_app.processEvents()
        gomb = _child(window, "cropResetButton")
        assert gomb.property("enabled") is False, (
            "vágatlan képen, kijelölés nélkül nincs mit alaphelyzetbe állítani"
        )

        _kattints(window, gomb, qt_app)
        edit = engine.rootContext().contextProperty("editController")
        assert edit.property("canUndo") is False, (
            "a tiltott gombra adott kattintás fölösleges undo-lépést tolt"
        )
        assert _ini_szoveg(tmp_path) == "", "tiltott gomb nem írhat inibe"

    def test_puszta_kijelolesnel_engedelyezett(self, qml_app, qt_app):
        """Mentett vágás nélkül is van mit elvetni, ha épp húznak egyet."""
        window, _, _ = qml_app
        _open_viewer(window, qt_app)
        panel = _child(window, "viewerEditorPanel")
        panel.setProperty("cropActive", True)
        qt_app.processEvents()
        overlay = _child(window, "cropOverlay")
        overlay.setProperty("cropRect", QRectF(0.1, 0.1, 0.3, 0.3))
        overlay.setProperty("hasSelection", True)
        qt_app.processEvents()
        assert _child(window, "cropResetButton").property("enabled") is True

    def test_mentett_vagasnal_engedelyezett(self, qml_app, qt_app):
        window, _, _ = qml_app
        _open_viewer(window, qt_app)
        panel = _vagas_alkalmazasa(window, qt_app)
        panel.setProperty("cropActive", True)
        qt_app.processEvents()
        assert _child(window, "cropResetButton").property("enabled") is True


class TestVisszavonhatosag:
    def test_a_visszavonas_gomb_visszahozza_a_vagast(
        self, qml_app, qt_app, tmp_path
    ):
        """#465: a `crop64` a szerkesztési láncban ül, tehát az elvetés a
        MEGLÉVŐ visszavonás-veremmel visszavonható — a Visszavonás gombra
        kattintva, nem a kontroller-metódust hívva."""
        window, _, engine = qml_app
        _open_viewer(window, qt_app)
        panel = _vagas_alkalmazasa(window, qt_app)
        panel.setProperty("cropActive", True)
        qt_app.processEvents()
        _kattints(window, _child(window, "cropResetButton"), qt_app)
        assert "crop64" not in _ini_szoveg(tmp_path)

        edit = engine.rootContext().contextProperty("editController")
        assert edit.property("undoAction") == "crop", (
            "az elvetés nem 'crop' néven került a visszavonás-veremre: "
            + str(edit.property("undoAction"))
        )
        _kattints(window, _child(window, "editUndoButton"), qt_app)
        assert "crop64=1," in _ini_szoveg(tmp_path), (
            "a Visszavonás nem hozta vissza az elvetett vágást"
        )
