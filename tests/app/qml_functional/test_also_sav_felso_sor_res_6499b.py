"""A felső alsó-sor gombközei ténylegesen látszanak a kirajzolt képen (#6499)."""

from __future__ import annotations

import math
import os
import time
from pathlib import Path

from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QColor, QImage
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest
from support.jpeg_factory import make_minta_jpeg
from tests.support.varakozas import var_feltetelre


def _walk(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _item(window, name: str) -> QQuickItem:
    for item in _walk(window.contentItem()):
        if item.objectName() == name:
            return item
    item = window.findChild(QObject, name)
    assert isinstance(item, QQuickItem), f"{name} nem található a kirajzolt ablakban"
    return item


def _doboz(item: QQuickItem) -> tuple[float, float, float, float]:
    top_left = item.mapToScene(QPointF(0, 0))
    return top_left.x(), top_left.y(), item.width(), item.height()


def _kattint(window, item: QQuickItem, qt_app) -> None:
    point = item.mapToScene(item.boundingRect().center())
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )
    qt_app.processEvents()


def _stabil_kep(window, qt_app) -> QImage:
    hatarido = time.monotonic() + 3.0
    elozo = None
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        kep = window.grabWindow()
        if not kep.isNull() and elozo is not None and kep == elozo:
            return kep
        elozo = kep
    raise AssertionError("a főablak kirajzolása nem állt be 3 másodpercen belül")


def _pixel(kep: QImage, meret: float, x: float, y: float) -> QColor:
    px = math.floor(x * meret)
    py = math.floor(y * meret)
    assert 0 <= px < kep.width() and 0 <= py < kep.height(), (
        f"a mért képpont kilóg a renderből: ({px}, {py}) / "
        f"{kep.width()}×{kep.height()}"
    )
    return kep.pixelColor(px, py)


def _szintavolsag(a: QColor, b: QColor) -> float:
    return math.sqrt(
        sum((x - y) ** 2 for x, y in zip(a.getRgb()[:3], b.getRgb()[:3], strict=True))
    )


def _hatterszinu_oszlopok(
    kep: QImage,
    meret: float,
    bal: QQuickItem,
    jobb: QQuickItem,
    hatter: QColor,
) -> int:
    bal_x, _, bal_w, bal_h = _doboz(bal)
    jobb_x, _, _, jobb_h = _doboz(jobb)
    also_jobb = bal.mapToScene(QPointF(bal_w, bal_h / 2))
    felso_bal = jobb.mapToScene(QPointF(0, jobb_h / 2))
    y = (also_jobb.y() + felso_bal.y()) / 2
    y_px = math.floor(y * meret)
    bal_keret = [
        x
        for x in range(
            math.floor((bal_x + bal_w - 5) * meret),
            math.ceil((bal_x + bal_w) * meret),
        )
        if _szintavolsag(kep.pixelColor(x, y_px), hatter) > 12
    ]
    jobb_keret = [
        x
        for x in range(
            math.floor(felso_bal.x() * meret),
            math.ceil((felso_bal.x() + 5) * meret),
        )
        if _szintavolsag(kep.pixelColor(x, y_px), hatter) > 12
    ]
    assert bal_keret and jobb_keret, (
        f"a keret nem látszik a(z) {bal.objectName()} / {jobb.objectName()} "
        "párnál"
    )
    x0 = max(bal_keret) + 1
    x1 = min(jobb_keret)
    return sum(
        _szintavolsag(kep.pixelColor(x, y_px), hatter) <= 12
        for x in range(x0, x1)
    )


def _sarkok_kerekitettek(
    kep: QImage,
    meret: float,
    button: QQuickItem,
    felso_hatter: QColor,
    also_hatter: QColor,
) -> list[str]:
    shade = button.findChild(QObject, "picasaButtonHoverShadeTop")
    assert isinstance(shade, QQuickItem), (
        f"{button.objectName()}: nem található a gomb kirajzolt háttere"
    )
    background = shade.parentItem()
    assert background is not None
    x, y, width, height = _doboz(background)
    corners = (
        ("bal felső", x + 0.5, y + 0.5, x + 3.5, y + 0.5),
        ("jobb felső", x + width - 0.5, y + 0.5, x + width - 3.5, y + 0.5),
        ("bal alsó", x + 0.5, y + height - 0.5, x + 3.5, y + height - 0.5),
        (
            "jobb alsó",
            x + width - 0.5,
            y + height - 0.5,
            x + width - 3.5,
            y + height - 0.5,
        ),
    )
    hibak = []
    for name, corner_x, corner_y, edge_x, edge_y in corners:
        # A fél pixeles jobb szélek antialias-sávja jobbra esik; a következő
        # pixel adja ugyanazt a legkülső sarkot, amit a bal oldalon floor mér.
        sarok_x = corner_x + (0.5 if name.startswith("jobb") else 0.0)
        sarok = _pixel(kep, meret, sarok_x, corner_y)
        keret = _pixel(kep, meret, edge_x, edge_y)
        hatter = felso_hatter if "felső" in name else also_hatter
        if _szintavolsag(sarok, hatter) > 35:
            hibak.append(
                f"{name}: sarok {sarok.getRgb()[:3]}, háttér {hatter.getRgb()[:3]}, "
                f"doboz=({x:.1f},{y:.1f},{width:.1f},{height:.1f})"
            )
        if _szintavolsag(keret, hatter) <= 18:
            hibak.append(f"{name}: a keret a lekerekítés után nem jelenik meg")
    return hibak


def _also_sav_kivagasa(window, kep: QImage, meret: float, cel: str) -> None:
    sav = _item(window, "trayMainBar")
    _, y, _, height = _doboz(sav)
    y_px = math.floor(y * meret)
    height_px = math.ceil(height * meret)
    Path(cel).parent.mkdir(parents=True, exist_ok=True)
    assert kep.copy(0, y_px, kep.width(), height_px).save(cel, "PNG"), (
        f"az alsó sáv kiadásképe nem menthető: {cel}"
    )


def test_felso_sor_res_es_negy_kulon_lekerekitett_gomb(
    qml_app_szines_belyegkep, qt_app
):
    """A rést és a sarkokat képpontból vizsgálja, három ablakmagasságon."""
    window, controller, _engine = qml_app_szines_belyegkep
    assert controller.photos.rowCount() >= 2, "a valódi próbaképek nem töltődtek be"
    konyvtar = Path(controller.watchedFolders[0])
    for index in range(3):
        make_minta_jpeg(
            konyvtar / f"0-6499b-{index}.jpg", size=(320, 240), seed=index + 20
        )
    controller.rescan()
    assert var_feltetelre(
        qt_app, lambda: controller.photos.rowCount() >= 5, 10.0
    ), "a mintázatos kiadásképek nem kerültek az indexbe"
    kijeloltek = [
        index
        for index, photo in enumerate(controller.photos.photos)
        if photo.name.startswith("0-6499b-")
    ]
    assert len(kijeloltek) == 3
    window.setProperty("selectedIndexes", kijeloltek)
    window.setProperty("selectedIndex", kijeloltek[0])
    window.setProperty("activeDrawerTab", "")
    window.setProperty("width", 1280)
    window.show()

    def thumbnails_keszek() -> bool:
        thumbs = [
            item
            for item in _walk(window.contentItem())
            if item.objectName() == "thumbImage"
            and item.isVisible()
            and item.property("paintedWidth") > 0
        ]
        return len(thumbs) >= 2 and window.isExposed()

    assert var_feltetelre(qt_app, thumbnails_keszek, 10.0), (
        "a kijelölt kép valódi bélyegképei nem rajzolódtak ki"
    )
    _kattint(window, _item(window, "trayHoldButton"), qt_app)
    assert var_feltetelre(qt_app, lambda: controller.heldCount == 3, 10.0), (
        "a három kijelölt kép nem került a valódi bélyegképes tálcába"
    )
    assert _item(window, "trayRotateLeft").isEnabled()
    assert _item(window, "trayRotateRight").isEnabled()

    alapmagassag = window.height()
    nevekkel = (
        ("trayRotateLeft", "trayRotateRight"),
        ("trayPanelToggle_people", "trayPanelToggle_places"),
        ("trayPanelToggle_places", "trayPanelToggle_tags"),
        ("trayPanelToggle_tags", "trayPanelToggle_properties"),
    )
    hibak = []
    for eltolás in (-5, 0, 5):
        celmagassag = alapmagassag + eltolás
        window.setHeight(celmagassag)
        hatarido = time.monotonic() + 3.0
        while time.monotonic() < hatarido and window.height() != celmagassag:
            qt_app.processEvents()
        assert window.height() == celmagassag, (
            f"az ablakmagasság nem állt be ({eltolás:+} px)"
        )

        kep = _stabil_kep(window, qt_app)
        meret = kep.width() / window.width()
        metadata = _item(window, "trayPanelToggle_properties")
        metadata_box = _doboz(metadata)
        hatter = _pixel(
            kep,
            meret,
            metadata_box[0] + metadata_box[2] + 2,
            metadata_box[1] + metadata_box[3] / 2,
        )
        people = _item(window, "trayPanelToggle_people")
        places = _item(window, "trayPanelToggle_places")
        people_x, people_y, people_w, people_h = _doboz(people)
        places_x, _, _, _ = _doboz(places)
        gap_x = (people_x + people_w + places_x) / 2
        felso_hatter = _pixel(kep, meret, gap_x, people_y + 0.5)
        also_hatter = _pixel(kep, meret, gap_x, people_y + people_h - 0.5)

        for bal_nev, jobb_nev in nevekkel:
            darab = _hatterszinu_oszlopok(
                kep,
                meret,
                _item(window, bal_nev),
                _item(window, jobb_nev),
                hatter,
            )
            if darab < 2:
                hibak.append(
                    f"{eltolás:+} px magasságnál {bal_nev} → {jobb_nev}: "
                    f"csak {darab} háttérképpont"
                )

        for nev in (
            "trayPanelToggle_people",
            "trayPanelToggle_places",
            "trayPanelToggle_tags",
            "trayPanelToggle_properties",
        ):
            hibak.extend(
                f"{eltolás:+} px magasságnál {nev}: {hiba}"
                for hiba in _sarkok_kerekitettek(
                    kep, meret, _item(window, nev), felso_hatter, also_hatter
                )
            )

        capture = os.environ.get("PICASAPY_6499B_CAPTURE_PATH")
        if capture and eltolás == 0:
            _also_sav_kivagasa(window, kep, meret, capture)

    assert not hibak, "a kirajzolt felső sáv hibái:\n- " + "\n- ".join(hibak)
