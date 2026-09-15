"""#3014: a kettős nézetben a KIJELÖLT oldal képe megy az albumba.

## A mérés

A jegy a válogató munkafolyamatot `TwoUpAddToAlbum` néven említette (a
#434 nyomán). ⛔ **A binárisban ilyen sztring nincs**: a `TwoUp` minta
mind a hat találata a `swap_2up_*` / `Confirm2up*` családba tartozik, és
`addtoalbum`-ra egyetlen, általános `addToAlbum` sztring van. Az
eredetiben tehát **nincs külön 2-up gomb** — a MEGLÉVŐ albumba tétel hat
a kijelölt oldalra, amit az `editpanel/selection_label` („Kijelölve")
jelvény mutat (`docs/specs/ui-audit-editor.md` 3. táblája).

## Ami NEM ebben van

A szerkesztő parancsai (mentés, visszavonás, forgatás) továbbra is a fő
képen dolgoznak: nálunk EGY szerkesztési állapot van, a másik oldal a
nyers fájlt mutatja. A második, önállóan szerkeszthető előnézet
(`editpanel/preview2` + `previewclip2`, 26 hivatkozás) — és vele az
ütközés-párbeszéd előfeltétele — külön jegy.
"""

from __future__ import annotations

from pathlib import Path

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


class TestAKijeloltOldal:
    def test_EGY_kep_modban_a_jelenlegi(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _nezot_nyit(window, qt_app)

        assert nezo.property("aktivSor") == nezo.property("currentIndex")

    def test_AB_modban_a_JOBB_oldal_az_alapertelmezes(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _nezot_nyit(window, qt_app)
        _kattint(window, qt_app, "viewerLayoutAb")

        assert nezo.property("aktivOldal") == "jobb"
        assert nezo.property("aktivSor") == nezo.property("currentIndex")

    def test_a_fokuszvalto_ATVISZI_a_kijelolt_sort(self, qml_app, qt_app):
        """Ez a válogatás lelke: a jelvény átmegy, és vele a parancsok
        célpontja is."""
        window, _controller, _engine = qml_app
        nezo = _nezot_nyit(window, qt_app)
        _kattint(window, qt_app, "viewerLayoutAb")
        _kattint(window, qt_app, "viewerSwapFocus")

        assert nezo.property("aktivOldal") == "bal"
        assert nezo.property("aktivSor") == nezo.property("abMasikSor")
        assert nezo.property("aktivSor") != nezo.property("currentIndex")

    def test_AA_modban_a_bal_oldal_UGYANAZ_a_kep(self, qml_app, qt_app):
        """Az „aa" mód ugyanazt mutatja kétszer — a fókusz átvitele nem
        változtathat célpontot."""
        window, _controller, _engine = qml_app
        nezo = _nezot_nyit(window, qt_app)
        _kattint(window, qt_app, "viewerLayoutAa")
        _kattint(window, qt_app, "viewerSwapFocus")

        assert nezo.property("aktivSor") == nezo.property("currentIndex")


class TestAzAlbumbaTetelLANCA:
    """A property önmagában nem bizonyíték — a PARANCS útját mérjük végig:
    menü → `addToAlbumRequested` → `controller.addRowsToAlbum` → `.picasa.ini`."""

    @staticmethod
    def _album_sorok(gyoker: Path, token: str) -> int:
        """Hány fotónak van `albums=` sora ezzel a tokennel."""
        darab = 0
        for ut in gyoker.rglob(".picasa.ini"):
            for sor in ut.read_text(encoding="utf-8", errors="replace").splitlines():
                if sor.startswith("albums=") and token in sor:
                    darab += 1
        return darab

    def test_a_BAL_oldal_kepe_kerul_az_albumba(self, qml_app, qt_app, tmp_path):
        window, controller, _engine = qml_app
        nezo = _nezot_nyit(window, qt_app)
        _kattint(window, qt_app, "viewerLayoutAb")

        jobb_sor = nezo.property("currentIndex")
        # az albumot a JOBB oldal képével hozzuk létre (üres listára a
        # vezérlő üres tokent ad — nincs mibe felvenni)
        token = controller.createAlbum("2up-proba", [jobb_sor])
        qt_app.processEvents()
        assert token
        assert self._album_sorok(tmp_path, token) == 1

        _kattint(window, qt_app, "viewerSwapFocus")
        assert nezo.property("aktivSor") != jobb_sor

        QMetaObject.invokeMethod(
            nezo, "openContextMenu", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", 5), Q_ARG("QVariant", 5),
        )
        qt_app.processEvents()
        menu = _gyerek(window, "viewerContextMenu")
        QMetaObject.invokeMethod(
            menu, "addToAlbumRequested", Qt.ConnectionType.DirectConnection,
            Q_ARG("QString", token),
        )
        qt_app.processEvents()
        QMetaObject.invokeMethod(menu, "close", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()

        assert self._album_sorok(tmp_path, token) == 2, (
            "a BAL oldal képe nem került az albumba — a parancs a fő képre ment"
        )
