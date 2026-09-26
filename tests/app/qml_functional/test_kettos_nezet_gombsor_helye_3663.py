"""#3663: a kettős nézet gombsorának helye, a „Kijelölve" jelvény és a
képre kattintásos fókuszváltás.

## A mérés (`docs/specs/ui-audit-editor.md` 3/b, élő mérés a #3665-ből)

* A három kapcsoló (`A` · `AB` · `AA`) és a két segédgomb (fókuszváltó,
  elrendezés-váltó) a filmszalag és a ▶ **UTÁN** áll, nem előtte — a #3013
  fordítva tette.
* A „Kijelölve" jelvény **szürke** (`#666666`), fehér **félkövér**
  felirattal — a #3013 tévesen `Theme.selectionBlue` kéket adott neki.
* A jelvény a `photo` Image UTÁN, azzal egy szinten (nem előtte) áll, hogy
  garantáltan a kép fölött rajzolódjon — a #3013 a kép ELÉ tette, ezért a
  kép időnként rátakart.
* A bal/jobb (fent/lent) képre kattintás áthelyezi az aktív oldalt — a
  #3013-ban ezt csak a `swap_2up_focus` gomb tette.

## Ami NEM ebben van

A jelvény pontos pixel-helye: a képlet a binárisból nem olvasható ki
(`ui-audit-editor.md` 3/b, „Bizonyítottsági fok" megjegyzés) — a mérce az
élő összevetés a Colab kulcsképekkel, ami ehhez a felhős fejlesztői körhöz
nem áll rendelkezésre.
"""

from __future__ import annotations

from PySide6.QtCore import Q_ARG, QEvent, QMetaObject, QObject, QPointF, Qt
from PySide6.QtGui import QMouseEvent
from PySide6.QtQuick import QQuickItem


def _kattints(qt_app, ablak, elem, x: float, y: float) -> None:
    """Valódi egérkattintás az `elem` LOKÁLIS (x, y) pontján.

    Ugyanaz a minta, mint a `test_voros_keret_kattintas_604.py`-ban: a
    TapHandler ugyanazt az egységes mutató-eseménysort kapja, mint a
    MouseArea, tehát a metódushívás helyett a VALÓDI kattintást mérjük.
    """
    globalis = elem.mapToScene(QPointF(x, y))
    for tipus in (QEvent.Type.MouseButtonPress, QEvent.Type.MouseButtonRelease):
        qt_app.sendEvent(
            ablak,
            QMouseEvent(
                tipus,
                globalis,
                globalis,
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton
                if tipus == QEvent.Type.MouseButtonPress
                else Qt.MouseButton.NoButton,
                Qt.KeyboardModifier.NoModifier,
            ),
        )
    qt_app.processEvents()


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


class TestAGombsorHelye:
    def test_a_kapcsolok_a_filmszalag_UTAN_allnak(self, qml_app, qt_app):
        """A felső sáv sorrendje: Play · ◀ · filmszalag · ▶ · A|AB|AA ·
        fókuszváltó · elrendezés-váltó (mérve, 1280 px)."""
        window, _controller, _engine = qml_app
        _nezot_nyit(window, qt_app)
        toolbar = _gyerek(window, "viewerTopBar")

        sorrend = [
            "viewerPlayButton",
            "viewerPrevButton",
            "viewerFilmstrip",
            "viewerNextButton",
            "viewerLayoutGroup",
            "viewerSwapFocus",
            "viewerSwapLayout",
        ]
        nevek = [g.objectName() for g in toolbar.findChildren(QObject)]
        indexek = [nevek.index(nev) for nev in sorrend]
        assert indexek == sorted(indexek), (
            "a gombok/csoportok NEM a mért sorrendben követik egymást "
            f"a felső sávban: {indexek}"
        )

    def test_a_szegmensek_a_ket_seged_elott_allnak(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _nezot_nyit(window, qt_app)
        toolbar = _gyerek(window, "viewerTopBar")
        nevek = [g.objectName() for g in toolbar.findChildren(QObject)]

        assert nevek.index("viewerLayoutGroup") < nevek.index("viewerSwapFocus")
        assert nevek.index("viewerSwapFocus") < nevek.index("viewerSwapLayout")


class TestAJelvenySzine:
    def test_a_jelveny_SZURKE_nem_kek(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _ab_modba(window, qt_app)

        jelveny = _gyerek(window, "viewerFocusBadge")
        szin = jelveny.property("color")
        # QColor.name() -> "#rrggbb"
        assert szin.name() == "#666666", (
            f"a jelvény háttere nem a mért szürke: {szin.name()}"
        )

    def test_a_felirat_FELKOVER_es_feher(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _ab_modba(window, qt_app)

        jelveny = _gyerek(window, "viewerFocusBadge")
        # a felirat a jelvény egyetlen Text gyereke — kereséssel típus
        # szerint biztosabb, mint névvel (nincs objectName-je)
        szovegek = [
            gy for gy in jelveny.findChildren(QQuickItem)
            if gy.metaObject().className().startswith("QQuickText")
        ]
        assert szovegek, "a jelvénynek nincs Text gyereke"
        assert szovegek[0].property("font").bold(), (
            "a jelvény felirata nem félkövér"
        )
        assert szovegek[0].property("color").name() == "#ffffff"


class TestAJelvenyZSorrendje:
    def test_a_jelveny_a_photoArea_UTAN_all_a_fatban(self, qml_app, qt_app):
        """A #3013 a jelvényt a `photoArea` GYEREKÉNEK, a `photo` ELÉ
        tette — ez okozta, hogy a kép időnként a jelvény FÖLÉ rajzolt. A
        javításban a jelvény a `photoArea` TESTVÉRE, utána deklarálva."""
        window, _controller, _engine = qml_app
        _ab_modba(window, qt_app)

        jelveny = _gyerek(window, "viewerFocusBadge")
        terulet = _gyerek(window, "viewerPhotoArea")
        assert jelveny.parent() is terulet.parent(), (
            "a jelvény már nem a fotó-terület testvére"
        )


class TestAKattintasosFokuszvaltas:
    def test_a_BAL_kepre_kattintva_a_BAL_lesz_aktiv(self, qml_app, qt_app):
        """#3663.4: AB módban a bal képre kattintva a jelvény (és az
        aktív oldal) a bal képhez kerül — eddig ezt csak a
        `swap_2up_focus` gomb tudta."""
        window, _controller, _engine = qml_app
        nezo = _ab_modba(window, qt_app)
        assert nezo.property("aktivOldal") == "jobb"

        bal_kep = _gyerek(window, "viewerImageElotte")
        szel = bal_kep.property("width")
        mag = bal_kep.property("height")
        assert szel and mag, "a bal kép mérete 0×0 — nincs mire kattintani"

        _kattints(qt_app, window, bal_kep, szel / 2, mag / 2)

        assert nezo.property("aktivOldal") == "bal"

    def test_a_JOBB_kepre_kattintva_a_JOBB_lesz_aktiv(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _ab_modba(window, qt_app)
        _kattint(window, qt_app, "viewerSwapFocus")
        assert nezo.property("aktivOldal") == "bal"

        jobb_kep = _gyerek(window, "viewerImage")
        szel = jobb_kep.property("width")
        mag = jobb_kep.property("height")
        assert szel and mag, "a jobb kép mérete 0×0 — nincs mire kattintani"

        _kattints(qt_app, window, jobb_kep, szel / 2, mag / 2)

        assert nezo.property("aktivOldal") == "jobb"

    def test_1up_modban_a_kepre_kattintas_NEM_valt_oldalt(self, qml_app, qt_app):
        """1up módban nincs második oldal — a kattintás ne írja át az
        `aktivOldal`-t (ami ilyenkor amúgy sem látszik, de a `photo`
        TapHandlere `layoutMode !== "1up"`-hoz kötött)."""
        window, _controller, _engine = qml_app
        nezo = _nezot_nyit(window, qt_app)
        assert nezo.property("layoutMode") == "1up"
        kezdeti = nezo.property("aktivOldal")

        jobb_kep = _gyerek(window, "viewerImage")
        szel = jobb_kep.property("width")
        mag = jobb_kep.property("height")
        _kattints(qt_app, window, jobb_kep, szel / 2, mag / 2)

        assert nezo.property("aktivOldal") == kezdeti
