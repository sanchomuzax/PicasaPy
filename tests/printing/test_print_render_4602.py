"""A nyomtatás a rácson látott rasztert használja (#4602)."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import replace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import piexif
import pytest
from PIL import Image
from PySide6.QtCore import QSettings
from PySide6.QtGui import QGuiApplication, QImage

from picasapy.cvimage import dekodolj_forrast
from picasapy.index import PhotoRecord
from picasapy.printing.layout import (
    PageGeometry,
    PrintFitMode,
    PrintOrientation,
    compute_print_layout,
)
from support.raw_factory import ir_dng

try:
    from PySide6.QtPrintSupport import QPrinterInfo  # noqa: F401

    from picasapy.app.print_controller import PrintController
except ImportError:  # pragma: no cover - hiányzó QtPrintSupport esetén
    PrintController = None

pytestmark = pytest.mark.skipif(
    PrintController is None,
    reason="a PySide6.QtPrintSupport modul hiányzik ezen a gépen",
)


@pytest.fixture(scope="module")
def qt_app():
    return QGuiApplication.instance() or QGuiApplication([])


def _pattern_jpeg(path, *, orientation: int | None = None):
    """Félpiros/félkék, nagy kontrasztú minta EXIF-forgatás mérésére."""
    image = Image.new("RGB", (120, 80))
    image.paste((240, 20, 20), (0, 0, 60, 80))
    image.paste((20, 30, 240), (60, 0, 120, 80))
    image.save(path, "JPEG", quality=100, subsampling=0)
    if orientation is not None:
        piexif.insert(
            piexif.dump(
                {"0th": {piexif.ImageIFD.Orientation: orientation}}
            ),
            str(path),
        )
    return path


def _record(path, *, filters=None, rotate_steps=0):
    return PhotoRecord(
        id=1,
        folder_path=str(path.parent),
        name=path.name,
        kind="image",
        size=path.stat().st_size,
        mtime_ns=path.stat().st_mtime_ns,
        star=False,
        caption=None,
        keywords=None,
        rotate_steps=rotate_steps,
        filters=filters,
        taken_at=None,
        orientation=0,
        width=120,
        height=80,
    )


def _controller(tmp_path, records):
    settings = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    controller = PrintController(
        photo_source=lambda: records,
        settings=settings,
    )
    # A FullPage mindkét területi méretkészletben szerepel.
    controller.setPrintSize("TELJES_OLDAL")
    return controller


def _print_outputs(controller, tmp_path, *, name):
    preview_path = tmp_path / f"{name}-preview.png"
    pdf_path = tmp_path / f"{name}.pdf"
    assert controller.renderPreviewPage(
        [0], "fit", "portrait", 1, 0, str(preview_path)
    )
    assert controller.renderPrintPreviewPdf(
        [0], "fit", "portrait", str(pdf_path)
    )
    preview = QImage(str(preview_path))
    assert not preview.isNull()
    assert pdf_path.is_file() and pdf_path.stat().st_size > 0

    raster = _rasterize_pdf(pdf_path, tmp_path, name)
    return controller, preview, raster


def _rasterize_pdf(pdf_path, tmp_path, name):
    """A PDF-oldal képpé alakítása, ha a Poppler jelen van a gépen."""
    pdftoppm = shutil.which("pdftoppm")
    if pdftoppm is None:
        return None
    prefix = tmp_path / f"{name}-pdf-raster"
    subprocess.run(
        [
            pdftoppm,
            "-f",
            "1",
            "-l",
            "1",
            "-singlefile",
            "-r",
            "96",
            "-png",
            str(pdf_path),
            str(prefix),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    raster = QImage(str(prefix.with_suffix(".png")))
    assert not raster.isNull()
    return raster


def _sample_points(controller, *, image_size):
    """A kép belsejéből vesz mintát, a laptól független aránykoordinátával."""
    portrait = controller._preview_page_geometry("", landscape=False)
    landscape = controller._preview_page_geometry("", landscape=True)
    size = controller._aktiv_meret()
    _landscape_page, page, pages = controller._grid_for_job(
        portrait,
        landscape,
        size.szeles_huvelyk * 96.0,
        size.magas_huvelyk * 96.0,
        1,
        PrintOrientation.PORTRAIT,
    )
    cell = pages[0].cells[0]
    placement = compute_print_layout(
        PageGeometry(width=cell.width, height=cell.height, margin=0.0),
        *image_size,
        PrintFitMode.FIT,
    )
    left = cell.x + placement.x
    top = cell.y + placement.y
    width, height = placement.width, placement.height
    return tuple(
        (
            (left + width * 0.5) / page.width,
            (top + height * fraction) / page.height,
        )
        for fraction in (0.25, 0.75)
    )


def _pixel(image: QImage, normalized_point):
    x_fraction, y_fraction = normalized_point
    x = min(image.width() - 1, round(x_fraction * image.width()))
    y = min(image.height() - 1, round(y_fraction * image.height()))
    return image.pixelColor(x, y)


def _assert_renders_match(preview, pdf_raster, points, assertion):
    assertion([_pixel(preview, point) for point in points])
    if pdf_raster is not None:
        assertion([_pixel(pdf_raster, point) for point in points])


def test_exif6_foto_a_pdfen_is_fuggolegesen_jelenik_meg(qt_app, tmp_path):
    source = _pattern_jpeg(tmp_path / "exif6.jpg", orientation=6)
    controller = _controller(tmp_path, [_record(source)])
    _, preview, pdf_raster = _print_outputs(
        controller, tmp_path, name="exif6"
    )
    points = _sample_points(controller, image_size=(80, 120))

    def assert_exif_orientation(colors):
        felso, also = colors
        assert felso.red() > felso.blue() * 2, (
            "az EXIF-6 felső sávja piros kell legyen a 90°-os tájolás után"
        )
        assert also.blue() > also.red() * 2, (
            "az EXIF-6 alsó sávja kék kell legyen a 90°-os tájolás után"
        )

    _assert_renders_match(preview, pdf_raster, points, assert_exif_orientation)


def test_szuro_es_ini_forgatas_a_pdfbe_egetodik(qt_app, tmp_path):
    source = _pattern_jpeg(tmp_path / "szerkesztett.jpg")
    controller = _controller(
        tmp_path,
        [_record(source, filters="bw=1;", rotate_steps=1)],
    )
    _, preview, pdf_raster = _print_outputs(
        controller, tmp_path, name="szerkesztett"
    )
    points = _sample_points(controller, image_size=(80, 120))

    def assert_filtered_and_rotated(colors):
        felso, also = colors
        for color in colors:
            channels = (color.red(), color.green(), color.blue())
            assert max(channels) - min(channels) <= 3, (
                "a bw szűrőnek szürke képpontot kell nyomtatnia"
            )
        assert felso.value() > also.value() + 25, (
            "a tárolt negyedfordulat után a piros fél kerül felülre"
        )

    _assert_renders_match(preview, pdf_raster, points, assert_filtered_and_rotated)


def test_raw_foto_pdfbe_nyomtathato(qt_app, tmp_path):
    source = ir_dng(tmp_path / "nyers.dng")
    controller = _controller(tmp_path, [_record(source)])

    assert controller.printPageCount([0], 1) == 1, (
        "a nyers képnek is nyomtatható oldalt kell kapnia"
    )
    _, preview, pdf_raster = _print_outputs(controller, tmp_path, name="nyers")
    points = _sample_points(controller, image_size=(64, 48))
    decoded = dekodolj_forrast(source)
    assert decoded is not None
    magassag, szelesseg = decoded.shape[:2]
    vart = [
        tuple(int(channel) for channel in decoded[round(magassag * fraction), szelesseg // 2][::-1])
        for fraction in (0.25, 0.75)
    ]

    def assert_raw_pixels(colors):
        for color, expected in zip(colors, vart, strict=True):
            actual = (color.red(), color.green(), color.blue())
            assert max(abs(left - right) for left, right in zip(actual, expected, strict=True)) <= 8, (
                "a RAW-nyomat képpontja térjen el legfeljebb 8 szinttel a "
                "közös dekóder ugyanott mért kimenetétől"
            )

    _assert_renders_match(preview, pdf_raster, points, assert_raw_pixels)


def test_video_records_are_skipped_before_image_decoding(tmp_path, qt_app, monkeypatch):
    """A videót a nyomtatásnak a képfájl beolvasása előtt ki kell zárnia."""
    import picasapy.app.print_controller as print_controller_module

    video_path = tmp_path / "felvetel.mp4"
    video_path.write_bytes(b"video")
    record = replace(_record(video_path), kind="video")
    controller = _controller(tmp_path, [record])
    calls = []

    def track_decoder(path):
        calls.append(("decode", path))
        raise OSError("videó nem képfájl")

    def track_renderer(*args, **kwargs):
        calls.append(("render", args[0]))
        raise OSError("videó nem képfájl")

    monkeypatch.setattr(print_controller_module, "_decode_image", track_decoder)
    monkeypatch.setattr(
        print_controller_module, "render_photo_pixels", track_renderer
    )

    assert controller.printPageCount([0], 1) == 0
    assert controller._render_photo(record).isNull()
    assert calls == []
