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

        #1420: a sáv egyetlen `RowLayout`-ja megszűnt (36,5 %-os osztópont),
        ezért az „egy sor implicitWidth-je" nem mérhető többé. Ami helyette
        mérhető — és erősebb is —: a minimumra állított ablakban a
        LEGJOBBSZÉLSŐ elem (a műveletsor) tényleges jobb széle beleférjen a
        sávba. Ha egy elem megnő (betű, fordítás, új gomb), ez bukik el, és
        akkor az állandót kell emelni, nem ezt a tesztet lazítani.

        Az állandó ma tiszta geometria (nincs benne feliratszélesség), de
        épp ezért kell ÉLŐ mérés: a levezetés csak addig igaz, amíg minden
        elem tényleg fix méretű marad.
        """
        window = qml_app[0]
        sav = _gyerek(window, "trayMainBar")
        sor = _gyerek(window, "trayActionRow")

        window.setProperty("width", sav.property("requiredWidth"))
        for _ in range(4):
            qt_app.processEvents()
        assert sav.property("compact") is True, (
            "a mért minimumon kompakt módot vártunk"
        )

        jobb_szel = _jobb_szel(sor)
        hatar = sav.property("width") - sav.property("rightMargin")
        assert jobb_szel <= hatar + TURES, (
            f"a műveletsor jobb széle ({jobb_szel}) túllóg a sáv "
            f"jobb margóján ({hatar}) — emeld a `requiredWidth`-et"
        )

    def test_a_minimumon_a_felso_sor_is_befer(self, qml_app, qt_app):
        """#1420: a jobb sáv FELSŐ sora (★ / forgatás / nagyítás-csúszka)
        betűfüggő tételeket is tartalmaz (a − és + jelek), ezért külön
        mérjük — ez a maradék hely, ahol a platform betűje még számít."""
        window = qml_app[0]
        sav = _gyerek(window, "trayMainBar")
        window.setProperty("width", sav.property("requiredWidth"))
        for _ in range(4):
            qt_app.processEvents()
        csillagok = _gyerek(window, "trayStarGroup")
        nagyitas = _gyerek(window, "trayZoomGroup")
        assert _jobb_szel(csillagok) <= nagyitas.mapToScene(
            QPointF(0, 0)
        ).x() + TURES, (
            "a csillag/forgatás csoport a minimumon belelóg a "
            "nagyítás-csúszkába"
        )
        assert _jobb_szel(nagyitas) <= sav.property("width") + TURES
