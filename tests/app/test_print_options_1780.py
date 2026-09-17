"""A #1780 printoptions-panel állapot- és kimeneti őrei."""

from __future__ import annotations

import os
from dataclasses import dataclass

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtGui import QGuiApplication, QImage

from picasapy.app.print_controller import PrintController
from picasapy.printing.options import TEXT_SIZE_VALUES, PrintOptions
from support.jpeg_factory import make_jpeg


@pytest.fixture(scope="module")
def qt_app():
    return QGuiApplication.instance() or QGuiApplication([])


@dataclass
class _Photo:
    folder_path: str
    name: str
    caption: str = "Megjegyzett kép"
    taken_at: str = "2024-01-02 03:04:05"
    width: int = 400
    height: int = 200


def _white_jpeg(path):
    image = QImage(400, 200, QImage.Format.Format_RGB32)
    image.fill(0xFFFFFFFF)
    assert image.save(str(path), "JPEG")
    return path


def _controller(tmp_path):
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    return PrintController(
        photo_source=lambda: photos,
        settings=settings,
    )


# A fixture-függvényben használt rekordlista egyetlen tesztben él; a helper
# paraméterezhetősége fontosabb lenne, mint egy újabb, Qt-szálat indító fixture.
photos: list[_Photo] = []


class TestPrintOptionsStorage:
    def test_mind_a_tizenegy_kulcs_es_a_meretlista_merve(self, qt_app, tmp_path):
        source = _white_jpeg(tmp_path / "kep.jpg")
        photos[:] = [_Photo(str(tmp_path), source.name)]
        controller = _controller(tmp_path)

        options = controller.printOptions()
        assert set(options) == {
            "textSource", "textPlacement", "textFont", "textSize", "textColor",
            "wrap", "border", "borderSize", "borderColor", "borderEdge",
            "evenBorder",
        }
        assert options["textSource"] == 0
        assert options["textPlacement"] == 0
        assert options["textFont"] == "Arial"
        assert options["textSize"] == 12
        assert options["borderSize"] == 10
        assert options["evenBorder"] is True
        assert controller.printTextSizes() == list(TEXT_SIZE_VALUES)

    def test_a_vezerlok_azonnal_mentenek_es_a_visszatoltes_visszaallit(self, qt_app, tmp_path):
        source = make_jpeg(tmp_path / "kep.jpg")
        photos[:] = [_Photo(str(tmp_path), source.name)]
        controller = _controller(tmp_path)
        eredeti = controller.printOptions()

        controller.setPrintOption("textSource", 2)
        controller.setPrintOption("textPlacement", 1)
        controller.setPrintOption("border", True)
        controller.setPrintOption("borderSize", 777)
        controller.setPrintOption("textColor", 0xFFFF0000)
        assert controller.printOptions()["borderSize"] == 777
        assert controller.printOptions()["textColor"] == 0xFFFF0000

        controller.restorePrintOptions(eredeti)
        assert controller.printOptions() == eredeti

    @pytest.mark.parametrize(
        ("name", "value", "expected"),
        [
            ("textSource", -1, 0),
            ("textSource", 99, 3),
            ("textPlacement", 99, 2),
            ("borderSize", -1, 0),
            ("borderSize", 9999, 1024),
            ("textSize", 13, 12),
        ],
    )
    def test_a_hatarertekek_nem_irnak_ervenytelen_allapotot(
        self, qt_app, tmp_path, name, value, expected
    ):
        source = make_jpeg(tmp_path / "kep.jpg")
        photos[:] = [_Photo(str(tmp_path), source.name)]
        controller = _controller(tmp_path)
        controller.setPrintOption(name, value)
        assert controller.printOptions()[name] == expected


class TestPrintOptionsText:
    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            (0, ""),
            (1, "Megjegyzett kép"),
            (2, "kep.jpg"),
            (3, "2024-01-02 03:04:05 · 400 × 200"),
        ],
    )
    def test_a_negy_feliratforras_kulon_el(self, source, expected):
        record = _Photo("/képek", "kep.jpg")
        assert PrintController._caption_text(
            record, PrintOptions(textSource=source)
        ) == expected

    @pytest.mark.parametrize("placement", [0, 1, 2])
    def test_mindharom_felirathely_png_kimeneten_fut(
        self, qt_app, tmp_path, placement
    ):
        source = _white_jpeg(tmp_path / "kep.jpg")
        photos[:] = [_Photo(str(tmp_path), source.name)]
        controller = _controller(tmp_path)
        controller.setPrintOption("textSource", 2)
        controller.setPrintOption("textPlacement", placement)
        controller.setPrintOption("textColor", 0xFFFF0000)
        output = tmp_path / f"preview-{placement}.png"

        assert controller.renderPreviewPage(
            [0], "fit", "portrait", 1, 0, str(output)
        )
        image = QImage(str(output))
        assert not image.isNull()
        assert image.width() > 0 and image.height() > 0
        assert sum(
            1
            for y in range(image.height())
            for x in range(image.width())
            if image.pixel(x, y) & 0x00FF0000
        ) > 0


class TestPrintOptionsRenderedOutput:
    def test_a_szegely_es_a_felirat_tenyleg_megjelenik_a_png_n(
        self, qt_app, tmp_path
    ):
        source = _white_jpeg(tmp_path / "kep.jpg")
        photos[:] = [_Photo(str(tmp_path), source.name)]
        controller = _controller(tmp_path)
        controller.setPrintOption("textSource", 2)
        controller.setPrintOption("textPlacement", 1)
        controller.setPrintOption("textColor", 0xFFFF0000)
        controller.setPrintOption("border", True)
        controller.setPrintOption("borderSize", 1024)
        controller.setPrintOption("borderColor", 0xFF0000FF)
        output = tmp_path / "printoptions.png"

        assert controller.renderPreviewPage(
            [0], "fit", "portrait", 1, 0, str(output)
        )
        image = QImage(str(output)).convertToFormat(QImage.Format.Format_RGB32)
        piros = kek = 0
        for y in range(image.height()):
            for x in range(image.width()):
                rgb = image.pixel(x, y) & 0x00FFFFFF
                piros += rgb == 0xFF0000
                kek += rgb == 0x0000FF
        assert piros > 0, "a felirat színe nem került rá az előnézetre"
        assert kek > 0, "a szegély színe nem került rá az előnézetre"
