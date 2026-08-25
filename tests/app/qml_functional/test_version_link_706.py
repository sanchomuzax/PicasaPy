"""QML-funkcionális tesztek: #706 — a verziócímke kattintható hivatkozás,
ami a GitHub Releases oldalára visz.

Miért így mérünk? A `Qt.openUrlExternally()` a `QDesktopServices::openUrl()`-t
hívja, ez pedig honorálja a `QDesktopServices.setUrlHandler()`-rel bejegyzett
séma-kezelőt. Így a teszt a VALÓDI kimenetet fogja meg — hogy a felület
melyik címet nyitná meg —, és közben egyetlen böngésző sem indul el.

A kattintást a VEZÉRLŐRE adjuk (`QTest.mouseClick` az ablakra, a címke
képernyő-koordinátáin), nem a kezelőfüggvény közvetlen hívásával: egy
közvetlen hívás akkor is zöld lenne, ha a címke valójában kattinthatatlan.
"""

from PySide6.QtCore import QCoreApplication, QEvent, QObject, QPoint, QPointF, Qt, Slot
from PySide6.QtGui import QDesktopServices, QHoverEvent
from PySide6.QtTest import QTest

KIADASOK_URL = "https://github.com/sanchomuzax/PicasaPy/releases/"


class UrlFogo(QObject):
    """A `https` séma kezelője a teszt idejére — eltárolja a kért címeket."""

    def __init__(self):
        super().__init__()
        self.cimek: list[str] = []

    @Slot("QUrl")
    def kezel(self, url):  # noqa: D102 - a Qt hívja
        self.cimek.append(url.toString())


def _cimke(window):
    cimke = window.findChild(QObject, "versionLabel")
    assert cimke is not None, "versionLabel nem található"
    return cimke


def _kozeppont(item) -> QPoint:
    kozep = item.mapToScene(
        QPointF(item.property("width") / 2, item.property("height") / 2)
    )
    return QPoint(round(kozep.x()), round(kozep.y()))


def _hover(window, pont: QPoint) -> None:
    """Egérmutató a pont fölé — offscreen a `QTest.mouseMove` nem szül
    hover-eseményt, ezért közvetlenül küldünk `QHoverEvent`-et.

    ELŐBB egy távoli pontra mozgatunk: a jelenet hover-állapota
    pozíció-alapú, és ha a mutató „már ott van", az újabb azonos pozíciójú
    esemény nem vált ki állapotváltozást. A távoli pont teszi a mérést
    sorrend-függetlenné."""
    for cel in (QPointF(0, 0), QPointF(pont)):
        elozo = QPointF(-1, -1)
        QCoreApplication.sendEvent(
            window, QHoverEvent(QEvent.Type.HoverMove, cel, cel, elozo)
        )
        QCoreApplication.processEvents()


def _url_fogo(qt_app):
    """Bejegyzett `https`-kezelő, ami a teszt végén visszaáll."""
    fogo = UrlFogo()
    QDesktopServices.setUrlHandler("https", fogo, "kezel")
    try:
        yield fogo
    finally:
        QDesktopServices.unsetUrlHandler("https")
        qt_app.processEvents()


class TestVerzioCimkeHivatkozas:
    """#706: a verziószám kattintható, és a kiadások oldalára visz."""

    def test_kattintasra_a_kiadasok_oldala_nyilik_meg(self, qml_app, qt_app):
        window = qml_app[0]
        cimke = _cimke(window)
        assert cimke.property("width") > 0, "a verziócímke nulla szélességű"

        fogo_gen = _url_fogo(qt_app)
        fogo = next(fogo_gen)
        try:
            QTest.mouseClick(
                window,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
                _kozeppont(cimke),
            )
            qt_app.processEvents()
            QTest.qWait(30)
            qt_app.processEvents()
            assert fogo.cimek == [KIADASOK_URL], (
                f"a kattintás nem a kiadások oldalát nyitotta meg: {fogo.cimek}"
            )
        finally:
            fogo_gen.close()

    def test_az_egermutato_kezre_valt(self, qml_app):
        window = qml_app[0]
        cimke = _cimke(window)
        kurzor = cimke.findChild(QObject, "versionCursor")
        assert kurzor is not None, (
            "a verziócímkének nincs kurzoralakot állító kezelője"
        )
        assert kurzor.property("cursorShape") == Qt.CursorShape.PointingHandCursor

    def test_ramutatasra_alahuzott_lesz(self, qml_app, qt_app):
        window = qml_app[0]
        cimke = _cimke(window)
        betu = cimke.property("font")
        assert betu.underline() is False, "alapállapotban ne legyen aláhúzva"

        # a mérés KÖZVETLENÜL a hover után történik: a buboréksúgó
        # felnyílása (saját popup-ablak) elveheti a hovert a címkétől,
        # ezért itt nincs `qWait` a hover és az állítás között.
        _hover(window, _kozeppont(cimke))
        assert cimke.property("font").underline() is True, (
            "rámutatásra nincs vizuális visszajelzés (aláhúzás)"
        )

    def test_billentyuzettel_aktivalhato(self, qml_app, qt_app):
        window = qml_app[0]
        cimke = _cimke(window)
        assert cimke.property("activeFocusOnTab") is True, (
            "a verziócímke nem érhető el billentyűzettel (activeFocusOnTab)"
        )
        cimke.forceActiveFocus()
        qt_app.processEvents()
        assert cimke.property("activeFocus") is True

        fogo_gen = _url_fogo(qt_app)
        fogo = next(fogo_gen)
        try:
            QTest.keyClick(window, Qt.Key.Key_Return)
            qt_app.processEvents()
            QTest.qWait(30)
            qt_app.processEvents()
            assert fogo.cimek == [KIADASOK_URL], (
                f"Enter nem nyitotta meg a kiadások oldalát: {fogo.cimek}"
            )
        finally:
            fogo_gen.close()

    def test_a_fokusz_lathato(self, qml_app, qt_app):
        window = qml_app[0]
        cimke = _cimke(window)
        jelolo = cimke.findChild(QObject, "versionFocusRing")
        assert jelolo is not None, "nincs látható fókuszjelölés a verziócímkén"
        assert jelolo.property("visible") is False, (
            "fókusz nélkül ne látszódjon a fókuszjelölés"
        )
        cimke.forceActiveFocus()
        qt_app.processEvents()
        # #1423: előbb a fókuszt magát erősítjük meg. Enélkül egy hatástalan
        # forceActiveFocus() ugyanúgy „nem látszik a jelölés" hibaüzenetet
        # adna, mint egy tényleg hiányzó fókuszjelölés.
        assert cimke.property("activeFocus") is True, (
            "a fókusz nem ment át a verziócímkére"
        )
        assert jelolo.property("visible") is True, (
            "fókuszban nem látszik a fókuszjelölés"
        )

    def test_a_buboreksugo_megmondja_hova_visz(self, qml_app):
        """A szám maga nem árulja el, hova visz — a súgónak ki kell mondania.

        A `ToolTip.text` csatolt property-t a `property()` nem adja vissza,
        ezért a címke saját `tooltipText` property-jéből olvassuk, amire a
        csatolt property is kötve van."""
        cimke = _cimke(qml_app[0])
        sugo = cimke.property("tooltipText")
        assert sugo, "a verziócímkének nincs buboréksúgó-szövege"
        assert "GitHub" in sugo, (
            f"a buboréksúgó nem mondja meg, hova visz: {sugo!r}"
        )
