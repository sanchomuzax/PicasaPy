"""#2191 — a kimeneti gombsor túlcsordulás-gombja („További lehetőségek…").

Az eredetiben a sor konténere **`overflow:` típusú**, és van egy dedikált
gombja a ki nem férő tételeknek: `outputlayout/morebutton` (55 × 36, mint
a másik nyolc). Keskeny ablaknál a maradék gomb e mögé kerül — nem tűnik
el és nem nyomódik össze.

Feliratok az eredeti szövegtárból:

| | angol | magyar |
|---|---|---|
| felirat | More... | **További lehetőségek...** |
| buboréksúgó | Click here for more options | **Kattintson ide a további opciókért** |

⚠️ A felugró lista PONTOS kinézete **nincs mérve** (a `respack.yt` csak a
gombot adja, a tartalom futásidőben épül). A próbák ezért a
*tartalmát* mérik — hogy a hiányzó gombokat sorolja, és csak azokat —,
nem a megjelenését.
"""

from __future__ import annotations

import time

from PySide6.QtCore import QObject
from PySide6.QtQuick import QQuickItem


def _walk(item: QQuickItem):
    for gy in item.childItems():
        yield gy
        yield from _walk(gy)


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        try:
            if feltetel():
                return True
        except (AttributeError, TypeError, RuntimeError):
            pass
        qt_app.processEvents()
        time.sleep(0.005)
    return False


#: Mért határ: egy cella 59 képpont, a sor 150 képpontnál kezdődik,
#: tehát az öt gomb 5 × 59 + 150 = 445 képpontos ablakig fér ki.
SZUK = 400
SZELES = 1600

#: A kimeneti sor gombjai, a respack deklarációs sorrendjében.
GOMBOK = [
    "trayPrintButton",
    "trayEmailButton",
    "trayExportButton",
    "trayCollageButton",
    "trayMovieButton",
]


def _lista(ertek) -> list:
    """A QML tömb Pythonban `QJSValue` — az nem iterálható közvetlenül."""
    if ertek is None:
        return []
    atalakito = getattr(ertek, "toVariant", None)
    return list(atalakito()) if atalakito is not None else list(ertek)


def _elem(window, nev):
    obj = window.findChild(QObject, nev)
    assert obj is not None, f"nincs ilyen elem: {nev}"
    return obj


def _lathato_gombok(window) -> list[str]:
    return [g for g in GOMBOK if (window.findChild(QObject, g) or None)
            and window.findChild(QObject, g).isVisible()]


def _szelesites(window, qt_app, szelesseg: int) -> None:
    window.setWidth(szelesseg)
    qt_app.processEvents()
    _var(qt_app, lambda: False, 0.3)


class TestATulcsordulasGomb:
    def test_letezik(self, qml_app, qt_app):
        window, _c, _e = qml_app
        assert _var(qt_app, lambda: window.findChild(QObject, "trayMoreButton"))

    def test_a_felirat_es_a_sugo_a_MERT_szoveg(self, qml_app, qt_app):
        window, _c, _e = qml_app
        assert _var(qt_app, lambda: window.findChild(QObject, "trayMoreButton"))
        gomb = _elem(window, "trayMoreButton")
        # A `qml_app` fixture NEM telepít fordítót, ezért futásidőben a
        # forrásszöveg (angol) látszik — a magyar alakot a `.ts`-ből
        # mérjük, ld. `test_a_MAGYAR_alak_a_forditasban`.
        assert gomb.property("text") == "More..."

    def test_a_buborekgsugo_a_TOBBI_gomb_mintajara_szol(self):
        """A `ToolTip.text` csatolt tulajdonság — Pythonból nem olvasható,
        ezért forrásból mérjük. A három sor EGYÜTT kell: `text` nélkül
        nincs mit mutatni, `visible` nélkül soha nem jelenik meg."""
        from pathlib import Path

        import picasapy.app as app_csomag

        qml = (Path(app_csomag.__file__).parent / "qml" / "PicasaPy"
               / "TrayBar.qml").read_text(encoding="utf-8")
        kezd = qml.index('objectName: "trayMoreButton"')
        blokk = qml[kezd:kezd + 900]
        for sor in ('ToolTip.text: qsTr("Click here for more options")',
                    "ToolTip.visible:", "ToolTip.delay:"):
            assert sor in blokk, f"a túlcsordulás-gombról hiányzik: {sor}"

    def test_a_MAGYAR_alak_a_forditasban(self):
        """A mért magyar szövegek az eredeti szövegtárából valók — nem
        szabad szabadon fordítani őket."""
        import re
        from pathlib import Path

        import picasapy.app as app_csomag

        ts = (Path(app_csomag.__file__).parent / "i18n"
              / "picasapy_hu.ts").read_text(encoding="utf-8")
        blokk = re.search(
            r"<name>TrayBar</name>(.*?)</context>", ts, re.S
        )
        assert blokk is not None, "nincs TrayBar kontextus a fordításban"
        szoveg = blokk.group(1)
        for forras, magyar in (
            ("More...", "További lehetőségek..."),
            ("Click here for more options",
             "Kattintson ide a további opciókért"),
        ):
            assert f"<source>{forras}</source>" in szoveg, (
                f"a TrayBar kontextusból hiányzik: {forras}"
            )
            assert f"<translation>{magyar}</translation>" in szoveg, (
                f"hiányzik vagy más a magyar alak: {magyar}"
            )

    def test_SZELES_ablaknal_NEM_latszik(self, qml_app, qt_app):
        window, _c, _e = qml_app
        assert _var(qt_app, lambda: window.findChild(QObject, "trayMoreButton"))
        _szelesites(window, qt_app, SZELES)
        assert _elem(window, "trayMoreButton").isVisible() is False, (
            "széles ablakon is látszik a túlcsordulás-gomb, pedig minden "
            "gomb kifér"
        )

    def test_KESKENY_ablaknal_LATSZIK(self, qml_app, qt_app):
        window, _c, _e = qml_app
        assert _var(qt_app, lambda: window.findChild(QObject, "trayMoreButton"))
        _szelesites(window, qt_app, SZUK)
        assert _var(
            qt_app, lambda: _elem(window, "trayMoreButton").isVisible() is True
        ), "keskeny ablakon nem jelent meg a túlcsordulás-gomb"


class TestALathatoGombokSzama:
    def test_szukiteskor_CSOKKEN(self, qml_app, qt_app):
        window, _c, _e = qml_app
        assert _var(qt_app, lambda: window.findChild(QObject, "trayActionRow"))
        _szelesites(window, qt_app, SZELES)
        szeles = len(_lathato_gombok(window))
        _szelesites(window, qt_app, SZUK)
        keskeny = len(_lathato_gombok(window))
        assert keskeny < szeles, (
            f"szűkítéskor nem csökkent a látható gombok száma "
            f"({szeles} → {keskeny})"
        )

    def test_a_gombok_NEM_nyomodnak_ossze(self, qml_app, qt_app):
        """A mért 55 × 36 a gombokra kötelező — a szűk hely nem
        zsugoríthatja őket, azért van a túlcsordulás-gomb."""
        window, _c, _e = qml_app
        assert _var(qt_app, lambda: window.findChild(QObject, "trayPrintButton"))
        _szelesites(window, qt_app, SZUK)
        for nev in GOMBOK:
            gomb = window.findChild(QObject, nev)
            if gomb is None or not gomb.isVisible():
                continue
            assert gomb.width() >= 55, f"{nev} összenyomódott: {gomb.width()}"


class TestAFelugroLista:
    def test_a_HIANYZO_gombokat_sorolja(self, qml_app, qt_app):
        """Nem az összeset — csak azokat, amik nem fértek ki."""
        window, _c, _e = qml_app
        assert _var(qt_app, lambda: window.findChild(QObject, "trayActionRow"))
        _szelesites(window, qt_app, SZUK)
        sor = _elem(window, "trayActionRow")
        rejtett = _lista(sor.property("rejtettFeliratok"))
        assert rejtett, "keskeny ablakon egy felirat sincs a rejtettek közt"
        lathato = len(_lathato_gombok(window))
        assert len(rejtett) == len(GOMBOK) - lathato, (
            f"a rejtettek száma ({len(rejtett)}) nem egyezik a hiányzókkal "
            f"({len(GOMBOK)} − {lathato})"
        )

    def test_szeles_ablaknal_URES(self, qml_app, qt_app):
        window, _c, _e = qml_app
        assert _var(qt_app, lambda: window.findChild(QObject, "trayActionRow"))
        _szelesites(window, qt_app, SZELES)
        assert not _lista(_elem(window, "trayActionRow").property("rejtettFeliratok"))


class TestMikortolHatElesben:
    """A mechanizmus megvan — de a MAI öt gombbal, a legkisebb ablak
    (800 képpont) fölött **egyszer sem lép működésbe**. Ez végigpásztázott
    mérés, nem levezetés: a küszöb nem lineáris a szélességben, mert a
    kivezetett gombok és a csoportelválasztók maguk is eltűnnek szűküléskor,
    és ezzel helyet adnak vissza a kimeneti soroknak.

    A gomb így is kell: az eredetiben **kilenc** kimeneti gomb van, nálunk
    öt. A hiányzó négy megépítésekor ez a próba elbukik — és akkor épp azt
    fogja jelenteni, amit kell: mostantól élesben is látszik a
    „További lehetőségek…", tehát kézzel is nézd meg.
    """

    def test_a_LEGKISEBB_ablak_folott_sehol_nincs_rejtett(
        self, qml_app, qt_app
    ):
        window, _c, _e = qml_app
        assert _var(qt_app, lambda: window.findChild(QObject, "trayActionRow"))
        sor = _elem(window, "trayActionRow")
        talalt = []
        for szelesseg in range(window.minimumWidth(), 2001, 20):
            _szelesites(window, qt_app, szelesseg)
            rejtett = _lista(sor.property("rejtettFeliratok"))
            if rejtett:
                talalt.append((szelesseg, rejtett))
        assert not talalt, (
            f"a túlcsordulás élesben is bekapcsol — {len(talalt)} "
            f"szélességen, elsőként {talalt[0][0]} képpontnál "
            f"({talalt[0][1]}). Ez nem hiba, de ELLENŐRIZD kézzel is, és "
            f"írd át ezt a próbát"
        )


class TestAListaEsAGombokEGYUTT:
    """A felugró lista feliratai a GOMBOKÉ — nem külön `qsTr()` hívások.

    Az első változatom külön listát írt (`Email`, `Movie`), miközben a
    gombokon `E-Mail` és `Movie` áll: két igazságforrásból a lista némán
    elcsúszott volna, és a fordítás-őr két sosem látott szöveget kért
    számon (a CI ezt meg is fogta).
    """

    def test_a_felugro_a_gombok_feliratat_veszi(self, qml_app, qt_app):
        window, _c, _e = qml_app
        assert _var(qt_app, lambda: window.findChild(QObject, "trayActionRow"))
        _szelesites(window, qt_app, SZELES)
        sor = _elem(window, "trayActionRow")
        feliratok = _lista(sor.property("gombFeliratok"))
        gombokon = [_elem(window, nev).property("text") for nev in GOMBOK]
        assert feliratok == gombokon, (
            "a felugró lista feliratai eltérnek a gombokétól — két "
            "igazságforrás"
        )

    def test_a_forras_NEM_ismetli_meg_a_szovegeket(self):
        """Forrás-szintű őr: a lista a gombok `text`-jére hivatkozzon."""
        from pathlib import Path

        import picasapy.app as app_csomag

        qml = (Path(app_csomag.__file__).parent / "qml" / "PicasaPy"
               / "TrayBar.qml").read_text(encoding="utf-8")
        kezd = qml.index("readonly property var gombFeliratok:")
        blokk = qml[kezd:qml.index("]", kezd)]
        assert "qsTr(" not in blokk, (
            "a felirat-lista újra `qsTr()`-t hív — a gombok `text`-jét "
            "kell átvennie, különben a két hely elcsúszhat"
        )
