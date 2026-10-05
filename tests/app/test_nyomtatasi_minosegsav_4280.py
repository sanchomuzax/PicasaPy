"""A nyomtatási minőségsávok a két bináris küszöb összegéből jönnek (#4280)."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings

from picasapy.app.print_controller import PrintController
from picasapy.printing.dpi import nyomtatasi_minoseg_kod
from support.jpeg_factory import make_jpeg


@pytest.mark.parametrize(
    ("dpi", "vart"),
    [(99, 0), (100, 1), (149, 1), (150, 2)],
)
def test_a_kuszobok_egyenloseggel_besorolasi_kodot_adnak(dpi, vart):
    assert nyomtatasi_minoseg_kod(dpi) == vart


def test_a_ket_kuszob_kulon_is_felulirhato():
    assert nyomtatasi_minoseg_kod(
        180, best_kuszob=180, good_kuszob=120
    ) == 2
    assert nyomtatasi_minoseg_kod(
        120, best_kuszob=180, good_kuszob=120
    ) == 1
    assert nyomtatasi_minoseg_kod(
        119, best_kuszob=180, good_kuszob=120
    ) == 0


class _Photo:
    def __init__(self, folder: str, name: str, width: int, height: int):
        self.folder_path = folder
        self.name = name
        self.width = width
        self.height = height


def test_a_ellenorzo_lista_minden_kephez_kodot_ad_es_a_beallitast_hasznalja(
    tmp_path,
):
    meretek = {
        "best.jpg": (1080, 720),  # 180 DPI 6x4 hüvelyken
        "good.jpg": (900, 600),  # 150 DPI
        "bad.jpg": (660, 440),  # 110 DPI
    }
    for name, size in meretek.items():
        make_jpeg(tmp_path / name, size=size)
    photos = [
        _Photo(str(tmp_path), name, *size)
        for name, size in meretek.items()
    ]
    settings = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    settings.setValue("printing/dpiWarning", 175)
    settings.setValue("printing/dpiSevere", 120)
    controller = PrintController(
        photo_source=lambda: photos, settings=settings
    )

    quality = controller.printQuality([0, 1, 2], "M4X6")
    rows = controller.reviewPictures([0, 1, 2], "M4X6")

    assert quality["bestThreshold"] == 175
    assert quality["goodThreshold"] == 120
    assert [(row["name"], row["qualityCode"]) for row in rows] == [
        ("bad.jpg", 0),
        ("good.jpg", 1),
        ("best.jpg", 2),
    ]
