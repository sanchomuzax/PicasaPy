"""#4329: felső menüpontok — nezet."""

import pytest

from tests.app.qml_functional._felsomenupontok_helpers_4329 import (
    _ABLAKMAGASSAG_ELTOLASOK,
    _kattints,
    _kijeloles,
    _magassag,
    _nyisd_meg_felso_menut,
    _varj,
)


@pytest.fixture
def qml_app_small_pictures(qt_app, tmp_path, monkeypatch):
    from picasapy.app import small_picture_filter
    from support.jpeg_factory import make_jpeg

    # Ez a próba az eredeti alapértéket méri: a közös fixture kikapcsolását visszavonjuk.
    monkeypatch.setattr(small_picture_filter, "DEFAULT_SHOW_ONLY_BIG_IMAGES", True)
    from tests.app.qml_functional.conftest import _build_qml_app

    def keszits_kepeket(lib):
        make_jpeg(lib / "big.jpg", size=(400, 300))
        make_jpeg(lib / "small.jpg", size=(100, 100))

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=keszits_kepeket,
        show_only_big_images=None,
    )


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_nezet_edit_view_kattintas_megnyitja_a_kijelolt_kepeket(
    qml_app, qt_app, height_offset
):
    window, _controller, _engine = qml_app
    _magassag(window, height_offset)
    _menu_bar, _menu, _fejléc, item = _nyisd_meg_felso_menut(
        qt_app, window, "view", "menuViewEditView"
    )
    assert item.property("enabled") is False
    _kijeloles(window, qt_app, [0])
    assert _varj(qt_app, lambda: item.property("enabled") is True)

    _kattints(qt_app, item)

    assert _varj(qt_app, lambda: window.property("viewerOpen") is True), (
        "a Nézet ▸ Edit View nem nyitotta meg a kijelölt képet"
    )


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_nezet_small_pictures_kattintas_szur_es_perzisztens(
    qml_app_small_pictures, qt_app, height_offset
):
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController

    window, controller, _engine = qml_app_small_pictures
    _magassag(window, height_offset)

    def lathato_nevek():
        return {photo.name for photo in controller.photos.photos}

    assert controller.showOnlyBigImages is True
    assert lathato_nevek() == {"big.jpg"}

    _menu_bar, _menu, _fejlec, item = _nyisd_meg_felso_menut(
        qt_app, window, "view", "menuViewThumbnailsOnly"
    )
    assert item.property("checkable") is True
    assert item.property("enabled") is True
    assert item.property("placeholder") is False
    assert item.property("checked") is False
    _kattints(qt_app, item)

    assert _varj(qt_app, lambda: controller.showOnlyBigImages is False)
    assert _varj(qt_app, lambda: lathato_nevek() == {"big.jpg", "small.jpg"})

    controller._get_settings().sync()
    uj_beallitas = QSettings(
        controller._get_settings().fileName(), QSettings.Format.IniFormat
    )
    uj_vezerlo = AppController(
        controller._db_path,
        tuple(controller._roots),
        controller._provider,
        settings=uj_beallitas,
    )
    assert uj_vezerlo.showOnlyBigImages is False
    uj_vezerlo.shutdown()
    assert uj_vezerlo.waitForBackgroundWorkers(30.0)
    uj_vezerlo.deleteLater()
    qt_app.processEvents()

    _menu_bar, _menu, _fejlec, item = _nyisd_meg_felso_menut(
        qt_app, window, "view", "menuViewThumbnailsOnly"
    )
    assert item.property("checked") is True
    _kattints(qt_app, item)

    assert _varj(qt_app, lambda: controller.showOnlyBigImages is True)
    assert _varj(qt_app, lambda: lathato_nevek() == {"big.jpg"})
