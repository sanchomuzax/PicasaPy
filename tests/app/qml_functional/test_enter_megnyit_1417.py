"""Az `Enter` megnyitja a nézőt a bélyegkép-rácsból (#1417).

## Az eredeti — bizonyíték

`docs/specs/picasa-gyorsbillentyuk.md` (helyi menük rekordtáblája, a
`0x00a6aee0` hívói): az `Enter` a bélyegkép-rács helyi menüjének
**félkövér, alapértelmezett** tétele — a kijelölt képet nyitja meg a
nézőben. Ez a négy olyan kombináció egyike, ami CSAK helyi menüben él, a
`SHORTCUTS.XML`-ben nincs benne; a #1154 feltárása találta meg.

Nálunk eddig csak a dupla kattintás nyitott (`ThumbDelegate.onDoubleClicked`
→ `LightboxFeed.openRequested`), az `Enter` a rácsban néma volt.

## A teszt

⚠️ **Valódi billentyűesemény** megy az ablakra, a fókuszlánc dönti el, ki
kapja meg — nem függvényhívás. A #1148 és a #1200 is azért maradt zöld egy
használhatatlan funkció fölött, mert a teszt a kezelőt hívta közvetlenül.

A negatív ág legalább olyan fontos: az `Enter`-nek a keresőmezőben,
illetve kijelölés nélkül NEM szabad nézőt nyitnia.
"""

from pathlib import Path

from PySide6.QtCore import QEvent, QMetaObject, QObject, Qt
from PySide6.QtGui import QKeyEvent

from support.jpeg_factory import make_jpeg
from support.qml_focus import fokuszt_ad


def _ujraolvas(controller, qt_app) -> None:
    controller.rescan()
    for _ in range(200):
        qt_app.processEvents()
        if controller.waitForBackgroundWorkers(0.05):
            break
    qt_app.processEvents()


def _feed(qml_app, qt_app):
    """Négy képes mappa a fixture két alapképe mellé."""
    window, controller, _ = qml_app
    lib = Path(controller.watchedFolders[0])
    mappa = lib / "alma"
    mappa.mkdir(exist_ok=True)
    for i in range(4):
        make_jpeg(mappa / f"alma{i}.jpg", size=(80, 60))
    _ujraolvas(controller, qt_app)
    assert len(controller.feedGroups) >= 1
    return window, controller


def _gyerek(window, nev):
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"a(z) {nev} nem található"
    return elem


def _fokusz(elem, qt_app):
    """A közös, megerősítő fókuszadás (#1423)."""
    fokuszt_ad(elem, qt_app)


def _billentyu(window, qt_app, key, mods=Qt.KeyboardModifier.NoModifier):
    qt_app.sendEvent(window, QKeyEvent(QEvent.Type.KeyPress, key, mods))
    qt_app.processEvents()


def _allj(window, qt_app, sor):
    window.setProperty("selectedIndexes", [sor])
    window.setProperty("selectedIndex", sor)
    qt_app.processEvents()


class TestEnterMegnyitja:
    def test_enter_a_kijelolt_kepet_nyitja(self, qml_app, qt_app):
        window, _c = _feed(qml_app, qt_app)
        _allj(window, qt_app, 2)
        _fokusz(_gyerek(window, "photoGrid"), qt_app)
        assert window.property("viewerOpen") is False

        _billentyu(window, qt_app, Qt.Key.Key_Return)

        assert window.property("viewerOpen") is True, (
            "az Enter nem nyitotta meg a nézőt a rácsból"
        )
        assert _gyerek(window, "photoViewer").property("currentIndex") == 2

    def test_a_numerikus_enter_is_nyit(self, qml_app, qt_app):
        """A numerikus billentyűzet Entere külön kód (`Key_Enter`)."""
        window, _c = _feed(qml_app, qt_app)
        _allj(window, qt_app, 1)
        _fokusz(_gyerek(window, "photoGrid"), qt_app)

        _billentyu(window, qt_app, Qt.Key.Key_Enter)

        assert window.property("viewerOpen") is True
        assert _gyerek(window, "photoViewer").property("currentIndex") == 1

    def test_kijeloles_nelkul_nem_nyit(self, qml_app, qt_app):
        window, _c = _feed(qml_app, qt_app)
        window.setProperty("selectedIndexes", [])
        window.setProperty("selectedIndex", -1)
        qt_app.processEvents()
        _fokusz(_gyerek(window, "photoGrid"), qt_app)

        _billentyu(window, qt_app, Qt.Key.Key_Return)

        assert window.property("viewerOpen") is False, (
            "kijelölés nélkül nincs mit megnyitni"
        )


class TestAholNemNyithat:
    """Az `Enter`-nek máshol saját dolga van — a rács nem veheti el.

    ⚠️ Mindegyik eset ELŐBB a rácsra viszi a fókuszt (ott az `Enter`
    bizonyítottan nyit), és csak azután a szövegmezőre — enélkül a teszt
    attól is zöld lenne, hogy a rács soha nem kapott fókuszt.
    """

    def test_a_keresomezoben_nem_nyit(self, qml_app, qt_app):
        window, _c = _feed(qml_app, qt_app)
        _allj(window, qt_app, 2)
        _fokusz(_gyerek(window, "photoGrid"), qt_app)
        _fokusz(_gyerek(window, "searchField"), qt_app)

        _billentyu(window, qt_app, Qt.Key.Key_Return)

        assert window.property("viewerOpen") is False, (
            "a keresőmezőben leütött Enter megnyitotta a nézőt"
        )

    def test_a_cimkemezoben_nem_nyit(self, qml_app, qt_app):
        """A Címkék panel beviteli mezőjében az Enter a címkét adja hozzá."""
        window, _c = _feed(qml_app, qt_app)
        _allj(window, qt_app, 2)
        window.setProperty("activeDrawerTab", "tags")
        qt_app.processEvents()
        _fokusz(_gyerek(window, "photoGrid"), qt_app)
        _fokusz(_gyerek(window, "tagInput"), qt_app)

        _billentyu(window, qt_app, Qt.Key.Key_Return)

        assert window.property("viewerOpen") is False, (
            "a címkemezőben leütött Enter megnyitotta a nézőt"
        )

    def test_nyitott_parbeszedben_nem_nyit(self, qml_app, qt_app):
        """Nyitott (modális) párbeszéd alatt az Enter a párbeszédé.

        A párbeszédet VALÓBAN megnyitjuk — a csak elrejtve létező mezőre
        erőltetett fókusz nem szól semmiről: ott a fókusz a rácson marad.
        """
        window, _c = _feed(qml_app, qt_app)
        _allj(window, qt_app, 2)
        _fokusz(_gyerek(window, "photoGrid"), qt_app)
        parbeszed = _gyerek(window, "renameDialog")
        QMetaObject.invokeMethod(
            parbeszed, "open", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert parbeszed.property("visible") is True
        _fokusz(_gyerek(window, "renameField"), qt_app)

        _billentyu(window, qt_app, Qt.Key.Key_Return)

        assert window.property("viewerOpen") is False, (
            "a nyitott párbeszéd fölött az Enter megnyitotta a nézőt"
        )


class TestHelyiMenu:
    """A jegy 2. pontja: a helyi menü megfelelő tétele félkövér, és a
    gyorsbillentyűje az `Enter` — ez a felfedezhetőség."""

    def test_a_megnyitas_felkover_es_entert_hirdet(self, qml_app, qt_app):
        window, _c = _feed(qml_app, qt_app)
        tetel = _gyerek(window, "contextMenuOpen")
        assert tetel.property("font").bold() is True, (
            "az alapértelmezett tétel nem félkövér"
        )
        assert "Enter" in tetel.property("text")
