"""#7338 — a Fájltípusok beállítás OK után azonnal szinkronizál."""

from __future__ import annotations

import threading
from pathlib import Path

import pytest
from PIL import Image

from conftest import _build_qml_app
from support.jpeg_factory import make_minta_jpeg
from tests.app.qml_functional.test_menu_talca_egyeb_valodi_5135_b import (
    _gyerek,
    _klikk_ablakban,
    _varj,
)
from tests.app.qml_functional.test_parbeszedek_valodi_5150_b import (
    _beallitasok_megnyit,
    _fulre_kattint,
)

_BMP = "masodik.bmp"
_JPEG = "elso.jpg"
_MAGASSAG_ELTOLASOK = (-5, 0, 5)


def _keszits_kepeket(lib: Path) -> None:
    make_minta_jpeg(lib / _JPEG, size=(120, 90), seed=7338)
    Image.new("RGB", (80, 60), (30, 120, 210)).save(lib / _BMP, format="BMP")


@pytest.fixture
def filetype_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_kepeket,
    )


def _nevek(controller) -> set[str]:
    return {photo.name for photo in controller.photos.photos}


def _fajltipus_ful(window, qt_app, magassag_elteres: int):
    options = _beallitasok_megnyit(window, qt_app)
    options.setHeight(options.height() + magassag_elteres)
    _fulre_kattint(qt_app, options, "optionsTabFileTypes", 2)
    return options


@pytest.mark.parametrize("magassag_elteres", _MAGASSAG_ELTOLASOK)
def test_ok_csak_valtozasnal_indit_szinkront_es_frissiti_a_konyvtarat(
    filetype_app, qt_app, monkeypatch, magassag_elteres: int
):
    window, controller, _engine = filetype_app
    window.show()
    window.requestActivate()
    assert _varj(qt_app, lambda: _nevek(controller) == {_JPEG, _BMP})

    import picasapy.app.controller as controller_module

    sync_calls = []
    original_sync_tree = controller_module.sync_tree

    def count_sync_tree(*args, **kwargs):
        sync_calls.append(kwargs.get("enabled_filetypes"))
        return original_sync_tree(*args, **kwargs)

    monkeypatch.setattr(controller_module, "sync_tree", count_sync_tree)

    # Változatlan értékek elfogadása nem kérhet új könyvtárszinkront.
    options = _fajltipus_ful(window, qt_app, magassag_elteres)
    _klikk_ablakban(qt_app, options, _gyerek(options, "optionsOkButton"))
    assert _varj(qt_app, lambda: options.property("visible") is False)
    assert sync_calls == []
    assert controller._sync_running is False

    # A már indexelt BMP a kikapcsolás után eltűnik a könyvtárból, a fájl megmarad.
    options = _fajltipus_ful(window, qt_app, 0)
    bmp = _gyerek(options, "optionsFileTypeBmpCheck")
    assert bmp.property("checked") is True
    _klikk_ablakban(qt_app, options, bmp)
    assert bmp.property("checked") is False
    _klikk_ablakban(qt_app, options, _gyerek(options, "optionsOkButton"))
    assert _varj(
        qt_app,
        lambda: not controller._sync_running and _nevek(controller) == {_JPEG},
    )
    assert len(sync_calls) == 1
    assert (Path(controller._roots[0]) / _BMP).is_file()

    # A korábban szűrt fájl visszajön, amikor a csoportot újra bekapcsoljuk.
    options = _fajltipus_ful(window, qt_app, 0)
    bmp = _gyerek(options, "optionsFileTypeBmpCheck")
    assert bmp.property("checked") is False
    _klikk_ablakban(qt_app, options, bmp)
    _klikk_ablakban(qt_app, options, _gyerek(options, "optionsOkButton"))
    assert _varj(
        qt_app,
        lambda: not controller._sync_running and _nevek(controller) == {_JPEG, _BMP},
    )
    assert len(sync_calls) == 2
    assert (Path(controller._roots[0]) / _BMP).is_file()


@pytest.mark.parametrize("magassag_elteres", _MAGASSAG_ELTOLASOK)
def test_futó_szinkron_utan_a_legujabb_fajltipus_szuro_is_ervenyesul(
    filetype_app, qt_app, monkeypatch, magassag_elteres: int
):
    window, controller, _engine = filetype_app
    window.show()
    window.requestActivate()
    assert _varj(qt_app, lambda: _nevek(controller) == {_JPEG, _BMP})

    import picasapy.app.controller as controller_module

    first_sync_started = threading.Event()
    allow_first_sync_to_finish = threading.Event()
    sync_filetype_snapshots = []
    original_sync_tree = controller_module.sync_tree

    def pause_first_sync(*args, **kwargs):
        sync_filetype_snapshots.append(kwargs.get("enabled_filetypes"))
        if len(sync_filetype_snapshots) == 1:
            first_sync_started.set()
            if not allow_first_sync_to_finish.wait(15):
                raise TimeoutError("az első szinkron nem kapott feloldást")
        return original_sync_tree(*args, **kwargs)

    monkeypatch.setattr(controller_module, "sync_tree", pause_first_sync)
    controller.rescan()
    assert _varj(qt_app, first_sync_started.is_set)

    try:
        options = _fajltipus_ful(window, qt_app, magassag_elteres)
        bmp = _gyerek(options, "optionsFileTypeBmpCheck")
        assert bmp.property("checked") is True
        _klikk_ablakban(qt_app, options, bmp)
        _klikk_ablakban(qt_app, options, _gyerek(options, "optionsOkButton"))
        assert _varj(qt_app, lambda: options.property("visible") is False)
    finally:
        allow_first_sync_to_finish.set()

    assert _varj(
        qt_app,
        lambda: len(sync_filetype_snapshots) >= 2
        and not controller._sync_running
        and _nevek(controller) == {_JPEG},
    )
    assert sync_filetype_snapshots[0] is None
    assert sync_filetype_snapshots[-1] is not None
    assert "bmp" not in sync_filetype_snapshots[-1]
    assert (Path(controller._roots[0]) / _BMP).is_file()
