"""A nyomtatás Review listája minőségi sávok szerint rendez (#7249)."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QSettings

from picasapy.app.print_controller import PrintController


@dataclass
class _Photo:
    folder_path: str
    name: str
    width: int
    height: int


def test_review_lista_minosegi_csoportokban_bemeneti_sorrenddel(tmp_path):
    # 4×6 hüvelykes nyomatnál a méretek rendre 220, 90, 140, 160, 60, 110 DPI-t adnak.
    photos = [
        _Photo(str(tmp_path), "best-elso.jpg", 1320, 880),
        _Photo(str(tmp_path), "low-elso.jpg", 540, 360),
        _Photo(str(tmp_path), "good-elso.jpg", 840, 560),
        _Photo(str(tmp_path), "best-masodik.jpg", 960, 640),
        _Photo(str(tmp_path), "low-masodik.jpg", 360, 240),
        _Photo(str(tmp_path), "good-masodik.jpg", 660, 440),
    ]
    settings = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    controller = PrintController(photo_source=lambda: photos, settings=settings)

    review = controller.reviewPictures(list(range(len(photos))), "M4X6")

    assert [(row["name"], row["qualityCode"]) for row in review] == [
        ("low-elso.jpg", 0),
        ("low-masodik.jpg", 0),
        ("good-elso.jpg", 1),
        ("good-masodik.jpg", 1),
        ("best-elso.jpg", 2),
        ("best-masodik.jpg", 2),
    ]
