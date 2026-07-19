"""QML-funkcionális tesztek: busy-jelzés az alsó kék sávban (#70).

A fény-csík (busySweep) a controller.isWorking-re köt; az animátor csak
látható (busy) állapotban fut, idle-ben a csík el sem látszik. A nézőt és
az image provider valós betöltését nem érintjük (ld. #53).
"""

from PySide6.QtCore import QObject


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


class TestBusySweep:
    def test_sweep_follows_is_working(self, qml_app, qt_app):
        window, controller, _lib, _engine = qml_app
        sweep = _child(window, "busySweep")
        # a fixture alatt indult VALÓS thumbnail-kérések sorban álló
        # jelzéseit előbb leürítjük, különben a kézi emit-ek közé érkeznek
        for _ in range(10):
            qt_app.processEvents()
            if not controller.isWorking:
                break
        # a kézi jelzés azonos szálról direktben fut le — a QML-kötés
        # szinkron frissül, processEvents nélkül ellenőrzünk
        controller._provider.activeCountChanged.emit(1)
        assert controller.isWorking is True
        assert sweep.property("visible") is True
        controller._provider.activeCountChanged.emit(0)
        assert controller.isWorking is False
        assert sweep.property("visible") is False

    def test_sync_job_shows_sweep(self, qml_app, qt_app):
        from PySide6.QtCore import QEventLoop, QTimer

        window, controller, _lib, _engine = qml_app
        sweep = _child(window, "busySweep")
        loop = QEventLoop()
        controller.syncFinished.connect(loop.quit)
        controller.rescan()
        qt_app.processEvents()
        assert sweep.property("visible") is True
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
        qt_app.processEvents()
        assert sweep.property("visible") is False
