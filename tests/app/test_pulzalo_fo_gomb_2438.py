"""#2438: a panel FŐ gombja pulzál — az eredeti „throb" állapota.

Az eredeti Picasában **13 elem** villog, név szerint (a `respack.yt`
`superbutton` kötéslistájából); nálunk **egyetlen gomb sem**. Ez nem
díszítés: ez mondja meg a felhasználónak, melyik gombra kell nyomnia a
művelet befejezéséhez.

## Amit a mérés AD, és amit NEM

* **AD**: a pulzálás a KERETET mozgatja (`#629BC3` és a nyugalmi keret
  között), a kitöltést nem — az eredeti `_t` állapotképe is csak a keretben
  tér el.
* **NEM AD**: az ÜTEMET. Sem a periódus, sem a görbe nincs mérve. A
  választott 800 ms oda, 800 ms vissza, `Easing.InOutSine` — ez a MI
  döntésünk, visszafogott és egyenletes. Ha egyszer valaki lemér egy
  képernyőfelvételt, ezt a két számot kell cserélni.

## Amit szándékosan NEM kötöttem be

A „Speciális effektusok használata" jelölő (`optionsUiTransitionsCheck`)
ma **tiltott helyőrző** — nincs mögötte élő beállítás. Ahhoz kötni a
pulzálást azt a látszatot keltené, hogy a kapcsoló működik. A `throbbing`
tulajdonság a hívóé; amint lesz élő beállítás, egyetlen kötés bekapcsolja.
"""

from __future__ import annotations

import pytest
from PySide6.QtGui import QColor


@pytest.fixture
def app_module():
    import picasapy.app.application as module

    return module


def _load_button(app_module, properties=None):
    from PySide6.QtQml import QQmlComponent, QQmlEngine

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    factory = QQmlComponent(
        engine, str(app_module._APP_DIR / "qml" / "PicasaPy" / "PicasaButton.qml")
    )
    item = factory.createWithInitialProperties({"text": "Mehet", **(properties or {})})
    assert item is not None, factory.errorString()
    return item, factory, engine


class TestAPulzalasFeltetelei:
    def test_alapbol_NEM_pulzal(self, app_module, qt_app):
        gomb, _f, _e = _load_button(app_module)
        assert gomb.property("throbbing") is False
        assert gomb.property("throbFut") is False

    def test_bekapcsolva_pulzal(self, app_module, qt_app):
        gomb, _f, _e = _load_button(app_module, {"throbbing": True})
        assert gomb.property("throbFut") is True

    def test_a_TILTOTT_gomb_nem_pulzal(self, app_module, qt_app):
        """Ami nem kattintható, arra nincs értelme mutogatni."""
        gomb, _f, _e = _load_button(
            app_module, {"throbbing": True, "enabled": False}
        )
        assert gomb.property("throbFut") is False

    def test_LENYOMVA_nem_pulzal(self, app_module, qt_app):
        gomb, _f, _e = _load_button(app_module, {"throbbing": True, "down": True})
        assert gomb.property("throbFut") is False


class TestAMegnyomasLeallitja:
    def test_kattintas_utan_megall(self, app_module, qt_app):
        """„A pulzálás leáll, amikor a gombot megnyomták" — a gomb elvégezte
        a dolgát, nincs mire tovább mutatnia."""
        gomb, _f, _e = _load_button(app_module, {"throbbing": True})
        assert gomb.property("throbFut") is True

        gomb.clicked.emit()
        qt_app.processEvents()

        assert gomb.property("throbFut") is False, (
            "a gomb a kattintás után is pulzál — a felhasználót olyasmire "
            "biztatja, amit már megtett"
        )

    def test_a_hivo_UJRA_indithatja(self, app_module, qt_app):
        gomb, _f, _e = _load_button(app_module, {"throbbing": True})
        gomb.clicked.emit()
        qt_app.processEvents()
        assert gomb.property("throbFut") is False

        gomb.setProperty("throbbing", False)
        gomb.setProperty("throbbing", True)
        qt_app.processEvents()

        assert gomb.property("throbFut") is True


class TestAKitoltesERINTETLEN:
    def test_a_pulzalas_csak_a_keretet_mozgatja(self, app_module, qt_app):
        """Az eredeti `_t` állapotképe is csak a keretben tér el."""
        nyugodt, _f1, _e1 = _load_button(app_module)
        pulzalo, _f2, _e2 = _load_button(app_module, {"throbbing": True})

        assert QColor(pulzalo.property("surfaceTop")) == QColor(
            nyugodt.property("surfaceTop")
        )
        assert QColor(pulzalo.property("surfaceBottom")) == QColor(
            nyugodt.property("surfaceBottom")
        )
