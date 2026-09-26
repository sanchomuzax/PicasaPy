"""Az „aa" mód két párhuzamos szerkesztése és az ütközés-párbeszéd (#3014).

## A mérés (`docs/specs/ui-audit-editor.md` 4/b és 4/b.1)

- Belépéskor MINDKÉT fél a kép jelenlegi szerkesztési láncával indul — nem a
  nyers képpel (ez a #3013 „bal = szerkesztés előtti" követelményét váltja).
- „Módosult" = a fél lánca ≠ a belépéskori lánc.
- Kilépéskor (egy kép vagy AB mód) a döntési tábla:

  | első (bal/fent) | második (jobb/lent) | teendő |
  |---|---|---|
  | módosult | érintetlen | az elsőt tartja — kérdés nélkül |
  | érintetlen | módosult | a másodikat tartja — kérdés nélkül |
  | érintetlen | érintetlen | nincs teendő |
  | módosult | módosult, egyforma | az aktívat tartja — kérdés nélkül |
  | módosult | módosult, különböző | „Ne kérdezzen újra" ⇒ az aktív; különben párbeszéd |

- A párbeszéd gombjai `Bal`/`Jobb` vagy `Fent`/`Lent` (elrendezés szerint) és
  `Mégse`; az alapértelmezett gomb az AKTÍV félé; Mégse ⇒ a kettős nézet marad.

A párbeszéd gombjait VALÓDI egérkattintással nyomjuk (`QTest.mouseClick` a
gomb jelenet-koordinátáin), nem a kezelő hívásával: egy közvetlen hívás
akkor is zöld volna, ha a gomb takart vagy tiltott.

## A modell

A fő vezérlő a KIJELÖLT felet szerkeszti és írja az ini-t; a másik fél a
második rekeszben CSAK MEMÓRIÁBAN él. A fókuszváltás a két fél láncát
cseréli. Ezért a teszt mindkét irányt próbálja: azt is, amikor a
megtartandó fél épp a memóriás.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

_KULCS = "DoNotAskOnEnd2Up"


def _gyerek(gyoker, nev):
    objektum = gyoker.findChild(QObject, nev)
    assert objektum is not None, f"{nev} nem található"
    return objektum


def _nezot_nyit(window, qt_app):
    window.setProperty("viewerOpen", True)
    qt_app.processEvents()
    nezo = _gyerek(window, "photoViewer")
    QMetaObject.invokeMethod(
        nezo, "show", Qt.ConnectionType.DirectConnection, Q_ARG("QVariant", 0)
    )
    qt_app.processEvents()
    return nezo


def _szegmens(window, qt_app, nev):
    QMetaObject.invokeMethod(
        _gyerek(window, nev), "kattints", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()


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


def _szerkeszt(nezo, qt_app, effekt):
    """Effekt a KIJELÖLT félre — a szerkesztő-panel ugyanezt a vezérlőt hívja."""
    nezo.property("editCtl").applyEffect(effekt)
    qt_app.processEvents()


def _ini_lanc(nezo) -> str:
    """A jelenlegi kép `filters=` sora a `.picasa.ini`-ből."""
    modell = nezo.property("photosModel")
    fajl = Path(modell.filePathAt(nezo.property("currentIndex")))
    ini = fajl.parent / ".picasa.ini"
    if not ini.exists():
        return ""
    szakasz = ""
    for sor in ini.read_text(encoding="utf-8").splitlines():
        if sor.startswith("[") and sor.endswith("]"):
            szakasz = sor[1:-1]
        elif szakasz == fajl.name and sor.startswith("filters="):
            return sor[len("filters=") :]
    return ""


def _parbeszed(window):
    return _gyerek(window, "aaUtkozesDialog")


def _nyitva(window) -> bool:
    return _parbeszed(window).property("opened") is True


def _aa(window, qt_app):
    nezo = _nezot_nyit(window, qt_app)
    _szegmens(window, qt_app, "viewerLayoutAa")
    return nezo


def _ket_kulonbozo(window, qt_app, jobb="bw", bal="sepia"):
    """A jobb (alapból aktív) fél `jobb`-at kap, a bal `bal`-t; a végén a
    BAL az aktív."""
    nezo = _aa(window, qt_app)
    _szerkeszt(nezo, qt_app, jobb)
    _szegmens(window, qt_app, "viewerSwapFocus")
    _szerkeszt(nezo, qt_app, bal)
    return nezo


class TestABelepes:
    def test_mindket_fel_a_JELENLEGI_lanccal_indul(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _nezot_nyit(window, qt_app)
        _szerkeszt(nezo, qt_app, "bw")
        mentett = _ini_lanc(nezo)
        assert "bw" in mentett

        _szegmens(window, qt_app, "viewerLayoutAa")

        assert nezo.property("editCtl").property("chainValue") == mentett
        assert nezo.property("masodikEditCtl").property("chainValue") == mentett

    def test_a_bal_fel_is_SZERKESZTETT_kepet_mutat(self, qml_app, qt_app):
        """Nem a nyers fájl — a második rekesz előnézete."""
        window, _controller, _engine = qml_app
        _aa(window, qt_app)
        forras = _gyerek(window, "viewerImageElotte").property("source").toString()
        assert forras.startswith("image://editpreview/"), forras
        assert "@masodik" in forras

    def test_a_masodik_fel_szerkesztese_NEM_irja_az_init(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _aa(window, qt_app)
        _szegmens(window, qt_app, "viewerSwapFocus")
        _szerkeszt(nezo, qt_app, "sepia")
        # a bal az aktív ⇒ az ini-t a fő vezérlő (bal) írja, a jobb memóriás
        assert "sepia" in _ini_lanc(nezo)
        _szegmens(window, qt_app, "viewerSwapFocus")
        # csere után a jobb (érintetlen) lánca áll az ini-ben, a bal memóriás
        assert "sepia" not in _ini_lanc(nezo)
        assert "sepia" in nezo.property("masodikEditCtl").property("chainValue")


class TestADontesiTabla:
    def test_elso_modosult_masodik_erintetlen(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _aa(window, qt_app)
        _szegmens(window, qt_app, "viewerSwapFocus")
        _szerkeszt(nezo, qt_app, "sepia")
        # vissza a jobbra: a megtartandó bal fél MOST memóriás
        _szegmens(window, qt_app, "viewerSwapFocus")

        _szegmens(window, qt_app, "viewerLayoutOnly1up")

        assert not _nyitva(window)
        assert nezo.property("layoutMode") == "1up"
        assert "sepia" in _ini_lanc(nezo)

    def test_elso_erintetlen_masodik_modosult(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _aa(window, qt_app)
        _szerkeszt(nezo, qt_app, "bw")
        # a bal lesz aktív: a megtartandó jobb fél memóriás
        _szegmens(window, qt_app, "viewerSwapFocus")

        _szegmens(window, qt_app, "viewerLayoutOnly1up")

        assert not _nyitva(window)
        assert nezo.property("layoutMode") == "1up"
        assert "bw" in _ini_lanc(nezo)

    def test_mindketto_erintetlen(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _aa(window, qt_app)
        _szegmens(window, qt_app, "viewerSwapFocus")

        _szegmens(window, qt_app, "viewerLayoutOnly1up")

        assert not _nyitva(window)
        assert nezo.property("layoutMode") == "1up"
        assert _ini_lanc(nezo) == ""

    def test_mindketto_modosult_EGYFORMAN(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _ket_kulonbozo(window, qt_app, jobb="bw", bal="bw")

        _szegmens(window, qt_app, "viewerLayoutOnly1up")

        assert not _nyitva(window)
        assert nezo.property("layoutMode") == "1up"
        assert "bw" in _ini_lanc(nezo)

    def test_mindketto_modosult_KULONBOZOEN_parbeszed(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _ket_kulonbozo(window, qt_app)

        _szegmens(window, qt_app, "viewerLayoutOnly1up")

        assert _nyitva(window)
        # a módváltás a válaszig várakozik
        assert nezo.property("layoutMode") == "aa"

    def test_ne_kerdezzen_ujra_eseten_az_AKTIV_marad(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _engine.rootContext().contextProperty("confirmSettings").setSuppressed(
            _KULCS, True
        )
        nezo = _ket_kulonbozo(window, qt_app)  # a bal (sepia) az aktív

        _szegmens(window, qt_app, "viewerLayoutOnly1up")

        assert not _nyitva(window)
        assert nezo.property("layoutMode") == "1up"
        assert "sepia" in _ini_lanc(nezo)
        assert "bw" not in _ini_lanc(nezo)

    def test_AB_modba_valtas_is_kilepes(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _ket_kulonbozo(window, qt_app)

        _szegmens(window, qt_app, "viewerLayoutAb")

        assert _nyitva(window)
        assert nezo.property("layoutMode") == "aa"


class TestAParbeszed:
    def test_BAL_gomb_a_bal_felet_tartja(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _ket_kulonbozo(window, qt_app)  # bal = sepia, jobb = bw
        _szegmens(window, qt_app, "viewerSwapFocus")  # a jobb az aktív
        _szegmens(window, qt_app, "viewerLayoutOnly1up")

        _kattints(window, qt_app, "aaUtkozesElsoButton")

        assert not _nyitva(window)
        assert nezo.property("layoutMode") == "1up"
        assert "sepia" in _ini_lanc(nezo)
        assert "bw" not in _ini_lanc(nezo)

    def test_JOBB_gomb_a_jobb_felet_tartja(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _ket_kulonbozo(window, qt_app)  # a bal az aktív
        _szegmens(window, qt_app, "viewerLayoutOnly1up")

        _kattints(window, qt_app, "aaUtkozesMasodikButton")

        assert not _nyitva(window)
        assert nezo.property("layoutMode") == "1up"
        assert "bw" in _ini_lanc(nezo)
        assert "sepia" not in _ini_lanc(nezo)

    def test_MEGSE_utan_a_kettos_nezet_marad(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _ket_kulonbozo(window, qt_app)
        aktiv = nezo.property("editCtl").property("chainValue")
        masik = nezo.property("masodikEditCtl").property("chainValue")
        _szegmens(window, qt_app, "viewerLayoutOnly1up")

        _kattints(window, qt_app, "aaUtkozesMegseButton")

        assert not _nyitva(window)
        assert nezo.property("layoutMode") == "aa"
        assert nezo.property("editCtl").property("chainValue") == aktiv
        assert nezo.property("masodikEditCtl").property("chainValue") == masik
        # és a következő kilépés ismét kérdez
        _szegmens(window, qt_app, "viewerLayoutOnly1up")
        assert _nyitva(window)

    def test_a_gombfeliratok_vizszintesen_BAL_JOBB(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _ket_kulonbozo(window, qt_app)
        _szegmens(window, qt_app, "viewerLayoutOnly1up")

        assert _gyerek(window, "aaUtkozesElsoButton").property("text") == "Left"
        assert _gyerek(window, "aaUtkozesMasodikButton").property("text") == "Right"

    def test_a_gombfeliratok_fuggolegesen_FENT_LENT(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _ket_kulonbozo(window, qt_app)
        _szegmens(window, qt_app, "viewerSwapLayout")
        _szegmens(window, qt_app, "viewerLayoutOnly1up")

        assert _gyerek(window, "aaUtkozesElsoButton").property("text") == "Top"
        assert _gyerek(window, "aaUtkozesMasodikButton").property("text") == "Bottom"

    def test_az_ALAPERTELMEZETT_gomb_az_aktiv_bal_fele(self, qml_app, qt_app):
        """Enter = az alapértelmezett gomb; a bal az aktív ⇒ a bal marad."""
        window, _controller, _engine = qml_app
        nezo = _ket_kulonbozo(window, qt_app)  # a bal (sepia) az aktív
        _szegmens(window, qt_app, "viewerLayoutOnly1up")

        assert _gyerek(window, "aaUtkozesElsoButton").property("alapertelmezett")
        assert not _gyerek(window, "aaUtkozesMasodikButton").property(
            "alapertelmezett"
        )
        QTest.keyClick(window, Qt.Key.Key_Return)
        qt_app.processEvents()

        assert not _nyitva(window)
        assert "sepia" in _ini_lanc(nezo)

    def test_az_ALAPERTELMEZETT_gomb_az_aktiv_jobb_fele(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _ket_kulonbozo(window, qt_app)
        _szegmens(window, qt_app, "viewerSwapFocus")  # a jobb (bw) az aktív
        _szegmens(window, qt_app, "viewerLayoutOnly1up")

        assert _gyerek(window, "aaUtkozesMasodikButton").property("alapertelmezett")
        QTest.keyClick(window, Qt.Key.Key_Return)
        qt_app.processEvents()

        assert not _nyitva(window)
        assert "bw" in _ini_lanc(nezo)

    def test_a_NE_KERDEZZEN_jelolo_elnyomja_a_kovetkezot(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        beallitas = _engine.rootContext().contextProperty("confirmSettings")
        nezo = _ket_kulonbozo(window, qt_app)
        _szegmens(window, qt_app, "viewerLayoutOnly1up")

        _kattints(window, qt_app, "aaUtkozesNeKerdezzenCheck")
        _kattints(window, qt_app, "aaUtkozesMasodikButton")

        assert beallitas.isSuppressed(_KULCS)
        assert nezo.property("layoutMode") == "1up"

    def test_a_jelolo_MEGSEVEL_nem_ir(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        beallitas = _engine.rootContext().contextProperty("confirmSettings")
        _ket_kulonbozo(window, qt_app)
        _szegmens(window, qt_app, "viewerLayoutOnly1up")

        _kattints(window, qt_app, "aaUtkozesNeKerdezzenCheck")
        _kattints(window, qt_app, "aaUtkozesMegseButton")

        assert not beallitas.isSuppressed(_KULCS)


class TestANezoBezarasa:
    def test_bezaraskor_a_memorias_modositas_nem_vesz_el(self, qml_app, qt_app):
        """Csak a memóriás fél módosult ⇒ a tábla szerint azt kell tartani."""
        window, _controller, _engine = qml_app
        nezo = _aa(window, qt_app)
        _szerkeszt(nezo, qt_app, "bw")
        _szegmens(window, qt_app, "viewerSwapFocus")  # a bw-s jobb memóriás
        modell = nezo.property("photosModel")
        fajl = Path(modell.filePathAt(nezo.property("currentIndex")))

        window.setProperty("viewerOpen", False)
        qt_app.processEvents()

        assert "bw" in (fajl.parent / ".picasa.ini").read_text(encoding="utf-8")
