"""A szerkesztő parancsai a KIJELÖLT oldalra hatnak (#3187, 3. lépés).

## A mérés és a modell

A #3014 óta a „Kijelölve" jelvény és a válogató parancsok (albumba tétel) a
kijelölt oldalt követik; a szerkesztő parancsai viszont a fő képen dolgoztak,
mert nálunk EGY szerkesztési állapot volt. A #3187 első két lépése hozta a
második előnézet-rekeszt.

Ez a lépés a **hozzárendelést** fordítja meg: a **FŐ vezérlő mindig a KIJELÖLT
oldalt szerkeszti**, a második rekesz a másikat. Így a szerkesztő-panel
egyetlen kötése sem változik (104 kötés!), a parancsok mégis a kijelölt
oldalra hatnak — és a két oldal képe is követi a hozzárendelést.

## Amit ez az őr állít

- AB módban fókuszváltás után a fő vezérlő a BAL oldal fotóját szerkeszti;
- a két kép forrása CSERÉL: a kijelölt fél a fő rekeszből, a másik a
  `@masodik`-ból jön;
- egy effekt a KIJELÖLT oldal `.picasa.ini`-jébe kerül, nem a fő képébe;
- „aa" és egy képes módban a célpont VÁLTOZATLANUL a jelenlegi kép.
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


def _forras(window, nev):
    return _gyerek(window, nev).property("source").toString()


def _lancok(gyoker: Path) -> dict[str, str]:
    """Fájlnév → `filters=` sor az összes `.picasa.ini`-ből."""
    ki: dict[str, str] = {}
    for ut in gyoker.rglob(".picasa.ini"):
        szakasz = ""
        for sor in ut.read_text(encoding="utf-8", errors="replace").splitlines():
            if sor.startswith("[") and sor.endswith("]"):
                szakasz = sor[1:-1]
            elif sor.startswith("filters=") and szakasz:
                ki[szakasz] = sor[len("filters=") :]
    return ki


class TestAFoVezerloAKijeloltOldalt:
    def test_fokuszvaltas_utan_a_BAL_fotot_szerkeszti(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _nezot_nyit(window, qt_app)
        _kattint(window, qt_app, "viewerLayoutAb")
        _kattint(window, qt_app, "viewerSwapFocus")

        modell = nezo.property("photosModel")
        bal_azonosito = modell.idAt(nezo.property("abMasikSor"))
        assert nezo.property("editCtl").property("previewSource").startswith(
            f"image://editpreview/{bal_azonosito}?"
        )

    def test_a_masodik_rekesz_a_MASIK_oldalt_kapja(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _nezot_nyit(window, qt_app)
        _kattint(window, qt_app, "viewerLayoutAb")
        _kattint(window, qt_app, "viewerSwapFocus")

        modell = nezo.property("photosModel")
        jobb_azonosito = modell.idAt(nezo.property("currentIndex"))
        assert nezo.property("masodikEditCtl").property("previewSource").startswith(
            f"image://editpreview/{jobb_azonosito}@masodik?"
        )

    def test_a_ket_kep_forrasa_CSEREL(self, qml_app, qt_app):
        """A kijelölt fél a fő rekeszből jön, a másik a `@masodik`-ból."""
        window, _controller, _engine = qml_app
        _nezot_nyit(window, qt_app)
        _kattint(window, qt_app, "viewerLayoutAb")

        # alapból a JOBB az aktív: a fő kép a fő rekeszből
        assert "@masodik" not in _forras(window, "viewerImage")
        assert "@masodik" in _forras(window, "viewerImageElotte")

        _kattint(window, qt_app, "viewerSwapFocus")

        assert "@masodik" in _forras(window, "viewerImage")
        assert "@masodik" not in _forras(window, "viewerImageElotte")


class TestAzEffektACELPONTBA:
    def test_az_effekt_a_KIJELOLT_oldal_inijebe_kerul(self, qml_app, qt_app, tmp_path):
        window, _controller, _engine = qml_app
        nezo = _nezot_nyit(window, qt_app)
        _kattint(window, qt_app, "viewerLayoutAb")
        _kattint(window, qt_app, "viewerSwapFocus")

        modell = nezo.property("photosModel")
        bal_fajl = Path(modell.filePathAt(nezo.property("abMasikSor"))).name
        jobb_fajl = Path(modell.filePathAt(nezo.property("currentIndex"))).name

        nezo.property("editCtl").applyEffect("bw")
        qt_app.processEvents()

        lancok = _lancok(tmp_path)
        assert "bw" in lancok.get(bal_fajl, ""), lancok
        assert "bw" not in lancok.get(jobb_fajl, ""), lancok


class TestAmiVALTOZATLAN:
    def test_egy_kep_modban_a_jelenlegi_kep(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _nezot_nyit(window, qt_app)

        modell = nezo.property("photosModel")
        azonosito = modell.idAt(nezo.property("currentIndex"))
        assert nezo.property("editCtl").property("previewSource").startswith(
            f"image://editpreview/{azonosito}?"
        )

    def test_aa_modban_a_fokuszvaltas_nem_valt_celpontot(self, qml_app, qt_app):
        """#3013: ott a bal fél a szerkesztés ELŐTTI kép — nem cél."""
        window, _controller, _engine = qml_app
        nezo = _nezot_nyit(window, qt_app)
        _kattint(window, qt_app, "viewerLayoutAa")
        _kattint(window, qt_app, "viewerSwapFocus")

        modell = nezo.property("photosModel")
        azonosito = modell.idAt(nezo.property("currentIndex"))
        assert nezo.property("editCtl").property("previewSource").startswith(
            f"image://editpreview/{azonosito}?"
        )
        assert _forras(window, "viewerImageElotte").startswith("file:")
