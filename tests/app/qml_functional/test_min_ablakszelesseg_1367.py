"""Az alsó műveletsáv nem lóghat ki az ablakból (#1367).

A #1345 a gombokat a mért 55×36-os FIX cellákba tette. Ennek ára van: a
gombok többé nem zsugorodnak, tehát a sáv kompakt igénye 722-ről ~830
képpontra nőtt. Ez alatt a jobb szélső elem (a zöld „Feltöltés a Google
Fotókba") **kicsúszik a látható területről**.

## Miért nem beégetett képpontszám az állítás

A sáv igénye **betű- és nyelvfüggő** — a windows-CI pontosan ezen bukott el
egyszer 1280-on (ld. a `TrayBar.qml` `compactThreshold` kommentjét). Ezért az
őr nem azt állítja, hogy „legalább 850", hanem hogy

    az ablak minimális szélessége ≥ a sáv MÉRT igénye,

és hogy ezen a minimumon a sáv jobb széle **befér**. A mért igényt a Qt
számolja ki a tényleges tartalomból (`RowLayout.implicitWidth`), tehát a
másik platformon is a helyi betűvel mér.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QPointF

#: Fél képpont tűrés: a QML geometriája tört szám lehet.
TURES = 0.5


def _gyerek(window, nev):
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _jobb_szel(elem) -> float:
    return elem.mapToScene(QPointF(elem.property("width"), 0)).x()


class TestMinimalisAblakszelesseg:
    def test_az_ablak_minimuma_fedi_a_sav_mert_igenyet(self, qml_app, qt_app):
        window = qml_app[0]
        sav = _gyerek(window, "trayMainBar")
        igeny = sav.property("requiredWidth")
        assert igeny > 0, "a tálca nem adja meg a mért szélesség-igényét"
        assert window.property("minimumWidth") >= igeny - TURES, (
            f"az ablak minimuma ({window.property('minimumWidth')}) kisebb, "
            f"mint a sáv mért igénye ({igeny})"
        )

    def test_a_minimumon_a_sav_jobb_szele_befer(self, qml_app, qt_app):
        """A minimumra állított ablakban egyetlen elem sem lóg ki."""
        window = qml_app[0]
        window.setProperty("width", window.property("minimumWidth"))
        for _ in range(4):
            qt_app.processEvents()

        szelesseg = window.property("width")
        for nev in ("trayUploadButton", "trayMainBar"):
            elem = window.findChild(QObject, nev)
            if elem is None:
                continue
            assert _jobb_szel(elem) <= szelesseg + TURES, (
                f"a(z) {nev} kilóg a minimumra állított ablakból: "
                f"{_jobb_szel(elem)} > {szelesseg}"
            )

    def test_a_mert_allando_fedi_az_ELO_kompakt_igenyt(self, qml_app, qt_app):
        """A `requiredWidth` MÉRT állandó — ez az őr méri újra élőben.

        Nem köthettük közvetlenül a sor `implicitWidth`-éhez: az a mindenkori
        MÓDOT tükrözi, a mód viszont a szélességtől függ — visszacsatolás
        lenne, és az ablak soha nem váltana kompaktra.

        Ezért itt kompakt módba állítjuk az ablakot, LEMÉRJÜK a sor tényleges
        igényét, és azt állítjuk, hogy az állandó fedi. Ha a betű vagy a
        fordítás nő, ez bukik el — és akkor az állandót kell emelni, nem ezt
        a tesztet lazítani."""
        window = qml_app[0]
        sav = _gyerek(window, "trayMainBar")
        sor = _gyerek(window, "trayRowLayout")

        window.setProperty("width", 900)
        for _ in range(4):
            qt_app.processEvents()
        assert sav.property("compact") is True, "900 px-en kompakt módot vártunk"

        # a margókat a sor és a sáv szélességének különbségéből vesszük:
        # a `QQuickAnchors` nem konvertálható Pythonra
        margok = sav.property("width") - sor.property("width")
        elo_igeny = sor.property("implicitWidth") + margok
        assert sav.property("requiredWidth") >= elo_igeny - TURES, (
            f"a mért állandó ({sav.property('requiredWidth')}) már nem fedi a "
            f"sáv élő kompakt igényét ({elo_igeny}) — emeld az állandót"
        )
