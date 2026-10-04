"""#4150: a jobb fiók, a nyomtatási súgó és a két elavult párosítás.

A viselkedéspróbák a valódi Main.qml-ablakban mozgatják és kattintják a
vezérlőket. A súgók láthatóságára legfeljebb három másodpercet várnak.
"""

from __future__ import annotations

import csv
import time
from pathlib import Path

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QMetaObject,
    QObject,
    QPoint,
    QPointF,
    Qt,
)
from PySide6.QtGui import QHoverEvent
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest

from conftest import _build_qml_app
from support.jpeg_factory import make_jpeg

GYOKER = Path(__file__).resolve().parents[3]
ELEM_CSV = GYOKER / "docs" / "specs" / "ui-lefedettseg-elemek.csv"


def _elem(gyoker, nev: str):
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _var(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        try:
            if feltetel():
                return True
        except (AttributeError, RuntimeError, TypeError):
            pass
        time.sleep(0.01)
    qt_app.processEvents()
    try:
        return bool(feltetel())
    except (AttributeError, RuntimeError, TypeError):
        return False


def _pont(elem) -> QPoint:
    """A kattintási/ráállási pontot a tényleges QML-geometriából veszi."""
    kozeppont = elem.mapToScene(
        QPointF(elem.width() / 2, elem.height() / 2)
    )
    return QPoint(round(kozeppont.x()), round(kozeppont.y()))


def _kattint(ablak, elem) -> None:
    QTest.mouseClick(ablak, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
                     _pont(elem))


def _raall(ablak, elem) -> None:
    cel = _pont(elem)
    # A tesztek offscreen módban futnak: QTest.mouseMove pozicionálja a
    # mutatót, a QHoverEvent pedig eljuttatja a valódi QML-ablakhoz.
    # A távoli pont miatt az egymást követő ráállások nem függnek a
    # tesztek sorrendjétől.
    for pont in (QPoint(0, 0), cel):
        QTest.mouseMove(ablak, pont, 5)
        cel_f = QPointF(pont)
        QCoreApplication.sendEvent(
            ablak,
            QHoverEvent(
                QEvent.Type.HoverMove, cel_f, cel_f, QPointF(-1, -1)
            ),
        )
        QCoreApplication.processEvents()


def _tooltip(elem, nev: str, qt_app, ablak):
    tooltip = elem.findChild(QObject, nev)
    assert tooltip is not None, f"{nev} buboréksúgó nincs a vezérlőn"
    if not ablak.isActive():
        ablak.requestActivate()
        assert QTest.qWaitForWindowActive(ablak, 3000), (
            f"a(z) {ablak.objectName()} ablak nem lett aktív"
        )
    _raall(ablak, elem)
    pont = _pont(elem)
    talalat = ablak.contentItem().childAt(pont.x(), pont.y())
    talalat_nev = (
        None if talalat is None else
        (talalat.objectName(), talalat.metaObject().className())
    )
    assert _var(qt_app, lambda: tooltip.property("visible")), (
        f"{nev} buboréksúgója ráállásra nem jelent meg; "
        f"hovered={elem.property('hovered')}, enabled={elem.property('enabled')}, "
        f"pont={pont}, ablak={ablak.width()}x{ablak.height()}, "
        f"window={elem.window() is ablak}, inverse={elem.mapFromScene(QPointF(pont))}, "
        f"hit={talalat_nev}"
    )
    return str(tooltip.property("text"))


def _csv_sorok() -> dict[str, dict[str, str]]:
    with ELEM_CSV.open(encoding="utf-8", newline="") as fajl:
        return {sor["elem"]: sor for sor in csv.DictReader(fajl)}


@pytest.mark.parametrize("magassag_elteres", [-5, 0, 5])
def test_a_fiok_felirata_sugoi_es_gombjai_a_foablakban(
    qml_app, qt_app, magassag_elteres
):
    ablak, _controller, _engine = qml_app
    celmagassag = ablak.height() + magassag_elteres
    ablak.setHeight(celmagassag)
    assert _var(qt_app, lambda: ablak.height() == celmagassag)

    ablak.setProperty("activeDrawerTab", "properties")
    fiok = _elem(ablak, "rightDrawer")
    assert _var(
        qt_app,
        lambda: abs(fiok.width() - fiok.property("alapSzelesseg")) <= 3,
    ), "a Properties panel nem nyílt ki"
    cim = _elem(ablak, "rightDrawerTitle")
    assert cim.property("visible") is True
    assert str(cim.property("text")) in {"Properties", "Tulajdonságok"}, (
        "a jobb fiók címe nem a kiválasztott lap specifikáció szerinti neve"
    )

    meret = _elem(ablak, "rightDrawerSizeToggle")
    assert _tooltip(meret, "drawerHeaderTooltip", qt_app, ablak) in {
        "Switch between small/large side panel",
        "Váltás a kis és a nagy oldalpanel közt",
    }
    _kattint(ablak, meret)
    assert _var(qt_app, lambda: fiok.property("nagy") is True), (
        "a valódi méretváltó kattintás nem kapcsolt nagy fiókra"
    )
    elvart = min(
        ablak.width() * fiok.property("nagyArany"),
        fiok.property("nagyPlafon"),
    )
    assert _var(qt_app, lambda: abs(fiok.width() - elvart) <= 3), (
        "a fiók nem a saját szélességi képletére váltott"
    )

    zaras = _elem(ablak, "rightDrawerClose")
    assert _tooltip(zaras, "drawerHeaderTooltip", qt_app, ablak) in {
        "Close this side panel", "Oldalpanel bezárása",
    }
    _kattint(ablak, zaras)
    assert _var(qt_app, lambda: ablak.property("activeDrawerTab") == ""), (
        "a valódi bezáró kattintás nem zárta be a fiókot"
    )


@pytest.mark.parametrize("magassag_elteres", [-5, 0, 5])
def test_a_nyomtatas_sugogombja_es_beallitas_sugoja_a_foablakbol_elerheto(
    qml_app, qt_app, magassag_elteres
):
    ablak, _controller, _engine = qml_app
    assert QMetaObject.invokeMethod(
        ablak, "openPrint", Qt.ConnectionType.DirectConnection
    )
    nyomtatas = _elem(ablak, "printDialog")
    assert isinstance(nyomtatas, QQuickWindow)
    assert _var(qt_app, lambda: nyomtatas.property("visible")), (
        "a főablak nem nyitotta meg a nyomtatási párbeszédet"
    )
    celmagassag = nyomtatas.height() + magassag_elteres
    nyomtatas.setHeight(celmagassag)
    assert _var(qt_app, lambda: nyomtatas.height() == celmagassag), (
        "a Nyomtatás párbeszéd nem vette fel a tesztmagasságot"
    )

    beallitas = _elem(nyomtatas, "printOptionsButton")
    assert _tooltip(
        beallitas, "printOptionsTooltip", qt_app, nyomtatas
    ) in {
        "Configure borders and text for Photos to be printed",
        "A nyomtatni kívánt fotók szegélyeinek és szövegének beállítása",
    }
    _kattint(nyomtatas, beallitas)
    panel = _elem(nyomtatas, "printOptionsPanel")
    assert _var(qt_app, lambda: panel.property("visible")), (
        "a Nyomtatás beállításgombja nem nyitotta meg a panelt"
    )
    panel.setProperty("visible", False)

    sugo = _elem(nyomtatas, "printHelpButton")
    assert str(sugo.property("text")) in {"Help", "Súgó"}
    _kattint(nyomtatas, sugo)
    help_window = _elem(nyomtatas, "helpWindow")
    assert _var(qt_app, lambda: help_window.property("visible")), (
        "a Nyomtatás Súgó gombja nem nyitotta meg a saját súgóablakát"
    )
    help_window.setProperty("visible", False)
    nyomtatas.setProperty("visible", False)
    assert _var(qt_app, lambda: not nyomtatas.property("visible")), (
        "a nyomtatási próba végén modális ablak maradt nyitva"
    )

    sorok = _csv_sorok()
    for nev in ("printpanel/captionoptionsbutton", "printpanel/phelpbutton"):
        assert sorok[nev]["allapot"] == "megvan", f"{nev} CSV-állapota elavult"
        assert "PrintDialog.qml" in sorok[nev]["bizonyitek"]
    froogle = sorok["printpanel/froogle"]
    assert froogle["allapot"] == "nem-cel"
    assert "megszűnt" in froogle["megjegyzes"].lower()


def _kepek_albumonkent(lib: Path) -> None:
    for album in range(4):
        mappa = lib / f"album{album}"
        mappa.mkdir()
        for kep in range(8):
            make_jpeg(mappa / f"kep{kep:02d}.jpg", size=(160, 120))


@pytest.fixture
def qml_app_tobb_albummal(qt_app, tmp_path):
    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_kepek_albumonkent)


@pytest.mark.parametrize("magassag_elteres", [-5, 0, 5])
def test_az_initialscan_es_a_throttle_meglevo_vezerloi_mukodnek_es_parositottak(
    qml_app_tobb_albummal, qt_app, monkeypatch, magassag_elteres
):
    ablak, controller, _engine = qml_app_tobb_albummal
    celmagassag = ablak.height() + magassag_elteres
    ablak.setHeight(celmagassag)
    assert _var(qt_app, lambda: ablak.height() == celmagassag)
    sorok = _csv_sorok()
    vart = {
        "initialscan/cancel": "InitialScanDialog.qml",
        "initialscan/radio_complete": "InitialScanDialog.qml",
        "initialscan/radio_limited": "InitialScanDialog.qml",
        "initialscan/radiogroup": "InitialScanDialog.qml",
        "throttle/prevalbum": "PicasaScrollBar.qml",
        "throttle/nextalbum": "PicasaScrollBar.qml",
    }
    for nev, fajlnev in vart.items():
        assert nev in sorok, f"hiányzik a CSV-sor: {nev}"
        assert sorok[nev]["allapot"] == "megvan", f"{nev} nincs megvan-ra párosítva"
        assert fajlnev in sorok[nev]["bizonyitek"]
    for nev in ("throttle/albumscrolltop", "throttle/albumscrollbottom"):
        assert nev in sorok
        assert sorok[nev]["allapot"] == "nem-cel", (
            f"{nev} fel/le nyíl maradjon kihagyva a #857 döntés szerint"
        )
        assert "gorgetosav-album-ugro.md" in sorok[nev]["bizonyitek"]

    alkalmazasok = []
    monkeypatch.setattr(
        type(controller), "applyInitialScan",
        lambda self, scope: alkalmazasok.append(scope), raising=False,
    )
    dialog = _elem(ablak, "initialScanDialog")
    dialog.setProperty("migrationStep", False)
    assert QMetaObject.invokeMethod(dialog, "open", Qt.ConnectionType.DirectConnection)
    assert _var(qt_app, lambda: dialog.property("visible"))

    korlatozott = _elem(ablak, "initialScanNarrow")
    teljes = _elem(ablak, "initialScanWide")
    assert _var(
        qt_app,
        lambda: korlatozott.isVisible() and teljes.isVisible()
        and korlatozott.width() > 0 and teljes.width() > 0,
    ), "az InitialScan rádiógombjai nem készültek el"
    assert korlatozott.parent() == teljes.parent(), "a rádiók nem közös csoportban vannak"
    _kattint(ablak, teljes)
    assert _var(qt_app, lambda: teljes.property("checked") is True), (
        f"radio kattintás nem működött; checked={teljes.property('checked')}, "
        f"visible={teljes.isVisible()}, enabled={teljes.property('enabled')}, "
        f"pont={_pont(teljes)}, ablak={ablak.width()}x{ablak.height()}, "
        f"radio-ablak={teljes.window().width()}x{teljes.window().height()}"
    )
    assert korlatozott.property("checked") is False
    _kattint(ablak, korlatozott)
    assert _var(qt_app, lambda: korlatozott.property("checked") is True)
    assert teljes.property("checked") is False
    assert dialog.property("choice") == "narrow"
    QTest.keyClick(ablak, Qt.Key.Key_Escape)
    assert _var(qt_app, lambda: dialog.property("visible") is False), (
        "az InitialScan bezárása nem szakította meg a folyamatot"
    )
    assert alkalmazasok == [], "a bezárás választás alkalmazása nélkül történik"

    racs = _elem(ablak, "photoGrid")
    sav = _elem(ablak, "feedScrollBar")
    elozo = _elem(ablak, "scrollPrevAlbum")
    kovetkezo = _elem(ablak, "scrollNextAlbum")
    assert sav.property("albumUgras") is True
    assert elozo.isVisible() and kovetkezo.isVisible(), (
        "a rács albumváltó gombjai nem látszanak a görgetősávon"
    )
    kezdet = float(racs.property("contentY"))
    _kattint(ablak, kovetkezo)
    assert _var(qt_app, lambda: float(racs.property("contentY")) > kezdet + 1), (
        "a következő album gomb nem ugrott a következő csoportra"
    )
    _kattint(ablak, elozo)
    assert _var(qt_app, lambda: abs(float(racs.property("contentY")) - kezdet) <= 3), (
        "az előző album gomb nem ugrott vissza az előző csoportra"
    )
