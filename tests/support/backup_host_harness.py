"""Közös kiszolgáló a mentés-panel (#3504) VALÓDI kattintásos teszteihez.

A `BackupHost` (#3504, a korábbi külön ablakos `BackupDialog` helyett) már
nem `Window`, hanem sima `Item` — a `GiftCdHost` mintájára. A
`QTest.mouseClick` viszont valódi `QWindow`-t kér célul, ezért a hosztot
egy `QQuickView`-ba kell ágyazni (a `collage_canvas_harness._panel`
mintája, #947).
"""

from __future__ import annotations

from PySide6.QtCore import QDeadlineTimer, QEventLoop, QTimer, QUrl
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickView

#: életben tartja a `view`/`komponens` példányokat — enélkül a GC alól
#: kicsúszna a QML-fa, még mielőtt a teszt végigfutna
_KEEPALIVE: list[object] = []


def epits_ablakot(qml_dir, context_props: dict, width: int = 1024,
                   height: int = 250):
    """A `BackupHost` valódi, kirajzolt ablakban.

    `context_props`: a QML gyökér-kontextusnak adandó tulajdonságok
    (pl. `backupController`). Visszaadja a `(view, root)` párt — a
    kattintás célja a `view`, a tulajdonságoké/jelzéseké a `root`.
    """
    view = QQuickView()
    engine = view.engine()
    engine.addImportPath(str(qml_dir))
    for nev, ertek in context_props.items():
        engine.rootContext().setContextProperty(nev, ertek)
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)

    komponens = QQmlComponent(engine)
    komponens.setData(
        b"import QtQuick\nimport PicasaPy 1.0\n"
        b'BackupHost { objectName: "backupHost" }\n',
        QUrl(),
    )
    assert [e.toString() for e in komponens.errors()] == [], (
        komponens.errorString()
    )
    root = komponens.create()
    assert root is not None
    root.setParentItem(view.contentItem())
    view.resize(width, height)
    root.setWidth(width)
    root.setHeight(height)
    view.show()
    assert _var_a_megjelenesre(view), "az ablak nem jelent meg"
    _KEEPALIVE.extend((view, komponens))
    return view, root


def _var_a_megjelenesre(view, ezredmasodperc: int = 5000) -> bool:
    """Megvárja az ablak megjelenését — SAJÁT eseményhurokkal (#947 mintája:
    `QTest.qWaitForWindowExposed` réteges jelenetnél holtpontra futhat)."""
    hurok = QEventLoop()
    hatarido = QDeadlineTimer(ezredmasodperc)
    idozito = QTimer()
    idozito.setInterval(20)

    def figyel():
        if view.isExposed() or hatarido.hasExpired():
            hurok.quit()

    idozito.timeout.connect(figyel)
    idozito.start()
    hurok.exec()
    idozito.stop()
    return view.isExposed()
