"""#3651: a „Szerkesztés jóváhagyása" kérdés a kettős nézet „aa"/„ab"
módjába LÉPÉSKOR, ha egy modális eszköz (Vágás/Retusálás/Szöveg/Vörösszem)
nyitva ÉS módosult.

## A mérés (`docs/specs/ui-audit-editor.md` 4/b.1 2. lépés + 3/c szakasz)

A `0x0056a260` (belépés „aa"/„ab" módba) a 2-up kilépési létra (4/b, #3644)
UTÁN hívja a `0x005f8d80` kaput — ez a `CThumbUI::ConfirmAbandonModifiedEdit*`
párbeszéd (`IDS_ENDEDITMODALITY_*`):

| elem | hivatalos magyar |
|---|---|
| cím | Szerkesztés jóváhagyása |
| szöveg | Elfogadja az aktuális kép módosításait? |
| 0. gomb | Módosítások alkalmazása |
| 1. gomb | Módosítások elvetése |
| 2. gomb | Mégse |
| jelölő | Ne kérdezzen újból, mindig fogadja el a módosításokat |

Mégsére a módváltás elmarad, az eszköz nyitva marad. A teszt VALÓDI
kattintással nyomja a gombokat (`QTest.mouseClick` a jelenet-koordinátákon),
nem a kezelő közvetlen hívásával.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QPoint, QPointF, QRectF, Qt
from PySide6.QtTest import QTest

_KULCS = "DoNotAskOnEndEditModality"


def _gyerek(gyoker, nev):
    objektum = gyoker.findChild(QObject, nev)
    assert objektum is not None, f"{nev} nem található"
    return objektum


def _nezot_nyit(window, qt_app):
    window.setProperty("viewerOpen", True)
    viewer = _gyerek(window, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    qt_app.processEvents()
    return viewer


def _kattints(window, qt_app, nev):
    """Valódi egérkattintás a vezérlő közepére."""
    elem = _gyerek(window, nev)
    kozep = elem.mapToScene(
        QPointF(elem.property("width") / 2, elem.property("height") / 2)
    )
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def _parbeszed(window):
    return _gyerek(window, "endEditModalityDialog")


def _nyitva(window) -> bool:
    return _parbeszed(window).property("opened") is True


def _vagast_nyit_modositva(window, qt_app):
    """A vágó-eszköz megnyitása, húzott (de nem alkalmazott) kijelöléssel."""
    panel = _gyerek(window, "viewerEditorPanel")
    panel.setProperty("cropActive", True)
    qt_app.processEvents()
    overlay = _gyerek(window, "cropOverlay")
    overlay.setProperty("cropRect", QRectF(0.25, 0.25, 0.5, 0.5))
    overlay.setProperty("hasSelection", True)
    qt_app.processEvents()
    return panel, overlay


class TestAFeltetel:
    def test_modositatlan_vagasnal_nincs_kerdes(self, qml_app, qt_app):
        """Nyitott, de kijelölés NÉLKÜLI vágás — nincs mit menteni, a
        módváltás kérdés nélkül megy át (a nyitott eszköz sorsa a
        fókuszváltás lezáró kapujáé, #3686 — ez a jegy csak a kérdést adja)."""
        window, _controller, _engine = qml_app
        _nezot_nyit(window, qt_app)
        panel = _gyerek(window, "viewerEditorPanel")
        panel.setProperty("cropActive", True)
        qt_app.processEvents()

        _kattints(window, qt_app, "viewerLayoutAa")

        assert not _nyitva(window)
        assert _gyerek(window, "photoViewer").property("layoutMode") == "aa"

    def test_eszkoz_nelkul_nincs_kerdes(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _nezot_nyit(window, qt_app)

        _kattints(window, qt_app, "viewerLayoutAa")

        assert not _nyitva(window)
        assert _gyerek(window, "photoViewer").property("layoutMode") == "aa"

    def test_modositott_vagasnal_megjelenik_a_kerdes(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _nezot_nyit(window, qt_app)
        _vagast_nyit_modositva(window, qt_app)

        _kattints(window, qt_app, "viewerLayoutAa")

        assert _nyitva(window)
        # a módváltás a válaszig várakozik
        assert _gyerek(window, "photoViewer").property("layoutMode") == "1up"

    def test_a_cim_es_a_szoveg_hivatalos(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _nezot_nyit(window, qt_app)
        _vagast_nyit_modositva(window, qt_app)

        _kattints(window, qt_app, "viewerLayoutAa")

        parbeszed = _parbeszed(window)
        assert parbeszed.property("title") == "Confirm Edit"
        uzenet = _gyerek(window, "endEditModalityUzenet")
        assert uzenet.property("text") == "Apply changes to the current image?"


class TestAValaszok:
    def test_alkalmaz_menti_a_vagast_es_belep_a_modba(
        self, qml_app, qt_app, tmp_path
    ):
        window, _controller, _engine = qml_app
        nezo = _nezot_nyit(window, qt_app)
        panel, _overlay = _vagast_nyit_modositva(window, qt_app)
        _kattints(window, qt_app, "viewerLayoutAa")
        assert _nyitva(window)

        _kattints(window, qt_app, "endEditModalityApplyButton")

        assert not _nyitva(window)
        assert nezo.property("layoutMode") == "aa"
        assert panel.property("cropActive") is False
        ini = tmp_path / "kepek" / ".picasa.ini"
        assert "crop64=1," in ini.read_text(encoding="utf-8")

    def test_elvet_eldobja_a_vagast_es_belep_a_modba(self, qml_app, qt_app, tmp_path):
        window, _controller, _engine = qml_app
        nezo = _nezot_nyit(window, qt_app)
        panel, _overlay = _vagast_nyit_modositva(window, qt_app)
        _kattints(window, qt_app, "viewerLayoutAa")
        assert _nyitva(window)

        _kattints(window, qt_app, "endEditModalityDiscardButton")

        assert not _nyitva(window)
        assert nezo.property("layoutMode") == "aa"
        assert panel.property("cropActive") is False
        ini = tmp_path / "kepek" / ".picasa.ini"
        szoveg = ini.read_text(encoding="utf-8") if ini.exists() else ""
        assert "crop64" not in szoveg

    def test_megse_utan_a_mod_marad_es_az_eszkoz_nyitva(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _nezot_nyit(window, qt_app)
        panel, overlay = _vagast_nyit_modositva(window, qt_app)
        _kattints(window, qt_app, "viewerLayoutAa")
        assert _nyitva(window)

        _kattints(window, qt_app, "endEditModalityCancelButton")

        assert not _nyitva(window)
        assert nezo.property("layoutMode") == "1up"
        assert panel.property("cropActive") is True
        assert overlay.property("hasSelection") is True
        # és a következő belépés ismét kérdez
        _kattints(window, qt_app, "viewerLayoutAa")
        assert _nyitva(window)


class TestANeKerdezzenJelolo:
    def test_a_jelolo_elnyomja_a_kovetkezot_es_alkalmaz(
        self, qml_app, qt_app, tmp_path
    ):
        window, _controller, _engine = qml_app
        engine = _engine
        beallitas = engine.rootContext().contextProperty("confirmSettings")
        nezo = _nezot_nyit(window, qt_app)
        panel, _overlay = _vagast_nyit_modositva(window, qt_app)
        _kattints(window, qt_app, "viewerLayoutAa")

        _kattints(window, qt_app, "endEditModalityNeKerdezzenCheck")
        _kattints(window, qt_app, "endEditModalityDiscardButton")

        assert beallitas.isSuppressed(_KULCS)
        assert nezo.property("layoutMode") == "aa"

        # visszalépés 1up-ra, majd új vágás — MOSTANTÓL kérdés nélkül
        # alkalmaz (a jelző nem az imént ELVETETT választ ismétli)
        _kattints(window, qt_app, "viewerLayoutOnly1up")
        _vagast_nyit_modositva(window, qt_app)

        _kattints(window, qt_app, "viewerLayoutAb")

        assert not _nyitva(window)
        assert panel.property("cropActive") is False
        ini = tmp_path / "kepek" / ".picasa.ini"
        assert "crop64=1," in ini.read_text(encoding="utf-8")

    def test_a_jelolo_MEGSEVEL_nem_ir(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        beallitas = _engine.rootContext().contextProperty("confirmSettings")
        _nezot_nyit(window, qt_app)
        _vagast_nyit_modositva(window, qt_app)
        _kattints(window, qt_app, "viewerLayoutAa")

        _kattints(window, qt_app, "endEditModalityNeKerdezzenCheck")
        _kattints(window, qt_app, "endEditModalityCancelButton")

        assert not beallitas.isSuppressed(_KULCS)
