"""#7320: a futó HTML-export megerősítéssel megszakítható."""

from __future__ import annotations

import time
from pathlib import Path
from threading import Event
from types import SimpleNamespace

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPointF, Qt
from PySide6.QtTest import QTest
from tests.app.qml_functional.conftest import _build_qml_app


@pytest.fixture
def qml_app(qt_app, tmp_path, request):
    def make_photos(folder):
        from tests.support.jpeg_factory import make_jpeg

        make_jpeg(folder / "a.jpg", size=(80, 60))

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=make_photos,
        belyegkep_meret=128,
        valodi_belyegkep=True,
        keep_modul=request.module,
    )


def _varj(qt_app, feltetel, timeout_s: float = 10.0) -> bool:
    hatarido = time.monotonic() + timeout_s
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.05)
    qt_app.processEvents()
    return bool(feltetel())


def _gyerek(gyoker, nev: str):
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _kattint(elem) -> None:
    pont = elem.mapToScene(
        QPointF(float(elem.width()) / 2, float(elem.height()) / 2)
    ).toPoint()
    QTest.mouseClick(
        elem.window(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        pont,
    )


@pytest.mark.parametrize("magassag_elteres", [-5, 0, 5])
def test_a_futo_webexport_megerositesnel_folytathato_vagy_megszakithato(
    qml_app, qt_app, monkeypatch, tmp_path, magassag_elteres
):
    from picasapy.app import webexport_controller as webexport_modul
    from picasapy.app.busy_registry import get_app_busy_registry
    from picasapy.app.webexport_controller import WebExportController

    main_window, app_controller, engine = qml_app
    vezerlo = WebExportController(
        photo_source=lambda: app_controller.photos.photos,
        settings=app_controller._get_settings(),
    )
    engine.rootContext().setContextProperty("webExportController", vezerlo)
    QMetaObject.invokeMethod(
        main_window, "openWebExport", Qt.ConnectionType.DirectConnection
    )
    assert _varj(
        qt_app,
        lambda: main_window.findChild(QObject, "webExportDialog") is not None,
    ), "a webexport-párbeszéd nem épült fel"
    dialog = main_window.findChild(QObject, "webExportDialog")
    dialog.setProperty("height", dialog.property("height") + magassag_elteres)
    dialog.setProperty("targetFolder", str(tmp_path / "webexport-kimenet"))

    belepett = Event()
    felold = Event()
    megszakitast_latott = Event()

    def fake_prepare(_photos, _target_dir, _settings, *, is_cancelled=None):
        belepett.set()
        while not felold.is_set() and not (is_cancelled and is_cancelled()):
            time.sleep(0.01)
        if is_cancelled and is_cancelled():
            megszakitast_latott.set()
            raise InterruptedError("webexport cancelled")
        return SimpleNamespace(photos=(SimpleNamespace(name="a.jpg"),), skipped=())

    monkeypatch.setattr(webexport_modul, "prepare_photo_exports", fake_prepare)
    monkeypatch.setattr(
        webexport_modul,
        "run_web_export",
        lambda _template, target, _album, _settings, **_kwargs: SimpleNamespace(
            output_files=(Path(target) / "index.html",)
        ),
    )

    try:
        QMetaObject.invokeMethod(
            dialog, "startExport", Qt.ConnectionType.DirectConnection
        )
        assert _varj(qt_app, belepett.is_set), "a háttér-export nem indult el"
        cancel_button = _gyerek(dialog, "webExportCloseButton")
        assert cancel_button.property("enabled"), "futás közben le van tiltva a Mégse"
        _kattint(cancel_button)

        confirm = _gyerek(dialog, "webExportCancelDialog")
        assert _varj(qt_app, lambda: confirm.property("visible")), (
            "a futó export megszakításához nem jelent meg megerősítés"
        )
        assert confirm.property("title") == "Want to Cancel?"
        assert _gyerek(dialog, "webExportCancelMessageLabel").property("text") == (
            "Do you want to cancel this operation?"
        )
        assert _gyerek(dialog, "webExportCancelYesButton").property("text") == (
            "Cancel Operation"
        )
        assert _gyerek(dialog, "webExportCancelNoButton").property("text") == (
            "Don't Cancel"
        )

        _kattint(_gyerek(dialog, "webExportCancelNoButton"))
        assert _varj(qt_app, lambda: not confirm.property("visible"))
        assert dialog.property("exporting"), "a Don't Cancel leállította az exportot"
        assert not megszakitast_latott.is_set()

        felold.set()
        assert _varj(qt_app, lambda: not dialog.property("exporting")), (
            "a folytatott export nem zárult le"
        )
        assert _gyerek(dialog, "webExportResultText").property("visible")

        # Újabb futás: a megerősített megszakítás ne hagyjon sikeres eredményt.
        belepett.clear()
        felold.clear()
        megszakitast_latott.clear()
        dialog.setProperty("lastOutputFolder", "previous-success")
        dialog.setProperty("lastPageCount", 8)
        QMetaObject.invokeMethod(
            dialog, "startExport", Qt.ConnectionType.DirectConnection
        )
        assert _varj(qt_app, belepett.is_set), "a második háttér-export nem indult el"
        _kattint(cancel_button)
        assert _varj(qt_app, lambda: confirm.property("visible"))
        _kattint(_gyerek(dialog, "webExportCancelYesButton"))
        registry = get_app_busy_registry()
        assert _varj(
            qt_app,
            lambda: not dialog.property("exporting")
            and not vezerlo.exportRunning()
            and registry.activeCount == 0,
        ), "a megszakított export vagy az állapotjelzés beragadt"
        assert megszakitast_latott.is_set()
        assert not _gyerek(dialog, "webExportResultText").property("visible")
        assert dialog.property("lastOutputFolder") == ""
    finally:
        felold.set()
        assert vezerlo.waitForExport(10.0), "a teszt webexport-szála nem állt le"
