"""#1526: az „Automatikus kitöltés" a szövegmező helyi menüjéből — ÉLŐ kapcsoló.

A Picasa szövegmező-helyimenüje (`Address` menüosztály) hét tételes, és a
hetedik az `ID_AUTOCOMPLETE`: a mezők kiegészítése **kikapcsolható**, onnan,
ahol zavarja. Nálunk a tétel a #422 óta ott volt, de `placeholder: true`
jelöléssel — kattinthatatlanul.

A teszt a VALÓDI menütételt süti el, és a hatást két helyen méri:

* a `controller.autoComplete` beállításban (és a `QSettings`-ben, tehát az
  újraindítás után is);
* a keresőmező javaslat-buborékjának LÁTHATÓSÁGÁN — enélkül a kapcsoló
  jelölőnégyzet volna a semmibe.
"""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject, Qt

from picasapy.app.text_input_controller import AUTO_COMPLETE_KEY


def _elem(root, nev: str) -> QObject:
    obj = root.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def _elsut(window, qt_app, nev: str) -> None:
    tetel = _elem(window, nev)
    assert not tetel.property("placeholder"), (
        f"a(z) {nev} menüpont helyfoglaló (#416), tehát halott"
    )
    assert tetel.property("enabled") is True, f"a(z) {nev} le van tiltva"
    QMetaObject.invokeMethod(tetel, "triggered", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


class TestAKapcsoloElo:
    def test_a_tetel_NEM_helyfoglalo_es_kapcsolhato(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        tetel = _elem(window, "textMenuAutoComplete")
        assert not tetel.property("placeholder")
        assert tetel.property("checkable") is True
        assert tetel.property("enabled") is True

    def test_alapbol_BE_van_kapcsolva(self, qml_app, qt_app):
        """Az eredetiben a kiegészítés működik, a menütétel a
        kikapcsolására való."""
        window, controller, _engine = qml_app
        assert controller.autoComplete is True
        assert _elem(window, "textMenuAutoComplete").property("checked") is True

    def test_a_menupontrol_kikapcsolhato(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _elsut(window, qt_app, "textMenuAutoComplete")
        assert controller.autoComplete is False

    def test_ujra_elsutve_visszakapcsol(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _elsut(window, qt_app, "textMenuAutoComplete")
        _elsut(window, qt_app, "textMenuAutoComplete")
        assert controller.autoComplete is True

    def test_a_beallitas_TULELI_az_ujrainditast(self, qml_app, qt_app):
        """Nem a QML-tulajdonságot nézzük, hanem a beállítás-tárat: ugyanazt
        olvasná be egy újraindult alkalmazás."""
        window, controller, _engine = qml_app
        _elsut(window, qt_app, "textMenuAutoComplete")
        mentett = controller._get_settings().value(AUTO_COMPLETE_KEY)
        assert str(mentett).strip().lower() in ("false", "0")


class TestAKapcsoloTENYLEG_KAPCSOL:
    """A kapcsoló nem jelölőnégyzet a semmibe: a javaslat-buborék eltűnik."""

    def _buborek_eloallitas(self, window, qt_app):
        """Valódi javaslat-buborék: beírt keresőszöveg + találat."""
        _elem(window, "searchField").setProperty("text", "kep")
        bubi = _elem(window, "searchSuggestions")
        bubi.setProperty(
            "suggestions",
            [{"kind": "folder", "name": "kepek", "count": 2, "param": "/x"}],
        )
        qt_app.processEvents()
        return bubi

    def test_bekapcsolva_a_buborek_LATSZIK(self, qml_app, qt_app):
        """Kontroll-mérés: a következő teszt eltűnése csak ehhez képest
        bizonyít bármit."""
        window, _controller, _engine = qml_app
        bubi = self._buborek_eloallitas(window, qt_app)
        assert bubi.property("visible") is True

    def test_kikapcsolva_a_kereso_buborekja_ELTUNIK(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        bubi = self._buborek_eloallitas(window, qt_app)
        assert bubi.property("visible") is True

        _elsut(window, qt_app, "textMenuAutoComplete")
        qt_app.processEvents()

        assert controller.autoComplete is False
        assert bubi.property("visible") is False
