"""A kettős nézet AB oldala a SAJÁT előnézet-rekeszén át rendereli a
másik képet (#3187, 2. lépés).

## Miért

AB módban a másik fél MÁS fotót mutat. A #3187 előtt ez a NYERS fájl volt,
tehát ha annak a fotónak mentett `filters=` lánca van, **ugyanaz a kép
kétféleképp látszott a programban**: a rácsban és az egy képes nézetben a
mentett láncával, a kettős nézet másik felén nyersen. A második
előnézet-rekesz (`EditController(slot="masodik")`) ezt oldja fel.

## Amit ez az őr állít

- AB módban a másik kép forrása az `editpreview` szolgáltatóé, és a MÁSODIK
  rekesz kulcsát viszi (`@masodik`);
- „aa" módban (#3014 óta) ez a fél is a második rekeszé: a két fél
  ugyanannak a fotónak két önálló szerkesztése (`ui-audit-editor.md`
  4/b.1). A #3013 „nyers fájl = szerkesztés előtti" viselkedését ez váltotta
  fel — a részletes őr a `test_aa_utkozes_3014.py`;
- a nézőből kilépve a második rekesz munkamenete is záruljon.

## Amit NEM állít

A LÁTVÁNYT (mit rajzol a lánc) — azt a render-oldali próbák mérik.
"""

from __future__ import annotations

from PySide6.QtCore import QObject


def _gyerek(window, nev):
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"a(z) {nev} nincs a jelenetben"
    return elem


def _nezot_nyit(window, qt_app):
    nezo = _gyerek(window, "photoViewer")
    nezo.setProperty("currentIndex", 0)
    nezo.setProperty("visible", True)
    qt_app.processEvents()
    return nezo


def _modba(window, qt_app, mod):
    nezo = _nezot_nyit(window, qt_app)
    nezo.setProperty("layoutMode", mod)
    qt_app.processEvents()
    return nezo


class TestABModban:
    def test_a_masik_kep_a_MASODIK_rekeszbol_jon(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _modba(window, qt_app, "ab")

        forras = _gyerek(window, "viewerImageElotte").property("source").toString()
        assert forras.startswith("image://editpreview/"), forras
        assert "@masodik" in forras, forras

    def test_a_ket_oldal_KULON_rekeszt_hasznal(self, qml_app, qt_app):
        """A fő kép rekesze nem a másodiké — különben egymást írnák felül."""
        window, _controller, _engine = qml_app
        _modba(window, qt_app, "ab")

        fo = _gyerek(window, "viewerImage").property("source").toString()
        masodik = _gyerek(window, "viewerImageElotte").property("source").toString()
        assert "@masodik" not in fo
        assert "@masodik" in masodik


class TestAAModban:
    def test_az_aa_fel_is_a_MASODIK_rekeszbol_jon(self, qml_app, qt_app):
        """#3014: a nyers fájl helyett a második fél saját szerkesztése."""
        window, _controller, _engine = qml_app
        _modba(window, qt_app, "aa")

        forras = _gyerek(window, "viewerImageElotte").property("source").toString()
        assert forras.startswith("image://editpreview/"), forras
        assert "@masodik" in forras

    def test_az_aa_modban_VAN_masodik_munkamenet(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _modba(window, qt_app, "aa")
        masodik = nezo.property("masodikEditCtl")
        assert masodik is not None
        assert masodik.property("previewSource") != ""


class TestLezaras:
    def test_a_nezobol_kilepve_a_masodik_rekesz_is_zar(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _modba(window, qt_app, "ab")
        masodik = nezo.property("masodikEditCtl")
        assert masodik.property("previewSource") != ""

        nezo.setProperty("visible", False)
        qt_app.processEvents()

        assert masodik.property("previewSource") == ""
