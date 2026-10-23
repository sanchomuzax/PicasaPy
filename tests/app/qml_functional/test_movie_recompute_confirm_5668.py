"""A film kézi újraszámolása mindig kérdez, az emlékezés csak Igenre él (#5668)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPoint, Qt
from PySide6.QtTest import QTest

from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.jpeg_factory import make_minta_jpeg
from tests.support.varakozas import var_feltetelre

#: a kiadáskép csak kérésre készül, a hívó adja a mappát
KIADASKEP_MAPPA = "PICASAPY_5668_KIADASKEP_MAPPA"


@pytest.fixture
def qml_app(qt_app, tmp_path):
    """Mintázatos képekkel: a kiadásképen valódi kép látszik (agent #225)."""

    def kepek(lib):
        make_minta_jpeg(lib / "a.jpg", size=(320, 240), seed=31)
        make_minta_jpeg(lib / "b.jpg", size=(320, 240), seed=32)

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=kepek,
        belyegkep_meret=256,
        valodi_belyegkep=True,
    )


def _elem(gyoker, nev):
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található a QML-fában"
    return elem


def _kattintas(window, qt_app, item):
    """A valódi vezérlő aktuális közepére kattint."""
    kozep = item.mapToScene(item.boundingRect().center())
    QTest.mouseClick(
        item.window() or window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def _var(qt_app, feltetel, lejarat_ms=10000):
    return var_feltetelre(qt_app, feltetel, lejarat_ms / 1000)


def test_ures_filmlistanal_kerdez_es_a_ne_kerdezzen_jelolo_csak_igent_jegyzi(
    qml_app, qt_app, tmp_path, request
):
    window, _controller, engine = qml_app
    request.addfinalizer(
        lambda: [
            dialog.close()
            for dialog in (
                window.findChild(QObject, "movieRecomputeConfirmDialog"),
                window.findChild(QObject, "movieDialog"),
            )
            if dialog is not None
        ]
    )
    confirm_settings = engine.rootContext().contextProperty("confirmSettings")
    assert not confirm_settings.isSuppressed("askapplyconfirm")

    window.setProperty("selectedIndexes", [0, 1])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    _kattintas(window, qt_app, _elem(window, "trayMovieButton"))
    movie_dialog = _elem(window, "movieDialog")
    assert _var(qt_app, lambda: movie_dialog.property("visible")), (
        "a főablak Filmkészítése nem nyitotta meg a filmkészítőt"
    )
    _kattintas(window, qt_app, _elem(window, "movieTabClips"))
    slide_list = _elem(window, "movieSlideList")
    assert slide_list.property("count") == 0, "a tesztnek üres szövegdia-listával kell indulnia"

    recompute = _elem(window, "movieRecomputeButton")
    confirm = window.findChild(QObject, "movieRecomputeConfirmDialog")
    assert confirm is not None, "hiányzik az újraszámolás megerősítő párbeszéde"
    message = _elem(window, "movieRecomputeConfirmMessageLabel")
    mappa = os.environ.get(KIADASKEP_MAPPA)
    movie_tabs = _elem(window, "movieTabs")
    eredeti_magassag = window.height()
    for eltolás in (-5, 0, 5):
        window.resize(window.width(), eredeti_magassag + eltolás)
        qt_app.processEvents()
        if movie_tabs.property("currentIndex") != 1:
            _kattintas(window, qt_app, _elem(window, "movieTabClips"))
        confirm_settings.setSuppressed("askapplyconfirm", False)

        _kattintas(window, qt_app, recompute)
        assert _var(qt_app, lambda: confirm.property("visible")), (
            "üres szövegdia-listánál is kérdeznie kell az újraszámolás előtt"
        )
        assert message.property("text") == (
            "This will generate a new movie removing all the text slides you added. Are you sure?"
        )
        if eltolás == 0 and mappa:
            image = window.grabWindow()
            assert not image.isNull(), "a megerősítő párbeszéd renderelt képe üres"
            cel = Path(mappa) / "film_ujraszamolas_5668.png"
            assert image.save(str(cel), "PNG"), f"nem menthető a kiadáskép: {cel}"

        _kattintas(
            window, qt_app, _elem(window, "movieRecomputeConfirmRememberCheck")
        )
        _kattintas(window, qt_app, _elem(window, "movieRecomputeConfirmNoButton"))
        assert _var(qt_app, lambda: not confirm.property("visible")), (
            "a Nem választás nem zárta be a megerősítést"
        )
        assert not confirm_settings.isSuppressed("askapplyconfirm"), (
            "a Nem választás a bejelölt emlékezés ellenére sem mentheti a beállítást"
        )
        assert slide_list.property("count") == 0

        _kattintas(window, qt_app, recompute)
        assert _var(qt_app, lambda: confirm.property("visible")), (
            "a Nem választás után a következő újraszámolásnak újra kérdeznie kell"
        )
        _kattintas(
            window, qt_app, _elem(window, "movieRecomputeConfirmRememberCheck")
        )
        _kattintas(window, qt_app, _elem(window, "movieRecomputeConfirmYesButton"))
        assert _var(qt_app, lambda: not confirm.property("visible")), (
            "az Igen választás után a párbeszéd nem zárult be"
        )
        assert confirm_settings.isSuppressed("askapplyconfirm"), (
            "a bejelölt emlékezést az Igen választásnak kell rögzítenie"
        )

        _kattintas(window, qt_app, _elem(window, "movieTabClips"))
        _kattintas(window, qt_app, recompute)
        assert _var(qt_app, lambda: movie_tabs.property("currentIndex") == 0), (
            "az elnyomott kérdés után az újraszámolásnak kérdés nélkül kell lefutnia"
        )
        assert not confirm.property("visible")
