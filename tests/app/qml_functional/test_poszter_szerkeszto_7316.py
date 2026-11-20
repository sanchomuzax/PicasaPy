"""#7316 - a kész poszter után a szerkesztő az utolsó lapot mutatja.

Az eredeti poszterkezelő (`0x00530c10`, a lapciklus után `0x0053de70`) sikeres
futás után szerkesztőnézetre vált, és az utolsó létrejött lapot mutatja; a
forráskép a kijelölésben marad. A próba a valódi Létrehozás menüből indítja a
posztert egy kijelölt képpel, és a kirajzolt nézőt méri, nem a belső hívásokat.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QSignalSpy, QTest

import picasapy.printing.dpi as dpi
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.varakozas import var_feltetelre

_FORRAS_NEV = "color_patches.jpg"
_UTOLSO_LAP_NEV = f"1-1-{_FORRAS_NEV}"


def _chart(lib):
    yy, xx = np.indices((800, 800), dtype=np.uint16)
    rgb = np.empty((800, 800, 3), dtype=np.uint8)
    rgb[..., 0] = (xx // 40 * 31 + yy // 40 * 17) % 256
    rgb[..., 1] = xx % 256
    rgb[..., 2] = yy % 256
    Image.fromarray(rgb, "RGB").save(
        lib / _FORRAS_NEV, format="JPEG", quality=100, subsampling=0
    )


@pytest.fixture(autouse=True)
def _amerikai_papirbeallitas(monkeypatch):
    monkeypatch.setattr(dpi, "_metrikus_teruleti_meres", lambda: False)


@pytest.fixture(scope="module")
def poster_editor_app(
    qt_app,
    tmp_path_factory,
    _module_qml_warnings,
    _module_user_folder_guard,
):
    """A teljes QML-ablakot egyszer építi fel a poszter-próbákhoz."""
    amerikai = pytest.MonkeyPatch()
    amerikai.setattr(dpi, "_metrikus_teruleti_meres", lambda: False)
    app = _build_qml_app(
        qt_app,
        tmp_path_factory.mktemp("poster-7316"),
        kepeket_keszit=_chart,
    )
    try:
        window, controller, engine = next(app)
        yield window, controller, engine
    finally:
        try:
            next(app, None)
        finally:
            amerikai.undo()


@pytest.fixture(autouse=True)
def _tiszta_allapot_utana(request, qt_app):
    """Minden próba nézőmentes, párbeszédmentes állapotból indul és oda tér vissza.

    A modulszintű alkalmazásban a hibaág eredmény-párbeszéde és a megnyitott
    néző átlógna a következő próbába."""
    yield
    if "poster_editor_app" not in request.fixturenames:
        return
    window, _controller, _engine = request.getfixturevalue("poster_editor_app")
    window.setProperty("viewerOpen", False)
    eredmeny = window.findChild(QObject, "createResultDialog")
    if eredmeny is not None and eredmeny.property("opened") is True:
        QMetaObject.invokeMethod(eredmeny, "close", Qt.ConnectionType.DirectConnection)
        var_feltetelre(
            qt_app, lambda: eredmeny.property("opened") is not True, 5.0
        )


def _qml_lista(ertek) -> list:
    """Egy QML `var` lista Pythonban: az érték `list` vagy `QJSValue` is lehet."""
    if hasattr(ertek, "toVariant"):
        ertek = ertek.toVariant()
    return list(ertek or [])


def _var(qt_app, condition, message: str, seconds: float = 10.0):
    if not var_feltetelre(qt_app, condition, seconds):
        raise AssertionError(message)


def _elem(root, name: str):
    item = root.findChild(QObject, name)
    assert item is not None, f"nem található a kirajzolt {name} vezérlő"
    return item


def _kattintas(item):
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        item.window(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )


def _forras_kijelolese(window, controller, qt_app) -> str:
    """A forráskép (az egyetlen kép) kijelölése, az útvonalát adja vissza."""
    sor = controller.photos.rowOfPath(
        str(Path(controller.currentFolder) / _FORRAS_NEV)
    )
    assert sor >= 0, "a forráskép nincs a rácsban"
    window.setProperty("selectedIndexes", [sor])
    window.setProperty("selectedIndex", sor)
    qt_app.processEvents()
    return controller.photos.filePathAt(sor)


def _poszter_inditasa_menubol(window, controller, qt_app):
    """Létrehozás ▸ Poszter valódi kattintással, majd az OK gomb."""
    create_menu = _elem(window, "menuCreateRoot")
    assert QMetaObject.invokeMethod(
        create_menu, "open", Qt.ConnectionType.DirectConnection
    )
    poster = _elem(window, "menuCreatePoster")
    _var(
        qt_app,
        lambda: create_menu.property("opened") is True and poster.isVisible(),
        "a Poszter menüpont nem jelent meg teljesen",
    )
    assert poster.property("enabled") is True
    _kattintas(poster)
    _var(
        qt_app,
        lambda: (
            window.findChild(QObject, "posterDialog") is not None
            and _elem(window, "posterDialog").property("opened") is True
        ),
        "a menükattintás nem nyitotta meg a Poszter párbeszédet",
    )
    dialog = _elem(window, "posterDialog")
    _kattintas(_elem(dialog, "posterAcceptButton"))
    _var(
        qt_app,
        lambda: dialog.property("opened") is not True,
        "a Poszter párbeszéd elfogadása nem zárta be a párbeszédet",
    )


def _eredmeny_parbeszed_nyitva(window) -> bool:
    dialog = window.findChild(QObject, "createResultDialog")
    return dialog is not None and dialog.property("opened") is True


def _normalizalt(path: str) -> str:
    return str(Path(path))


def test_siker_utan_az_utolso_lap_nyilik_a_szerkesztoben_a_forras_kijelolve_marad(
    poster_editor_app, qt_app
):
    window, controller, _engine = poster_editor_app
    forras = _forras_kijelolese(window, controller, qt_app)
    mappa = Path(forras).parent
    assert window.property("viewerOpen") is not True

    finished = QSignalSpy(controller.posterFinished)
    failed = QSignalSpy(controller.posterFailed)
    _poszter_inditasa_menubol(window, controller, qt_app)

    _var(
        qt_app,
        lambda: finished.count() > 0 or failed.count() > 0,
        "a poszter háttérmunkája nem jelzett befejezést vagy hibát",
        seconds=20.0,
    )
    assert failed.count() == 0, (
        f"a poszter hibát jelzett: {failed.at(0)[0] if failed.count() else ''}"
    )

    # Az eredeti az utolsó létrejött lapot (`1-1-<név>.jpg`) mutatja.
    _var(
        qt_app,
        lambda: window.property("viewerOpen") is True,
        "a poszter elkészülte után nem nyílt meg a néző/szerkesztő",
        seconds=20.0,
    )
    viewer = window.ensurePhotoViewer()
    varhato = _normalizalt(str(mappa / _UTOLSO_LAP_NEV))
    _var(
        qt_app,
        lambda: _normalizalt(str(viewer.property("currentPath"))) == varhato,
        "a néző nem az utolsó poszterlapot mutatja: "
        f"{viewer.property('currentPath')!r} != {varhato!r}",
    )

    # A siker visszajelzése maga a szerkesztő: eredmény-párbeszéd nem nyílik.
    assert not _eredmeny_parbeszed_nyitva(window), (
        "az eredmény-párbeszéd a szerkesztő helyett/mellett is megnyílt"
    )

    # A forráskép a kijelölésben marad (a sorindexek a beszúrás után eltolódtak).
    kijeloltek = [int(sor) for sor in _qml_lista(window.property("selectedIndexes"))]
    assert len(kijeloltek) == 1, f"a kijelölés megváltozott: {kijeloltek}"
    assert _normalizalt(controller.photos.filePathAt(kijeloltek[0])) == _normalizalt(
        forras
    ), "a kijelölés nem a forrásképen maradt"


def test_hibaag_valtozatlan_latszo_hibajelzes_es_nem_nyilik_szerkeszto(
    poster_editor_app, qt_app, monkeypatch
):
    from picasapy.app import poster_controller

    window, controller, _engine = poster_editor_app
    _forras_kijelolese(window, controller, qt_app)
    window.setProperty("viewerOpen", False)
    qt_app.processEvents()

    def hibas_folyamat(command, **kwargs):
        Path(command[-1]).write_text(
            json.dumps({"error": "szintetikus poszterhiba 7316"}), encoding="utf-8"
        )
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="")

    monkeypatch.setattr(poster_controller, "_run", hibas_folyamat)

    failed = QSignalSpy(controller.posterFailed)
    _poszter_inditasa_menubol(window, controller, qt_app)
    _var(
        qt_app,
        lambda: failed.count() > 0,
        "a hibás poszterfolyamat nem jelzett hibát",
        seconds=20.0,
    )

    _var(
        qt_app,
        lambda: _eredmeny_parbeszed_nyitva(window),
        "a poszter hibájáról nem jelent meg látható hibajelzés",
    )
    szoveg = str(_elem(window, "createResultText").property("text"))
    assert "The poster tiles could not be created." in szoveg
    assert "szintetikus poszterhiba 7316" in szoveg
    assert window.property("viewerOpen") is not True, (
        "hiba után nem nyílhat meg a szerkesztő"
    )


def test_a_lap_modellbe_kerulesere_var_es_utana_nyitja_meg(
    poster_editor_app, qt_app
):
    """A lap csak a célzott újraolvasás után kerül a rácsba: addig nem nyílik."""
    window, controller, _engine = poster_editor_app
    forras = _forras_kijelolese(window, controller, qt_app)
    mappa = Path(forras).parent
    uj_lap = mappa / "9-9-modellre-var.jpg"
    shutil.copyfile(forras, uj_lap)
    assert controller.photos.rowOfPath(str(uj_lap)) < 0, "a lap már a rácsban van"
    window.setProperty("viewerOpen", False)
    qt_app.processEvents()

    controller.posterFinished.emit([str(uj_lap)])
    qt_app.processEvents()
    assert window.property("viewerOpen") is not True, (
        "a néző megnyílt, pedig a lap még nincs a rácsmodellben"
    )

    controller.resyncFolder(str(mappa))
    _var(
        qt_app,
        lambda: window.property("viewerOpen") is True,
        "a lap rácsba kerülése után nem nyílt meg a néző",
        seconds=20.0,
    )
    viewer = window.ensurePhotoViewer()
    _var(
        qt_app,
        lambda: _normalizalt(str(viewer.property("currentPath")))
        == _normalizalt(str(uj_lap)),
        "a néző nem a frissen indexelt lapot mutatja",
    )
    assert not _eredmeny_parbeszed_nyitva(window)


def test_ha_a_lap_nem_kerul_a_racsba_az_eredmeny_parbeszed_jelez(
    poster_editor_app, qt_app
):
    """Tartalék: a siker ilyenkor sem maradhat visszajelzés nélkül."""
    window, controller, _engine = poster_editor_app
    _forras_kijelolese(window, controller, qt_app)
    window.setProperty("viewerOpen", False)
    qt_app.processEvents()
    opener = _elem(window, "posterResultOpener")
    opener.setProperty("waitMs", 300)
    nincs_a_racsban = str(Path(controller.currentFolder) / "nincs" / "1-1-ures.jpg")

    controller.posterFinished.emit([nincs_a_racsban])

    _var(
        qt_app,
        lambda: _eredmeny_parbeszed_nyitva(window),
        "a rácsba nem került lapnál nem jelent meg az eredmény-párbeszéd",
    )
    szoveg = str(_elem(window, "createResultText").property("text"))
    assert "Poster tiles saved." in szoveg
    assert nincs_a_racsban in szoveg
    assert window.property("viewerOpen") is not True
