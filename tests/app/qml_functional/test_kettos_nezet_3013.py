"""#3013: a kettős nézet A/AA szegmense és a szerkesztés előtti-utáni kép.

## A mérés (`docs/specs/ui-audit-editor.md`)

A három üzemmód **egyetlen háromszegmenses vezérlő**
(`editpanel/layout_2up_group`), a hivatalos magyar buboréksúgókkal:

| elem | buboréksúgó |
|---|---|
| `only_1up_toggle` | „Csak egy kép megjelenítése" |
| `aa_2up_toggle` | „Ugyanazon kép megjelenítése kétszer" |
| `ab_2up_toggle` | „Két különböző kép megjelenítése" |

A kizárást **nem** `checked`-kötés adja, hanem a `Property uptarget`:
a lenyomott gomb a MÁSIK KETTŐT engedi fel, önmagát nem — ezért nem tud a
mi rádió-csapdánkba futni (#1468). Alapértelmezés: `only_1up_toggle`
(`Property setpressed 1`).

2-up módban jelenik meg a `swap_2up_focus` („Fókusz váltása a képek
között"), és a „Kijelölve" jelvény mutatja az aktív oldalt.

## Ami NEM ebben van

Az **AB mód** (két különböző kép), az albumba tétel és az
ütközés-párbeszéd a #3014-é. A harmadik szegmens ezért itt **tiltott** —
nem néma, hanem láthatóan még nem használható.
"""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject, Qt


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


from PySide6.QtCore import Q_ARG  # noqa: E402 — a helper fölött kell


class TestASzegmensek:
    def test_mind_a_HAROM_szegmens_ott_van(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _nezot_nyit(window, qt_app)

        for nev in ("viewerLayoutOnly1up", "viewerLayoutAa", "viewerLayoutAb"):
            assert _gyerek(window, nev) is not None

    def test_az_EGY_KEP_az_alapertelmezes(self, qml_app, qt_app):
        """`Property setpressed 1` az `only_1up_toggle`-ön."""
        nezo = _nezot_nyit(qml_app[0], qt_app)
        assert nezo.property("layoutMode") == "1up"

    def test_az_AA_szegmens_valt(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _nezot_nyit(window, qt_app)

        QMetaObject.invokeMethod(
            _gyerek(window, "viewerLayoutAa"), "kattints",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        assert nezo.property("layoutMode") == "aa"

    def test_az_AKTIV_szegmensre_kattintva_LENYOMVA_marad(self, qml_app, qt_app):
        """`uptarget`-szemantika: a lenyomott gomb a másik kettőt engedi
        fel, önmagát nem. A rádió-csapda (#1468) mérése."""
        window, _controller, _engine = qml_app
        nezo = _nezot_nyit(window, qt_app)
        gomb = _gyerek(window, "viewerLayoutAa")

        for _ in range(2):
            QMetaObject.invokeMethod(
                gomb, "kattints", Qt.ConnectionType.DirectConnection
            )
            qt_app.processEvents()

        assert nezo.property("layoutMode") == "aa", (
            "a második kattintás elengedte az aktív szegmenst"
        )

    def test_az_AB_szegmens_TILTOTT_de_ott_van(self, qml_app, qt_app):
        """A #3014 hozza — addig látható, de nem használható. A néma
        no-op rosszabb volna: a felhasználó nem tudná, hogy nem működik."""
        window, _controller, _engine = qml_app
        _nezot_nyit(window, qt_app)

        assert _gyerek(window, "viewerLayoutAb").property("enabled") is False


class TestAMasodikKep:
    def test_AA_modban_KET_kep_latszik(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _nezot_nyit(window, qt_app)
        QMetaObject.invokeMethod(
            _gyerek(window, "viewerLayoutAa"), "kattints",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        assert _gyerek(window, "viewerImage").property("visible") is True
        assert _gyerek(window, "viewerImageElotte").property("visible") is True

    def test_EGY_kep_modban_a_masodik_REJTVE(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _nezot_nyit(window, qt_app)

        assert _gyerek(window, "viewerImageElotte").property("visible") is False

    def test_a_bal_oldal_a_SZERKESZTES_ELOTTI(self, qml_app, qt_app):
        """A szűretlen kép a nyers fájl URL-je — a `filters=` lánc nélkül."""
        window, _controller, _engine = qml_app
        _nezot_nyit(window, qt_app)
        QMetaObject.invokeMethod(
            _gyerek(window, "viewerLayoutAa"), "kattints",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        elotte = _gyerek(window, "viewerImageElotte").property("source").toString()
        assert elotte.startswith("file:"), (
            f"a bal oldal nem a nyers fájlt mutatja: {elotte}"
        )
        assert "editpreview" not in elotte


class TestAFokusz:
    def test_a_jelveny_az_AKTIV_oldalon_all(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _nezot_nyit(window, qt_app)
        QMetaObject.invokeMethod(
            _gyerek(window, "viewerLayoutAa"), "kattints",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        assert nezo.property("aktivOldal") == "jobb"
        assert _gyerek(window, "viewerFocusBadge").property("visible") is True

    def test_a_swap_ATVISZI_a_fokuszt(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _nezot_nyit(window, qt_app)
        QMetaObject.invokeMethod(
            _gyerek(window, "viewerLayoutAa"), "kattints",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        QMetaObject.invokeMethod(
            _gyerek(window, "viewerSwapFocus"), "kattints",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        assert nezo.property("aktivOldal") == "bal"

    def test_a_swap_CSAK_2up_modban_latszik(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _nezot_nyit(window, qt_app)

        assert _gyerek(window, "viewerSwapFocus").property("visible") is False
