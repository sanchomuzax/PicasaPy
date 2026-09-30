"""#4013: ugyanaz a crop-szabály érvényesül a teljes képútvonalon."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from picasapy.app.edit_controller import EditController
from picasapy.app.edit_preview import EditPreviewProvider
from picasapy.app.save_controller import _render_for_save
from picasapy.app.thumbnail_provider import ThumbnailProvider
from picasapy.export import ExportItem, ExportSettings, export_photos
from picasapy.index import open_index, photos_in_folder, sync_tree
from picasapy.ini.filters import parse_filters
from picasapy.ini.rect64 import Rect64, encode_rect64
from picasapy.thumbs import ThumbnailCache

# rontás-kontroll: picasapy.ini.rect64._SCALE = 131072 → 1 failed


_OLD_CROP = encode_rect64(Rect64(0.1, 0.0, 0.9, 1.0))
_CURRENT_CROP = encode_rect64(Rect64(0.25, 0.0, 0.75, 1.0))
_BORDER = "Border=1,3,1,0,00000000,00ffffff,0;"


def _make_photo(path: Path) -> Path:
    y, x = np.indices((60, 80))
    rgb = np.stack(
        ((x * 3 + y) % 256, (y * 5 + x) % 256, (x + y * 2) % 256), axis=2
    ).astype(np.uint8)
    Image.fromarray(rgb).save(path)
    return path


def _write_ini(photo: Path, filters: str, crop: str | None = None) -> None:
    lines = [f"[{photo.name}]", f"filters={filters}"]
    if crop is not None:
        lines.append(f"crop={crop}")
    (photo.parent / ".picasa.ini").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _qimage_rgb(image) -> np.ndarray:
    from PySide6.QtCore import QBuffer, QIODevice

    buffer = QBuffer()
    assert buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    assert image.save(buffer, "PNG")
    with Image.open(BytesIO(bytes(buffer.data()))) as decoded:
        return np.asarray(decoded.convert("RGB"), dtype=np.uint8)


def _export_rgb(path: Path) -> np.ndarray:
    payload = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(payload, cv2.IMREAD_COLOR)
    assert image is not None
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def _record(folder: Path, index_path: Path):
    with open_index(index_path) as conn:
        sync_tree(conn, folder)
        return photos_in_folder(conn, folder)[0]


def _assert_routes_match(
    photo: Path,
    filters: str,
    expected_shape: tuple[int, int, int],
    target_name: str,
    tmp_path: Path,
    viewer: ThumbnailProvider,
    preview: EditPreviewProvider,
) -> None:
    record = _record(photo.parent, tmp_path / "index.db")
    viewer.register_photos((record,))
    thumb = viewer.requestImage(str(record.id), None, None)

    preview.register("editor", photo, parse_filters(filters))
    preview_image = preview.requestImage("editor", None, None)

    saved_bgr = _render_for_save(photo, 0, filters)
    saved_rgb = cv2.cvtColor(saved_bgr, cv2.COLOR_BGR2RGB)

    target = tmp_path / target_name
    report = export_photos(
        [ExportItem(photo, filters=filters)],
        target,
        ExportSettings(jpeg_quality=100),
    )
    assert report.failed == ()
    exported_rgb = _export_rgb(report.exported[0])

    images = {
        "bélyegkép": _qimage_rgb(thumb),
        "szerkesztő előnézete": _qimage_rgb(preview_image),
        "mentés": saved_rgb,
        "export": exported_rgb,
    }
    assert expected_shape == next(iter(images.values())).shape
    assert {name: image.shape for name, image in images.items()} == {
        name: expected_shape for name in images
    }
    reference = images["mentés"].astype(np.int16)
    for name, image in images.items():
        mae = float(np.abs(image.astype(np.int16) - reference).mean())
        assert mae <= 6.0, f"{name} eltérése a mentéstől: MAE={mae:.3f}"


def test_nezo_thumb_elonezet_mentes_es_export_azonos_cropot_hasznal(qt_app, tmp_path):
    viewer = ThumbnailProvider(
        ThumbnailCache(tmp_path / "thumbs", size=128), max_threads=1
    )
    preview = EditPreviewProvider()
    photo = _make_photo(tmp_path / "kep.png")

    # (a) A crop64 csak előzmény: a hiányzó crop= miatt egyik út sem vághat.
    filters = f"crop64=1,{_OLD_CROP};{_BORDER}"
    _write_ini(photo, filters)
    _assert_routes_match(photo, filters, (68, 88, 3), "export-missing", tmp_path, viewer, preview)

    # (b) A külön crop= a meglévő crop64 helyén válik hatályossá.
    _write_ini(photo, filters, f"rect64({_CURRENT_CROP})")
    _assert_routes_match(photo, filters, (68, 48, 3), "export-current", tmp_path, viewer, preview)

    # (c) Az EditController saját vágása mindkét kulcsot írja, és ugyanúgy
    # jelenik meg a nézőben, a bélyegképen, a mentésben és az exportban.
    _write_ini(photo, _BORDER)
    controller = EditController(preview)
    controller.beginEdit("own-crop", str(photo))
    controller.applyCrop(0.25, 0.0, 0.5, 1.0)
    own_filters = controller._session.to_value()
    assert f"crop=rect64({_CURRENT_CROP})" in (photo.parent / ".picasa.ini").read_text(
        encoding="utf-8"
    )
    controller.endEdit()
    _assert_routes_match(photo, own_filters, (60, 40, 3), "export-own", tmp_path, viewer, preview)


def _controller_preview_size(controller, preview, qt_app) -> tuple[int, int]:
    assert controller.waitForBackgroundWorkers(10.0)
    qt_app.processEvents()
    image = preview.requestImage(controller._kulcs, None, None)
    return image.width(), image.height()


def test_memorias_sajat_vagas_a_munkamenet_cropjat_hasznalja(qt_app, tmp_path):
    photo = _make_photo(tmp_path / "memorias-vagas.png")
    _write_ini(photo, "")
    preview = EditPreviewProvider()
    controller = EditController(preview)

    controller.beginEditInMemory("memory-crop", str(photo))
    controller.applyCrop(0.25, 0.0, 0.5, 1.0)

    assert _controller_preview_size(controller, preview, qt_app) == (40, 60)
    assert "crop=" not in (photo.parent / ".picasa.ini").read_text(encoding="utf-8")


def test_crop64_előzmény_nem_ébred_fel_effekttől_es_sajat_vagas_aktiválja(
    qt_app, tmp_path
):
    photo = _make_photo(tmp_path / "crop-előzmény.png")
    legacy = f"crop64=1,{_OLD_CROP};"
    _write_ini(photo, legacy)
    preview = EditPreviewProvider()
    controller = EditController(preview)

    controller.beginEdit("history-crop", str(photo))
    assert controller.hasCrop is False
    assert controller.cropSelection is None
    controller.applyEffect("bw")

    ini_text = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
    assert "crop=" not in ini_text
    assert _controller_preview_size(controller, preview, qt_app) == (80, 60)

    controller.applyCrop(0.25, 0.0, 0.5, 1.0)
    ini_text = (photo.parent / ".picasa.ini").read_text(encoding="utf-8")
    assert "crop64=1," in ini_text
    assert f"crop=rect64({_CURRENT_CROP})" in ini_text
    assert _controller_preview_size(controller, preview, qt_app) == (40, 60)


def test_memorias_crop64_előzmény_effekt_es_sajat_vagas_sorrendje(qt_app, tmp_path):
    photo = _make_photo(tmp_path / "memorias-előzmény.png")
    _write_ini(photo, f"crop64=1,{_OLD_CROP};")
    preview = EditPreviewProvider()
    controller = EditController(preview)

    controller.beginEditInMemory("memory-history-crop", str(photo))
    assert controller.hasCrop is False
    assert controller.cropSelection is None
    controller.applyEffect("bw")
    assert _controller_preview_size(controller, preview, qt_app) == (80, 60)
    assert "crop=" not in (photo.parent / ".picasa.ini").read_text(encoding="utf-8")

    controller.applyCrop(0.25, 0.0, 0.5, 1.0)
    assert _controller_preview_size(controller, preview, qt_app) == (40, 60)
    assert "crop=" not in (photo.parent / ".picasa.ini").read_text(encoding="utf-8")


def test_arva_crop_kulcs_lanc_nelkul_nem_aktiv_vagas(qt_app, tmp_path):
    """Az ini-ben van `crop=`, de a láncban nincs `crop64`: a render nem vág, tehát
    a felület sem mutathat aktív vágást, és a felkínált téglalap alkalmazható."""
    photo = _make_photo(tmp_path / "arva-crop.png")
    _write_ini(photo, "bw=1;", crop=f"rect64({_OLD_CROP})")
    preview = EditPreviewProvider()
    controller = EditController(preview)

    controller.beginEdit("arva-crop", str(photo))
    assert controller.hasCrop is False
    assert controller.cropSelection is None
    assert _controller_preview_size(controller, preview, qt_app) == (80, 60)

    controller.applyCrop(0.25, 0.0, 0.5, 1.0)
    assert _controller_preview_size(controller, preview, qt_app) == (40, 60)
