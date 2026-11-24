"""#7373 — A javaslatküszöb módosítása után azonnal frissüljenek a javaslatok.

A Beállítások ▸ Névcímkék fülén a Javaslatküszöb csúszka mozgatása és az OK
után a Személyek panel javaslatai azonnal frissülnek (az eredeti 0x005cf5b0
OK-kezelő küszöbváltozás-kapuja).
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
from PySide6.QtCore import QObject, QPointF, QSettings, Qt, Slot
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QSignalSpy, QTest

from picasapy.app.face_scan_controller import FaceScanController
from picasapy.faces.clustering import (
    DEFAULT_SUGGEST_STEP,
    step_to_threshold,
)
from picasapy.index import open_index
from support.varakozas import var_feltetelre

_QML_FILE = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "picasapy"
    / "app"
    / "qml"
    / "PicasaPy"
    / "OptionsDialog.qml"
)


class _DummyController(QObject):
    """Minimális kontroller az OptionsDialog betöltéséhez."""

    @Slot(str, result=bool)
    def fileTypeEnabled(self, _group):
        return True

    @Slot(int, result=int)
    def lastOptionsTab(self, _count):
        return 7

    @Slot(int)
    def saveLastOptionsTab(self, _tab):
        pass

    @Slot()
    def rescan(self):
        pass


def _arc(conn, nev_fajl: str, lenyomat, *, allapot="unnamed", nev=None) -> int:
    conn.execute(
        "INSERT INTO photos (folder_id, name, kind, size, mtime_ns) "
        "VALUES (1, ?, 'image', 0, 0)",
        (nev_fajl,),
    )
    foto = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
    conn.execute(
        "INSERT INTO face (photo_id, rect_left, rect_top, rect_right, "
        "rect_bottom, det_conf, right_eye_x, right_eye_y, left_eye_x, "
        "left_eye_y, nose_x, nose_y, mouth_right_x, mouth_right_y, "
        "mouth_left_x, mouth_left_y, state, person_name, embedding) "
        "VALUES (?, 0.1, 0.1, 0.4, 0.4, 0.9, 0.2, 0.2, 0.3, 0.2, 0.25, 0.3, "
        "0.22, 0.35, 0.28, 0.35, ?, ?, ?)",
        (foto, allapot, nev, np.asarray(lenyomat, dtype=np.float32).tobytes()),
    )
    return conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]


def _kozeli_vektor(alap: np.ndarray, hasonlosag: float) -> np.ndarray:
    meroleges = np.array([0.0, 1.0], dtype=np.float32)
    vektor = hasonlosag * alap + np.sqrt(max(0.0, 1.0 - hasonlosag**2)) * meroleges
    return (vektor / np.linalg.norm(vektor)).astype(np.float32)


def _javaslat_nev(db_path: Path, face_id: int) -> str | None:
    with open_index(db_path) as conn:
        row = conn.execute(
            "SELECT suggested_name FROM face WHERE id = ?", (face_id,)
        ).fetchone()
        return row["suggested_name"] if row else None


@pytest.fixture
def teszt_kornyezet(qt_app, tmp_path):
    """Előkészített adatbázis és vezérlő egy nevesített és egy köztes hasonlóságú arccal."""
    db_path = tmp_path / "index.db"
    settings_path = tmp_path / "settings.ini"

    alap = np.array([1.0, 0.0], dtype=np.float32)
    kuszob_85 = step_to_threshold(DEFAULT_SUGGEST_STEP)
    kuszob_75 = step_to_threshold(75)
    kozepe = (kuszob_85 + kuszob_75) / 2.0

    with open_index(db_path) as conn:
        conn.execute("INSERT INTO folders (path, has_ini) VALUES ('/teszt', 0)")
        _arc(conn, "elek.jpg", alap, allapot="named", nev="Teszt Elek")
        arc_id = _arc(conn, "ketes.jpg", _kozeli_vektor(alap, kozepe))
        conn.commit()

    settings = QSettings(str(settings_path), QSettings.Format.IniFormat)
    ctl = FaceScanController(db_path, settings=settings)
    return ctl, db_path, arc_id, settings


@pytest.fixture
def options_dialog(qt_app, teszt_kornyezet):
    """OptionsDialog.qml betöltése a valódi FaceScanController-rel."""
    from PySide6.QtQml import QQmlComponent, QQmlEngine

    ctl, db_path, arc_id, settings = teszt_kornyezet
    engine = QQmlEngine()
    engine.addImportPath(str(_QML_FILE.parent.parent))
    engine.rootContext().setContextProperty("controller", _DummyController())
    engine.rootContext().setContextProperty("faceScanController", ctl)

    component = QQmlComponent(engine, str(_QML_FILE))
    assert not component.isError(), component.errorString()
    window = component.create()
    assert window is not None

    tab_bar = window.findChild(QQuickItem, "optionsTabBar")
    tab_bar.setProperty("currentIndex", 7)  # Name Tags fül
    window.setProperty("visible", True)
    qt_app.processEvents()

    try:
        yield window, ctl, db_path, arc_id, settings
    finally:
        window.setProperty("visible", False)
        window.deleteLater()
        engine.deleteLater()
        qt_app.processEvents()


def _gyerek(szulo, nev: str):
    elem = szulo.findChild(QQuickItem, nev)
    assert elem is not None, f"Nem található gyerek: {nev}"
    return elem


def _kattints(window, qt_app, elem) -> None:
    assert var_feltetelre(qt_app, lambda: elem.width() > 0 and elem.height() > 0)
    os_ = elem
    while os_ is not None:
        os_.ensurePolished()
        os_ = os_.parentItem()
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2)).toPoint()
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont)
    qt_app.processEvents()


class TestJavaslatkuszobValtozas7373:
    def test_recalculate_suggestions_vezerlo_ujraszamol_es_jelez(self, teszt_kornyezet, qt_app):
        """1. követelmény: a lazított küszöb újraszámolása javaslatot ad és emitál."""
        ctl, db_path, arc_id, settings = teszt_kornyezet
        assert _javaslat_nev(db_path, arc_id) is None

        # 75-re lazítjuk a tárolt lépcsőt
        ctl.setSuggestionThreshold(75)

        spy = QSignalSpy(ctl.unnamedCountChanged)
        # Háttérben induló újraszámolás
        ctl.recalculateSuggestions()
        assert ctl.waitForBackgroundWorkers(5.0), "A háttérszál nem állt le időben"

        assert _javaslat_nev(db_path, arc_id) == "Teszt Elek"
        assert spy.count() >= 1, "unnamedCountChanged nem érkezett meg"

    def test_recalculate_suggestions_tiltott_javaslatoknal_nem_fut(self, teszt_kornyezet):
        """Ha a javaslatok tiltva vannak, a recalculateSuggestions nem végez munkát."""
        ctl, db_path, arc_id, settings = teszt_kornyezet
        ctl.setSuggestionsEnabled(False)
        ctl.setSuggestionThreshold(75)

        spy = QSignalSpy(ctl.unnamedCountChanged)
        ctl.recalculateSuggestions()
        assert ctl.waitForBackgroundWorkers(5.0)

        assert _javaslat_nev(db_path, arc_id) is None
        assert spy.count() == 0

    def test_options_dialog_lazitott_kuszob_ok_utan_frissul(self, options_dialog, qt_app):
        """1. követelmény (felületi): a Beállítások ablakban a csúszka lazítása és OK után
        újratöltődik a javaslat és megérkezik az unnamedCountChanged."""
        window, ctl, db_path, arc_id, settings = options_dialog
        assert _javaslat_nev(db_path, arc_id) is None

        slider = _gyerek(window, "optionsFaceSuggestionThresholdSlider")
        ok_button = _gyerek(window, "optionsOkButton")

        # Állítsuk a csúszkát 75-re és váltsuk ki a moved eseményt
        slider.setProperty("value", 75)
        slider.moved.emit()
        qt_app.processEvents()

        spy = QSignalSpy(ctl.unnamedCountChanged)

        # OK gombra kattintás
        _kattints(window, qt_app, ok_button)
        assert ctl.waitForBackgroundWorkers(5.0), "A háttérszál nem állt le az OK után"

        assert ctl.suggestionThreshold() == 75
        assert _javaslat_nev(db_path, arc_id) == "Teszt Elek"
        assert spy.count() >= 1

    def test_options_dialog_valtozatlan_kuszobnel_nem_szamol_ujra(self, options_dialog, qt_app):
        """2. követelmény: változatlan küszöbnél az OK nem hívja a javaslatokat_ujraszamol-t."""
        window, ctl, db_path, arc_id, settings = options_dialog
        ok_button = _gyerek(window, "optionsOkButton")

        with patch("picasapy.app.face_scan_controller_suggestions_mixin.javaslatokat_ujraszamol") as mock_ujraszamol:
            _kattints(window, qt_app, ok_button)
            ctl.waitForBackgroundWorkers(1.0)
            mock_ujraszamol.assert_not_called()

    def test_options_dialog_csoportkuszob_onmagaban_nem_szamol_ujra(self, options_dialog, qt_app):
        """3. követelmény: a csoportküszöb módosítása önmagában nem indít újraszámolást."""
        window, ctl, db_path, arc_id, settings = options_dialog
        cluster_slider = _gyerek(window, "optionsFaceClusterThresholdSlider")
        ok_button = _gyerek(window, "optionsOkButton")

        # Csak a csoportküszöböt módosítjuk
        cluster_slider.setProperty("value", 75)
        cluster_slider.moved.emit()
        qt_app.processEvents()

        with patch("picasapy.app.face_scan_controller_suggestions_mixin.javaslatokat_ujraszamol") as mock_ujraszamol:
            _kattints(window, qt_app, ok_button)
            ctl.waitForBackgroundWorkers(1.0)
            mock_ujraszamol.assert_not_called()

        assert ctl.clusterThreshold() == 75
        assert ctl.suggestionThreshold() == DEFAULT_SUGGEST_STEP
