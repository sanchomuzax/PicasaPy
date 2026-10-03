"""A Kiegyenesítés teljes nézetének mérete a #69-es referencia szerint."""

from __future__ import annotations

from pathlib import Path
from time import monotonic

import numpy as np
import pytest
from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtGui import QColor, QImage
from PySide6.QtTest import QTest

from tests.app.qml_functional.conftest import _build_qml_app
from tests.app.qml_functional.test_szerkeszto_sav_forgatott_kepen_4022 import (
    _renderelt_rgb,
)


_PALETTE_COLORS = np.asarray(
    (
        (254, 0, 0), (0, 255, 1), (0, 0, 254), (255, 255, 0),
        (0, 255, 255), (255, 0, 254), (255, 255, 255), (0, 0, 0),
        (128, 128, 128), (200, 151, 121), (60, 90, 150), (91, 140, 59),
        (229, 200, 60), (119, 60, 140), (240, 240, 240), (30, 30, 30),
    ),
    dtype=np.uint8,
)
_REFERENCE_FRAME_LEFT = 283
_REFERENCE_IMAGE_CENTER = (781.5, 487.5)
_REFERENCE_IMAGE_SIZE = (800, 800)


def _color_patches(lib: Path) -> None:
    """A job-69 palettaképe és egy 24 képes mappa a teljes nézethez."""
    pixels = np.empty((800, 800, 3), dtype=np.uint8)
    for row in range(4):
        for column in range(4):
            color = _PALETTE_COLORS[row * 4 + column]
            pixels[row * 200 : (row + 1) * 200,
                   column * 200 : (column + 1) * 200] = color
    image = QImage(
        pixels.data, 800, 800, 800 * 3, QImage.Format.Format_RGB888
    ).copy()
    assert image.save(str(lib / "color_patches.jpg"), "JPG", 100)

    # A teszt teljes képernyőképe a referencia 24 képes mappájának navigációs
    # és állapotsorát is kirajzolja; csak a második fájl a mért palettakép.
    for name, color in (
        ("a_before.jpg", (60, 90, 150)),
        *((f"z_photo_{index:02}.jpg", (index * 7, 80, 140))
          for index in range(2, 24)),
    ):
        thumbnail = QImage(80, 80, QImage.Format.Format_RGB32)
        thumbnail.fill(QColor(*color))
        assert thumbnail.save(str(lib / name), "JPG", 90)


def _item(window, name: str):
    item = window.findChild(QObject, name)
    assert item is not None, f"{name} nem található a főablakban"
    return item


def _wait_for(qt_app, predicate, message: str, timeout_s: float = 5.0) -> None:
    deadline = monotonic() + timeout_s
    while not predicate() and monotonic() < deadline:
        qt_app.processEvents()
        QTest.qWait(10)
    qt_app.processEvents()
    assert predicate(), message


def _box(item) -> tuple[float, float, float, float]:
    points = [
        item.mapToScene(QPointF(x, y))
        for x, y in (
            (0, 0),
            (item.width(), 0),
            (0, item.height()),
            (item.width(), item.height()),
        )
    ]
    return (
        min(point.x() for point in points),
        min(point.y() for point in points),
        max(point.x() for point in points),
        max(point.y() for point in points),
    )


def _painted_box(item) -> tuple[float, float, float, float]:
    """A képpontokból rajzolt kép határait adja, nem a nagyobb Image-dobozt."""
    x0, y0, x1, y1 = _box(item)
    width = float(item.property("paintedWidth"))
    height = float(item.property("paintedHeight"))
    return (
        x0 + (x1 - x0 - width) / 2,
        y0 + (y1 - y0 - height) / 2,
        x0 + (x1 - x0 + width) / 2,
        y0 + (y1 - y0 + height) / 2,
    )


def _click(window, item, qt_app) -> None:
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=point.toPoint())
    qt_app.processEvents()


@pytest.mark.parametrize(
    "kiegyenesites", (False, True), ids=("fit-nezet", "kiegyenesites")
)
def test_kiegyenesites_800px_kep_es_bal_fiok_renderelt_geometriaja(
    qt_app, tmp_path, kiegyenesites
):
    """Az illesztett és a Kiegyenesítés nézet 800 px-es fotóját méri."""
    generator = _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_color_patches,
        valodi_belyegkep=True,
    )
    window, controller, _engine = next(generator)
    try:
        window.setProperty("width", 1280)
        window.setProperty("height", 1005)
        # A referencia-felvételen a feliratmező rejtve van: az alsó sávban
        # nincs „Make a caption!” helyőrző, a fotó alját sem takarja.
        controller.setCaptionVisible(False)
        window.setProperty("viewerOpen", True)
        qt_app.processEvents()
        viewer = _item(window, "photoViewer")
        viewer.setProperty("currentIndex", 1)
        photo = _item(window, "viewerImage")
        _wait_for(
            qt_app,
            lambda: "color_patches.jpg"
            in str(viewer.property("currentFilePath")),
            "a 24 képes referencia mappa második képe nem a palettakép",
        )
        panel = _item(window, "viewerEditorPanel")
        panel.setProperty("activeTab", 0)
        _wait_for(
            qt_app,
            lambda: panel.property("visible") is True,
            "a néző szerkesztőpanelje nem nyílt meg",
        )
        if kiegyenesites:
            _click(window, _item(window, "editToolTilt"), qt_app)

        photo_area = _item(window, "viewerPhotoArea")
        drawer = _item(window, "viewerLeftDrawer")
        toolbar = _item(window, "editorToolBar")
        grid = _item(window, "straightenGridOverlay")
        _wait_for(
            qt_app,
            lambda: float(photo.property("paintedWidth")) > 0
            and float(photo.property("paintedHeight")) > 0
            and toolbar.property("visible") is kiegyenesites
            and grid.property("visible") is kiegyenesites,
            "a 800×800-as fotó, eszközsáv vagy háló nem rajzolódott ki",
        )

        screenshot = window.grabWindow()
        assert not screenshot.isNull(), "a főablak renderelt képe üres"
        # A teljes ablakos referencia felső filmszalagja valódi fotókat
        # mutat; az üres helyőrzővel készített screenshot diffje félrevezető.
        elso_belyegkep = screenshot.pixelColor(
            round(645 * float(screenshot.devicePixelRatio())),
            round(58 * float(screenshot.devicePixelRatio())),
        )
        assert (
            abs(elso_belyegkep.red() - 60) <= 40
            and abs(elso_belyegkep.green() - 90) <= 40
            and abs(elso_belyegkep.blue() - 150) <= 40
        ), (
            "a filmszalag első bélyegképe nem a mappa első, kék próbaképe: "
            f"{elso_belyegkep.getRgb()[:3]}"
        )
        kepernyo_fajl = (
            "kiegyenesites-4063-elotte.png"
            if kiegyenesites
            else "illesztett-nezet-4063.png"
        )
        assert screenshot.save(str(tmp_path / kepernyo_fajl))
        dpr = float(screenshot.devicePixelRatio())
        rendered = _renderelt_rgb(screenshot)
        image_item_box = _box(photo)
        image_box = _painted_box(photo)
        area_box = _box(photo_area)
        drawer_box = _box(drawer)
        toolbar_box = _box(toolbar) if kiegyenesites else None

        # A paletta 16 alapszínének maszkja a rács-vonalakat átugorja; a
        # határokat az egyes sor- és oszlopfutások szélső pixelei adják.
        color_diff = np.abs(
            rendered.astype(np.int16)[:, :, None, :]
            - _PALETTE_COLORS.astype(np.int16)[None, None, :, :]
        )
        palette_mask = np.any(np.all(color_diff <= 8, axis=3), axis=2)
        x_start = round(image_box[0] * dpr)
        x_end = round(image_box[2] * dpr)
        y_start = round(image_box[1] * dpr)
        y_end = round(image_box[3] * dpr)
        row = round((image_box[1] + 5) * dpr)
        col = round((image_box[0] + 5) * dpr)
        horizontal = np.flatnonzero(palette_mask[row, x_start:x_end])
        vertical = np.flatnonzero(palette_mask[y_start:y_end, col])
        assert horizontal.size and vertical.size, "a palettakép nem látható"
        pixel_box = (
            (x_start + horizontal[0]) / dpr,
            (y_start + vertical[0]) / dpr,
            (x_start + horizontal[-1] + 1) / dpr,
            (y_start + vertical[-1] + 1) / dpr,
        )

        gray_row = round((area_box[1] + 5) * dpr)
        gray_from = round((drawer_box[2] - 5) * dpr)
        gray_to = round((drawer_box[2] + 20) * dpr)
        gray_pixels = np.all(
            rendered[gray_row, gray_from:gray_to] == (128, 128, 128), axis=1
        )
        assert gray_pixels.any(), "a képmező szürke háttere nem látható"
        frame_left = gray_from + int(np.flatnonzero(gray_pixels)[0])
        frame_left /= dpr

        image_size = (pixel_box[2] - pixel_box[0], pixel_box[3] - pixel_box[1])
        image_center = ((pixel_box[0] + pixel_box[2]) / 2,
                        (pixel_box[1] + pixel_box[3]) / 2)
        print(
            "#4063 render: "
            f"drawer={drawer_box}, panel={_box(panel)}, photo_area={area_box}, "
            f"image_item_box={image_item_box}, image_box={image_box}, "
            f"pixel_box={pixel_box}, "
            f"pixel_size={image_size}, frame_left={frame_left}, "
            f"image_center={image_center}, "
            f"toolbar={toolbar_box}, grid_visible={grid.property('visible')}"
        )

        # A specifikáció 280 px-es paneltartalma mellett a teljes bal fiók
        # és a szürke képmező x=283-nál kezdődik (ui-audit-editor.md).
        hibak = []
        if abs(float(panel.width()) - 280) > 0.05:
            hibak.append(f"a szerkesztőpanel szélessége {panel.width()}, várt 280")
        if abs(float(drawer.width()) - _REFERENCE_FRAME_LEFT) > 0.05:
            hibak.append(
                f"a bal fiók szélessége {drawer.width()}, "
                f"a #69-es képmezőhatárhoz 283 kell"
            )
        if abs(frame_left - _REFERENCE_FRAME_LEFT) > 1 / dpr:
            hibak.append(
                f"a renderelt szürke képmező x={frame_left:.2f}-nál kezdődik, "
                f"a #69-es referencia x={_REFERENCE_FRAME_LEFT}-nál"
            )
        if toolbar_box is not None:
            area_center_x = (area_box[0] + area_box[2]) / 2
            toolbar_center_x = (toolbar_box[0] + toolbar_box[2]) / 2
            if abs(toolbar_center_x - area_center_x) > 0.5:
                hibak.append(
                    f"a Kiegyenesítés eszközsorának közepe "
                    f"x={toolbar_center_x:.1f}, "
                    f"a képmező közepe x={area_center_x:.1f}"
                )

        # A képméret a képpontokból jön, a közép a kirajzolt QML-dobozból.
        # A ±1 px engedi a Qt platformok egyképpontos raster-különbségét.
        if not all(
            abs(mert - vart) <= 1
            for mert, vart in zip(image_size, _REFERENCE_IMAGE_SIZE, strict=True)
        ):
            hibak.append(
                f"a renderelt 800×800-as kép mérete {image_size}, várt 800×800"
            )
        if not all(
            abs(mert - vart) <= 1
            for mert, vart in zip(
                image_center, _REFERENCE_IMAGE_CENTER, strict=True
            )
        ):
            hibak.append(
                f"a kirajzolt kép közepe {image_center}, "
                f"a #69-es referencia közepe {_REFERENCE_IMAGE_CENTER}"
            )
        assert not hibak, "\n".join(hibak)
    finally:
        try:
            next(generator)
        except StopIteration:
            pass
