"""#7415: a kiegyenesített kijelölést forrásképi crop64-ként kell tárolni."""

from __future__ import annotations

import re

import pytest

from picasapy.ini.rect64 import decode_rect64
from support.jpeg_factory import make_jpeg


@pytest.fixture
def controller_and_photo(qt_app, tmp_path):
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider

    provider = EditPreviewProvider()
    controller = EditController(provider)
    photo = make_jpeg(tmp_path / "IMG_0001.jpg", size=(1024, 256))
    return controller, provider, photo


def _crop_pixels(controller, width: int = 1024, height: int = 256):
    crop_op = next(op for op in reversed(controller._session.ops) if op.matches("crop64"))
    rect = decode_rect64(crop_op.params[1])
    return tuple(
        round(value * dimension)
        for value, dimension in (
            (rect.left, width),
            (rect.top, height),
            (rect.right, width),
            (rect.bottom, height),
        )
    )


def _apply_tilt_crop(controller, provider, photo, box):
    ini = photo.parent / ".picasa.ini"
    ini.write_text(
        "[IMG_0001.jpg]\nfilters=tilt=1,0.391249,0.000000;\n",
        encoding="utf-8",
    )
    controller.beginEdit("1", str(photo))
    assert controller.waitForBackgroundWorkers(10.0)
    width, height = provider.source_image("1", photo).shape[1::-1]
    x, y, crop_width, crop_height = box
    controller.applyCrop(x / width, y / height, crop_width / width, crop_height / height)
    saved_ini = ini.read_text(encoding="utf-8")
    assert re.search(r"crop64=1,[0-9a-f]{16};", saved_ini)


@pytest.mark.parametrize(
    ("box", "expected"),
    [
        # A: a 415×187-es kijelölt doboz; a kerekített UI-koordináták
        # a Picasa 415×187-es Manual feliratát adják.
        ((220.0, 36.5, 414.5, 186.5), (262, 41, 633, 208)),
        # C: a harmadik minta, a vízszintes középre igazítás ellenőrzésével.
        ((427.0, 16.5, 414.5, 227.8), (425, 38, 786, 237)),
    ],
)
def test_kiegyenesitett_crop_a_meres_szerint_vetul_vissza(
    controller_and_photo, box, expected
):
    controller, provider, photo = controller_and_photo
    _apply_tilt_crop(controller, provider, photo, box)

    actual = _crop_pixels(controller)
    assert all(abs(got - want) <= 1 for got, want in zip(actual, expected, strict=True))


def test_kiegyenesitett_crop_b_meresi_merete(controller_and_photo):
    controller, provider, photo = controller_and_photo
    _apply_tilt_crop(controller, provider, photo, (75.0, 56.0, 311.3, 103.5))

    left, top, right, bottom = _crop_pixels(controller)
    assert (right - left, bottom - top) == (293, 98)


def test_tilt_nelkul_a_crop_tovabbra_is_a_kijelolt_doboz(controller_and_photo):
    controller, _provider, photo = controller_and_photo
    controller.beginEdit("1", str(photo))
    controller.applyCrop(220 / 1024, 37 / 256, 415 / 1024, 187 / 256)

    assert _crop_pixels(controller) == (220, 37, 635, 224)
