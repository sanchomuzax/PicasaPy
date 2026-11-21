"""A „Clear cache files" kapcsoló az Opciókban (#5897, átalakítva a #7332-ben).

Az #5897 a kapcsolót tartósan mentette, és kilépéskor ürítette a lemezes ÉS
memóriabeli bélyegkép-tárat. A #7332 az eredeti viselkedéshez igazította
(`0x005cfdeb`-`0x005cfe48`): az OK után, ha a jelölő be van kapcsolva, a
MEMÓRIABELI tár azonnal ürül és a jelölő kikapcsoltra áll vissza; a lemezes
tárhoz az OK nem nyúl, kilépéskor semmi nem üríti. Ezért a régi
„kilépéskor ürít" próba itt az OK utáni hatást méri, és külön őrzi, hogy a
kilépés már nem töröl.
"""

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


def _memoriatar_kitoltese(controller) -> None:
    """Egy szűrt bélyegképet tesz a memóriarekeszbe, mint a szerkesztett fotók."""
    from PySide6.QtGui import QImage

    kep = QImage(8, 8, QImage.Format.Format_RGB32)
    kep.fill(0x336699)
    controller._provider._memo.put(("7332",), kep)
    assert controller._provider._memo.get(("7332",)) is not None


def _memoriatar_tele(controller) -> bool:
    return controller._provider._memo.get(("7332",)) is not None


@pytest.mark.parametrize("magassag_eltolas", (-5, 0, 5))
def test_general_kapcsolo_ok_utan_uriti_a_memoriat_es_visszaall(
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
    _memoriatar_kitoltese(controller)
    lemezes_elotte = {
        path: path.read_bytes() for path in _cache_fajlok(tmp_path)
    }
    dialog = _beallitasok_megnyit(
        window, qt_app, window.property("menuBar")
    )
    checkbox = _gyerek(dialog, "optionsClearCacheFilesCheck")

    assert checkbox.property("text") == "Clear cache files"
    assert checkbox.property("checked") is False

    _kattints_ablakban(qt_app, dialog, checkbox)
    assert checkbox.property("checked") is True
    assert _memoriatar_tele(controller), (
        "a jelölő kattintásra azonnal ürítette a memóriatárat"
    )

    if (
        magassag_eltolas == 0
        and (screenshot := os.environ.get("PICASAPY_5897_KIADASKEP"))
    ):
        _kiadaskepekent_mentsd(window, dialog, Path(screenshot))

    # #5906: a módosítás az OK-ra lép életbe
    ok_button = _gyerek(dialog, "optionsOkButton")
    _kattints_ablakban(qt_app, dialog, ok_button)
    assert _varj(qt_app, lambda: dialog.property("visible") is False), (
        "az Opciók OK gombja nem zárta be a párbeszédet"
    )
    assert not _memoriatar_tele(controller), (
        "az OK nem ürítette a memóriabeli bélyegkép-tárat (#7332)"
    )
    assert controller.disposePreviewsOnExit is False, (
        "az OK nem állította vissza kikapcsoltra a jelölőt (#7332)"
    )
    assert {
        path: path.read_bytes() for path in _cache_fajlok(tmp_path)
    } == lemezes_elotte, "az OK a lemezes bélyegkép-tárat is módosította"

    dialog = _beallitasok_megnyit(
        window, qt_app, window.property("menuBar")
    )
    checkbox = _gyerek(dialog, "optionsClearCacheFilesCheck")
    assert checkbox.property("checked") is False, (
        "a Clear cache files nem állt vissza kikapcsoltra az OK után"
    )

    controller.shutdown()
    assert {
        path: path.read_bytes() for path in _cache_fajlok(tmp_path)
    } == lemezes_elotte, "kilépéskor már nem ürülhet a lemezes bélyegkép-tár"


def test_kikapcsolt_jelolovel_az_ok_nem_urit(cache_app, qt_app, tmp_path):
    window, controller, _engine = cache_app
    _elokeszit(window, qt_app, controller)
    assert _varj(qt_app, lambda: bool(_cache_fajlok(tmp_path)))
    _memoriatar_kitoltese(controller)
    dialog = _beallitasok_megnyit(
        window, qt_app, window.property("menuBar")
    )
    checkbox = _gyerek(dialog, "optionsClearCacheFilesCheck")
    assert checkbox.property("checked") is False

    _kattints_ablakban(qt_app, dialog, _gyerek(dialog, "optionsOkButton"))

    assert _varj(qt_app, lambda: dialog.property("visible") is False)
    assert _memoriatar_tele(controller), (
        "kikapcsolt jelölőnél az OK ürítette a memóriatárat"
    )
    assert _cache_fajlok(tmp_path)


def test_regi_mentett_bejeloles_az_elso_ok_utan_urit_es_nullazodik(
    cache_app, qt_app
):
    """Az #5897-ben mentett `true` érték: a jelölő bejelölve nyílik, és az
    OK (a jelölő érintése nélkül is) ürít és visszaállítja, mint az eredeti,
    ahol az OK utáni ág a kulcs aktuális értékét nézi."""
    window, controller, _engine = cache_app
    _elokeszit(window, qt_app, controller)
    controller.setDisposePreviewsOnExit(True)
    _memoriatar_kitoltese(controller)
    dialog = _beallitasok_megnyit(
        window, qt_app, window.property("menuBar")
    )
    checkbox = _gyerek(dialog, "optionsClearCacheFilesCheck")
    assert checkbox.property("checked") is True

    _kattints_ablakban(qt_app, dialog, _gyerek(dialog, "optionsOkButton"))

    assert _varj(qt_app, lambda: dialog.property("visible") is False)
    assert not _memoriatar_tele(controller)
    assert controller.disposePreviewsOnExit is False


@pytest.mark.parametrize("magassag_eltolas", (-5, 0, 5))
def test_general_kapcsolo_cancel_elveti_a_valtoztatast(
    cache_app, qt_app, magassag_eltolas
):
    window, controller, _engine = cache_app
    _elokeszit(window, qt_app, controller)
    kezdeti_magassag = window.height()
    window.setHeight(kezdeti_magassag + magassag_eltolas)
    assert _varj(qt_app, lambda: window.height() == kezdeti_magassag + magassag_eltolas)
    dialog = _beallitasok_megnyit(
        window, qt_app, window.property("menuBar")
    )
    checkbox = _gyerek(dialog, "optionsClearCacheFilesCheck")
    assert checkbox.property("checked") is False
    assert controller.disposePreviewsOnExit is False
    _memoriatar_kitoltese(controller)

    _kattints_ablakban(qt_app, dialog, checkbox)
    assert checkbox.property("checked") is True
    assert controller.disposePreviewsOnExit is False, (
        "a jelölő kattintásra azonnal módosította a tartós beállítást"
    )

    cancel_button = _gyerek(dialog, "optionsCancelButton")
    _kattints_ablakban(qt_app, dialog, cancel_button)
    assert _varj(qt_app, lambda: dialog.property("visible") is False), (
        "az Opciók Mégse gombja nem zárta be a párbeszédet"
    )
    assert controller.disposePreviewsOnExit is False, (
        "a Mégse nem vonta vissza a Clear cache files módosítását"
    )
    assert _memoriatar_tele(controller), (
        "a Mégse ürítette a memóriabeli bélyegkép-tárat"
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
