"""A Nézet menü pipái keret nélkül jelennek meg (#5885)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtQuick import QQuickWindow

from conftest import _build_qml_app
from tests.app.qml_functional._felsomenupontok_helpers_4329 import _objektum
from tests.app.qml_functional._fomenu_4420_menu import _megnyit
from tests.support.jpeg_factory import make_minta_jpeg
from tests.support.varakozas import var_feltetelre

_KEPEK = 8
_KIADASKEP_KORNYEZET = "PICASAPY_5885_SCREENSHOT"


def _mintakepeket_keszit(konyvtar: Path) -> None:
    fotok = konyvtar / "fotok"
    fotok.mkdir()
    for index in range(_KEPEK):
        make_minta_jpeg(
            fotok / f"minta_{index:02}.jpg",
            size=(320, 240),
            seed=5885 + index,
        )


@pytest.fixture
def nezet_app(qt_app, tmp_path, request):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_mintakepeket_keszit,
        belyegkep_meret=144,
        valodi_belyegkep=True,
        show_only_big_images=True,
        keep_modul=request.module,
    )


def _terheles_utan(nezet_app, qt_app):
    ablak, vezerlo, _engine = nezet_app
    ablak.show()
    ablak.requestActivate()
    qt_app.processEvents()
    gyoker = Path(str(vezerlo.watchedFolders[0])) / "fotok"
    vezerlo.selectFolder(str(gyoker))
    assert var_feltetelre(
        qt_app, lambda: len(vezerlo.photos.photos) == _KEPEK, 10.0
    ), "a tesztfotók nem töltődtek be a könyvtárba"
    ablak.setProperty("selectedIndexes", [0])
    ablak.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    return ablak


def _jelenet_pixel(kep: QImage, elem, x: float, y: float) -> QColor:
    pont = elem.mapToScene(QPointF(x, y))
    dpr = kep.devicePixelRatio() or 1.0
    return kep.pixelColor(round(pont.x() * dpr), round(pont.y() * dpr))


def _jelolo_pixelek(kep: QImage, jelolo) -> list[tuple[int, int, QColor]]:
    bal_fent = jelolo.mapToScene(QPointF(0.0, 0.0))
    dpr = kep.devicePixelRatio() or 1.0
    bal = round(bal_fent.x() * dpr)
    fent = round(bal_fent.y() * dpr)
    szeles = max(1, round(float(jelolo.property("width")) * dpr))
    magas = max(1, round(float(jelolo.property("height")) * dpr))
    return [
        (x, y, kep.pixelColor(x, y))
        for y in range(fent, fent + magas)
        for x in range(bal, bal + szeles)
    ]


def _sor_hattere(kep: QImage, jelolo) -> QColor:
    # A jelölő bal oldalán maradó belső margóban nincs felirat; a sor jobb
    # szélén a gyorsbillentyű szövege állhat.
    return _jelenet_pixel(
        kep,
        jelolo,
        -2.0,
        float(jelolo.property("height")) / 2.0,
    )


def _ures_jelolo(kep: QImage, tetel, nev: str) -> None:
    jelolo = tetel.property("indicator")
    assert jelolo is not None, f"{nev}: hiányzik a jelölőhely"
    assert float(jelolo.property("width")) > 0
    pixelek = _jelolo_pixelek(kep, jelolo)
    hatter = _sor_hattere(kep, jelolo)
    elteresek = [(x, y, szin.name()) for x, y, szin in pixelek if szin != hatter]
    assert not elteresek, (
        f"{nev}: az üres jelölőhely eltér a menüsor hátterétől; "
        f"első eltérő képpontok: {elteresek[:8]}, háttér={hatter.name()}"
    )


def _pipa_keret_nelkul(kep: QImage, tetel, nev: str) -> None:
    jelolo = tetel.property("indicator")
    assert jelolo is not None, f"{nev}: hiányzik a jelölő"
    pixelek = _jelolo_pixelek(kep, jelolo)
    hatter = _sor_hattere(kep, jelolo)
    dpr = kep.devicePixelRatio() or 1.0
    szeles = max(1, round(float(jelolo.property("width")) * dpr))
    magas = max(1, round(float(jelolo.property("height")) * dpr))
    nem_hatter = [(x, y, szin) for x, y, szin in pixelek if szin != hatter]
    assert nem_hatter, f"{nev}: a kipipált tételen nem látszik pipa"

    bal_fent = jelolo.mapToScene(QPointF(0.0, 0.0))
    bal = round(bal_fent.x() * dpr)
    fent = round(bal_fent.y() * dpr)
    keret = [
        (x, y, szin)
        for x, y, szin in nem_hatter
        if x in {bal, bal + szeles - 1} or y in {fent, fent + magas - 1}
    ]
    assert not keret, (
        f"{nev}: keret rajzolódik a pipa köré: "
        f"{[(x, y, szin.name()) for x, y, szin in keret[:8]]}"
    )


def _behuzas_megmarad(tetel, nev: str) -> None:
    jelolo = tetel.property("indicator")
    tartalom = tetel.property("contentItem")
    assert jelolo is not None, f"{nev}: hiányzik a jelölőhely"
    assert tartalom is not None, f"{nev}: hiányzik a felirat"
    vart_behuzas = float(jelolo.property("width")) + float(
        tetel.property("spacing")
    )
    tenyleges_behuzas = float(tartalom.property("leftPadding"))
    assert tenyleges_behuzas == pytest.approx(vart_behuzas), (
        f"{nev}: a felirat behúzása {tenyleges_behuzas}px, "
        f"a jelölőhely és a térköz együtt {vart_behuzas}px"
    )


def _kiadaskeppet_ment(ablak, menu_ablak: QQuickWindow) -> None:
    cel = os.environ.get(_KIADASKEP_KORNYEZET)
    if not cel:
        return

    hatter = ablak.grabWindow().convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
    menu = menu_ablak.grabWindow().convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
    assert not hatter.isNull(), "a főablak képe üres"
    assert not menu.isNull(), "a Nézet menü képe üres"

    dpr = hatter.devicePixelRatio() or 1.0
    menu_pozicio = menu_ablak.position() - ablak.position()
    painter = QPainter(hatter)
    painter.drawImage(round(menu_pozicio.x() * dpr), round(menu_pozicio.y() * dpr), menu)
    painter.end()

    cel_ut = Path(cel)
    cel_ut.parent.mkdir(parents=True, exist_ok=True)
    assert hatter.save(str(cel_ut), "PNG"), f"a kiadáskép nem menthető: {cel_ut}"


def test_a_nezet_menu_pipa_nem_rajzol_negyzetet(nezet_app, qt_app):
    ablak = _terheles_utan(nezet_app, qt_app)
    menu_bar = ablak.property("menuBar")
    assert menu_bar is not None, "a menüsor nem épült fel"
    menu = _megnyit(menu_bar, qt_app, "&View")
    assert var_feltetelre(qt_app, lambda: menu.property("opened") is True, 3.0)

    library = _objektum(ablak, "menuViewLibraryView")
    small = _objektum(ablak, "menuViewSmallThumbnails")
    normal = _objektum(ablak, "menuViewNormalThumbnails")
    properties = _objektum(ablak, "menuViewProperties")
    small_pictures = _objektum(ablak, "menuViewThumbnailsOnly")
    assert all(
        item is not None
        for item in (library, small, normal, properties, small_pictures)
    )
    assert library.property("checked") is True
    assert small.property("checked") is False
    assert normal.property("checked") is True
    assert properties.property("checked") is False
    assert small_pictures.property("checked") is False
    assert var_feltetelre(qt_app, lambda: normal.property("visible") is True, 3.0)

    for item, nev in (
        (small, "Kis indexképek"),
        (normal, "Normál indexképek"),
        (properties, "Tulajdonságok"),
        (small_pictures, "Kis képek"),
    ):
        _behuzas_megmarad(item, nev)

    menu_ablak = normal.window()
    assert isinstance(menu_ablak, QQuickWindow)
    qt_app.processEvents()
    kep = menu_ablak.grabWindow()
    assert not kep.isNull(), "a megnyitott Nézet menü renderképe üres"
    _kiadaskeppet_ment(ablak, menu_ablak)

    _ures_jelolo(kep, small, "Kis indexképek")
    _ures_jelolo(kep, properties, "Tulajdonságok")
    _ures_jelolo(kep, small_pictures, "Kis képek")
    _pipa_keret_nelkul(kep, normal, "Normál indexképek")
    _pipa_keret_nelkul(kep, library, "Könyvtárnézet")
