"""#3756: kettős nézetben BAL fókusznál a „Selected" jelvény a felső
sávra csúszott, és a feliratsáv (a kék infó-sáv, `TrayBar.qml`) a JOBB
kép adatait mutatta, nem a kijelöltét.

## A jelvény (`viewerFocusBadge`)

A `#3663` mérése négyzetes próbaképekkel igazolta a jelvény helyét — de
négyzetes képnél a bal/jobb fél letterbox-margója egyenlő, tehát a hiba
nem látszott. Élő, ELTÉRŐ arányú fotókkal (`test_kettos_nezet_fokusz_
nagyitas_3741.py` `ket_kep`: `a.jpg` 640×400, `b.jpg` 300×500, ALLÓ) a
bal (`photoElotte`) fél a magasságra illesztve tölti ki a rekeszt —
felső margója majdnem 0. A jelvény korábbi képlete (`kepFent - height -
merolegesRes`) ekkor a `viewerTopBar` SÁVJÁBA lóg (mérve: a jelvény teteje
36 px, a felső sáv alja 75 px — a jelvény a sávon BELÜL áll, nem fölötte).

A javítás: a vízszintes elrendezésben a jelvény `y`-ja nem mehet a közös
szülő (a fotó-terület és a jelvény TESTVÉRSZINTJE, közvetlenül a felső
sáv ALATT) teteje fölé — ez garantálja, hogy sosem takarja a felső sáv
vezérlőit (▶, ◀, filmszalag stb.), függetlenül a fókuszban lévő kép
arányától.

## A feliratsáv (`trayBar` → `viewerInfo(row)`)

A `Main.qml` a tálca `viewerIndex`-ét a néző `currentIndex`-éhez kötötte —
csakhogy `currentIndex` MINDIG a jobb/alsó félé (`PhotoViewer.qml`
`photo` `source`-a), a kijelölt oldal pedig `aktivSor` (bal fókusznál az
`abMasikSor`). Bal fókusznál a sáv így a NEM kijelölt kép nevét, dátumát,
méretét és sorszámát mutatta. A javítás a kötést `aktivSor`-ra viszi.
"""

from __future__ import annotations

from tests.app.qml_functional.test_kettos_nezet_fokusz_nagyitas_3741 import (
    _bal_fokusz,
    ket_kep,  # noqa: F401 - fixture
)
from tests.app.qml_functional.test_kettos_nezet_gombsor_helye_3663 import (
    _ab_modba,
    _elem_teglalap,
    _gyerek,
    _klikk,
)

_TURES = 1.0


class TestAJelvenyNemTakarjaAFelsoSavot:
    """Kész-ha 1. pont: a jelvény bal fókusznál sem takar vezérlőt."""

    def test_bal_fokusznal_a_jelveny_a_felso_sav_ALATT_all(
        self, ket_kep, qt_app  # noqa: F811
    ):
        window, _controller, _engine = ket_kep
        window.resize(1280, 1024)
        window.show()
        for _ in range(20):
            qt_app.processEvents()

        _bal_fokusz(window, qt_app)

        topsav = _elem_teglalap(_gyerek(window, "viewerTopBar"))
        jelveny = _elem_teglalap(_gyerek(window, "viewerFocusBadge"))

        assert jelveny["fent"] >= topsav["lent"] - _TURES, (
            f"a jelvény teteje ({jelveny['fent']:.0f} px) a felső sáv "
            f"({topsav['fent']:.0f}…{topsav['lent']:.0f} px) BELSEJÉBE "
            "lóg — takarhatja a ▶/◀ gombokat"
        )

    def test_jobb_fokusznal_is_a_felso_sav_ALATT_all(self, ket_kep, qt_app):  # noqa: F811
        """Ellenpróba: a korábban is helyes jobb fókusz a javítás UTÁN is
        a sáv alatt marad (a klemp nem mozdítja el feleslegesen)."""
        window, _controller, _engine = ket_kep
        window.resize(1280, 1024)
        window.show()
        for _ in range(20):
            qt_app.processEvents()
        nezo = _ab_modba(window, qt_app)
        assert nezo.property("aktivOldal") == "jobb"

        topsav = _elem_teglalap(_gyerek(window, "viewerTopBar"))
        jelveny = _elem_teglalap(_gyerek(window, "viewerFocusBadge"))

        assert jelveny["fent"] >= topsav["lent"] - _TURES


class TestAFeliratsavAKijeloltKepetKoveti:
    """Kész-ha 2. pont: a feliratsáv (kék infó-sáv) a KIJELÖLT kép
    nevét, dátumát, méretét és sorszámát mutatja, nem a jobb/alsó félét."""

    def test_bal_fokusznal_a_bal_kep_adatai_latszanak(self, ket_kep, qt_app):  # noqa: F811
        window, _controller, _engine = ket_kep
        window.resize(1280, 1024)
        window.show()
        for _ in range(20):
            qt_app.processEvents()

        _bal_fokusz(window, qt_app)

        info = _gyerek(window, "trayInfoText")
        szoveg = info.property("nyersSzoveg")
        assert "b.jpg" in szoveg, (
            f"a feliratsáv nem a kijelölt (bal) kép nevét mutatja: {szoveg!r}"
        )
        assert "a.jpg" not in szoveg, (
            f"a feliratsáv a NEM kijelölt (jobb) kép nevét mutatja: {szoveg!r}"
        )

    def test_jobb_fokusznal_a_jobb_kep_adatai_latszanak(self, ket_kep, qt_app):  # noqa: F811
        window, _controller, _engine = ket_kep
        window.resize(1280, 1024)
        window.show()
        for _ in range(20):
            qt_app.processEvents()
        nezo = _ab_modba(window, qt_app)
        assert nezo.property("aktivOldal") == "jobb"

        info = _gyerek(window, "trayInfoText")
        szoveg = info.property("nyersSzoveg")
        assert "a.jpg" in szoveg, (
            f"a feliratsáv nem a kijelölt (jobb) kép nevét mutatja: {szoveg!r}"
        )
        assert "b.jpg" not in szoveg

    def test_kattintassal_valtott_fokusz_is_kovetve(self, ket_kep, qt_app):  # noqa: F811
        """A fókuszváltás nem csak a `viewerSwapFocus` gombbal, hanem a
        képre kattintással is működik (#3663.4 mintája) — a feliratsávnak
        ezt is követnie kell."""
        window, _controller, _engine = ket_kep
        window.resize(1280, 1024)
        window.show()
        for _ in range(20):
            qt_app.processEvents()
        nezo = _ab_modba(window, qt_app)
        assert nezo.property("aktivOldal") == "jobb"

        _klikk(qt_app, window, _gyerek(window, "viewerImageElotte"))
        assert nezo.property("aktivOldal") == "bal"

        info = _gyerek(window, "trayInfoText")
        szoveg = info.property("nyersSzoveg")
        assert "b.jpg" in szoveg
        assert "a.jpg" not in szoveg
