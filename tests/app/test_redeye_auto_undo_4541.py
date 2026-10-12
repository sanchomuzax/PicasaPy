"""#4541: az automatikus szemjavítások kerete, kattintásos visszavonása és Resetje."""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.app.edit_controller import EditController
from picasapy.app.edit_preview import EditPreviewProvider
from picasapy.edit.session import EditSession
from picasapy.ini.filters import FilterOp
from picasapy.ini.redeye import parse_redeye_eye_circles, parse_redeye_regions
from picasapy.ini.rect64 import Rect64, encode_rect64
from support.jpeg_factory import make_jpeg

_AUTO_EYES = ((0.25, 0.4, 0.1), (0.7, 0.6, 0.05))
_IDENTITY = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0))


@pytest.fixture
def redeye_controller(qt_app, tmp_path, monkeypatch):
    provider = EditPreviewProvider()
    controller = EditController(provider)
    photo = make_jpeg(tmp_path / "auto-redeye.jpg", size=(400, 200))
    controller.beginEdit("auto-redeye", str(photo))
    monkeypatch.setattr(
        provider,
        "redeye_auto_result_with_size",
        lambda *_args: (2, _AUTO_EYES, (400, 200), (400, 200), _IDENTITY),
    )
    controller.enterRedeyeTool()
    return controller


def _pending_eye_circles(controller: EditController):
    session = controller._session_with_redeye_pending()
    operation = next(operation for operation in session.ops if operation.name == "redeye")
    return parse_redeye_eye_circles(operation, 400, 200)


def test_automatikus_szemek_negyzete_kattintassal_visszavonhato(redeye_controller):
    assert redeye_controller.redeyeRegionCount == 2
    assert redeye_controller.redeyeRegions == [
        {"x": pytest.approx(0.2), "y": pytest.approx(0.3),
         "w": pytest.approx(0.1), "h": pytest.approx(0.2)},
        {"x": pytest.approx(0.675), "y": pytest.approx(0.55),
         "w": pytest.approx(0.05), "h": pytest.approx(0.1)},
    ]

    assert redeye_controller.removeRedeyeRegionAt(0.25, 0.4) is True
    assert redeye_controller.redeyeRegionCount == 1
    assert redeye_controller.redeyeRegions[0]["x"] == pytest.approx(0.675)
    assert len(_pending_eye_circles(redeye_controller)) == 1
    assert redeye_controller.canReapplyRedeyeAuto is True


def test_automatikus_keret_a_felismeresi_kep_meretet_hasznalja(
    qt_app, tmp_path, monkeypatch
):
    provider = EditPreviewProvider()
    controller = EditController(provider)
    photo = make_jpeg(tmp_path / "cropped-auto-redeye.jpg", size=(400, 200))
    controller.beginEdit("cropped-auto-redeye", str(photo))
    monkeypatch.setattr(
        provider,
        "redeye_auto_result_with_size",
        lambda *_args: (
            1,
            ((0.5, 0.5, 0.1),),
            (100, 200),
            (100, 200),
            _IDENTITY,
        ),
    )

    controller.enterRedeyeTool()

    rectangle = controller.redeyeRegions[0]
    assert rectangle["w"] == pytest.approx(0.2)
    assert rectangle["h"] == pytest.approx(0.1)


def test_automatikus_keret_a_voros_szem_utani_vagashoz_igazodik(
    qt_app, tmp_path, monkeypatch
):
    from picasapy.app import edit_preview
    from picasapy.faces.redeye import EyeCircle

    provider = EditPreviewProvider()
    controller = EditController(provider)
    photo = make_jpeg(tmp_path / "post-redeye-crop.jpg", size=(400, 200))
    controller.beginEdit("post-redeye-crop", str(photo))
    controller._session = EditSession().set_redeye_regions(()).append_crop(
        Rect64(left=0.25, top=0.25, right=0.75, bottom=0.75)
    )
    monkeypatch.setattr(
        edit_preview,
        "detect_eye_circles",
        lambda _image: (EyeCircle(120, 100, 10),),
    )

    controller.enterRedeyeTool()

    rectangle = controller.redeyeRegions[0]
    assert rectangle["x"] == pytest.approx(0.05)
    assert rectangle["y"] == pytest.approx(0.4)
    assert rectangle["w"] == pytest.approx(0.1)
    assert rectangle["h"] == pytest.approx(0.2)
    assert controller.removeRedeyeRegionAt(0.1, 0.5) is True
    assert controller.redeyeRegionCount == 0


def test_detektalas_a_crop_ini_altal_normalizalt_elonezetet_hasznalja(
    monkeypatch, tmp_path
):
    from picasapy.app import edit_preview
    from picasapy.faces.redeye import EyeCircle

    provider = EditPreviewProvider()
    image = np.zeros((200, 400, 3), dtype=np.uint8)
    monkeypatch.setattr(provider, "_resolve_source", lambda *_args, **_kwargs: image)
    monkeypatch.setattr(
        provider._crop_reader,
        "read",
        lambda *_args: (encode_rect64(Rect64(0.25, 0.0, 0.75, 1.0)), True),
    )
    seen_sizes = []
    def detect(rendered):
        seen_sizes.append((rendered.shape[1], rendered.shape[0]))
        return (EyeCircle(50, 50, 10),)

    monkeypatch.setattr(edit_preview, "detect_eye_circles", detect)
    monkeypatch.setattr(edit_preview, "count_redeye_spots", lambda *_args, **_kwargs: 1)
    old_crop = FilterOp(
        "crop64", ("1", encode_rect64(Rect64(0.1, 0.0, 0.9, 1.0)))
    )

    result = provider.redeye_auto_result_with_size(
        "crop-normalized", tmp_path / "photo.jpg", (old_crop,)
    )

    assert seen_sizes == [(200, 200)]
    assert result[2] == (200, 200)
    assert result[1] is not None
    assert result[1][0] == pytest.approx((0.25, 0.25, 0.05))


def test_auto_geometria_nem_futtatja_ujra_az_utotag_effektjeit(
    monkeypatch, tmp_path
):
    from picasapy.app import edit_preview
    from picasapy.faces.redeye import EyeCircle
    from picasapy.render.op_geometry import LancHelyzet

    provider = EditPreviewProvider()
    image = np.zeros((200, 400, 3), dtype=np.uint8)
    monkeypatch.setattr(provider, "_resolve_source", lambda *_args, **_kwargs: image)
    monkeypatch.setattr(
        provider,
        "_render_cached_jelentes",
        lambda _key, source, _ops: (
            source,
            None,
            LancHelyzet.kezdo(source.shape[1], source.shape[0]),
        ),
    )
    monkeypatch.setattr(
        edit_preview,
        "detect_eye_circles",
        lambda _image: (EyeCircle(120, 80, 10),),
    )
    monkeypatch.setattr(edit_preview, "count_redeye_spots", lambda *_args, **_kwargs: 1)

    def unexpected_render(*_args, **_kwargs):
        raise AssertionError("A vetítéshez nem futhat újra a teljes utótag-render.")

    monkeypatch.setattr(edit_preview, "apply_filters", unexpected_render)
    crop_value = encode_rect64(Rect64(0.25, 0.25, 0.75, 0.75))
    monkeypatch.setattr(
        provider._crop_reader,
        "read",
        lambda *_args: (crop_value, True),
    )
    post_crop = FilterOp("crop64", ("1", crop_value))
    slow_effect = FilterOp("unsharp", ("1", "0.5", "0.5"))

    result = provider.redeye_auto_result_with_size(
        "geometry-only", tmp_path / "photo.jpg", (), (post_crop, slow_effect)
    )

    assert result[3] == (200, 100)
    assert result[4] == ((1.0, 0.0, -100.0), (0.0, 1.0, -50.0))


def test_kezzel_huzott_regio_a_voros_szem_reteg_kepkoordinatajat_tarolja(
    qt_app, tmp_path, monkeypatch
):
    provider = EditPreviewProvider()
    controller = EditController(provider)
    photo = make_jpeg(tmp_path / "manual-after-crop.jpg", size=(400, 200))
    controller.beginEdit("manual-after-crop", str(photo))
    crop = Rect64(0.25, 0.25, 0.75, 0.75)
    controller._session = EditSession().set_redeye_regions(()).append_crop(crop)
    monkeypatch.setattr(
        provider,
        "redeye_auto_result_with_size",
        lambda *_args: (0, (), (400, 200), (200, 100), ((1.0, 0.0, -100.0), (0.0, 1.0, -50.0))),
    )

    controller.enterRedeyeTool()
    controller.addRedeyeRegion(0.1, 0.2, 0.1, 0.2)

    operation = next(op for op in controller._session_with_redeye_pending().ops if op.name == "redeye")
    region = parse_redeye_regions(operation)[0]
    assert region.left == pytest.approx(0.3, abs=1e-5)
    assert region.top == pytest.approx(0.35, abs=1e-5)
    assert region.right == pytest.approx(0.35, abs=1e-5)
    assert region.bottom == pytest.approx(0.45, abs=1e-5)
    overlay_region = controller.redeyeRegions[0]
    assert overlay_region["x"] == pytest.approx(0.1)
    assert overlay_region["y"] == pytest.approx(0.2)
    assert overlay_region["w"] == pytest.approx(0.1)
    assert overlay_region["h"] == pytest.approx(0.2)


def test_reset_az_automatikus_javitast_es_a_regiokat_is_torli(redeye_controller):
    assert len(_pending_eye_circles(redeye_controller)) == 2
    assert redeye_controller.canReapplyRedeyeAuto is False

    redeye_controller.resetRedeyeRegions()

    assert redeye_controller.redeyeRegionCount == 0
    assert _pending_eye_circles(redeye_controller) == ()
    assert redeye_controller.redeyeFoundCount == -1
    assert redeye_controller.canReapplyRedeyeAuto is True
    assert redeye_controller.redeyeAutoReset is True


def test_undo_visszaallitja_a_reset_elotti_automatikus_allapotot(redeye_controller):
    redeye_controller.resetRedeyeRegions()
    assert redeye_controller.canUndoRedeyeRegion is True

    redeye_controller.undoRedeyeRegion()

    assert redeye_controller.redeyeRegionCount == 2
    assert len(_pending_eye_circles(redeye_controller)) == 2
    assert redeye_controller.canReapplyRedeyeAuto is False
    assert redeye_controller.redeyeAutoReset is False


def test_auto_ujrafuttatasa_eltunteti_a_reset_utani_allapotot(redeye_controller):
    redeye_controller.resetRedeyeRegions()

    redeye_controller.runRedeyeAuto()

    assert redeye_controller.redeyeRegionCount == 2
    assert redeye_controller.canReapplyRedeyeAuto is False
    assert redeye_controller.redeyeAutoReset is False
