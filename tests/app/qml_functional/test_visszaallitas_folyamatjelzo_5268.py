"""#5268: a Fájl ▸ Visszaállítás alatt a mentés folyamatjelzője látszik."""

from __future__ import annotations

import os
from pathlib import Path
from threading import Event

from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QSignalSpy, QTest

from picasapy.app import save_controller as save_controller_module
from support.qt_wait import wait_for_signal
from tests.app.qml_functional._fomenu_4420_menu import _megnyit
from tests.support.varakozas import var_feltetelre


_ABLAKMAGASSAG_ELTOLASOK = (-5, 0, 5)


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> None:
    assert var_feltetelre(qt_app, feltetel, masodperc), (
        "a felületi feltétel nem teljesült a határidőn belül"
    )


def _elem(ablak, nev: str) -> QQuickItem:
    elem = ablak.findChild(QQuickItem, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _kattint(ablak, qt_app, elem: QQuickItem) -> None:
    assert elem.property("enabled") is True, (
        f"{elem.objectName() or 'a menüpont'} nem kattintható"
    )
    assert elem.width() > 0 and elem.height() > 0
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        kozep.toPoint(),
    )
    qt_app.processEvents()


def _kijelol(ablak, qt_app, sorok: list[int]) -> None:
    ablak.setProperty("selectedIndexes", sorok)
    ablak.setProperty("selectedIndex", sorok[0] if sorok else -1)
    qt_app.processEvents()


def _mentsen_elotte(controller, qt_app, sorok: list[int]) -> None:
    wait_for_signal(
        controller.saveFinished,
        lambda: controller.saveRowsToDisk(sorok),
        description="a Visszaállításhoz szükséges mentés",
        process_events_with=qt_app,
    )
    _varj(qt_app, lambda: controller.hasSavedBackup(sorok))


def _kepernyokep(ablak, tmp_path: Path, offset: int) -> Path:
    kep = ablak.grabWindow()
    assert not kep.isNull(), "az offscreen ablak képe üres"
    megadott = os.environ.get("PICASAPY_5268_SCREENSHOT", "")
    cel = (
        Path(megadott)
        if megadott and offset == 0
        else tmp_path / f"visszaallitas-folyamatjelzo-{offset:+d}.png"
    )
    cel.parent.mkdir(parents=True, exist_ok=True)
    assert kep.save(str(cel)), f"a képernyőkép nem menthető: {cel}"
    return cel


def test_a_fajl_menu_visszaallitasa_kozben_latszik_a_folyamatjelzo(
    qml_app, qt_app, tmp_path, monkeypatch
):
    window, controller, _engine = qml_app
    menu_bar = window.property("menuBar")
    sorok = [0, 1]
    assert controller.photos.rowCount() >= len(sorok)
    utak = [Path(str(controller.photos.filePathAt(sor))) for sor in sorok]
    alapmagassag = window.height()

    for offset in _ABLAKMAGASSAG_ELTOLASOK:
        celmagassag = alapmagassag + offset
        window.resize(window.width(), celmagassag)
        _varj(qt_app, lambda celmagassag=celmagassag: window.height() == celmagassag)
        _kijelol(window, qt_app, sorok)
        _mentsen_elotte(controller, qt_app, sorok)

        elkezdodott = Event()
        folytathato = Event()
        eredeti_visszaallit = save_controller_module.revert

        def varakozo_visszaallit(
            path,
            *,
            elindult=elkezdodott,
            engedely=folytathato,
            eredeti=eredeti_visszaallit,
        ):
            if Path(path) == utak[-1]:
                elindult.set()
                assert engedely.wait(5), (
                    "a visszaállítási próbaművelet beragadt"
                )
            return eredeti(path)

        with monkeypatch.context() as patch:
            patch.setattr(save_controller_module, "revert", varakozo_visszaallit)
            kesz = QSignalSpy(controller.revertFinished)
            _megnyit(menu_bar, qt_app, "&File")
            menu_tetel = _elem(window, "menuFileRevert")
            assert menu_tetel.property("enabled") is True
            _kattint(window, qt_app, menu_tetel)

            parbeszed = window.findChild(QObject, "revertConfirmDialog")
            assert parbeszed is not None
            _varj(
                qt_app,
                lambda parbeszed=parbeszed: parbeszed.property("visible") is True,
            )
            _kattint(window, qt_app, _elem(window, "revertOkButton"))

            try:
                _varj(qt_app, elkezdodott.is_set)
                _varj(
                    qt_app,
                    lambda: abs(controller.saveProgressPercent - 50.0) <= 0.1,
                )
                panel = _elem(window, "saveProgressPanel")
                _kepernyokep(window, tmp_path, offset)
                assert panel.property("visible") is True, (
                    "a Fájl ▸ Visszaállítás fut, de a mentés folyamatjelzője "
                    "rejtve maradt"
                )
                assert _elem(window, "saveProgressPanelText").property("text") == (
                    "Reverting Files."
                )

                kep = window.grabWindow()
                assert not kep.isNull()
                toltes = _elem(window, "saveProgressPanelBarFill")
                assert toltes.width() > 0
                pont = toltes.mapToScene(
                    QPointF(toltes.width() / 2, toltes.height() / 2)
                )
                dpr = kep.devicePixelRatio()
                pixel = kep.pixelColor(round(pont.x() * dpr), round(pont.y() * dpr))
                assert pixel == toltes.property("color"), (
                    "a folyamatjelző kitöltése nem látszik a renderelt képen"
                )
            finally:
                folytathato.set()

            _varj(qt_app, lambda kesz=kesz: kesz.count() == 1)
            _varj(qt_app, lambda: not controller.saveProgressActive)
