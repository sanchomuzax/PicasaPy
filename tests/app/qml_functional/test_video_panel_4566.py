"""#4566: videó megnyitásakor a bal oldalon a videó-panel áll a fülsáv helyén.

Spec: `docs/specs/ui-audit-editor.md` (a `movietab` szakasza). A videó-fül
bekapcsolva ELTÜNTETI a fülsávot, és a helyén a `movieeditpanel` gombjai
állnak. A teszt valódi főablakban, valódi kattintással ellenőrzi a gombokat,
mindhárom -5 / 0 / +5 képpontos ablakmagasságon.

Negyedik gomb (`movieeditpanel/export_youtube`) szándékosan NINCS itt: a
#4229 lefedettségi tábla `nem-cel`-re teszi, a spec viszont négyet ír elő —
ez nyitott döntés, nem tesztkérdés.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg
from tests.app.qml_functional.conftest import _build_qml_app

_ABLAKMAGASSAG_ELTOLASOK = (-5, 0, 5)


def _videoleiras(lib: Path) -> None:
    make_jpeg(lib / "a.jpg", size=(320, 160))
    # szándékosan érvénytelen videó: a panel a kiterjesztésből dönt
    (lib / "b.mp4").write_bytes(b"\x00" * 64)


@pytest.fixture
def qml_app_video(qt_app, tmp_path):
    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_videoleiras)


def _elem(window, nev: str):
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található a főablakban"
    return elem


def _var(qt_app, feltetel, leiras: str, masodperc: float = 3.0) -> None:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return
        time.sleep(0.01)
    qt_app.processEvents()
    assert feltetel(), f"időkorláton belül nem teljesült: {leiras}"


def _kattint(window, qt_app, elem) -> None:
    assert elem.property("visible") is True, f"{elem.objectName()} nem látszik"
    assert elem.isEnabled(), f"{elem.objectName()}: a gomb le van tiltva"
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def _video_sor(viewer) -> int:
    modell = viewer.property("photosModel")
    for sor in range(2):
        if modell.isVideoAt(sor):
            return sor
    raise AssertionError("a próbamappában nincs videó")


def _nyisd_meg_a_videot(window, viewer, qt_app) -> int:
    window.setProperty("width", 1280)
    window.setProperty("height", 1005)
    window.setProperty("viewerOpen", True)
    sor = _video_sor(viewer)
    viewer.setProperty("currentIndex", sor)
    _var(
        qt_app,
        lambda: _elem(window, "videoEditPanel").property("visible") is True,
        "a videó-panel nem jelent meg videónál",
    )
    return sor


def _megerosites_nyitva(window) -> bool:
    dialog = window.findChild(QObject, "movieResetConfirmDialog")
    return dialog is not None and dialog.property("visible") is True


class TestVideoPanelAFulsavHelyen:
    def test_a_fulsav_helyen_a_negy_gomb_nem_a_szerkesztopanel_all(
        self, qml_app_video, qt_app
    ):
        window, _controller, _engine = qml_app_video
        viewer = window.findChild(QObject, "photoViewer")
        _nyisd_meg_a_videot(window, viewer, qt_app)
        assert _elem(window, "viewerEditorPanel").property("visible") is False
        for nev in (
            "movieeditpanel/reset_trim",
            "movieeditpanel/capture_frame",
            "movieeditpanel/export_movie",
        ):
            assert _elem(window, nev).property("visible") is True, nev


class TestVideoPanelKattintas:
    @pytest.mark.parametrize("eltolas", _ABLAKMAGASSAG_ELTOLASOK)
    def test_mind_harom_gomb_valodi_kattintassal_mukodik(
        self, qml_app_video, qt_app, eltolas
    ):
        window, controller, _engine = qml_app_video
        viewer = window.findChild(QObject, "photoViewer")
        sor = _nyisd_meg_a_videot(window, viewer, qt_app)
        window.setHeight(window.height() + eltolas)
        _var(
            qt_app,
            lambda: window.height() == 1005 + eltolas,
            f"az ablakmagasság {eltolas:+d} képponttal változzon",
        )

        reset = _elem(window, "movieeditpanel/reset_trim")
        export = _elem(window, "movieeditpanel/export_movie")
        capture = _elem(window, "movieeditpanel/capture_frame")
        # vágás nélkül a visszaállítás és az export szürke
        assert not reset.isEnabled()
        assert not export.isEnabled()

        controller.setMovieTrim(sor, 200, 1600)
        _var(qt_app, reset.isEnabled, "a visszaállítás a vágás után aktív")
        assert export.isEnabled()

        _kattint(window, qt_app, export)
        if sys.platform.startswith("linux"):
            ertesites = _elem(window, "videoCaptureNotice")
            _var(
                qt_app,
                lambda: "This feature is not supported for Linux"
                in str(ertesites.property("text")),
                "a Linux-es exportkorlát üzenete",
            )

        # az eredeti előbb rákérdez (`CThumbUI::UndomovieEdits`): a „Nem"
        # a vágást megtartja, a „Szerkesztések eltávolítása" törli
        _kattint(window, qt_app, reset)
        _var(qt_app, lambda: _megerosites_nyitva(window), "a megerősítés nyílik")
        _kattint(window, qt_app, _elem(window, "movieResetConfirmNoButton"))
        _var(qt_app, lambda: not _megerosites_nyitva(window), "a „Nem” bezár")
        assert reset.isEnabled(), "a „Nem” után is törlődött a vágás"

        _kattint(window, qt_app, reset)
        _var(qt_app, lambda: _megerosites_nyitva(window), "a megerősítés nyílik")
        _kattint(window, qt_app, _elem(window, "movieResetConfirmYesButton"))
        _var(
            qt_app,
            lambda: not reset.isEnabled(),
            "a visszaállítás a vágást törli",
        )
        assert not export.isEnabled()

        ertesites = _elem(window, "videoCaptureNotice")
        ertesites.setProperty("text", "")
        _kattint(window, qt_app, capture)
        _var(
            qt_app,
            lambda: str(ertesites.property("text")) != "",
            "a képkocka-mentés visszajelzése",
        )
