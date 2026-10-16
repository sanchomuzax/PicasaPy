"""#5127: a tálca E-Mail, Exportálás és Nyomtatás gombja valódi egérkattintással.

A kép a rácsról kerül a tálcára (valódi húzással, az 5008-as segéddel), majd
a gombra VALÓDI egérkattintás megy a gomb közepére, az ablak koordinátáiban.
A hatást a megnyíló párbeszéd láthatóságán mérjük. A `clicked` jelet és a
`triggered` jelzést sem hívjuk közvetlenül.

Külső program nem indul: a levélküldés a párbeszéd „Küldés” gombjáig nem jut
el, és a `_popen` helyettesítője így is minden indítást rögzít.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

import picasapy.app.email_controller as email_module
from conftest import _build_qml_app
from support.qt_wait import varj_feltetelre
from tests.app.qml_functional.test_huzas_hianyzoi_5008 import (
    _HEIGHT_DELTAS,
    _hold_grid_photo_in_tray,
    _path_row,
)


@pytest.fixture
def talca_qml_app(qt_app, tmp_path, request, monkeypatch):
    """Főablak e-mail-vezérlővel; a külső levelezőindítás helyettesítve van."""
    kimenet = tmp_path / "csatolmanyok"
    kimenet.mkdir()
    monkeypatch.setattr(email_module, "_mkdtemp", lambda prefix: str(kimenet))
    inditott_parancsok: list[list[str]] = []
    monkeypatch.setattr(email_module, "_which", lambda _nev: "/usr/bin/xdg-email")
    monkeypatch.setattr(
        email_module, "_popen", lambda argv: inditott_parancsok.append(list(argv))
    )
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        email_vezerlo=True,
        keep_modul=request.module,
    )
    assert inditott_parancsok == [], "a teszt külső levelezőprogramot indított"


def _latszik(window, nev: str) -> bool:
    elem = window.findChild(QObject, nev)
    return elem is not None and bool(elem.property("visible"))


def _valodi_kattintas(window, qt_app, nev: str) -> None:
    gomb = window.findChild(QQuickItem, nev)
    assert gomb is not None, f"a(z) {nev} gomb nem található"
    assert gomb.property("enabled") is True, f"a(z) {nev} gomb le van tiltva"
    pont = gomb.mapToItem(
        window.contentItem(), QPointF(gomb.width() / 2, gomb.height() / 2)
    )
    assert 0 <= pont.x() < window.width() and 0 <= pont.y() < window.height(), (
        f"a(z) {nev} gomb a főablakon kívül van: {pont}"
    )
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    qt_app.processEvents()


def _kep_a_talcara(window, qt_app, engine, controller) -> Path:
    """A rács első képe valódi húzással a tálcára kerül, és az a kijelölés."""
    photo = Path(controller.currentFolder) / "a.jpg"
    row = _path_row(controller, photo)
    _hold_grid_photo_in_tray(window, qt_app, engine, controller, photo)
    window.setProperty("selectedIndexes", [row])
    window.setProperty("selectedIndex", row)
    qt_app.processEvents()
    return photo


def _kattintas_nyit(window, qt_app, engine, controller, gomb, parbeszed):
    """Közös váz: tálcára tétel, kattintás előtti állapot, kattintás, megnyílás."""
    _kep_a_talcara(window, qt_app, engine, controller)
    assert not _latszik(window, parbeszed), (
        f"a(z) {parbeszed} már a kattintás előtt látszott"
    )
    _valodi_kattintas(window, qt_app, gomb)
    assert varj_feltetelre(
        qt_app, lambda: _latszik(window, parbeszed), 10.0
    ), f"a(z) {gomb} gomb nem nyitotta meg a(z) {parbeszed} párbeszédet"


@pytest.mark.parametrize("height_delta", _HEIGHT_DELTAS)
def test_talca_email_gomb_valodi_kattintasra_megnyitja_a_levelezo_parbeszedet(
    talca_qml_app, qt_app, height_delta
):
    window, controller, engine = talca_qml_app
    window.resize(window.width(), window.height() + height_delta)
    qt_app.processEvents()

    _kattintas_nyit(
        window, qt_app, engine, controller, "trayEmailButton", "emailChoiceDialog"
    )

    dialog = window.findChild(QObject, "emailChoiceDialog")
    try:
        csatolmanyok = list(dialog.property("attachmentPaths"))
        assert len(csatolmanyok) == 1, (
            "a levelezőben nem a tálcán kijelölt egy kép van csatolva"
        )
        assert Path(str(csatolmanyok[0])).is_file()
    finally:
        dialog.setProperty("visible", False)
        qt_app.processEvents()


@pytest.mark.parametrize("height_delta", _HEIGHT_DELTAS)
def test_talca_export_gomb_valodi_kattintasra_megnyitja_az_export_parbeszedet(
    talca_qml_app, qt_app, height_delta
):
    window, controller, engine = talca_qml_app
    window.resize(window.width(), window.height() + height_delta)
    qt_app.processEvents()

    _kattintas_nyit(
        window, qt_app, engine, controller, "trayExportButton", "exportDialog"
    )

    dialog = window.findChild(QObject, "exportDialog")
    try:
        assert bool(dialog.property("opened")) is True
    finally:
        dialog.close()
        qt_app.processEvents()


@pytest.mark.parametrize("height_delta", _HEIGHT_DELTAS)
def test_talca_nyomtatas_gomb_valodi_kattintasra_megnyitja_a_nyomtatas_parbeszedet(
    talca_qml_app, qt_app, height_delta
):
    window, controller, engine = talca_qml_app
    window.resize(window.width(), window.height() + height_delta)
    qt_app.processEvents()

    _kattintas_nyit(
        window, qt_app, engine, controller, "trayPrintButton", "printDialog"
    )

    dialog = window.findChild(QObject, "printDialog")
    try:
        assert dialog.property("visible") is True
    finally:
        dialog.setProperty("visible", False)
        qt_app.processEvents()
