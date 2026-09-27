"""#3014: az AB mód (két KÜLÖNBÖZŐ kép) és az elrendezés-váltó őrei.

## A mérés (`docs/specs/ui-audit-editor.md`, 2-up szakasz)

| elem | hivatalos magyar buboréksúgó |
|---|---|
| `editpanel/ab_2up_toggle` | „Két különböző kép megjelenítése" |
| `editpanel/swap_2up_layout` | „Váltás a vízszintes és a függőleges elrendezés között" |

⭐ A szegmensek MÉRT sorrendje `only_1up` · **`ab_2up`** · `aa_2up` (a
respack `LS`/`MS`/`RS` szegmensrajza). A #3013 a két 2-up szegmenst
fordítva rakta le — ez a lap rögzíti a helyes sorrendet.

⭐ Az ütközés-párbeszéd NÉGY helyzet-gombja („Bal/Jobb" vs. „Fent/Lent")
bizonyítja, hogy az elrendezés KÉT TENGELYŰ: a `swap_2up_layout` nem
dísz, hanem a párbeszéd feliratait is eldönti. Ezért a jelvény és a két
kép elhelyezése is a tengelyt követi.

## Ami NEM ebben van

Az albumba tétel (`TwoUpAddToAlbum`) és maga az ütközés-párbeszéd — a
#3014 második köre.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest
from support.jpeg_factory import make_jpeg

from tests.app.qml_functional.conftest import _build_qml_app


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


def _kattint(window, qt_app, nev):
    QMetaObject.invokeMethod(
        _gyerek(window, nev), "kattints", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()


def _ab_modba(window, qt_app):
    nezo = _nezot_nyit(window, qt_app)
    _kattint(window, qt_app, "viewerLayoutAb")
    return nezo


class TestAzABMod:
    def test_az_AB_szegmens_MAR_HASZNALHATO(self, qml_app, qt_app):
        """A #3013 tiltva hagyta („a #3014 hozza") — most engedve van."""
        window, _controller, _engine = qml_app
        _nezot_nyit(window, qt_app)

        assert _gyerek(window, "viewerLayoutAb").property("enabled") is True

    def test_az_AB_szegmens_valt(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _ab_modba(window, qt_app)

        assert nezo.property("layoutMode") == "ab"

    def test_a_ket_oldal_KULONBOZO_kepet_mutat(self, qml_app, qt_app):
        """Ez a mód ÍGÉRETE — enélkül a buboréksúgó hazudik."""
        window, _controller, _engine = qml_app
        nezo = _ab_modba(window, qt_app)

        assert nezo.property("abMasikSor") != nezo.property("currentIndex")

    def test_AA_modban_UGYANAZ_a_ket_oldal(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _nezot_nyit(window, qt_app)
        _kattint(window, qt_app, "viewerLayoutAa")

        assert nezo.property("abMasikSor") == nezo.property("currentIndex")

    def test_a_masik_oldal_a_SAJAT_rekeszen_at_jon(self, qml_app, qt_app):
        """#3187: a másik oldal a MÁSODIK előnézet-rekeszén át rendereli.

        ⚠️ Ez a próba korábban azt állította, hogy AB módban a másik oldal a
        NYERS fájlt mutatja — az akkori állapot leírása volt, nem szándék: a
        #3014 törzse is kimondta, hogy „nálunk egy szerkesztési állapot van".
        A #3187 óta van második rekesz, és azért kell, mert a másik oldal MÁS
        fotót mutat: annak a mentett `filters=` láncával kell látszania,
        ahogy a rácsban és az egy képes nézetben is — különben ugyanaz a kép
        kétféleképp látszik a programban.

        A próba SZÁNDÉKA változatlan: a két fél NE ugyanabból a forrásból
        jöjjön. Ezt most a rekesz-kulcs (`@masodik`) mondja ki.

        #3773: a bal (`viewerImageElotte`) a `currentIndex`-et, a jelenlegi
        (kijelölt) képet mutatja — azt a FŐ vezérlő rendereli; a jobb
        (`viewerImage`) a `abMasikSor`-t, a NEM kijelölt „másik" oldalt — azt
        a második rekesz.
        """
        window, _controller, _engine = qml_app
        _ab_modba(window, qt_app)

        forras = _gyerek(window, "viewerImage").property("source").toString()
        assert forras.startswith("image://editpreview/"), forras
        assert "@masodik" in forras, forras
        fo = _gyerek(window, "viewerImageElotte").property("source").toString()
        assert "@masodik" not in fo

    def test_mindket_kep_LATSZIK_AB_modban(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _ab_modba(window, qt_app)

        assert _gyerek(window, "viewerImage").property("visible") is True
        assert _gyerek(window, "viewerImageElotte").property("visible") is True


class TestASzegmensSorrend:
    def test_a_MERT_sorrend_1up_AB_AA(self, qml_app, qt_app):
        """`only_1up` · `ab_2up` · `aa_2up` — a respack LS/MS/RS rajza."""
        window, _controller, _engine = qml_app
        _nezot_nyit(window, qt_app)

        csoport = _gyerek(window, "viewerLayoutGroup")
        nevek = [
            gyerek.property("objectName")
            for gyerek in csoport.children()
            if gyerek.property("objectName")
            and str(gyerek.property("objectName")).startswith("viewerLayout")
        ]
        assert nevek == [
            "viewerLayoutOnly1up",
            "viewerLayoutAb",
            "viewerLayoutAa",
        ], f"a szegmensek sorrendje nem a MÉRT: {nevek}"


class TestAzElrendezesValto:
    def test_a_valto_CSAK_2up_modban_latszik(self, qml_app, qt_app):
        """`editpanel.tre:1172` — `m_hidden` az alapállapot."""
        window, _controller, _engine = qml_app
        _nezot_nyit(window, qt_app)

        assert _gyerek(window, "viewerSwapLayout").property("visible") is False

    def test_2up_modban_MEGJELENIK(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _ab_modba(window, qt_app)

        assert _gyerek(window, "viewerSwapLayout").property("visible") is True

    def test_a_VIZSZINTES_az_alapertelmezes(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _ab_modba(window, qt_app)

        assert nezo.property("fuggolegesElrendezes") is False

    def test_a_valto_ATFORDIT_es_VISSZA(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _ab_modba(window, qt_app)

        _kattint(window, qt_app, "viewerSwapLayout")
        assert nezo.property("fuggolegesElrendezes") is True

        _kattint(window, qt_app, "viewerSwapLayout")
        assert nezo.property("fuggolegesElrendezes") is False

    def test_VIZSZINTESEN_a_ket_kep_EGYMAS_MELLETT_all(self, qml_app, qt_app):
        """A #3013-ban mindkét kép fél széles volt, de a fő kép KÖZÉPRE
        horgonyozva — a két kép EGYMÁSRA csúszott. Ez a próba a tényleges
        vízszintes átfedést méri, nem a méretet."""
        window, _controller, _engine = qml_app
        _ab_modba(window, qt_app)

        # #3741: a két kép a saját felének keretében áll — a közös
        # koordináta a jelenet, nem a szülőhöz képesti `x`
        bal = _gyerek(window, "viewerImageElotte")
        jobb = _gyerek(window, "viewerImage")
        bal_jobb_szele = bal.mapToScene(QPointF(bal.property("width"), 0)).x()
        jobb_kezdete = jobb.mapToScene(QPointF(0, 0)).x()
        assert jobb_kezdete >= bal_jobb_szele - 1, (
            "a fő kép átlóg a másik kép területére "
            f"(bal vége: {bal_jobb_szele}, fő kezdete: {jobb_kezdete})"
        )

    def test_FUGGOLEGESEN_a_ket_kep_EGYMAS_ALATT_all(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _ab_modba(window, qt_app)
        _kattint(window, qt_app, "viewerSwapLayout")

        felso = _gyerek(window, "viewerImageElotte")
        also = _gyerek(window, "viewerImage")
        felso_alja = felso.mapToScene(QPointF(0, felso.property("height"))).y()
        also_teteje = also.mapToScene(QPointF(0, 0)).y()
        assert also_teteje >= felso_alja - 1, (
            "a fő kép átlóg a felső kép területére "
            f"(felső alja: {felso_alja}, fő teteje: {also_teteje})"
        )


def _negy_kep(lib) -> None:
    for nev in ("a", "b", "c", "d"):
        make_jpeg(lib / f"{nev}.jpg", size=(120, 90))


@pytest.fixture
def negy_kepes_app(qt_app, tmp_path):
    gen = _build_qml_app(qt_app, tmp_path, kepeket_keszit=_negy_kep)
    yield next(gen)
    try:
        next(gen)
    except StopIteration:
        pass


def _valodi_klikk(window, qt_app, elem) -> None:
    """Valódi egérkattintás az elem közepére (`QTest.mouseClick`) — a
    `TapHandler` tényleges célterületén át."""
    pont = elem.mapToScene(QPointF(elem.property("width") / 2,
                                   elem.property("height") / 2))
    QTest.mouseClick(window, Qt.MouseButton.LeftButton,
                     Qt.KeyboardModifier.NoModifier,
                     QPoint(int(pont.x()), int(pont.y())))
    for _ in range(20):
        qt_app.processEvents()


def _filmszalag_elem(window, sor: int):
    film = _gyerek(window, "viewerFilmstrip")
    for elem in film.property("contentItem").childItems():
        if elem.property("racsSor") == sor:
            return elem
    raise AssertionError(f"a filmszalagon nincs {sor}. sor")


def _ab_modba_latszo_ablakban(window, qt_app):
    window.resize(1280, 1024)
    window.show()
    for _ in range(20):
        qt_app.processEvents()
    nezo = _nezot_nyit(window, qt_app)
    _valodi_klikk(window, qt_app, _gyerek(window, "viewerLayoutAb"))
    assert nezo.property("layoutMode") == "ab"
    return nezo


class TestAFilmszalag:
    def test_AB_modban_a_JOBB_oldal_kepet_valtja(self, qml_app, qt_app):
        """A válogató munkafolyamat lelke: a `swap_2up_focus` választja
        ki, melyik felet lapozzuk. #3773: a bal a `currentIndex`-et
        mutatja — a `masodikIndex` (a JOBB oldal) állítása ezért nem
        mozdíthatja a fő képet."""
        window, _controller, _engine = qml_app
        nezo = _ab_modba(window, qt_app)
        _kattint(window, qt_app, "viewerSwapFocus")
        assert nezo.property("aktivOldal") == "jobb"

        elotte = nezo.property("currentIndex")
        nezo.setProperty("masodikIndex", elotte)
        qt_app.processEvents()

        assert nezo.property("currentIndex") == elotte, (
            "a jobb oldal lapozása elmozdította a fő képet"
        )
        assert nezo.property("abMasikSor") == elotte

    def test_a_BAL_oldal_a_fo_kepet_valtja(self, qml_app, qt_app):
        """#3773: a bal a `currentIndex`-et mutatja és alapból kijelölt —
        a `currentIndex` közvetlen állítása ezért a bal oldalt lapozza."""
        window, _controller, _engine = qml_app
        nezo = _ab_modba(window, qt_app)
        assert nezo.property("aktivOldal") == "bal"

        nezo.setProperty("currentIndex", 1)
        qt_app.processEvents()

        assert nezo.property("currentIndex") == 1

    def test_filmszalag_kattintas_bal_fokusznal_a_BAL_kepet_csereli(
        self, negy_kepes_app, qt_app
    ):
        """#3773: VALÓDI kattintás a filmszalag elemére — a kijelölt (bal)
        oldal cserélődik, a jobb a következő képre áll vele."""
        window = negy_kepes_app[0]
        nezo = _ab_modba_latszo_ablakban(window, qt_app)
        assert nezo.property("aktivOldal") == "bal"

        _valodi_klikk(window, qt_app, _filmszalag_elem(window, 2))

        assert nezo.property("currentIndex") == 2
        assert nezo.property("aktivSor") == 2
        assert nezo.property("abMasikSor") == 3

    def test_filmszalag_kattintas_jobb_fokusznal_a_JOBB_kepet_csereli(
        self, negy_kepes_app, qt_app
    ):
        """#3773: jobb fókusznál a kijelölt JOBB oldal cserélődik, a bal
        (`currentIndex`) helyben marad."""
        window = negy_kepes_app[0]
        nezo = _ab_modba_latszo_ablakban(window, qt_app)
        _valodi_klikk(window, qt_app, _gyerek(window, "viewerImage"))
        assert nezo.property("aktivOldal") == "jobb"

        _valodi_klikk(window, qt_app, _filmszalag_elem(window, 3))

        assert nezo.property("currentIndex") == 0
        assert nezo.property("abMasikSor") == 3
        assert nezo.property("aktivSor") == 3
