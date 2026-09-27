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
| jelölő | Ne kérdezzen újból, mindig fogadja el a módosításokat |

Mégse gomb NINCS: a belépés a kaput `0x005f8d80(this, 1, 0, 0)` alakban
hívja, és a Mégse csak nem nulla 4. argumentumnál kerül a párbeszédbe
(`0x005f8e36`, 3/c 2. pont). Ha nincs mit kérdezni, a nyitott eszköz akkor
is lezárul, elvetéssel (3/c 2. pont).

A „módosult" a Vágásnál azt jelenti, hogy a kijelölés eltér a megnyitáskor
betöltöttől — egy már vágott kép érintetlen Vágás-eszköze nem módosult.

A teszt VALÓDI kattintással nyomja a gombokat (`QTest.mouseClick` a
jelenet-koordinátákon), nem a kezelő közvetlen hívásával.
"""

from __future__ import annotations

import pytest
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
    _kijelol(overlay, qt_app, QRectF(0.25, 0.25, 0.5, 0.5))
    return panel, overlay


def _kijelol(overlay, qt_app, teglalap):
    overlay.setProperty("cropRect", teglalap)
    overlay.setProperty("hasSelection", True)
    qt_app.processEvents()


def _eszkozt_nyit_kattintva(window, qt_app, gomb, allapot):
    """Az eszköz megnyitása a csempéjére kattintva (Alapvető javítások fül)."""
    panel = _gyerek(window, "viewerEditorPanel")
    panel.setProperty("activeTab", 0)
    qt_app.processEvents()
    _kattints(window, qt_app, gomb)
    assert panel.property(allapot) is True, f"a {gomb} kattintása nem nyitotta meg"
    return panel


class TestAFeltetel:
    def test_modositatlan_vagasnal_nincs_kerdes_es_bezarul(self, qml_app, qt_app):
        """Nyitott, de kijelölés NÉLKÜLI vágás — nincs mit kérdezni; a kapu
        ekkor is lezárja az eszközt, elvetéssel (3/c 2. pont)."""
        window, _controller, _engine = qml_app
        _nezot_nyit(window, qt_app)
        panel = _gyerek(window, "viewerEditorPanel")
        panel.setProperty("cropActive", True)
        qt_app.processEvents()

        _kattints(window, qt_app, "viewerLayoutAa")

        assert not _nyitva(window)
        assert _gyerek(window, "photoViewer").property("layoutMode") == "aa"
        assert panel.property("cropActive") is False

    def test_mar_vagott_kep_erintetlen_vagasa_nem_kerdez(
        self, qml_app, qt_app, tmp_path
    ):
        """A hamis riasztás ellen: a vágás ALKALMAZVA, az eszköz újranyitva
        (a mentett vágás betöltődik kijelölésnek), hozzá sem nyúlunk — ez
        nem módosítás."""
        window, _controller, _engine = qml_app
        nezo = _nezot_nyit(window, qt_app)
        panel = _eszkozt_nyit_kattintva(
            window, qt_app, "editToolCrop", "cropActive"
        )
        overlay = _gyerek(window, "cropOverlay")
        _kijelol(overlay, qt_app, QRectF(0.25, 0.25, 0.5, 0.5))
        _kattints(window, qt_app, "cropApplyButton")
        assert panel.property("cropActive") is False
        ini = tmp_path / "kepek" / ".picasa.ini"
        assert "crop64=1," in ini.read_text(encoding="utf-8")

        _eszkozt_nyit_kattintva(window, qt_app, "editToolCrop", "cropActive")
        assert overlay.property("hasSelection") is True, (
            "a mentett vágás nem töltődött be kijelölésnek — a teszt nem "
            "azt a helyzetet méri, amit kell"
        )

        _kattints(window, qt_app, "viewerLayoutAa")

        assert not _nyitva(window)
        assert nezo.property("layoutMode") == "aa"
        assert panel.property("cropActive") is False
        assert "crop64=1," in ini.read_text(encoding="utf-8")

    def test_mar_vagott_kep_atallitott_vagasa_kerdez(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _nezot_nyit(window, qt_app)
        _eszkozt_nyit_kattintva(window, qt_app, "editToolCrop", "cropActive")
        overlay = _gyerek(window, "cropOverlay")
        _kijelol(overlay, qt_app, QRectF(0.25, 0.25, 0.5, 0.5))
        _kattints(window, qt_app, "cropApplyButton")
        _eszkozt_nyit_kattintva(window, qt_app, "editToolCrop", "cropActive")

        _kijelol(overlay, qt_app, QRectF(0.1, 0.1, 0.6, 0.6))
        _kattints(window, qt_app, "viewerLayoutAa")

        assert _nyitva(window)

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

    def test_nincs_megse_gomb_es_az_esc_nem_zar(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _nezot_nyit(window, qt_app)
        _vagast_nyit_modositva(window, qt_app)
        _kattints(window, qt_app, "viewerLayoutAa")
        assert _nyitva(window)

        # #3693: a Mégse gomb a fókuszváltás kapujával OSZTOTT elem — itt
        # LÉTEZIK, csak rejtett (a `RowLayout` a rejtett elemet kihagyja a
        # sorból, tehát a többi gomb helye nem csúszik el tőle).
        gomb = window.findChild(QObject, "endEditModalityCancelButton")
        assert gomb is not None
        assert gomb.property("visible") is False
        QTest.keyClick(window, Qt.Key.Key_Escape)
        qt_app.processEvents()

        assert _nyitva(window)
        assert nezo.property("layoutMode") == "1up"

    def test_aa_bol_ab_be_lepve_is_kerdez(self, qml_app, qt_app):
        """aa → ab: előbb a 2-up kilépési létra, utána az eszköz kérdése."""
        window, _controller, _engine = qml_app
        nezo = _nezot_nyit(window, qt_app)
        _kattints(window, qt_app, "viewerLayoutAa")
        assert nezo.property("layoutMode") == "aa"
        panel, _overlay = _vagast_nyit_modositva(window, qt_app)

        _kattints(window, qt_app, "viewerLayoutAb")

        assert _nyitva(window)
        assert nezo.property("layoutMode") == "aa"
        _kattints(window, qt_app, "endEditModalityDiscardButton")
        assert nezo.property("layoutMode") == "ab"
        assert panel.property("cropActive") is False


class TestAMasikHaromEszkoz:
    """A Retusálás / Szöveg / Vörösszem lezáró ága — az eszközt a
    csempéjére kattintva nyitjuk."""

    @pytest.mark.parametrize(
        ("gomb", "allapot"),
        (
            ("editToolRetouch", "retouchActive"),
            ("editToolText", "textActive"),
            ("editToolRedeye", "redeyeActive"),
        ),
    )
    def test_erintetlen_eszkoz_kerdes_nelkul_bezarul(
        self, qml_app, qt_app, gomb, allapot
    ):
        window, _controller, _engine = qml_app
        nezo = _nezot_nyit(window, qt_app)
        panel = _eszkozt_nyit_kattintva(window, qt_app, gomb, allapot)

        _kattints(window, qt_app, "viewerLayoutAa")

        assert not _nyitva(window)
        assert nezo.property("layoutMode") == "aa"
        assert panel.property(allapot) is False

    def test_modositott_retusalas_kerdez_es_elvetve_bezarul(self, qml_app, qt_app):
        """A félbehagyott folt jelzőjét (`retouchPatchPending`) a teszt
        állítja be — a kérdés feltétele a panel állapota, nem a festés."""
        window, _controller, _engine = qml_app
        nezo = _nezot_nyit(window, qt_app)
        panel = _eszkozt_nyit_kattintva(
            window, qt_app, "editToolRetouch", "retouchActive"
        )
        panel.setProperty("retouchPatchPending", True)
        qt_app.processEvents()

        _kattints(window, qt_app, "viewerLayoutAa")
        assert _nyitva(window)
        assert panel.property("retouchActive") is True

        _kattints(window, qt_app, "endEditModalityDiscardButton")

        assert not _nyitva(window)
        assert nezo.property("layoutMode") == "aa"
        assert panel.property("retouchActive") is False


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

    def test_bejeloletlen_jelolo_nem_ir(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        beallitas = _engine.rootContext().contextProperty("confirmSettings")
        _nezot_nyit(window, qt_app)
        _vagast_nyit_modositva(window, qt_app)
        _kattints(window, qt_app, "viewerLayoutAa")

        _kattints(window, qt_app, "endEditModalityApplyButton")

        assert not beallitas.isSuppressed(_KULCS)
