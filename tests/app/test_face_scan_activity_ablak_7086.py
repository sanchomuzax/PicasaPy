"""Az arckeresés aktivitásfigyelője csak az ablakok eseményeit nézze (#7086).

Az alkalmazás egészére telepített Python-eseményszűrő minden Qt-eseménynél
(időzítő, metahívás, képválasz, frissítés) Python-kódot futtatott; a valódi
programban görgetéskor mérve másodpercenként 1300-1700 hívás. Mindegyikhez a
GIL kell, és amíg a bélyegkép-szálak dolgoztak, a fő szál eseményenként sorban
állt: hálózati mappán görgetve a felület lefagyott. A bevitel (egér, billentyű,
görgő) mindig az ablakhoz érkezik, ezért elég az ablakokat figyelni.
"""

from __future__ import annotations

from PySide6.QtCore import QCoreApplication, QEvent, QObject, Qt
from PySide6.QtGui import QKeyEvent, QWindow


class _Engine:
    def rootObjects(self):
        return []


def _billentyu() -> QKeyEvent:
    return QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_A, Qt.KeyboardModifier.NoModifier, "a")


def test_az_ablakra_erkezo_bevitel_szunetelteti_az_arckeresest(qt_app):
    from picasapy.app.face_scan_activity import FaceScanActivityMonitor

    ablak = QWindow()
    ablak.create()
    now = [100.0]
    monitor = FaceScanActivityMonitor(qt_app, _Engine(), clock=lambda: now[0])
    try:
        monitor._ablakok_figyelese()
        assert not monitor.should_pause()
        QCoreApplication.sendEvent(ablak, _billentyu())
        assert monitor.should_pause(), "az ablakra érkező billentyű nem jutott el a figyelőhöz"
        now[0] += 31.0
        assert not monitor.should_pause()
    finally:
        monitor.stop()
        ablak.destroy()


def test_nem_ablak_objektum_esemenye_nem_megy_at_a_python_szuron(qt_app):
    from picasapy.app.face_scan_activity import FaceScanActivityMonitor

    hivasok = [0]

    class _Szamlalo(FaceScanActivityMonitor):
        def eventFilter(self, watched, event):  # noqa: N802
            hivasok[0] += 1
            return super().eventFilter(watched, event)

    monitor = _Szamlalo(qt_app, _Engine(), clock=lambda: 100.0)
    try:
        cel = QObject()
        for _ in range(20):
            QCoreApplication.sendEvent(cel, QEvent(QEvent.Type.User))
        QCoreApplication.sendEvent(cel, _billentyu())
        assert hivasok[0] == 0, (
            f"{hivasok[0]} nem-ablak eseményt kapott a Python-szűrő: "
            "az egész alkalmazásra van telepítve"
        )
    finally:
        monitor.stop()
