"""#4537 — a „További lehetőségek…” (`outputlayout/morebutton`) felugrója
függőleges gombok oszlopa, nem szöveges menü.

Az eredetiben a túlcsordulás-gomb a ki nem férő kimeneti gombokat egy
függőleges oszlopban kínálja (`docs/specs/picasa-keptalca.md` 23.3, erős
bizalmi fok). Nálunk eddig egy egyszerű, szöveges `Menu` állt itt; most
ugyanúgy 55 × 36-os gombok állnak egymás alatt, ikonnal és felirattal, mint
a sávban.

Mit mérnek a próbák (valódi kattintással, a főablakban):

- a felugró megnyílik a gombra kattintva;
- a tételek egy oszlopban állnak: azonos `x`, `y` pontosan 36-os lépésben;
- minden tétel az ablakon BELÜL van, −5 / 0 / +5 képpontos ablakmagasságnál;
- a tétel ugyanazt a jelet küldi, mint a sávbeli gomb, és az engedélyezettsége
  követi az eredeti gombét;
- a felugró csak a KI NEM FÉRŐ tételeket sorolja (mint eddig).

⚠️ A felugró PONTOS nyílási iránya (fölfelé vagy lefelé) és takarása
NINCS mérve (`picasa-keptalca.md` 23.5). A próba csak azt követeli meg, hogy
a tálca alján a felugró a látható területen maradjon; az irány a mi döntésünk.
"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QObject, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QSignalSpy, QTest

#: Mért kimeneti gomb-mező (`picasa-keptalca.md` 11.): 55 × 36, a cella 59.
GOMB_SZELESSEG = 55
GOMB_MAGASSAG = 36

#: A kimeneti sor szűk ablaknál (ld. `test_kimeneti_tulcsordulas_2191.py`),
#: ahol a túlcsordulás-gomb látszik, és van ki nem férő tétel.
SZUK = 400

#: A sorrend a respack deklarációs sorrendje; ugyanaz, mint a sávban.
JELEK = [
    "printRequested",
    "emailRequested",
    "exportRequested",
    "collageRequested",
    "movieRequested",
]


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


def _elem(window, nev: str) -> QObject:
    obj = window.findChild(QObject, nev)
    assert obj is not None, f"nincs ilyen elem: {nev}"
    return obj


def _kattint(window, qt_app, item) -> None:
    assert item.width() > 0 and item.height() > 0, "a kattintási cél mérete nulla"
    pont = item.mapToScene(item.boundingRect().center()).toPoint()
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont)
    qt_app.processEvents()


def _tray_a_jelekkel(window) -> QObject:
    """A `printRequested` jelet hordozó TrayBar-gyökér (a gomb felmenő láncán)."""
    obj = _elem(window, "trayMoreButton")
    while obj is not None:
        if obj.metaObject().indexOfSignal("printRequested()") >= 0:
            return obj
        obj = obj.parent()
    raise AssertionError("nem találom a TrayBar-gyökeret a jelekhez")


def _vizuális_gyerekek(elem):
    for gy in elem.childItems():
        yield gy
        yield from _vizuális_gyerekek(gy)


def _felugro_tetelei(window) -> list[QQuickItem]:
    """A felugró tételei: a felugró TARTALMÁBAN keressük (nem az ablakban),
    mert a `Popup` tartalma az ablak overlay-rétegén ül."""
    tartalom = _elem(window, "trayMoreMenu").property("contentItem")
    return [i for i in _vizuális_gyerekek(tartalom) if i.objectName() == "trayMoreItem"]


def _nyitas(window, qt_app) -> None:
    gomb = _elem(window, "trayMoreButton")
    _kattint(window, qt_app, gomb)
    nyitva = _var(
        qt_app, lambda: _elem(window, "trayMoreMenu").property("opened") is True
    )
    assert nyitva, (
        "a „További lehetőségek…” gombra kattintva nem nyílt meg a felugró "
        f"(gomb: {gomb.width()}×{gomb.height()}, látszik: {gomb.isVisible()}, "
        f"ablak: {window.width()}×{window.height()})"
    )


def _magassag_beallitas(window, qt_app, magassag: int) -> None:
    window.requestActivate()
    _var(qt_app, lambda: window.isActive(), 2.0)
    window.setWidth(SZUK)
    window.setHeight(magassag)
    qt_app.processEvents()
    # a tálca-sor átrendezését ki kell várni, különben a kattintás a régi
    # helyre esik
    _var(qt_app, lambda: False, 1.0)


@pytest.fixture
def alap_magassag(qml_app, qt_app):
    window, _c, _e = qml_app
    assert _var(qt_app, lambda: window.findChild(QObject, "trayMoreButton"))
    yield window.height()
    # a nyitva hagyott felugró és a tétel által nyitott nyomtató-párbeszéd
    # ne maradjon a következő próbára (a párbeszéd modálisan elnyeli a
    # kattintásokat)
    felugro = window.findChild(QObject, "trayMoreMenu")
    if felugro is not None and felugro.property("opened") is True:
        felugro.close()
    nyomtatas = window.findChild(QObject, "printDialog")
    if nyomtatas is not None and nyomtatas.property("visible") is True:
        nyomtatas.close()
    qt_app.processEvents()


@pytest.mark.parametrize("eltolas", [-5, 0, 5])
class TestFuggolegesOszlop:
    def test_a_tetelek_EGY_oszlopot_alkotnak(self, qml_app, qt_app, alap_magassag, eltolas):
        window, _c, _e = qml_app
        _magassag_beallitas(window, qt_app, alap_magassag + eltolas)
        _nyitas(window, qt_app)

        tetelek = _felugro_tetelei(window)
        assert tetelek, "a felugróban nincs tétel, pedig van ki nem férő gomb"
        tetelek.sort(key=lambda t: t.mapToScene(t.boundingRect().topLeft()).y())

        x_ertekek = {round(t.mapToScene(t.boundingRect().topLeft()).x()) for t in tetelek}
        assert len(x_ertekek) == 1, f"a tételek nem egy oszlopban állnak: x = {x_ertekek}"

        for elso, masodik in zip(tetelek, tetelek[1:], strict=False):
            y1 = elso.mapToScene(elso.boundingRect().topLeft()).y()
            y2 = masodik.mapToScene(masodik.boundingRect().topLeft()).y()
            assert round(y2 - y1) == GOMB_MAGASSAG, (
                f"a tételek lépése {y2 - y1}, a mért gombmagasság {GOMB_MAGASSAG}"
            )
            assert elso.width() == GOMB_SZELESSEG and elso.height() == GOMB_MAGASSAG, (
                f"a tétel mérete {elso.width()}×{elso.height()}, mért: "
                f"{GOMB_SZELESSEG}×{GOMB_MAGASSAG}"
            )

    def test_a_felugro_az_ablakon_BELUL_marad(self, qml_app, qt_app, alap_magassag, eltolas):
        window, _c, _e = qml_app
        _magassag_beallitas(window, qt_app, alap_magassag + eltolas)
        _nyitas(window, qt_app)

        ablak_magassag = window.height()
        for tetel in _felugro_tetelei(window):
            fent = tetel.mapToScene(tetel.boundingRect().topLeft()).y()
            lent = fent + tetel.height()
            assert fent >= 0 and lent <= ablak_magassag, (
                f"a felugró tétele kilóg az ablakból: {fent}–{lent} "
                f"(ablak magassága {ablak_magassag})"
            )


class TestATetelekViselkedese:
    def test_a_tetel_a_sávbeli_gomb_JELET_küldi(self, qml_app, qt_app, alap_magassag):
        window, _c, _e = qml_app
        _magassag_beallitas(window, qt_app, alap_magassag)
        # a kimeneti gombok kijelölés nélkül letiltottak — egy kép kell
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        qt_app.processEvents()
        sor = _elem(window, "trayActionRow")
        kiferok = int(sor.property("kiferoCellak"))
        tray = _tray_a_jelekkel(window)
        jelek = QSignalSpy(tray, f"2{JELEK[kiferok]}()")

        _nyitas(window, qt_app)
        tetelek = _felugro_tetelei(window)
        assert tetelek
        tetelek.sort(key=lambda t: t.mapToScene(t.boundingRect().topLeft()).y())
        _kattint(window, qt_app, tetelek[0])

        assert _var(qt_app, lambda: jelek.count() == 1), (
            f"az első felugró-tétel nem a(z) {JELEK[kiferok]} jelet küldte "
            f"(a rejtett listában az első: {kiferok}. kimeneti gomb)"
        )

    def test_a_tetel_engedelyezettsege_KOVETI_a_gombot(self, qml_app, qt_app, alap_magassag):
        window, _c, _e = qml_app
        _magassag_beallitas(window, qt_app, alap_magassag)
        _nyitas(window, qt_app)
        sor = _elem(window, "trayActionRow")
        kiferok = int(sor.property("kiferoCellak"))
        tetelek = _felugro_tetelei(window)
        # Az eredeti gomb neve a kiferő sorrendben: print, email, export, …
        gomb_nevek = [
            "trayPrintButton", "trayEmailButton", "trayExportButton",
            "trayCollageButton", "trayMovieButton",
        ]
        for i, tetel in enumerate(
            sorted(tetelek, key=lambda t: t.mapToScene(t.boundingRect().topLeft()).y())
        ):
            gomb = _elem(window, gomb_nevek[kiferok + i])
            assert bool(tetel.property("enabled")) == bool(gomb.property("enabled")), (
                f"a felugró {i}. tétele nem követi az eredeti gomb engedélyezettségét"
            )
