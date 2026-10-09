"""A háttérkép az EXIF-helyes, szerkesztett képből készül (#4604)."""

from __future__ import annotations

import numpy as np
from PIL import Image
from PySide6.QtCore import QSettings

from picasapy.app import collage_prefs, wallpaper
from picasapy.export.exporter import render_photo_pixels
from picasapy.index import open_index, sync_tree
from picasapy.ini.filters import parse_filters_prefix
from picasapy.lazy_cv2 import cv2


def test_hatterkep_az_exif_helyes_szerkesztett_keppontokat_tartalmazza(
    qt_app, tmp_path, monkeypatch
) -> None:
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.thumbs import ThumbnailCache

    foto_mappa = tmp_path / "fotok"
    foto_mappa.mkdir()
    source = foto_mappa / "exif-szerkesztett.jpg"
    y, x = np.indices((80, 128), dtype=np.uint16)
    rgb = np.empty((80, 128, 3), dtype=np.uint8)
    rgb[..., 0] = x * 2
    rgb[..., 1] = y * 3
    rgb[..., 2] = (x * 5 + y * 7) % 256
    exif = Image.Exif()
    exif[274] = 6  # EXIF: 90° clockwise
    Image.fromarray(rgb, "RGB").save(
        source, format="JPEG", quality=100, subsampling=0, exif=exif
    )
    (foto_mappa / ".picasa.ini").write_text(
        "[exif-szerkesztett.jpg]\n"
        "filters=bw=1;\n"
        "rotate=rotate(2)\n"
        "flipped=flipped(2)\n",
        encoding="utf-8",
    )
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, foto_mappa)

    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    kollazsok = tmp_path / "picasa" / "Kollázsok"
    settings.setValue(collage_prefs.OUTPUT_DIR_KEY, str(kollazsok))
    controller = AppController(
        tmp_path / "index.db",
        (str(foto_mappa),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    controller.selectFolder(str(foto_mappa))
    monkeypatch.setattr(wallpaper, "set_desktop_background", lambda _bmp: "teszt")
    try:
        assert controller.setPhotoAsDesktopBackground(0) is True

        bmp_path = next((kollazsok.parent).glob("*/picasabackground.bmp"))
        actual = cv2.imdecode(
            np.frombuffer(bmp_path.read_bytes(), dtype=np.uint8), cv2.IMREAD_COLOR
        )
        expected = render_photo_pixels(
            source,
            parse_filters_prefix("bw=1;"),
            rotate_steps=2,
            flip_flags=2,
        )

        assert expected.shape[:2] == (128, 80)
        np.testing.assert_array_equal(actual, expected)
    finally:
        controller.shutdown()
