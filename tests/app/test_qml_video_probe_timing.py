"""A QTest egér-időbélyegeit használó videópróba-gesztusok (#4674)."""

import importlib.util
from pathlib import Path

from PySide6.QtCore import QPoint, Qt


_PROBE_UT = Path(__file__).with_name("qml_video_probe.py")
_SPEC = importlib.util.spec_from_file_location("qml_video_probe_timing", _PROBE_UT)
assert _SPEC is not None and _SPEC.loader is not None
_PROBE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_PROBE)


def test_az_elozo_kattintas_utan_a_qtest_idobelye_valasztja_el_a_kovetkezot():
    class QTestRecorder:
        def __init__(self):
            self.esemenyek = []

        def mouseClick(self, window, button, *, pos, delay):
            self.esemenyek.append(("click", window, button, pos, delay))

        def mouseDClick(self, window, button, *, pos, delay):
            self.esemenyek.append(("double-click", window, button, pos, delay))

        def mouseMove(self, window, pos, *, delay):
            self.esemenyek.append(("move", window, pos, delay))

    qtest = QTestRecorder()
    window = object()
    point = QPoint(40, 50)
    button = Qt.MouseButton.LeftButton
    interval_ms = 400

    _PROBE.qtest_egerlepes(
        qtest,
        window,
        point,
        button,
        interval_ms,
        dupla=False,
        elozo_gesztus_volt=False,
    )
    _PROBE.qtest_egerlepes(
        qtest,
        window,
        point,
        button,
        interval_ms,
        dupla=True,
        elozo_gesztus_volt=True,
    )

    assert qtest.esemenyek == [
        ("click", window, button, point, 10),
        ("move", window, point + QPoint(1, 0), interval_ms + 1),
        ("click", window, button, point, 10),
        ("click", window, button, point, 10),
    ]
