"""A bélyegkép-cache kiürítése az Opciók kapcsolója alapján (#5897)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtTest import QTest

from support.jpeg_factory import make_minta_jpeg
from support.varakozas import var_feltetelre
from conftest import _build_qml_app
from tests.app.qml_functional.test_menu_talca_egyeb_valodi_5135_b import (
    _elokeszit,
)
from tests.app.qml_functional.test_menu_talca_egyeb_valodi_5135_d import (
    _beallitasok_megnyit,
)


def _keszits_kepeket(konyvtar: Path) -> None:
    fotok = konyvtar / "fotok"
    fotok.mkdir()
    for index in range(1, 3):
        make_minta_jpeg(
            fotok / f"foto-{index}.jpg",
            size=(320, 240),
            seed=index,
        )


@pytest.fixture
def cache_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_kepeket,
        belyegkep_meret=256,
        valodi_belyegkep=True,
    )


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, feltetel, masodperc)


def _gyerek(szulo, nev: str):
    gyerek = szulo.findChild(type(szulo), nev)
    if gyerek is None:
        from PySide6.QtCore import QObject

        gyerek = szulo.findChild(QObject, nev)
    assert gyerek is not None, f"{nev} nem található"
    return gyerek


def _cache_fajlok(tmp_path: Path) -> list[Path]:
    return list((tmp_path / "thumbs").rglob("*.jpg"))


def _kattints_ablakban(qt_app, ablak, elem) -> None:
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(ablak, Qt.MouseButton.LeftButton, pos=QPoint(round(pont.x()), round(pont.y())))
    qt_app.processEvents()


def _kiadaskepekent_mentsd(window, dialog, cel: Path) -> None:
    """A két élő QML-ablakot az aktuális képernyőképpé menti.

    Az offscreen Qt platform nem minden runneren adja vissza a külön
    top-level ablakok közös képernyőképét, ezért ilyenkor a két ténylegesen
    renderelt ablakot a saját képernyő-koordinátájukkal illeszti egymásra.
    """
    # A képernyő egészének képe offscreen platformon inicializálatlan
    # képpontokat is adhat, ezért mindig a két renderelt ablakot illesztjük.
    hatter = window.grabWindow()
    eloter = dialog.grabWindow()
    kep = QPixmap.fromImage(hatter)
    festo = QPainter(kep)
    festo.drawImage(QPoint(dialog.x() - window.x(), dialog.y() - window.y()), eloter)
    festo.end()
    cel.parent.mkdir(parents=True, exist_ok=True)
    assert kep.save(str(cel), "PNG"), f"a kiadáskép nem menthető: {cel}"


@pytest.mark.parametrize("magassag_eltolas", (-5, 0, 5))
def test_general_kapcsolo_valodi_kattintassal_mentodik_es_kilepeskor_urit(
    cache_app, qt_app, tmp_path, magassag_eltolas
):
    window, controller, _engine = cache_app
    _elokeszit(window, qt_app, controller)
    kezdeti_magassag = window.height()
    window.setHeight(kezdeti_magassag + magassag_eltolas)
    assert _varj(qt_app, lambda: window.height() == kezdeti_magassag + magassag_eltolas)
    assert _varj(qt_app, lambda: bool(_cache_fajlok(tmp_path))), (
        "a valódi bélyegkép-szolgáltató nem írt cache-fájlt"
    )
    dialog = _beallitasok_megnyit(
        window, qt_app, window.property("menuBar")
    )
    checkbox = _gyerek(dialog, "optionsClearCacheFilesCheck")

    assert checkbox.property("text") == "Clear cache files"
    assert checkbox.property("checked") is False

    _kattints_ablakban(qt_app, dialog, checkbox)
    assert checkbox.property("checked") is True
    assert controller.disposePreviewsOnExit is True
    controller._get_settings().sync()

    close_button = _gyerek(dialog, "optionsCloseButton")
    _kattints_ablakban(qt_app, dialog, close_button)
    assert _varj(qt_app, lambda: dialog.property("visible") is False), (
        "az Opciók bezáró gombja nem zárta be a párbeszédet"
    )

    dialog = _beallitasok_megnyit(
        window, qt_app, window.property("menuBar")
    )
    checkbox = _gyerek(dialog, "optionsClearCacheFilesCheck")
    assert checkbox.property("checked") is True, (
        "a Clear cache files állapota nem maradt meg újranyitás után"
    )

    if (
        magassag_eltolas == 0
        and (screenshot := os.environ.get("PICASAPY_5897_KIADASKEP"))
    ):
        _kiadaskepekent_mentsd(window, dialog, Path(screenshot))

    assert _cache_fajlok(tmp_path), "a kilépési próba előtt nincs cache-fájl"
    controller.shutdown()
    assert not _cache_fajlok(tmp_path), (
        "a bekapcsolt kapcsoló nem ürítette ki a bélyegkép-cache-t kilépéskor"
    )


def test_kikapcsolt_kapcsolo_kilepeskor_meghagyja_a_cachet(
    cache_app, qt_app, tmp_path
):
    window, controller, _engine = cache_app
    _elokeszit(window, qt_app, controller)
    dialog = _beallitasok_megnyit(
        window, qt_app, window.property("menuBar")
    )
    checkbox = _gyerek(dialog, "optionsClearCacheFilesCheck")
    assert checkbox.property("checked") is False
    assert controller.disposePreviewsOnExit is False

    fajlok = _cache_fajlok(tmp_path)
    assert fajlok, "a kilépési próba előtt nincs cache-fájl"
    tartalom = {path: path.read_bytes() for path in fajlok}

    controller.shutdown()

    assert all(path.is_file() and path.read_bytes() == data for path, data in tartalom.items()), (
        "kikapcsolt állapotban a kilépés módosította a bélyegkép-cache-t"
    )
