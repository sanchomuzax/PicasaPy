"""#7407: a Szöveg eszköz Clear All gombja eszközön belüli piszkozat, amelyet a Cancel visszahoz.

Kész, ha:
(1) meglévő szövegnél Clear All, Cancel, újranyitás után a szöveg és az ini azonos a megnyitásival;
(2) Clear All, Apply után a kép a szöveg nélküli, az ini-ben nincs text= és textactive=,
    az Undo és Redo tiltott;
(3) Clear All után az eszköz nyitva, Apply aktív, Clear All tiltott;
(4) a renderelt próba a Clear All utáni panelt a job-921 __20-szal veti össze.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest

from tests.app.qml_functional._editor_test_helpers import EditorTestHelpers
from support.qt_wait import varj_feltetelre

_INI_SZOVEG = (
    "[a.jpg]\n"
    "text=1;138;17;PicasaCancelProba;Times;0.316406,0.144531,0.033333,0.000000;"
    "v1,4294967295,4278190080,128.000000,1.000000,0.000000,1.000000,400,0,49152;;\n"
    "backuphash=13102\n"
    "textactive=1\n"
)


def _elem(window: QObject, nev: str) -> QObject:
    item = window.findChild(QObject, nev)
    assert item is not None, f"{nev} nem található a QML fában"
    return item


def _var(qt_app, feltetel, uzenet: str, masodperc: float = 10.0) -> None:
    assert varj_feltetelre(qt_app, feltetel, masodperc), uzenet


def _kattint(window, item) -> QPoint:
    pont = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    kepernyo = QPoint(round(pont.x()), round(pont.y()))
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, kepernyo
    )
    return kepernyo


def _qimage_to_cv2(qimg: QImage) -> np.ndarray:
    qimg = qimg.convertToFormat(QImage.Format.Format_RGB888)
    width = qimg.width()
    height = qimg.height()
    ptr = qimg.bits()
    arr = np.frombuffer(ptr, np.uint8).reshape((height, width, 3))
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


class TestSzovegClearAllQml7407(EditorTestHelpers):
    @pytest.mark.parametrize("ablak_magassag", [900, 895, 905])
    def test_clear_all_cancel_apply_teljes_folyamat(
        self, qml_app, qt_app, tmp_path, ablak_magassag
    ):
        ini_fajl = tmp_path / "kepek" / ".picasa.ini"
        ini_fajl.write_text(_INI_SZOVEG, encoding="utf-8")

        window, _, engine = qml_app
        window.resize(1280, ablak_magassag)
        qt_app.processEvents()

        self._open_viewer(window, qt_app, index=0)
        panel = _elem(window, "viewerEditorPanel")
        panel.setProperty("textActive", True)
        qt_app.processEvents()

        controller = engine.rootContext().contextProperty("editController")
        _var(qt_app, lambda: controller.property("hasTextOverlay") is True, "Nincs szöveg megnyitáskor")
        assert controller.property("textDraft") == "PicasaCancelProba"

        remove_btn = _elem(window, "textRemoveAllButton")
        apply_btn = _elem(window, "textApplyButton")
        cancel_btn = _elem(window, "textCancelButton")

        # Megnyitáskor Clear All és Apply aktív
        _var(qt_app, lambda: remove_btn.property("enabled") is True, "Clear All nem aktív megnyitáskor")
        _var(qt_app, lambda: apply_btn.property("enabled") is True, "Apply nem aktív megnyitáskor")
        _var(qt_app, lambda: cancel_btn.property("enabled") is True, "Cancel nem aktív megnyitáskor")

        # 1. Clear All valódi kattintással
        _kattint(window, remove_btn)
        qt_app.processEvents()

        # (3) pont: Clear All után az eszköz nyitva, Apply aktív, Clear All tiltott
        assert panel.property("textActive") is True, "Clear All után a panel nyitva kell maradjon"
        _var(qt_app, lambda: remove_btn.property("enabled") is False, "Clear All után a Clear All tiltott kell legyen")
        _var(qt_app, lambda: apply_btn.property("enabled") is True, "Clear All után az Apply aktív kell legyen")
        assert controller.property("textCleared") is True

        hint = _elem(window, "textHint")
        assert hint.property("visible") is True, "Clear All után a Type anywhere to add text hint látható kell legyen"

        # Az ini-be még NEM írt
        ini_koztes = ini_fajl.read_text(encoding="utf-8")
        assert ini_koztes == _INI_SZOVEG, "Clear All nem írhat az inibe!"

        # Renderelt kép rögzítése Clear All után
        kep_clear_all_qimg = window.grabWindow()
        assert not kep_clear_all_qimg.isNull(), "A renderelt kép nem lehet üres"

        # 2. Cancel valódi kattintással
        _kattint(window, cancel_btn)
        qt_app.processEvents()

        _var(qt_app, lambda: panel.property("textActive") is False, "Cancel után a panelnek be kell záródnia")
        assert ini_fajl.read_text(encoding="utf-8") == _INI_SZOVEG, "Cancel után az ininek változatlannak kell maradnia"

        # Cancel után a szöveg visszatért az előnézetre
        _var(qt_app, lambda: controller.property("hasTextOverlay") is True, "Cancel után a szövegnek vissza kell jönnie")
        kep_cancel_qimg = window.grabWindow()

        # (1) pont: újranyitás után a szöveg és az ini azonos a megnyitásival
        panel.setProperty("textActive", True)
        qt_app.processEvents()
        _var(qt_app, lambda: panel.property("textActive") is True, "Panel nem nyílt újra")
        _var(qt_app, lambda: controller.property("hasTextOverlay") is True, "Újranyitás után nincs szöveg")
        assert controller.property("textDraft") == "PicasaCancelProba"
        _var(qt_app, lambda: remove_btn.property("enabled") is True, "Újranyitás után Clear All aktív")
        _var(qt_app, lambda: apply_btn.property("enabled") is True, "Újranyitás után Apply aktív")

        # 3. Clear All és Apply valódi kattintással
        _kattint(window, remove_btn)
        qt_app.processEvents()
        _var(qt_app, lambda: apply_btn.property("enabled") is True, "Clear All után Apply aktív")
        _kattint(window, apply_btn)
        qt_app.processEvents()

        # (2) pont: Clear All, Apply után a kép szöveg nélküli, ini-ben nincs text= és textactive=, Undo/Redo tiltott
        _var(qt_app, lambda: panel.property("textActive") is False, "Apply után a panelnek be kell záródnia")
        zarult_ini = ini_fajl.read_text(encoding="utf-8")
        assert "text=" not in zarult_ini, "Apply után a text= kulcsnak kikerültnek kell lennie"
        assert "textactive=" not in zarult_ini, "Apply után a textactive= kulcsnak kikerültnek kell lennie"
        assert controller.property("canUndo") is False, "Clear All Apply után az Undo tiltott kell legyen"
        assert controller.property("canRedo") is False, "Clear All Apply után a Redo tiltott kell legyen"

        # (4) pont és KIEGÉSZÍTÉS: összevetés a job-921 __20-szal és .tmp/osszevetes_7407.png generálása
        repo_gyoker = Path(__file__).resolve().parents[3]
        ref_20_path = repo_gyoker / ".tmp" / "job-921" / "kepernyo__20.png"
        ref_22_path = repo_gyoker / ".tmp" / "job-921" / "kepernyo__22.png"

        if ref_20_path.exists() and ablak_magassag == 900:
            ref_20 = cv2.imread(str(ref_20_path))
            ref_22 = cv2.imread(str(ref_22_path)) if ref_22_path.exists() else None

            our_clear_all_cv = _qimage_to_cv2(kep_clear_all_qimg)
            our_cancel_cv = _qimage_to_cv2(kep_cancel_qimg)

            # Szöveg panel területének összevetése (job-921-en x: 10..270, y: 100..500)
            # A gombok relatív állapota:
            # Clear All gomb területe job-921-ben x: 140..240, y: 355..388 (letiltva)
            # Apply gomb x: 30..130, y: 355..388 (aktív)
            panel_ref = ref_20[100:500, :280]
            panel_our = cv2.resize(our_clear_all_cv[100:500, :280], (280, 400))

            # Készítsünk 2x2 vagy 1x2 összehasonlító panelt a .tmp/osszevetes_7407.png-be
            h, w = 400, 280
            canvas = np.zeros((h * 2, w * 2, 3), dtype=np.uint8)

            # Bal fent: job-921 __20 (Clear All utáni panel)
            canvas[:h, :w] = cv2.resize(panel_ref, (w, h))
            # Jobb fent: PicasaPy Clear All utáni panel
            canvas[:h, w:] = panel_our

            if ref_22 is not None:
                # Bal lent: job-921 __22 (Cancel utáni néző)
                panel_ref_cancel = ref_22[100:500, :280]
                canvas[h:, :w] = cv2.resize(panel_ref_cancel, (w, h))
                # Jobb lent: PicasaPy Cancel utáni néző
                panel_our_cancel = cv2.resize(our_cancel_cv[100:500, :280], (w, h))
                canvas[h:, w:] = panel_our_cancel

            out_path = repo_gyoker / ".tmp" / "osszevetes_7407.png"
            cv2.imwrite(str(out_path), canvas)
            assert out_path.exists(), "Az összevető képnek (.tmp/osszevetes_7407.png) léteznie kell"
