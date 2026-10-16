"""#5150 (5. rész): a tálca helyi menüje valódi egérkattintással.

A PicasaMenuBar-lista „Tálca" csoportjának tételei. A helyi menü a tálca
jobbklikkjével nyílik (valódi `QTest.mouseClick`), utána a tételen valódi bal
kattintás megy. Parancsot nem indítunk közvetlenül: nincs `triggered`,
`clicked`, `activated` hívás és nincs `.emit()`. A hatást az állapoton mérjük.

Lefedve ebben a fájlban:
- `trayContextMenuHandler` - a tálca jobbklikkje megnyitja a helyi menüt;
- `trayMenuViewAndEdit`, `trayMenuKeepSelection`, `trayMenuRemoveSelection`,
  `trayMenuRotateRight`, `trayMenuRotateLeft`, `trayMenuLocate`,
  `trayMenuProperties` - a helyi menü hét tétele (az elválasztó nem tétel).

A `trayMenuLocate` („Locate on Disk") a fájlkezelőt indítaná. A
`reveal_in_file_manager` helyettesítőjét figyeljük, a valódi program nem indul.

A többi tálca-tétel a `test_talca_eszkoztar_valodi_5150_b.py`-ban van.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

import picasapy.app.fileops_controller as fileops_module
from conftest import _build_qml_app
from support.varakozas import hibaturo_feltetel, var_feltetelre


@pytest.fixture
def talca_app(qt_app, tmp_path, request):
    yield from _build_qml_app(qt_app, tmp_path, keep_modul=request.module)


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def _gyerek(szulo, nev: str, tipus=QObject):
    elem = szulo.findChild(tipus, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _kattints(qt_app, elem, gomb=Qt.MouseButton.LeftButton) -> None:
    """Valódi egérkattintás az elem közepére, az elem SAJÁT ablakában.

    A helyi menü tételei külön ablakban élnek, ezért az elem `window()`-jához
    viszonyítunk, nem a főablakhoz (ahogy a `_fomenu_4420_menu._kattints`).
    """
    assert elem.isVisible() and elem.width() > 0 and elem.height() > 0, (
        f"{elem.objectName()}: nem látszik, vagy nulla méretű, nem kattintható"
    )
    elem.ensurePolished()
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        elem.window(),
        gomb,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def _nyitott(elem) -> bool:
    return elem.property("opened") is True or elem.property("visible") is True


def _zar(qt_app, objektum) -> None:
    """Takarítás: a megnyílt menüt bezárja (a `close` a takarításban szabad)."""
    QMetaObject.invokeMethod(objektum, "close", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def _lib(controller) -> Path:
    return Path(str(controller.currentFolder))


def _sor(controller, nev: str) -> int:
    sor = int(controller.photos.rowOfPath(str(_lib(controller) / nev)))
    assert sor >= 0, f"a kép nincs a rácsban: {nev}"
    return sor


def _kijelol(window, qt_app, sorok) -> None:
    window.setProperty("selectedIndexes", list(sorok))
    window.setProperty("selectedIndex", sorok[0] if sorok else -1)
    qt_app.processEvents()


def _tarolt(controller, kep: Path) -> dict | None:
    """A tálca eleme a `kep` útvonalon, vagy `None`, ha nincs a tálcán."""
    for elem in controller.trayItems:
        if Path(str(elem["path"])) == kep:
            return elem
    return None


def _megtartott(controller, kep: Path) -> bool:
    elem = _tarolt(controller, kep)
    return elem is not None and elem["held"] is True


def _jobb_kattintas_a_talcan(window, qt_app):
    """Valódi jobbklikk a tálca képsávján; a menü megnyílását megvárjuk.

    ⚠️ Nem a `trayMainBar` közepére kattintunk: mérve a sáv közepe és a jobb
    oldala nem nyitotta meg a menüt, a képsáv (`trayScratchStrip`) igen. A
    képsáv az a hely, ahová a felhasználó jobbklikkel.
    """
    _kattints(
        qt_app,
        _gyerek(window, "trayScratchStrip", QQuickItem),
        Qt.MouseButton.RightButton,
    )
    menu = _gyerek(window, "trayContextMenu")
    assert _varj(qt_app, lambda: _nyitott(menu)), (
        "a tálca jobbklikkje nem nyitotta meg a helyi menüt"
    )
    return menu


def _tetel_kattintas(window, qt_app, nev: str):
    """A tálca jobbklikkje, majd valódi bal kattintás a `nev` menütételen."""
    menu = _jobb_kattintas_a_talcan(window, qt_app)
    tetel = _gyerek(menu, nev, QQuickItem)
    assert _varj(qt_app, lambda: tetel.property("visible") is True), (
        f"{nev} nem látszik a helyi menüben"
    )
    _kattints(qt_app, tetel)
    return menu


def test_a_talca_jobbklikkje_megnyitja_a_helyi_menut(talca_app, qt_app):
    window, _controller, _engine = talca_app
    menu = _jobb_kattintas_a_talcan(window, qt_app)
    for nev in ("trayMenuViewAndEdit", "trayMenuLocate", "trayMenuProperties"):
        tetel = _gyerek(menu, nev, QQuickItem)
        assert tetel.property("visible") is True, f"{nev} nincs a megnyílt menüben"
    _zar(qt_app, menu)


def test_megjelenites_es_szerkesztes_megnyitja_a_nezot_a_kijelolt_kepen(
    talca_app, qt_app
):
    window, controller, _engine = talca_app
    sor = _sor(controller, "b.jpg")
    _kijelol(window, qt_app, [sor])
    assert window.property("viewerOpen") is False

    _tetel_kattintas(window, qt_app, "trayMenuViewAndEdit")

    assert _varj(qt_app, lambda: window.property("viewerOpen") is True), (
        "a Megjelenítés és szerkesztés tétel nem nyitotta meg a nézőt"
    )
    nezo = _gyerek(window, "photoViewer")
    assert _varj(qt_app, lambda: nezo.property("currentIndex") == sor), (
        "a néző nem a kijelölt képen nyílt meg"
    )


def test_a_hold_selection_megtartja_a_kepet_a_kijeloles_valtasa_utan_is(
    talca_app, qt_app
):
    window, controller, _engine = talca_app
    kep = _lib(controller) / "a.jpg"
    _kijelol(window, qt_app, [_sor(controller, "a.jpg")])
    assert not _megtartott(controller, kep), "a kép már a kattintás előtt rögzített volt"

    _tetel_kattintas(window, qt_app, "trayMenuKeepSelection")

    assert _varj(qt_app, lambda: _megtartott(controller, kep)), (
        "a Hold Selection nem rögzítette a kijelölt képet a tálcán"
    )
    _kijelol(window, qt_app, [_sor(controller, "b.jpg")])
    assert _varj(qt_app, lambda: _megtartott(controller, kep)), (
        "a rögzített kép a másik kijelölésre eltűnt a tálcáról"
    )


def test_a_remove_selection_eltavolitja_a_tarca_kijelolt_kepet(talca_app, qt_app):
    window, controller, _engine = talca_app
    kep = _lib(controller) / "a.jpg"
    sor = _sor(controller, "a.jpg")
    controller.holdRows([sor])
    _kijelol(window, qt_app, [sor])
    assert _tarolt(controller, kep) is not None, "a teszt előkészítése nem került a tálcára"

    _tetel_kattintas(window, qt_app, "trayMenuRemoveSelection")

    assert _varj(qt_app, lambda: _tarolt(controller, kep) is None), (
        "a Remove Selection nem vette le a kijelölt képet a tálcáról"
    )


def test_a_jobbra_forgatas_a_kijelolt_kepet_forgatja(talca_app, qt_app):
    window, controller, _engine = talca_app
    sor = _sor(controller, "a.jpg")
    _kijelol(window, qt_app, [sor])
    assert controller.photos.photos[sor].rotate_steps == 0

    _tetel_kattintas(window, qt_app, "trayMenuRotateRight")

    assert _varj(qt_app, lambda: controller.photos.photos[sor].rotate_steps == 1), (
        "az R&otate Clockwise nem forgatta el a kijelölt képet"
    )


def test_a_balra_forgatas_a_kijelolt_kepet_forgatja(talca_app, qt_app):
    window, controller, _engine = talca_app
    sor = _sor(controller, "a.jpg")
    _kijelol(window, qt_app, [sor])
    assert controller.photos.photos[sor].rotate_steps == 0

    _tetel_kattintas(window, qt_app, "trayMenuRotateLeft")

    # négy állás van, így a balra forgatás a három jobbra forgatással egyezik
    assert _varj(qt_app, lambda: controller.photos.photos[sor].rotate_steps == 3), (
        "a Rotate Counterclockwise nem forgatta el a kijelölt képet"
    )


def test_a_locate_on_disk_a_kep_mappajat_adja_at_a_helyettesitonek(
    talca_app, qt_app, monkeypatch
):
    """Helyettesítő: a valódi fájlkezelő-indítás ki van váltva."""
    window, controller, _engine = talca_app
    kep = _lib(controller) / "a.jpg"
    megnyitva: list[Path] = []
    monkeypatch.setattr(
        fileops_module,
        "reveal_in_file_manager",
        lambda path: megnyitva.append(Path(path)),
    )
    _kijelol(window, qt_app, [_sor(controller, "a.jpg")])

    _tetel_kattintas(window, qt_app, "trayMenuLocate")

    assert _varj(qt_app, lambda: len(megnyitva) == 1), (
        "a Locate on Disk nem indította a fájlkezelő-megnyitást"
    )
    assert megnyitva[0] == kep, f"a rossz képet nyitotta meg: {megnyitva[0]}"


def test_a_tulajdonsagok_tetel_a_tulajdonsagok_fület_nyitja_meg(talca_app, qt_app):
    window, controller, _engine = talca_app
    _kijelol(window, qt_app, [_sor(controller, "a.jpg")])
    assert window.property("activeDrawerTab") != "properties"

    _tetel_kattintas(window, qt_app, "trayMenuProperties")

    assert _varj(qt_app, lambda: window.property("activeDrawerTab") == "properties"), (
        "a Propert&ies tétel nem nyitotta meg a tulajdonságok fület"
    )
