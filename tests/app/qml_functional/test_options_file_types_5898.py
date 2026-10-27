"""#5898 — a File Types fül feliratai, alapértékei és a PNG mentése."""

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QPoint
from PySide6.QtGui import QPainter
from conftest import _build_qml_app
from tests.app.qml_functional.test_menu_talca_egyeb_valodi_5135_b import (
    _elokeszit,
    _gyerek,
    _klikk_ablakban,
    _vizualis_bejaras,
    _varj,
    _zar,
)
from support.jpeg_factory import make_minta_jpeg
from tests.app.qml_functional.test_parbeszedek_valodi_5150_b import (
    _beallitasok_megnyit,
    _fulre_kattint,
)

_KEPEK = ("a_elso.jpg", "b_masodik.jpg")


def _keszits_fotokat(lib: Path) -> None:
    mappa = lib / "fotok"
    mappa.mkdir()
    for seed, filename in enumerate(_KEPEK, start=1):
        make_minta_jpeg(mappa / filename, size=(320, 240), seed=seed)


@pytest.fixture
def file_types_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_fotokat,
        valodi_belyegkep=True,
    )


@pytest.mark.parametrize("height_offset", [-5, 0, 5])
def test_tiszta_profil_feliratai_alapertekei_es_png_mentese(
    file_types_app, qt_app, tmp_path, height_offset
):
    window, controller, _engine = file_types_app
    _elokeszit(window, qt_app, controller)
    window.setProperty("selectedIndexes", [0, 1])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()

    def thumb_image():
        for item in _vizualis_bejaras(window.contentItem()):
            source = item.property("source")
            source = source.toString() if hasattr(source, "toString") else str(source)
            if (
                item.objectName() == "thumbImage"
                and item.isVisible()
                and source.startswith("image://thumbs/")
            ):
                return item
        return None

    assert _varj(qt_app, lambda: thumb_image() is not None), (
        "a képrácsban nem épült fel bélyegkép"
    )

    options = _beallitasok_megnyit(window, qt_app)
    options.setHeight(options.height() + height_offset)
    _fulre_kattint(qt_app, options, "optionsTabFileTypes", 2)
    assert _gyerek(options, "optionsFileTypesHeading").isVisible()

    expected = {
        "optionsFileTypeBmpCheck": (".BMP", True),
        # #6060: alapból minden típus bekapcsolt, frissítés ne rejtsen el képet.
        "optionsFileTypeGifCheck": (".GIF", True),
        "optionsFileTypePngCheck": (".PNG", True),
        "optionsFileTypeTgaCheck": (".TGA", True),
        "optionsFileTypeTiffCheck": (".TIF, .TIFF", True),
        "optionsFileTypeWebpCheck": (".WEBP", True),
        "optionsFileTypePsdCheck": (".PSD (Photoshop)", True),
        "optionsFileTypeRawCheck": ("RAW formats", True),
        "optionsFileTypeMoviesCheck": (
            "Movies (.AVI, .MPG, .ASF, .WMV)",
            True,
        ),
        # A QuickTime-sor az eredetiben telepítésfüggő; nálunk a .MOV
        # lejátszás külön telepítés nélkül működik, ezért bekapcsolt.
        "optionsFileTypeQuickTimeCheck": ("Quicktime Movies (.MOV)", True),
    }
    for object_name, (label, checked) in expected.items():
        check = _gyerek(options, object_name)
        assert check.property("text") == label
        assert check.property("checked") is checked

    quicktime = _gyerek(options, "optionsFileTypeQuickTimeCheck")
    assert quicktime.property("enabled") is True

    if height_offset == 0:
        qt_app.processEvents()
        screenshot = window.grabWindow()
        dialog_image = options.grabWindow()
        assert not screenshot.isNull(), "nem készült képernyőkép"
        assert not dialog_image.isNull(), "nem készült kép a File Types párbeszédről"
        painter = QPainter(screenshot)
        painter.drawImage(
            QPoint(options.x() - window.x(), options.y() - window.y()),
            dialog_image,
        )
        painter.end()
        kepmappa = os.environ.get("PICASAPY_KIADASKEP_MAPPA")
        if kepmappa:
            assert screenshot.save(str(Path(kepmappa) / "5898-options-file-types.png"))

    png = _gyerek(options, "optionsFileTypePngCheck")
    _klikk_ablakban(qt_app, options, png)
    assert png.property("checked") is False

    # #5906: a File Types értéke az OK-ra kerül QSettings-be; utána ugyanaz
    # a párbeszéd újranyitva a tárolt PNG-értéket olvassa vissza.
    ok_button = _gyerek(options, "optionsOkButton")
    _klikk_ablakban(qt_app, options, ok_button)
    assert _varj(qt_app, lambda: options.property("visible") is False)
    assert _varj(qt_app, lambda: not controller.fileTypeEnabled("png"))
    reopened = _beallitasok_megnyit(window, qt_app)
    _fulre_kattint(qt_app, reopened, "optionsTabFileTypes", 2)
    assert _gyerek(reopened, "optionsFileTypePngCheck").property("checked") is False
    assert controller.fileTypeEnabled("png") is False

    _zar(qt_app, reopened)
