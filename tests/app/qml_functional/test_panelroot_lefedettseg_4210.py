"""#4210: a kamera- és filmkészítő-belépő a valódi főablakból használható."""

from __future__ import annotations

import csv
import time
from pathlib import Path

from PySide6.QtCore import QObject, QPoint, QPointF, QTranslator, Qt, QUrl
from PySide6.QtGui import QAccessible
from PySide6.QtQml import QQmlComponent
from PySide6.QtTest import QTest
import pytest

from support.collage_wiring_985 import (
    _elem,
    _eger_fel,
    _eger_le,
    _eger_mozog,
    _fulre_kattint_amig_valt,
    _kollazs_lapot_nyit,
)


def _obj(window, name: str):
    result = window.findChild(QObject, name)
    assert result is not None, f"{name} nem található a főablak QML-fájában"
    return result


def _click(qt_app, window, target) -> None:
    point = target.mapToScene(
        target.boundingRect().center()
    )
    assert 0 <= point.x() < window.width()
    assert 0 <= point.y() < window.height()
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )
    qt_app.processEvents()


def _until(qt_app, condition, description: str) -> None:
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if condition():
            return
        QTest.qWait(50)
    assert condition(), f"időtúllépés: {description}"


def _accessible_name(item) -> str:
    interface = QAccessible.queryAccessibleInterface(item)
    assert interface is not None, "a vezérlőnek nincs akadálymentességi felülete"
    return interface.text(QAccessible.Text.Name)


def _coverage_rows() -> dict[str, dict[str, str]]:
    path = (
        Path(__file__).resolve().parents[3]
        / "docs"
        / "specs"
        / "ui-lefedettseg-elemek.csv"
    )
    with path.open(encoding="utf-8", newline="") as file:
        return {row["elem"]: row for row in csv.DictReader(file)}


@pytest.fixture
def magyar_forditas(qt_app):
    import picasapy.app.application as app_module

    translator = QTranslator(qt_app)
    assert translator.load("picasapy_hu", str(app_module._I18N_DIR))
    qt_app.installTranslator(translator)
    yield translator
    qt_app.removeTranslator(translator)


def test_globaltabs_es_picasatab_valodi_fulekent_valt(qml_app, qt_app):
    window, controller, _ = qml_app
    tabsav = _obj(window, "documentTabStrip")
    _kollazs_lapot_nyit(window, qt_app)
    _until(
        qt_app,
        lambda: controller.property("collageOpen") is True,
        "a valódi kollázsprojekt-lap megnyitása",
    )
    project_tab = _elem(window, "documentTab0")
    assert project_tab is not None

    eredeti_magassag = window.height()
    for eltolás in (-5, 0, 5):
        window.resize(window.width(), eredeti_magassag + eltolás)
        qt_app.processEvents()
        assert window.height() == eredeti_magassag + eltolás

        global_tabs = _obj(window, "panelroot/globaltabs")
        assert global_tabs.isVisible()
        _fulre_kattint_amig_valt(window, qt_app, "documentTabLibrary", "library")
        assert tabsav.property("activeTabId") == "library"
        _fulre_kattint_amig_valt(window, qt_app, "documentTab0", "collage")
        assert tabsav.property("activeTabId") == "collage"


def test_a_kijelolt_csv_sorok_kimeneti_tesztre_hivatkoznak():
    expected = {
        "panelroot/picasatab": "megvan",
        "panelroot/globaltabs": "megvan",
        "panelroot/capturemovietab": "megvan",
        "panelroot/makemovietab": "megvan",
        "panelroot/youtab": "nem-cel",
        "video_control_bar/scaleslider": "megvan",
        "video_control_bar/trimslider": "megvan",
        "video_control_bar/volumeslider": "megvan",
    }
    rows = _coverage_rows()
    assert set(expected) <= set(rows)
    assert {name: rows[name]["allapot"] for name in expected} == expected
    for name, state in expected.items():
        if state == "megvan":
            assert "tests/" in rows[name]["bizonyitek"], name
    assert "m_hidden" in rows["panelroot/youtab"]["megjegyzes"]


def test_vagocsuszka_valodi_fomenuablakban_egerrel_mozog_minden_magassagon(
    qml_app, qt_app
):
    window, _, engine = qml_app
    import picasapy.app.application as app_module

    video_qml = Path(app_module._APP_DIR) / "qml" / "PicasaPy" / "VideoTrimSlider.qml"
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(video_qml)))
    assert component.status() == QQmlComponent.Status.Ready, component.errorString()
    video_view = component.create()
    assert video_view is not None, component.errorString()
    video_view.setParentItem(window.contentItem())
    video_view.setProperty("width", window.width())
    video_view.setProperty("height", 18)
    video_view.setProperty("durationMs", 5_000)
    qt_app.processEvents()

    slider = video_view
    end_thumb = _obj(video_view, "videoTrimEndThumb")
    assert slider.isVisible()
    changes = []
    slider.trimRequested.connect(lambda start, end: changes.append((start, end)))

    original_height = window.height()
    for delta in (-5, 0, 5):
        window.resize(window.width(), original_height + delta)
        slider.setProperty("width", window.width())
        qt_app.processEvents()
        assert window.height() == original_height + delta

        start = end_thumb.mapToScene(
            QPointF(end_thumb.width() / 2, end_thumb.height() / 2)
        ).toPoint()
        target = slider.mapToScene(
            QPointF(slider.width() * 0.70, slider.height() / 2)
        ).toPoint()
        _eger_le(window, start)
        _eger_mozog(window, target)
        _eger_fel(window, target)
        _until(qt_app, lambda: bool(changes), "a vágócsúszka egéreseménye")
        assert changes[-1][0] == -1, changes[-1]
        assert 0 < changes[-1][1] < 5_000, changes[-1]
        changes.clear()


def test_capture_es_movie_belolap_a_fomenu_kattintasaval_es_magyar_forditassal(
    magyar_forditas, qml_app, qt_app
):
    _ = magyar_forditas
    window, _, _ = qml_app
    window.setProperty("selectedIndexes", [0, 1])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()

    capture_button = _obj(window, "toolbarWebcamCaptureButton")
    # A tesztkörnyezet nem köt kamerát, ezért csak a valódi QML-es belépőt
    # engedélyezzük; a panel saját állapota ettől még „nem érhető el”.
    capture_button.setProperty("enabled", True)
    movie_button = _obj(window, "trayMovieButton")

    original_height = window.height()
    try:
        assert _accessible_name(capture_button) == "Rögzítés"
        assert _accessible_name(movie_button) == "Mozgófilmkészítés"
        for delta in (-5, 0, 5):
            window.resize(window.width(), original_height + delta)
            qt_app.processEvents()
            assert window.height() == original_height + delta

            _click(qt_app, window, capture_button)
            _until(
                qt_app,
                lambda: (
                    window.findChild(QObject, "captureMoviePanelPopup") is not None
                    and window.findChild(QObject, "captureMoviePanelPopup").property("visible")
                ),
                "a kamera-rögzítő panel megnyitása",
            )
            capture_popup = _obj(window, "captureMoviePanelPopup")
            _click(qt_app, window, _obj(window, "capturemoviepanelpopup/done"))
            _until(
                qt_app,
                lambda popup=capture_popup: not popup.property("visible"),
                "a kamera-rögzítő panel bezárása",
            )

            _click(qt_app, window, movie_button)
            _until(
                qt_app,
                lambda: (
                    window.findChild(QObject, "movieDialog") is not None
                    and window.findChild(QObject, "movieDialog").property("visible")
                ),
                "a Mozgófilmkészítés megnyitása",
            )
            movie_dialog = _obj(window, "movieDialog")
            _click(qt_app, window, _obj(window, "movieCancelButton"))
            _until(
                qt_app,
                lambda dialog=movie_dialog: not dialog.property("visible"),
                "a Mozgófilmkészítés bezárása",
            )
    finally:
        capture_button.setProperty("enabled", False)
