"""#4687: a lassú, hálózati stat nem fagyaszthatja meg az induló felületet."""

from __future__ import annotations

import threading
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQml import QQmlComponent, QQmlEngine

from picasapy.app.startup_diagnostics import StartupProgressLog
from picasapy.app.startup_status import StartupStatus
from picasapy.app.startup_maintenance import (
    StartupMaintenance,
    StartupMaintenanceStep,
)
from picasapy.index import sync as index_sync
from tests.support.varakozas import var_feltetelre


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, feltetel, masodperc)


def test_lassu_stat_alatt_latszik_a_fooldal_es_valtozik_a_splash_felirata(
    qt_app, monkeypatch, tmp_path: Path
) -> None:
    belepett = threading.Event()
    felold = threading.Event()
    dolgozo_szala = []
    eredeti_stat = index_sync._stat

    def lassu_stat(path, *args, **kwargs):
        dolgozo_szala.append(threading.get_ident())
        belepett.set()
        assert felold.wait(3), "a próba nem oldotta fel időben a lassított statot"
        return eredeti_stat(path, *args, **kwargs)

    monkeypatch.setattr(index_sync, "_stat", lassu_stat)

    window = QQuickWindow()
    window.resize(160, 90)
    from picasapy.app import application

    engine = QQmlEngine()
    engine.addImportPath(str(application._APP_DIR / "qml"))
    status = StartupStatus("Loading photo library…", parent=engine)
    feliratok = []
    status.statusTextChanged.connect(lambda: feliratok.append(status.statusText))
    engine.rootContext().setContextProperty("startupStatus", status)
    component = QQmlComponent(engine)
    component.setData(
        b"""
        import QtQuick
        import PicasaPy
        Item {
            width: 160
            height: 90
            property alias renderedStatus: splash.statusText
            SplashScreen {
                id: splash
                anchors.fill: parent
                statusText: startupStatus.statusText
            }
        }
        """,
        QUrl(),
    )
    root = component.create()
    assert root is not None, "a valódi SplashScreen QML nem épült fel"
    root.setParentItem(window.contentItem())
    window.show()

    progress_log = StartupProgressLog()
    naplo = tmp_path / "errorlog.txt"
    progress_log.install(naplo)
    maintenance = StartupMaintenance(progress_log, parent=qt_app)
    maintenance.statusChanged.connect(
        status.report, Qt.ConnectionType.QueuedConnection
    )
    befejezett = []
    maintenance.batchFinished.connect(
        lambda _key: befejezett.append(True), Qt.ConnectionType.QueuedConnection
    )

    try:
        maintenance.enqueue(
            "slow-stat",
            (
                StartupMaintenanceStep(
                    key="slow_stat",
                    name="Mappák ellenőrzése",
                    status_text="Checking folders…",
                    work=lambda: index_sync._stat(tmp_path),
                ),
            )
        )

        assert _varj(qt_app, belepett.is_set), "a lassított stat nem indult el"
        assert window.isVisible(), "a főablak nem maradt látható a lassú stat alatt"
        assert status.statusText == "Checking folders…"
        assert root.property("renderedStatus") == "Checking folders…"
        assert "Checking folders…" in feliratok
        assert dolgozo_szala and dolgozo_szala[0] != threading.get_ident(), (
            "a mappastat a Qt főszálán futott"
        )
    finally:
        felold.set()

    assert _varj(qt_app, lambda: bool(befejezett)), "a háttérlépés nem fejeződött be"
    assert maintenance.waitForBackgroundWorkers(3.0)
    tartalom = naplo.read_text(encoding="utf-8")
    assert "Mappák ellenőrzése elkezdődött" in tartalom
    assert "Mappák ellenőrzése befejeződött" in tartalom
    window.close()
    window.deleteLater()
    engine.deleteLater()
    qt_app.processEvents()
