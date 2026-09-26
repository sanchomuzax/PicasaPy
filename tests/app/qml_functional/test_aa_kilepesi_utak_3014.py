"""Az „aa" mód lezárása a KILÉPÉSI UTAKON — a program bezárása, a lapozás és
a néző elhagyása (#3014, a #3644 átnézésének leletei).

## A mérés (`docs/specs/ui-audit-editor.md` 4/c.1)

A `0x0056aad0` (`Confirm2up*`) hívói a teljes `.text` pásztázása szerint
(`paszta.py`, 2 884 879 utasítás) pontosan hatan vannak, és mindegyik a
`0xf4242` (Mégse) visszatérésre MEGÁLL:

- a program bezárása: `WM_SYSCOMMAND`/`SC_CLOSE` (`0x005e4d87`) →
  `0x0057c4e0` → `0x005e45c0` → `0x0056aad0` (`0x005e477d`); Mégse ⇒
  `0x0057c59c` → a program NEM zárul be;
- a lapozás: a `0xc90754` vtábla 10./11. rekesze (`0x00578c30` /
  `0x00578dc0`, előző/következő kép a `0x007172a0`/`0x00717260` lépéssel)
  ELŐSZÖR kérdez, Mégsére (`0x00578c72`) nem lapoz;
- a filmszalag: `filmstripmove` (`0x005deb29`) és `lb_preclick`
  (`0x005d34ed` → `0x005e45c0`) ugyanígy.

A „Vissza a könyvtárba" (`editpanel/albumview` → `0x00566270`) NEM kérdez —
de nem is dönt: a két fél állapota a `CThumbUI`-ban marad, a kérdés később jön.
Nálunk a néző bezárása mindkét munkamenetet lezárja, tehát ott a kérdés a
munkát védi (a párbeszéd a biztonságos oldal; ld. 4/c.1).

A kilépést VALÓDI úton indítjuk: a program bezárását a `QWindow.close()`
(`onClosing`) és a Fájl ▸ Kilépés közös `kilepes()` útja, a lapozást a
jobbra-nyíl billentyű, a néző elhagyását a „Vissza a könyvtárba" gomb
egérkattintása és az Esc billentyű.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest


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


def _billentyu(window, qt_app, gomb):
    QTest.keyClick(window, gomb)
    qt_app.processEvents()


def _szerkeszt(nezo, qt_app, effekt):
    nezo.property("editCtl").applyEffect(effekt)
    qt_app.processEvents()


def _ini_lanc(fajl: Path) -> str:
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


def _fajl(nezo, sor=None) -> Path:
    modell = nezo.property("photosModel")
    if sor is None:
        sor = nezo.property("currentIndex")
    return Path(modell.filePathAt(sor))


def _nyitva(window) -> bool:
    return _gyerek(window, "aaUtkozesDialog").property("opened") is True


def _aa(window, qt_app):
    nezo = _nezot_nyit(window, qt_app)
    _szegmens(window, qt_app, "viewerLayoutAa")
    return nezo


def _csak_a_memorias_modosult(window, qt_app):
    """A jobb (aktív) fél `bw`-t kap, aztán a fókusz a balra vált: a `bw`
    ettől kezdve CSAK a memóriás rekeszben él (az ini-ben a bal, érintetlen
    lánc áll) — ez a #3644 1. lelete."""
    nezo = _aa(window, qt_app)
    _szerkeszt(nezo, qt_app, "bw")
    _szegmens(window, qt_app, "viewerSwapFocus")
    assert "bw" not in _ini_lanc(_fajl(nezo))
    return nezo


def _ket_kulonbozo(window, qt_app):
    """Jobb = `bw` (memóriás), bal = `sepia` (aktív, az ini-ben)."""
    nezo = _aa(window, qt_app)
    _szerkeszt(nezo, qt_app, "bw")
    _szegmens(window, qt_app, "viewerSwapFocus")
    _szerkeszt(nezo, qt_app, "sepia")
    return nezo


class _KilepesFigyelo:
    """A `Qt.quit()` a motor `quit` jelzését adja — ezt figyeljük (a próba
    processzében nincs futó eseményhurok, tehát a jelzés nem zár be semmit)."""

    def __init__(self, engine):
        self._jelzesek: list[str] = []
        engine.quit.connect(lambda: self._jelzesek.append("quit"))

    @property
    def szam(self) -> int:
        return len(self._jelzesek)


def _kilepes_tovabbment(window, figyelo) -> bool:
    """A kilépés az „aa" kapun TÚLJUTOTT: vagy kilépett (`Qt.quit()`), vagy a
    #671 háttérmunka-kérdéséhez ért. Az utóbbi valós: a memóriás fél kiírása
    (`persistChain`) háttérmunkát indíthat, és a #671 akkor kérdez."""
    kerdes = window.findChild(QObject, "exitConfirm")
    return figyelo.szam == 1 or (
        kerdes is not None and kerdes.property("opened") is True
    )


class TestAProgramBezarasa:
    def test_az_ablak_X_e_KIIRJA_a_memorias_felet(self, qml_app, qt_app):
        """#3644 1.: fókuszváltás után a memóriás fél munkája nem veszhet el."""
        window, _controller, _engine = qml_app
        nezo = _csak_a_memorias_modosult(window, qt_app)
        fajl = _fajl(nezo)

        window.close()
        qt_app.processEvents()

        assert "bw" in _ini_lanc(fajl)

    def test_a_Fajl_Kilepes_is_KIIRJA(self, qml_app, qt_app):
        window, _controller, engine = qml_app
        figyelo = _KilepesFigyelo(engine)
        nezo = _csak_a_memorias_modosult(window, qt_app)
        fajl = _fajl(nezo)

        QMetaObject.invokeMethod(window, "kilepes", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()

        assert "bw" in _ini_lanc(fajl)
        assert _kilepes_tovabbment(window, figyelo)

    def test_ket_kulonbozo_szerkesztesnel_KERDEZ_es_nem_zar(self, qml_app, qt_app):
        window, _controller, engine = qml_app
        figyelo = _KilepesFigyelo(engine)
        _ket_kulonbozo(window, qt_app)

        window.close()
        qt_app.processEvents()

        assert _nyitva(window)
        assert window.isVisible()
        assert not _kilepes_tovabbment(window, figyelo)

    def test_a_Fajl_Kilepes_is_KERDEZ(self, qml_app, qt_app):
        window, _controller, engine = qml_app
        figyelo = _KilepesFigyelo(engine)
        _ket_kulonbozo(window, qt_app)

        QMetaObject.invokeMethod(window, "kilepes", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()

        assert _nyitva(window)
        assert not _kilepes_tovabbment(window, figyelo)

    def test_MEGSE_a_programot_nyitva_hagyja_mindket_munkaval(self, qml_app, qt_app):
        window, _controller, engine = qml_app
        figyelo = _KilepesFigyelo(engine)
        nezo = _ket_kulonbozo(window, qt_app)
        aktiv = nezo.property("editCtl").property("chainValue")
        masik = nezo.property("masodikEditCtl").property("chainValue")
        window.close()
        qt_app.processEvents()

        _kattints(window, qt_app, "aaUtkozesMegseButton")

        assert not _nyitva(window)
        assert window.isVisible()
        assert not _kilepes_tovabbment(window, figyelo)
        assert nezo.property("layoutMode") == "aa"
        assert nezo.property("editCtl").property("chainValue") == aktiv
        assert nezo.property("masodikEditCtl").property("chainValue") == masik

    def test_valasz_utan_a_VALASZTOTT_marad_es_kilep(self, qml_app, qt_app):
        window, _controller, engine = qml_app
        figyelo = _KilepesFigyelo(engine)
        nezo = _ket_kulonbozo(window, qt_app)
        fajl = _fajl(nezo)
        window.close()
        qt_app.processEvents()

        _kattints(window, qt_app, "aaUtkozesMasodikButton")  # a jobb: bw

        assert "bw" in _ini_lanc(fajl)
        assert "sepia" not in _ini_lanc(fajl)
        assert _kilepes_tovabbment(window, figyelo)


class TestALapozas:
    def test_ket_kulonbozo_szerkesztesnel_KERDEZ_es_nem_lapoz(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _ket_kulonbozo(window, qt_app)
        fajl = _fajl(nezo)

        _billentyu(window, qt_app, Qt.Key.Key_Right)

        assert _nyitva(window)
        assert nezo.property("currentIndex") == 0
        assert nezo.property("layoutMode") == "aa"
        # a memóriás fél munkája még megvan, az ini-ben az aktív áll
        assert "bw" in nezo.property("masodikEditCtl").property("chainValue")
        assert "sepia" in _ini_lanc(fajl)

    def test_MEGSE_utan_marad_a_kepen_mindket_munkaval(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _ket_kulonbozo(window, qt_app)
        aktiv = nezo.property("editCtl").property("chainValue")
        masik = nezo.property("masodikEditCtl").property("chainValue")
        _billentyu(window, qt_app, Qt.Key.Key_Right)

        _kattints(window, qt_app, "aaUtkozesMegseButton")

        assert not _nyitva(window)
        assert nezo.property("currentIndex") == 0
        assert nezo.property("layoutMode") == "aa"
        assert nezo.property("editCtl").property("chainValue") == aktiv
        assert nezo.property("masodikEditCtl").property("chainValue") == masik
        # és a következő lapozás ismét kérdez
        _billentyu(window, qt_app, Qt.Key.Key_Right)
        assert _nyitva(window)

    def test_valasz_utan_LAPOZ_es_a_valasztott_marad(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _ket_kulonbozo(window, qt_app)
        fajl = _fajl(nezo)
        _billentyu(window, qt_app, Qt.Key.Key_Right)

        _kattints(window, qt_app, "aaUtkozesMasodikButton")  # a jobb: bw

        assert not _nyitva(window)
        assert nezo.property("currentIndex") == 1
        assert "bw" in _ini_lanc(fajl)
        assert "sepia" not in _ini_lanc(fajl)

    def test_csak_a_memorias_modosult_KERDES_NELKUL_irodik(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _csak_a_memorias_modosult(window, qt_app)
        fajl = _fajl(nezo)

        _billentyu(window, qt_app, Qt.Key.Key_Right)

        assert not _nyitva(window)
        assert nezo.property("currentIndex") == 1
        assert "bw" in _ini_lanc(fajl)


class TestANezoElhagyasa:
    def test_a_Vissza_gomb_KERDEZ_es_a_nezo_nyitva_marad(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _ket_kulonbozo(window, qt_app)

        _kattints(window, qt_app, "viewerBackButton")

        assert _nyitva(window)
        assert window.property("viewerOpen") is True

    def test_az_Esc_is_KERDEZ(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _ket_kulonbozo(window, qt_app)

        _billentyu(window, qt_app, Qt.Key.Key_Escape)

        assert _nyitva(window)
        assert window.property("viewerOpen") is True

    def test_MEGSE_utan_a_kettos_nezet_marad(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _ket_kulonbozo(window, qt_app)
        masik = nezo.property("masodikEditCtl").property("chainValue")
        _kattints(window, qt_app, "viewerBackButton")

        _kattints(window, qt_app, "aaUtkozesMegseButton")

        assert not _nyitva(window)
        assert window.property("viewerOpen") is True
        assert nezo.property("layoutMode") == "aa"
        assert nezo.property("masodikEditCtl").property("chainValue") == masik

    def test_valasz_utan_BEZARUL_es_a_valasztott_marad(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _ket_kulonbozo(window, qt_app)
        fajl = _fajl(nezo)
        _kattints(window, qt_app, "viewerBackButton")

        _kattints(window, qt_app, "aaUtkozesMasodikButton")

        assert window.property("viewerOpen") is False
        assert "bw" in _ini_lanc(fajl)
        assert "sepia" not in _ini_lanc(fajl)

    def test_a_KOLLAZS_lapra_valtas_is_KERDEZ(self, qml_app, qt_app):
        """A néző a Main.qml közvetlen útjain is bezárulhat (kollázs, keresés,
        személy) — azoknak is a kapun kell átmenniük."""
        window, _controller, _engine = qml_app
        _ket_kulonbozo(window, qt_app)

        QMetaObject.invokeMethod(
            window, "openCollageTab", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        assert _nyitva(window)
        assert window.property("viewerOpen") is True


class TestAFokuszvaltasEszkozallapota:
    def test_a_kiegyenesites_csuszka_a_KIJELOLT_fel_erteket_mutatja(
        self, qml_app, qt_app
    ):
        """#3644 3.: a fókuszváltás után a csúszka nem ragadhat a másik fél
        döntési értékén."""
        window, _controller, _engine = qml_app
        nezo = _aa(window, qt_app)
        nezo.property("editCtl").setTilt(0.25)
        # a csúszka a jobb fél értékén áll (ahogy a felhasználó húzta)
        QMetaObject.invokeMethod(
            nezo, "syncTiltSlider", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        savo = _gyerek(window, "editorToolBar")
        assert abs(savo.property("csuszkaErtek") - 0.25) < 1e-6

        _szegmens(window, qt_app, "viewerSwapFocus")

        assert nezo.property("editCtl").property("tiltParam") == 0
        assert savo.property("csuszkaErtek") == 0


class TestAParbeszedBillentyuzete:
    def test_Tabbal_kijelolt_MEGSE_gombon_az_Enter_a_MEGSE(self, qml_app, qt_app):
        """#3644 4.: az Enter a FÓKUSZBAN álló gombot nyomja — az alapértelmezett
        csak akkor, ha egyik gomb sincs fókuszban."""
        window, _controller, _engine = qml_app
        nezo = _ket_kulonbozo(window, qt_app)
        _szegmens(window, qt_app, "viewerLayoutOnly1up")
        assert _nyitva(window)
        megse = _gyerek(window, "aaUtkozesMegseButton")
        for _ in range(8):
            if megse.property("activeFocus"):
                break
            _billentyu(window, qt_app, Qt.Key.Key_Tab)
        assert megse.property("activeFocus"), "a Mégse Tabbal nem érhető el"

        _billentyu(window, qt_app, Qt.Key.Key_Return)

        assert not _nyitva(window)
        assert nezo.property("layoutMode") == "aa", "az Enter nem a Mégsét nyomta"
