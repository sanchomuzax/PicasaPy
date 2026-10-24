"""#5703: a dátummódosítás címe és a köteg futásjelzése."""

from __future__ import annotations

import os
import threading
from pathlib import Path

import piexif
import pytest

from picasapy.app import timestamp_controller
from tests.app.qml_functional.conftest import _build_qml_app
from tests.app.qml_functional.test_adjust_timestamp_4332 import (
    _elem,
    _kattints,
    _var,
)
from tests.support.jpeg_factory import make_minta_jpeg

KIADASKEP_MAPPA = "PICASAPY_5703_KIADASKEP_MAPPA"
MAX_VARAKOZAS_MASODPERC = 3


@pytest.fixture
def timestamp_app(qt_app, tmp_path):
    def kepeket(lib):
        for seed, (name, taken_at) in enumerate(
            (
                ("a.jpg", "2020:01:01 12:00:00"),
                ("b.jpg", "2020:01:03 12:00:00"),
                ("c.jpg", "2020:01:04 12:00:00"),
            ),
            start=21,
        ):
            path = lib / name
            make_minta_jpeg(path, size=(320, 240), seed=seed)
            exif = piexif.dump(
                {
                    "0th": {},
                    "Exif": {piexif.ExifIFD.DateTimeOriginal: taken_at},
                }
            )
            piexif.insert(exif, str(path))

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=kepeket,
        belyegkep_meret=256,
        valodi_belyegkep=True,
    )


def _open_timestamp_dialog(window, controller, qt_app, count: int):
    assert controller.sortFolderBy(controller.currentFolder, "date")
    window.setProperty("selectedIndexes", list(range(count)))
    window.setProperty("selectedIndex", 0)
    window.show()
    qt_app.processEvents()

    tools_menu = _elem(window, "menuTools")
    tools_menu.open()
    _var(qt_app, lambda: tools_menu.property("visible"), "az Eszközök menü")
    _kattints(_elem(window, "menuToolsAdjustTimestamp"), qt_app, window)

    dialog = _elem(window, "adjustTimestampDialog")
    _var(qt_app, lambda: dialog.property("visible"), "a dátummódosító párbeszéd")
    return dialog


def test_egyetlen_kepnel_a_cim_nem_tartalmaz_elemszamot(timestamp_app, qt_app):
    window, _controller, _engine = timestamp_app

    dialog = _open_timestamp_dialog(window, _controller, qt_app, 1)

    assert dialog.property("title") == "Adjust Photo Date"
    _var(
        qt_app,
        lambda: _elem(window, "adjustTimestampDialog").property(
            "thumbnailLoaded"
        ),
        "az előnézeti kép betöltése",
    )

    mappa = os.environ.get(KIADASKEP_MAPPA)
    if mappa:
        qt_app.processEvents()
        kep = window.grabWindow()
        assert not kep.isNull(), "a kiadáskép üres"
        cel = Path(mappa) / "timestamp_5703.png"
        assert kep.save(str(cel), "PNG"), f"nem menthető a kiadáskép: {cel}"


def test_a_koteg_jelzese_sikeres_futas_utan_bezarul(
    timestamp_app, qt_app, monkeypatch
):
    window, _controller, _engine = timestamp_app
    _open_timestamp_dialog(window, _controller, qt_app, 2)
    entered = threading.Event()
    release = threading.Event()
    original_write = timestamp_controller._write_photo_exif_date

    def blocked_write(path, target):
        entered.set()
        if not release.wait(10):
            raise RuntimeError("a teszt nem engedte tovább a dátumírást")
        return original_write(path, target)

    monkeypatch.setattr(
        timestamp_controller, "_write_photo_exif_date", blocked_write
    )
    _kattints(_elem(window, "adjustTimestampAccept"), qt_app, window)

    try:
        _var(
            qt_app,
            entered.is_set,
            "a háttérben futó dátumírás",
            ido=MAX_VARAKOZAS_MASODPERC,
        )
        progress = _elem(window, "adjustTimestampProgress")
        assert progress.property("visible"), "a köteg alatt nem látszik futásjelzés"
        assert progress.property("title") == "Setting photo dates"
        assert _elem(window, "adjustTimestampProgressText").property("text") == (
            "Setting image time"
        )
    finally:
        release.set()

    _var(
        qt_app,
        lambda: not progress.property("visible"),
        "a sikeresen befejezett köteg jelzése bezárul",
    )


def test_hibanal_a_koteg_jelzese_bezarul(timestamp_app, qt_app, monkeypatch):
    window, _controller, _engine = timestamp_app
    _open_timestamp_dialog(window, _controller, qt_app, 2)
    entered = threading.Event()
    release = threading.Event()

    def failed_write(_path, _target):
        entered.set()
        if not release.wait(10):
            raise RuntimeError("a teszt nem engedte tovább a hibás dátumírást")
        raise OSError("a próbakép nem írható")

    monkeypatch.setattr(
        timestamp_controller, "_write_photo_exif_date", failed_write
    )
    _kattints(_elem(window, "adjustTimestampAccept"), qt_app, window)

    try:
        _var(
            qt_app,
            entered.is_set,
            "a háttérben futó dátumírás",
            ido=MAX_VARAKOZAS_MASODPERC,
        )
        progress = _elem(window, "adjustTimestampProgress")
        assert progress.property("visible"), "a köteg alatt nem látszik futásjelzés"
    finally:
        release.set()

    _var(
        qt_app,
        lambda: not progress.property("visible"),
        "a hibával leállt köteg jelzése bezárul",
    )
