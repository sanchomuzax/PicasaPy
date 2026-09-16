"""#3070 — a megjelenítési mód a felületen, KIRAJZOLT képpontokon mérve.

## Miért kirajzolt őr

A testvérfájl (`tests/app/test_tema_paletta_3070.py`) a tiszta függvényt
méri: jó-e a leképezés, marad-e az alfa. Az viszont semmit nem mond arról,
hogy a felület **tényleg** más színnel rajzol-e ki. A jegy elfogadási
feltétele ezért renderelt kimenetet kér — a tulajdonos szava a #2494-ből:
*„A tesztednek látnia kellett volna, nem csak kiszámolnia."*

Ez a próba egy kis jelenetet rajzol a `Theme` tokenjeivel (vászon, panel,
króm, fejléc), `grabWindow()`-val leveszi, és a KÉPPONTOK lumáját méri a mód
előtt és után.

## A mérce: a #1580 felvételei

A tulajdonos A/B felvételén a `Mac gamma (1.6)` a **felület elemeit**
+1,3…+4,2%-kal világosítja (a teljes képernyő lumája +3,32%, a központi fotó
+15,7%). A mi mért LUT-unk (`MAC_GAMMA_LUT`, a binárisba beégetett 256 bájt)
a téma világos paneljeire **+1,2…+3,5%**-ot ad — a sávba esik, tehát a két
egymástól független forrás (képernyőkép-mérés és bináris tábla) ugyanazt
mondja.

⚠️ **Amit ez az őr NEM állít:** hogy a teljes képernyő lumája pontosan
+3,32%-kal nő. Az a szám a felvétel ÖSSZETÉTELÉÉ (fotó + felület
arányában), nem a szabályé; egy laborban kirajzolt panel-mozaikon más arány
jön ki. A szabályt a LUT hordozza, ezt a próba a fentiek szerint méri.
"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickView
from PySide6.QtTest import QTest

_SZELES = 200
_MAGAS = 120

#: A négy sáv, amit kirajzolunk — mind a `Theme` VILÁGOS krómja, tehát rájuk
#: érvényes a #1580 felület-mérése.
_SAVOK = ("canvasBg", "panelBg", "chromeBg", "panelHeaderBg")

#: A #1580 felület-mérésének sávja (a felső határ a raszterezés miatt egy
#: hajszállal bővebb: a mért LUT +3,54%-ot ad a `chromeBg`-re).
_MIN_NOVEKMENY = 1.0
_MAX_NOVEKMENY = 4.5

_QML = """
import QtQuick
import PicasaPy

Rectangle {
    width: %d; height: %d
    color: Theme.canvasBg
    Column {
        anchors.fill: parent
        Rectangle { objectName: "sav0"; width: parent.width; height: 30; color: Theme.canvasBg }
        Rectangle { objectName: "sav1"; width: parent.width; height: 30; color: Theme.panelBg }
        Rectangle { objectName: "sav2"; width: parent.width; height: 30; color: Theme.chromeBg }
        Rectangle { objectName: "sav3"; width: parent.width; height: 30; color: Theme.panelHeaderBg }
    }
}
""" % (_SZELES, _MAGAS)

_KEEPALIVE: list = []


def _vezerlo():
    from PySide6.QtCore import QObject as QO

    from picasapy.app.display_mode_controller import DisplayModeMixin

    class Proba(DisplayModeMixin, QO):
        def __init__(self):
            super().__init__()
            self._init_display_mode()

    return Proba()


def _var_a_kirajzolasra(view: QQuickView, qt_app, masodperc: float = 10.0) -> None:
    for _ in range(5):
        qt_app.processEvents()
        QTest.qWait(20)
    elozo = None
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        mostani = view.grabWindow()
        if elozo is not None and mostani == elozo:
            return
        elozo = mostani
        time.sleep(0.01)
    qt_app.processEvents()


def _luma(szin: QColor) -> int:
    """A MÉRT egész luma (spec: `(77·R + 151·G + 28·B) >> 8`)."""
    return (77 * szin.red() + 151 * szin.green() + 28 * szin.blue()) >> 8


@pytest.fixture(scope="module")
def jelenet(qt_app):
    import picasapy.app.application as app_module

    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    component = QQmlComponent(view.engine())
    component.setData(_QML.encode("utf-8"), QUrl())
    hibak = [hiba.toString() for hiba in component.errors()]
    assert hibak == [], hibak
    root = component.create()
    assert root is not None
    root.setParentItem(view.contentItem())
    view.resize(_SZELES, _MAGAS)
    view.show()
    assert QTest.qWaitForWindowExposed(view)
    _var_a_kirajzolasra(view, qt_app)
    tema = view.engine().singletonInstance("PicasaPy", "Theme")
    assert tema is not None
    _KEEPALIVE.extend((view, root, component))
    yield view, tema, qt_app
    tema.setProperty("megjelenitesiPaletta", {})


def _savok_lumaja(view, qt_app) -> dict[str, int]:
    _var_a_kirajzolasra(view, qt_app)
    kep = view.grabWindow()
    ki = {}
    for i, nev in enumerate(_SAVOK):
        # a sáv közepe: 30 képpont magas sávok, a 15. soruk
        ki[nev] = _luma(kep.pixelColor(_SZELES // 2, i * 30 + 15))
    return ki


class TestAModKirajzolva:
    def test_a_mac_gamma_VILAGOSIT_a_kirajzolt_felületen(self, jelenet):
        view, tema, qt_app = jelenet
        elotte = _savok_lumaja(view, qt_app)

        vezerlo = _vezerlo()
        vezerlo.setDisplayMode("mac")
        paletta = vezerlo.uiPalette(tema.property("nyers"))
        assert len(paletta) >= 100, f"a paletta csak {len(paletta)} tokent hozott"
        tema.setProperty("megjelenitesiPaletta", paletta)

        utana = _savok_lumaja(view, qt_app)
        for nev in _SAVOK:
            assert utana[nev] > elotte[nev], (
                f"a(z) `{nev}` sáv NEM világosodott a kirajzolt képen: "
                f"{elotte[nev]} → {utana[nev]}"
            )
            szazalek = (utana[nev] - elotte[nev]) / elotte[nev] * 100
            assert _MIN_NOVEKMENY <= szazalek <= _MAX_NOVEKMENY, (
                f"a(z) `{nev}` növekménye {szazalek:.2f}%, a #1580 felület-"
                f"mérése +1,3…+4,2%-ot mutat ({elotte[nev]} → {utana[nev]})"
            )

    def test_ures_paletta_visszaallitja_a_nyers_kepet(self, jelenet):
        """A mód KIKAPCSOLÁSA tényleg visszaáll — nem ragad be a paletta."""
        view, tema, qt_app = jelenet
        tema.setProperty("megjelenitesiPaletta", {})
        nyers = _savok_lumaja(view, qt_app)

        vezerlo = _vezerlo()
        vezerlo.setDisplayMode("projector")
        tema.setProperty("megjelenitesiPaletta", vezerlo.uiPalette(tema.property("nyers")))
        sotetebb = _savok_lumaja(view, qt_app)
        assert all(sotetebb[n] < nyers[n] for n in _SAVOK), (
            f"a projektor mód nem sötétített: {nyers} → {sotetebb}"
        )

        tema.setProperty("megjelenitesiPaletta", {})
        assert _savok_lumaja(view, qt_app) == nyers, "a kikapcsolás nem állt vissza"

    def test_a_noop_mod_nem_valtoztat(self, jelenet):
        view, tema, qt_app = jelenet
        tema.setProperty("megjelenitesiPaletta", {})
        elotte = _savok_lumaja(view, qt_app)
        vezerlo = _vezerlo()
        vezerlo.setDisplayMode("normal")
        paletta = vezerlo.uiPalette(tema.property("nyers"))
        assert paletta == {}, "a no-op mód is palettát adott"
        tema.setProperty("megjelenitesiPaletta", paletta)
        assert _savok_lumaja(view, qt_app) == elotte


class TestABekotes:
    """A VALÓDI úton: a felhasználó módot választ → a felület színe változik.

    A fenti próbák a palettát maguk töltik a `Theme`-be; ez itt azt méri,
    hogy a `Main.qml` tényleg elvégzi ezt a mód váltásakor — enélkül a
    gyártósor kész, de bekötetlen (a #1596 tanulsága: a menü „csinál valamit",
    közben a felület nem mozdul).
    """

    def _tema(self, engine):
        return engine.singletonInstance("PicasaPy", "Theme")

    def _paletta(self, tema) -> dict:
        """A `var` property QJSValue-t ad — a puszta igazságérték semmit nem
        mond (egy üres szótár burkolója is igaz), ezért Python-oldali alakra
        váltunk."""
        from PySide6.QtQml import QJSValue

        ertek = tema.property("megjelenitesiPaletta")
        if isinstance(ertek, QJSValue):
            ertek = ertek.toVariant()
        return ertek or {}

    def test_a_modvaltas_feltolti_a_palettat(self, qml_app, qt_app):
        window, controller, engine = qml_app
        tema = self._tema(engine)
        assert tema is not None
        elotte = QColor(tema.property("chromeBg"))

        controller.setDisplayMode("projector")
        qt_app.processEvents()
        paletta = self._paletta(tema)
        assert len(paletta) >= 100, (
            f"a mód váltása nem töltötte fel a Theme palettáját ({len(paletta)} token)"
        )
        utana = QColor(tema.property("chromeBg"))
        assert _luma(utana) < _luma(elotte), (
            f"a króm nem sötétedett a projektor módban: {elotte.name()} → {utana.name()}"
        )

        controller.setDisplayMode("normal")
        qt_app.processEvents()
        assert self._paletta(tema) == {}, "a no-op módra nem ürült ki a paletta"
        assert QColor(tema.property("chromeBg")) == elotte

    def test_a_tema_valtas_ujraszamolja(self, qml_app, qt_app):
        """A sötét/világos váltás a NYERS értékeket cseréli — a palettának
        követnie kell, különben az előző téma színei ragadnának be."""
        window, controller, engine = qml_app
        tema = self._tema(engine)
        controller.setDisplayMode("projector")
        qt_app.processEvents()
        vilagos = QColor(self._paletta(tema)["chromeBg"])

        controller.setDarkTheme(True)
        qt_app.processEvents()
        sotet = QColor(self._paletta(tema)["chromeBg"])
        assert sotet != vilagos, "a téma váltása után a paletta beragadt"
        assert _luma(sotet) < _luma(vilagos)

        controller.setDarkTheme(False)
        controller.setDisplayMode("normal")
        qt_app.processEvents()


class TestADiavetitesKimarad:
    """11.7/3. és NY-4: a diavetítésre a mód NEM hat.

    A fotót a diavetítés a saját útján kapja (#1640), a rárajzolt csillag
    viszont `Theme`-tokenből jön — ha az a NYILVÁNOS színt olvasná, a mód a
    csillagot is átszínezné, és a hatókör-szerződés csendben sérülne. A
    forrás alakját rögzítjük, mert a hiba természete forrás-szintű.
    """

    def test_a_diavetites_a_NYERS_tokent_olvassa(self):
        import picasapy.app.application as app_module

        forras = (
            app_module._APP_DIR / "qml" / "PicasaPy" / "SlideshowView.qml"
        ).read_text(encoding="utf-8")
        szinek = [
            sor.strip()
            for sor in forras.splitlines()
            if "Theme." in sor and "Theme.nyers." not in sor and "fontSize" not in sor
        ]
        assert szinek == [], (
            "a diavetítés a NYILVÁNOS téma-színt olvassa, tehát a "
            "megjelenítési mód ráhat — a 11.7/3. szerint kimarad: "
            + " · ".join(szinek)
        )
