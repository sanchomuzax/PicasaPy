"""#3693: a „Szerkesztés jóváhagyása" kérdés a kettős nézet FÓKUSZVÁLTÁSAKOR
is, ha egy modális eszköz (Vágás/Retusálás/Szöveg/Vörösszem) nyitva ÉS
módosult — ugyanaz a kapu (`_eszkozZarasKapu`, `EndEditModalityDialog.qml`),
mint a #3651-es mód-belépésnél, de a mérés (`docs/specs/ui-audit-editor.md`
3/c szakasz) szerint MÁSIK argumentummal.

## A mérés

A fókuszváltó (`0x0056a160`) a váltás ELŐTT `0x005f8d80(this, 1, 0, 1)`-et
hív — a 4. argumentum `1` (a mód-belépés `0x0056a260`-nál `0`), ezért a
2. gomb (`il_Cancel`) ITT megjelenik (`0x005f8e36`). Mégsére (2) a fókusz
NEM vált, az eszköz nyitva marad a módosításával.

A teszt VALÓDI kattintással nyomja a gombokat/vezérlőket (`QTest.mouseClick`
a jelenet-koordinátákon, #2494-lecke), nem a kezelő közvetlen hívásával.
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


def _kattints(window, qt_app, nev):
    """Valódi egérkattintás a vezérlő/kép közepére."""
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


def _nezot_nyit(window, qt_app):
    window.setProperty("viewerOpen", True)
    viewer = _gyerek(window, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    qt_app.processEvents()
    return viewer


def _ab_belep(window, qt_app):
    """A nézőt „ab" módba viszi — a fókuszváltó gomb és a kép-kattintás
    csak 2-up módban él. ⚠️ SZÁNDÉKOSAN „ab", nem „aa": az „aa" mód a
    #3014/#3649 szerint a KIJELÖLT fél láncát írja az inibe, a másikat
    memóriában tartja, és a fókuszváltás a kettőt CSERÉLI — Alkalmazás
    UTÁN a fókuszváltás így a frissen alkalmazott vágást a memóriás
    (aznap nem írt) oldalra teszi át, ami a #3649 mérése szerint helyes,
    de itt csak zavarná az „azonnal az inibe kerül" ellenőrzést. „ab"
    módban két KÜLÖNBÖZŐ fotó áll a két félen, saját inisorral — a
    fókuszváltás kapuja ugyanaz, a lánc-csere mellékhatása nélkül."""
    nezo = _nezot_nyit(window, qt_app)
    _kattints(window, qt_app, "viewerLayoutAb")
    assert nezo.property("layoutMode") == "ab"
    return nezo


def _parbeszed(window):
    return _gyerek(window, "endEditModalityDialog")


def _nyitva(window) -> bool:
    return _parbeszed(window).property("opened") is True


def _kijelol(overlay, qt_app, teglalap):
    overlay.setProperty("cropRect", teglalap)
    overlay.setProperty("hasSelection", True)
    qt_app.processEvents()


def _vagast_nyit_modositva(window, qt_app):
    """A vágó-eszköz megnyitása, húzott (de nem alkalmazott) kijelöléssel."""
    panel = _gyerek(window, "viewerEditorPanel")
    panel.setProperty("cropActive", True)
    qt_app.processEvents()
    overlay = _gyerek(window, "cropOverlay")
    _kijelol(overlay, qt_app, QRectF(0.25, 0.25, 0.5, 0.5))
    return panel, overlay


def _eszkozt_nyit_kattintva(window, qt_app, gomb, allapot):
    """Az eszköz megnyitása a csempéjére kattintva (Alapvető javítások fül)."""
    panel = _gyerek(window, "viewerEditorPanel")
    panel.setProperty("activeTab", 0)
    qt_app.processEvents()
    _kattints(window, qt_app, gomb)
    assert panel.property(allapot) is True, f"a {gomb} kattintása nem nyitotta meg"
    return panel


class TestAFeltetel:
    def test_modositatlan_eszkoznel_nincs_kerdes_es_azonnal_valt(
        self, qml_app, qt_app
    ):
        window, _controller, _engine = qml_app
        nezo = _ab_belep(window, qt_app)
        panel = _gyerek(window, "viewerEditorPanel")
        panel.setProperty("cropActive", True)
        qt_app.processEvents()
        eredeti = nezo.property("aktivOldal")

        _kattints(window, qt_app, "viewerSwapFocus")

        assert not _nyitva(window)
        assert nezo.property("aktivOldal") != eredeti
        assert panel.property("cropActive") is False

    def test_eszkoz_nelkul_azonnal_valt(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _ab_belep(window, qt_app)
        eredeti = nezo.property("aktivOldal")

        _kattints(window, qt_app, "viewerSwapFocus")

        assert not _nyitva(window)
        assert nezo.property("aktivOldal") != eredeti

    def test_modositott_vagasnal_megjelenik_a_kerdes(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _ab_belep(window, qt_app)
        eredeti = nezo.property("aktivOldal")
        _vagast_nyit_modositva(window, qt_app)

        _kattints(window, qt_app, "viewerSwapFocus")

        assert _nyitva(window)
        # a fókuszváltás a válaszig várakozik
        assert nezo.property("aktivOldal") == eredeti

    def test_a_cim_es_a_szoveg_hivatalos(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _ab_belep(window, qt_app)
        _vagast_nyit_modositva(window, qt_app)

        _kattints(window, qt_app, "viewerSwapFocus")

        parbeszed = _parbeszed(window)
        assert parbeszed.property("title") == "Confirm Edit"
        uzenet = _gyerek(window, "endEditModalityUzenet")
        assert uzenet.property("text") == "Apply changes to the current image?"

    def test_itt_VAN_megse_gomb_a_modbelepessel_szemben(self, qml_app, qt_app):
        """3/c 2. pont: a fókuszváltó a kaput 4. argumentum `1`-gyel hívja —
        a mód-belépéssel (#3651, argumentum `0`, nincs Mégse) szemben itt a
        2. gomb megjelenik."""
        window, _controller, _engine = qml_app
        _ab_belep(window, qt_app)
        _vagast_nyit_modositva(window, qt_app)

        _kattints(window, qt_app, "viewerSwapFocus")

        gomb = _gyerek(window, "endEditModalityCancelButton")
        assert gomb.property("visible") is True


class TestAValaszok:
    def test_alkalmaz_menti_a_vagast_es_valt_fokuszt(self, qml_app, qt_app, tmp_path):
        window, _controller, _engine = qml_app
        nezo = _ab_belep(window, qt_app)
        eredeti = nezo.property("aktivOldal")
        panel, _overlay = _vagast_nyit_modositva(window, qt_app)
        _kattints(window, qt_app, "viewerSwapFocus")
        assert _nyitva(window)

        _kattints(window, qt_app, "endEditModalityApplyButton")

        assert not _nyitva(window)
        assert nezo.property("aktivOldal") != eredeti
        assert panel.property("cropActive") is False
        ini = tmp_path / "kepek" / ".picasa.ini"
        assert "crop64=1," in ini.read_text(encoding="utf-8")

    def test_elvet_eldobja_a_vagast_es_valt_fokuszt(self, qml_app, qt_app, tmp_path):
        window, _controller, _engine = qml_app
        nezo = _ab_belep(window, qt_app)
        eredeti = nezo.property("aktivOldal")
        panel, _overlay = _vagast_nyit_modositva(window, qt_app)
        _kattints(window, qt_app, "viewerSwapFocus")
        assert _nyitva(window)

        _kattints(window, qt_app, "endEditModalityDiscardButton")

        assert not _nyitva(window)
        assert nezo.property("aktivOldal") != eredeti
        assert panel.property("cropActive") is False
        ini = tmp_path / "kepek" / ".picasa.ini"
        szoveg = ini.read_text(encoding="utf-8") if ini.exists() else ""
        assert "crop64" not in szoveg

    def test_megse_nem_valt_fokuszt_es_az_eszkoz_nyitva_marad(
        self, qml_app, qt_app, tmp_path
    ):
        """3/c 2. pont: Mégsére `0xf4242`, a fókusz NEM vált — az eszköz a
        módosításával nyitva marad."""
        window, _controller, _engine = qml_app
        nezo = _ab_belep(window, qt_app)
        eredeti = nezo.property("aktivOldal")
        panel, overlay = _vagast_nyit_modositva(window, qt_app)
        _kattints(window, qt_app, "viewerSwapFocus")
        assert _nyitva(window)

        _kattints(window, qt_app, "endEditModalityCancelButton")

        assert not _nyitva(window)
        # rontás-kontroll: ha a `_megseDont()` (vagy az `onMegse` kötés)
        # eltűnne, és a Mégse gomb az Elvetés ágára esne vissza, ez a két
        # `assert` buknia kell — a fókusz átvált és a vágó-eszköz bezárul,
        # holott a 3/c szerint Mégsére semmi nem történhet.
        assert nezo.property("aktivOldal") == eredeti
        assert panel.property("cropActive") is True
        assert overlay.property("hasSelection") is True
        ini = tmp_path / "kepek" / ".picasa.ini"
        szoveg = ini.read_text(encoding="utf-8") if ini.exists() else ""
        assert "crop64" not in szoveg


class TestAKepreKattintassal:
    """A fókuszváltás a MÁSIK képre kattintva is ugyanezen a kapun megy —
    a nem aktív oldal Image-ének TapHandlere a #3693 előtt tiltva volt
    nyitott eszköznél (blokkolta a váltást); most a kapun át enged.

    #3773: belépéskor a BAL az aktív (`aktivOldal` alapértéke „bal"), a
    MÁSIK — nem aktív — oldal tehát a `viewerImage` (jobb)."""

    def test_modositott_retusalasnal_a_kepre_kattintva_is_kerdez(
        self, qml_app, qt_app
    ):
        window, _controller, _engine = qml_app
        nezo = _ab_belep(window, qt_app)
        eredeti = nezo.property("aktivOldal")
        panel = _eszkozt_nyit_kattintva(
            window, qt_app, "editToolRetouch", "retouchActive"
        )
        panel.setProperty("retouchPatchPending", True)
        qt_app.processEvents()

        _kattints(window, qt_app, "viewerImage")

        assert _nyitva(window)
        assert nezo.property("aktivOldal") == eredeti
        assert panel.property("retouchActive") is True

        _kattints(window, qt_app, "endEditModalityDiscardButton")

        assert not _nyitva(window)
        assert nezo.property("aktivOldal") != eredeti
        assert panel.property("retouchActive") is False

    def test_modositott_retusalasnal_a_kepre_kattintva_megse_nyitva_tart(
        self, qml_app, qt_app
    ):
        window, _controller, _engine = qml_app
        nezo = _ab_belep(window, qt_app)
        eredeti = nezo.property("aktivOldal")
        panel = _eszkozt_nyit_kattintva(
            window, qt_app, "editToolRetouch", "retouchActive"
        )
        panel.setProperty("retouchPatchPending", True)
        qt_app.processEvents()

        _kattints(window, qt_app, "viewerImage")
        _kattints(window, qt_app, "endEditModalityCancelButton")

        assert nezo.property("aktivOldal") == eredeti
        assert panel.property("retouchActive") is True
        assert panel.property("retouchPatchPending") is True


class TestAMasikHaromEszkoz:
    """A Retusálás / Szöveg / Vörösszem lezáró ága — az eszközt a
    csempéjére kattintva nyitjuk, a #3651 mintája szerint."""

    @pytest.mark.parametrize(
        ("gomb", "allapot"),
        (
            ("editToolRetouch", "retouchActive"),
            ("editToolText", "textActive"),
            ("editToolRedeye", "redeyeActive"),
        ),
    )
    def test_erintetlen_eszkoz_kerdes_nelkul_valt(
        self, qml_app, qt_app, gomb, allapot
    ):
        window, _controller, _engine = qml_app
        nezo = _ab_belep(window, qt_app)
        eredeti = nezo.property("aktivOldal")
        panel = _eszkozt_nyit_kattintva(window, qt_app, gomb, allapot)

        _kattints(window, qt_app, "viewerSwapFocus")

        assert not _nyitva(window)
        assert nezo.property("aktivOldal") != eredeti
        assert panel.property(allapot) is False


class TestANeKerdezzenJelolo:
    def test_a_jelolo_elnyomja_a_kovetkezo_fokuszvaltast_es_alkalmaz(
        self, qml_app, qt_app, tmp_path
    ):
        window, _controller, _engine = qml_app
        engine = _engine
        beallitas = engine.rootContext().contextProperty("confirmSettings")
        nezo = _ab_belep(window, qt_app)
        panel, _overlay = _vagast_nyit_modositva(window, qt_app)
        _kattints(window, qt_app, "viewerSwapFocus")

        _kattints(window, qt_app, "endEditModalityNeKerdezzenCheck")
        _kattints(window, qt_app, "endEditModalityDiscardButton")

        assert beallitas.isSuppressed(_KULCS)

        # új vágás, majd fókuszváltás — MOSTANTÓL kérdés nélkül alkalmaz
        eredeti = nezo.property("aktivOldal")
        _vagast_nyit_modositva(window, qt_app)

        _kattints(window, qt_app, "viewerSwapFocus")

        assert not _nyitva(window)
        assert nezo.property("aktivOldal") != eredeti
        assert panel.property("cropActive") is False
        ini = tmp_path / "kepek" / ".picasa.ini"
        assert "crop64=1," in ini.read_text(encoding="utf-8")
