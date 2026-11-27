"""A helyi vágási és vörösszem-számítás nem blokkolja a szerkesztőt (#7485)."""

from __future__ import annotations

import threading
import time
from types import SimpleNamespace

import pytest

from picasapy.app.edit_controller import EditController
from picasapy.app.edit_preview import EditPreviewProvider
from picasapy.ini.rect64 import Rect64
from support.jpeg_factory import make_jpeg


def _varj(qt_app, feltetel, timeout: float = 10.0) -> bool:
    hatarido = time.monotonic() + timeout
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.01)
    qt_app.processEvents()
    return feltetel()


def test_begin_edit_a_helyi_vagasi_javaslatot_hatterszalon_inditja(
    qt_app, tmp_path, monkeypatch
):
    from picasapy.app import edit_controller_crop_mixin as crop_module
    from picasapy.app import edit_preview_source

    photo = make_jpeg(tmp_path / "helyi.jpg", size=(48, 32))
    controller = EditController(EditPreviewProvider())
    fo_szal = threading.get_ident()
    dekodolo_szalszamai = []
    javaslat_szalszamai = []
    kesz_jelzesek = []
    eredeti_dekodol = edit_preview_source._decode_source

    def lassu_dekodol(*args, **kwargs):
        dekodolo_szalszamai.append(threading.get_ident())
        time.sleep(0.3)
        return eredeti_dekodol(*args, **kwargs)

    def javaslat(image, *, faces, aspect):
        javaslat_szalszamai.append(threading.get_ident())
        assert image is not None
        return (SimpleNamespace(key="test", rect=Rect64(0.1, 0.2, 0.8, 0.9)),)

    monkeypatch.setattr(edit_preview_source, "_decode_source", lassu_dekodol)
    monkeypatch.setattr(crop_module, "_decode_source", lassu_dekodol)
    monkeypatch.setattr(crop_module, "suggest_crops", javaslat)

    def olvasd_el_a_javaslatokat():
        kesz_jelzesek.append(controller.cropSuggestions)

    controller.cropSuggestionsChanged.connect(olvasd_el_a_javaslatokat)
    indulas = time.perf_counter()
    controller.beginEdit("helyi", str(photo))
    eltelt = time.perf_counter() - indulas
    # Az első jelzés a beginEdit része, a következőnek a worker befejezése adja.
    kesz_jelzesek.clear()

    assert eltelt < 0.1, f"a beginEdit {eltelt:.3f} s-ig blokkolt"
    assert _varj(qt_app, lambda: bool(kesz_jelzesek))
    assert len(kesz_jelzesek) == 1
    assert kesz_jelzesek[0][0] == pytest.approx(
        {"key": "test", "x": 0.1, "y": 0.2, "w": 0.7, "h": 0.7}
    )
    assert dekodolo_szalszamai and fo_szal not in dekodolo_szalszamai
    assert javaslat_szalszamai and fo_szal not in javaslat_szalszamai
    assert controller._provider._cached_source_image("helyi", photo) is not None
    # A másik képarány is ugyanazt a dekódolt, cache-elt tömböt használja.
    previous_decode_count = len(dekodolo_szalszamai)
    assert previous_decode_count == 1
    previous_notifications = len(kesz_jelzesek)
    controller.setCropAspect(1.0)
    assert controller.cropSuggestions == []
    assert _varj(qt_app, lambda: len(kesz_jelzesek) > previous_notifications)
    assert len(dekodolo_szalszamai) == previous_decode_count


def test_voros_szem_megnyitasa_hatterszalra_tereli_a_provider_szamitasat(
    qt_app, tmp_path, monkeypatch
):
    photo = make_jpeg(tmp_path / "voros.jpg", size=(48, 32))
    provider = EditPreviewProvider()
    controller = EditController(provider)
    controller.beginEdit("voros", str(photo))
    fo_szal = threading.get_ident()
    szalak = []

    def lassu_voros_szem(*_args):
        szalak.append(threading.get_ident())
        time.sleep(0.3)
        return 1, ((0.5, 0.5, 0.1),), (48, 32), (48, 32), (
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
        )

    monkeypatch.setattr(provider, "_redeye_auto_result_for_worker", lassu_voros_szem)
    indulas = time.perf_counter()
    controller.enterRedeyeTool()
    eltelt = time.perf_counter() - indulas

    assert eltelt < 0.1, f"az enterRedeyeTool {eltelt:.3f} s-ig blokkolt"
    assert controller.redeyeFoundCount == -1
    assert _varj(qt_app, lambda: controller.redeyeFoundCount == 1)
    assert szalak and fo_szal not in szalak
    assert controller.redeyeRegions == [
        pytest.approx(
            {"x": 0.43333333333333335, "y": 0.4, "w": 0.1333333333333333, "h": 0.2}
        )
    ]
    assert not (photo.parent / ".picasa.ini").exists()


def test_regi_voros_szem_eredmeny_kepvaltaskor_elavul_es_nincs_parhuzam(
    qt_app, tmp_path, monkeypatch
):
    first = make_jpeg(tmp_path / "elso.jpg", size=(48, 32))
    second = make_jpeg(tmp_path / "masodik.jpg", size=(48, 32))
    provider = EditPreviewProvider()
    controller = EditController(provider)
    controller.beginEdit("elso", str(first))
    lock = threading.Lock()
    aktiv = 0
    maximum_aktiv = 0

    def lassu_eredmeny(photo_id, *_args):
        nonlocal aktiv, maximum_aktiv
        with lock:
            aktiv += 1
            maximum_aktiv = max(maximum_aktiv, aktiv)
        try:
            time.sleep(0.25)
            return int(photo_id == "elso"), (), (48, 32), (48, 32), (
                (1.0, 0.0, 0.0),
                (0.0, 1.0, 0.0),
            )
        finally:
            with lock:
                aktiv -= 1

    monkeypatch.setattr(provider, "_redeye_auto_result_for_worker", lassu_eredmeny)
    indulas = time.perf_counter()
    controller.enterRedeyeTool()
    elso_enter_ido = time.perf_counter() - indulas
    controller.beginEdit("masodik", str(second))
    controller.enterRedeyeTool()

    assert elso_enter_ido < 0.1, f"az első eszköznyitás {elso_enter_ido:.3f} s-ig blokkolt"
    assert _varj(qt_app, lambda: controller.redeyeFoundCount == 0)
    assert controller.redeyeFoundCount == 0
    assert maximum_aktiv == 1


def test_bezaras_utan_a_voros_szem_worker_eredmenye_elavult(
    qt_app, tmp_path, monkeypatch
):
    photo = make_jpeg(tmp_path / "bezaras.jpg", size=(48, 32))
    provider = EditPreviewProvider()
    controller = EditController(provider)
    controller.beginEdit("bezaras", str(photo))

    def lassu_eredmeny(*_args):
        time.sleep(0.25)
        return 1, ((0.5, 0.5, 0.1),), (48, 32), (48, 32), (
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
        )

    monkeypatch.setattr(provider, "_redeye_auto_result_for_worker", lassu_eredmeny)
    indulas = time.perf_counter()
    controller.enterRedeyeTool()
    eltelt = time.perf_counter() - indulas
    controller.exitRedeyeTool()

    assert eltelt < 0.1, f"az enterRedeyeTool {eltelt:.3f} s-ig blokkolt"
    assert _varj(qt_app, lambda: controller.waitForBackgroundWorkers(0.02))
    qt_app.processEvents()
    assert controller.redeyeFoundCount == -1
    assert controller.redeyeRegions == []
