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

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt


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

    def test_a_masik_oldal_a_NYERS_fajlt_mutatja(self, qml_app, qt_app):
        """A `filters=` lánc nélkül — nem az `editpreview` szolgáltatót."""
        window, _controller, _engine = qml_app
        _ab_modba(window, qt_app)

        forras = _gyerek(window, "viewerImageElotte").property("source").toString()
        assert forras.startswith("file:")
        assert "editpreview" not in forras

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

        bal = _gyerek(window, "viewerImageElotte")
        jobb = _gyerek(window, "viewerImage")
        bal_jobb_szele = bal.property("x") + bal.property("width")
        assert jobb.property("x") >= bal_jobb_szele - 1, (
            "a fő kép átlóg a másik kép területére "
            f"(bal vége: {bal_jobb_szele}, fő kezdete: {jobb.property('x')})"
        )

    def test_FUGGOLEGESEN_a_ket_kep_EGYMAS_ALATT_all(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _ab_modba(window, qt_app)
        _kattint(window, qt_app, "viewerSwapLayout")

        felso = _gyerek(window, "viewerImageElotte")
        also = _gyerek(window, "viewerImage")
        felso_alja = felso.property("y") + felso.property("height")
        assert also.property("y") >= felso_alja - 1, (
            "a fő kép átlóg a felső kép területére "
            f"(felső alja: {felso_alja}, fő teteje: {also.property('y')})"
        )


class TestAFilmszalag:
    def test_AB_modban_a_BAL_oldal_kepet_valtja(self, qml_app, qt_app):
        """A válogató munkafolyamat lelke: a `swap_2up_focus` választja
        ki, melyik felet lapozzuk."""
        window, _controller, _engine = qml_app
        nezo = _ab_modba(window, qt_app)
        _kattint(window, qt_app, "viewerSwapFocus")
        assert nezo.property("aktivOldal") == "bal"

        elotte = nezo.property("currentIndex")
        nezo.setProperty("masodikIndex", elotte)
        qt_app.processEvents()

        assert nezo.property("currentIndex") == elotte, (
            "a bal oldal lapozása elmozdította a fő képet"
        )
        assert nezo.property("abMasikSor") == elotte

    def test_a_JOBB_oldal_a_fo_kepet_valtja(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _ab_modba(window, qt_app)
        assert nezo.property("aktivOldal") == "jobb"

        nezo.setProperty("currentIndex", 1)
        qt_app.processEvents()

        assert nezo.property("currentIndex") == 1
