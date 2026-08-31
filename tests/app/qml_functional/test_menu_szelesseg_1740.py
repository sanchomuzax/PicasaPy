"""#1740 — a menük szélessége igazodjon a felirataihoz.

**A bejelentés.** „A magyar menüfeliratok sok esetben csonkoltak, mert a
menü ablakok szélessége nincs az adott nyelvű fordításokhoz igazítva."

**Amit MÉRTÜNK.** A QtQuick.Controls `Menu`-je egyáltalán nem méri meg a
tételeit: a `contentWidth`-je 0 marad, a szélességét a háttér rögzített
`implicitWidth`-je adja — **200 képpont**, nyelvtől függetlenül. A
menüsáv 18 menüje mind pontosan 200 széles volt, miközben a magyar
feliratok 51 tételen 186 képpontnál szélesebb helyet kértek (a
leghosszabb: „Rendezés a legutóbbi változtatások alapján", 325 px).
Tehát nem az angolhoz igazodott — sehová nem igazodott.

Az őr ezért KÉT irányból fog:

1. `TestPicasaMenuMeri` — a komponens szintjén: egy hosszú feliratú tétel
   szélesíti a menüt, és nyelvváltás után (a feliratok cseréjekor) újra.
2. `TestMenusavMagyarul` — a VALÓDI menüsávon, magyar fordítással: egyetlen
   tétel felirata sem lóghat ki a menüből.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QTranslator, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem  # noqa: F401  (a QQuickItem* konverter)

import picasapy.app

_I18N_DIR = Path(picasapy.app.__file__).parent / "i18n"

#: A stílus alapértelmezett menüszélessége — a PicasaMenu alsó korlátja is.
ALAP_SZELESSEG = 200


#: A létrehozott objektumok és komponenseik életben tartása. A
#: `QQmlComponent.create()` eredményét a motor JavaScript-tulajdonba
#: adja; referencia nélkül a szemétgyűjtő a következő eseményhurokban
#: elviszi, és a teszt „already deleted" hibára fut.
_ELETBEN: list = []


def _keszits(engine, qml: str):
    """QML-forrásból objektum a MEGLÉVŐ motorral (import-útvonalastul)."""
    komponens = QQmlComponent(engine)
    komponens.setData(qml.encode("utf-8"), QUrl())
    hibak = [h.toString() for h in komponens.errors()]
    assert hibak == [], hibak
    objektum = komponens.create()
    assert objektum is not None
    QQmlEngine.setObjectOwnership(
        objektum, QQmlEngine.ObjectOwnership.CppOwnership
    )
    _ELETBEN.append((komponens, objektum))
    return objektum


def _menuk(gyoker) -> list[QObject]:
    """A fában lévő menük (a QML-típusnév `PicasaMenu_QMLTYPE_*`).

    A `PicasaMenuItem`/`PicasaMenuBar` neve is ezzel a betűsorral kezdődik,
    ezért az aláhúzás a mintában NEM elhagyható."""
    return [
        gy
        for gy in gyoker.findChildren(QObject)
        if gy.metaObject().className().startswith("PicasaMenu_QMLTYPE")
    ]


def _tetelek(menu) -> list[QObject]:
    return [
        gy
        for gy in menu.findChildren(QObject)
        if "MenuItem" in gy.metaObject().className()
    ]


class TestPicasaMenuMeri:
    """A komponens szerződése: a szélesség a tételekhez igazodik.

    A menü ABLAKBAN él, nem szabadon: egy szülő nélküli `Menu` meg sem
    nyílik („cannot show menu: parent is null"), tehát a megnyitásra kötött
    újramérést nem lehetne rajta próbára tenni."""

    _HOSSZU_FELIRAT = "Rendezés a legutóbbi változtatások alapján"

    @staticmethod
    def _ablak_qml(felirat: str) -> str:
        return (
            "import QtQuick\n"
            "import QtQuick.Controls\n"
            "import PicasaPy 1.0\n"
            "ApplicationWindow { width: 600; height: 300; visible: true\n"
            '  PicasaMenu { objectName: "m"\n'
            '    MenuItem { objectName: "tetel"; text: "%s" } } }\n'
            % felirat
        )

    def _menu(self, engine, felirat: str):
        ablak = _keszits(engine, self._ablak_qml(felirat))
        return ablak.findChild(QObject, "m")

    def test_a_rovid_menu_az_alap_szelessegen_marad(self, qml_app, qt_app):
        _window, _controller, engine = qml_app
        try:
            menu = self._menu(engine, "rövid")
            qt_app.processEvents()
            szeles = menu.property("implicitWidth")
            assert ALAP_SZELESSEG <= szeles <= ALAP_SZELESSEG + 16, (
                f"a rövid menü {szeles:.0f} képpont — se szűkebb nem lehet "
                "az eddigi 200-nál, se érdemben szélesebb"
            )
        finally:
            _ELETBEN.clear()

    def test_a_hosszu_tetel_szelesiti_a_menut(self, qml_app, qt_app):
        _window, _controller, engine = qml_app
        try:
            menu = self._menu(engine, self._HOSSZU_FELIRAT)
            qt_app.processEvents()
            tetel = menu.findChild(QObject, "tetel")
            assert tetel is not None
            kert = tetel.property("implicitWidth")
            assert kert > ALAP_SZELESSEG, (
                f"a próbafelirat csak {kert:.0f} képpontot kér — a teszt "
                "így nem bizonyítana semmit (más betűméret?)"
            )
            assert menu.property("implicitWidth") >= kert, (
                f"a menü {menu.property('implicitWidth'):.0f} képpont "
                f"széles, a leghosszabb tétele {kert:.0f} — a felirat "
                "csonkolódik (#1740)"
            )
        finally:
            _ELETBEN.clear()

    def test_a_felirat_megvaltozasa_ujramerest_valt_ki(self, qml_app, qt_app):
        """Nyelvváltáskor a feliratok cserélődnek — a menünek követnie kell.

        Az `implicitWidth`-kötés magától NEM futna újra (az `itemAt(i)`
        eredménye nem követhető tulajdonság), ezért a `PicasaMenu` a
        megnyitás előtt mér. A teszt ezt az utat járja: felirat csere,
        majd megnyitás."""
        _window, _controller, engine = qml_app
        try:
            menu = self._menu(engine, "rövid")
            qt_app.processEvents()
            elotte = menu.property("implicitWidth")

            menu.findChild(QObject, "tetel").setProperty(
                "text", self._HOSSZU_FELIRAT
            )
            qt_app.processEvents()

            menu.setProperty("visible", True)
            qt_app.processEvents()
            utana = menu.property("implicitWidth")
            menu.setProperty("visible", False)
            qt_app.processEvents()

            assert utana > elotte, (
                f"a hosszabb feliratra a menü {elotte:.0f}-ról nem "
                f"szélesedett ki ({utana:.0f}) — nyelvváltás után a "
                "feliratok csonkolva maradnának (#1740)"
            )
        finally:
            _ELETBEN.clear()


class TestMenusavMagyarul:
    """A VALÓDI menüsáv, a VALÓDI magyar fordítással."""

    _MENUSAV = (
        "import QtQuick\n"
        "import QtQuick.Controls\n"
        "import PicasaPy 1.0\n"
        "ApplicationWindow { width: 1200; height: 200; visible: true\n"
        '  menuBar: PicasaMenuBar { objectName: "bar" } }\n'
    )

    @pytest.fixture
    def magyar_menusav(self, qml_app, qt_app):
        forditó = QTranslator(qt_app)
        assert forditó.load("picasapy_hu", str(_I18N_DIR)), (
            f"a magyar .qm nem tölthető be innen: {_I18N_DIR}"
        )
        qt_app.installTranslator(forditó)
        _window, _controller, engine = qml_app
        engine.retranslate()
        ablak = _keszits(engine, self._MENUSAV)
        qt_app.processEvents()
        try:
            yield ablak.findChild(QObject, "bar")
        finally:
            qt_app.removeTranslator(forditó)
            _ELETBEN.clear()

    def test_egyetlen_magyar_menufelirat_sem_csonkol(
        self, magyar_menusav, qt_app
    ):
        menuk = _menuk(magyar_menusav)
        assert len(menuk) >= 10, (
            f"csak {len(menuk)} menüt találtunk a menüsávban — a mérés "
            "romlott el, nem a menük fogytak el"
        )
        vizsgalt = 0
        csonkolt: list[str] = []
        for menu in menuk:
            menu.setProperty("visible", True)
            qt_app.processEvents()
            szelesseg = menu.property("width") or 0
            for tetel in _tetelek(menu):
                tartalom = tetel.property("contentItem")
                if tartalom is None or not tetel.property("visible"):
                    continue
                vizsgalt += 1
                kert = tartalom.property("implicitWidth") or 0
                kapott = tartalom.property("width") or 0
                if kert > kapott + 0.5:
                    csonkolt.append(
                        f"{menu.property('title')} ▸ "
                        f"{tetel.property('text')!r} "
                        f"({kert:.0f} kell, {kapott:.0f} jut, "
                        f"a menü {szelesseg:.0f})"
                    )
            menu.setProperty("visible", False)
            qt_app.processEvents()

        assert vizsgalt > 50, (
            f"mindössze {vizsgalt} menütételt mértünk — üres őr"
        )
        assert csonkolt == [], (
            f"{len(csonkolt)} magyar menütétel felirata csonkol (#1740):\n"
            + "\n".join(csonkolt[:15])
        )
