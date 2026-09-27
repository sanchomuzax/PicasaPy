"""Közös kiszolgáló a mentés-panel (#3504) VALÓDI kattintásos teszteihez.

A `BackupHost` (#3504, a korábbi külön ablakos `BackupDialog` helyett) már
nem `Window`, hanem sima `Item` — a `GiftCdHost` mintájára. A
`QTest.mouseClick` viszont valódi `QWindow`-t kér célul, ezért a hosztot
egy `QQuickView`-ba kell ágyazni (a `collage_canvas_harness._panel`
mintája, #947).
"""

from __future__ import annotations

from PySide6.QtCore import QDeadlineTimer, QEventLoop, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickView

import picasapy.app.application as _app_module

#: életben tartja a `view`/`komponens` példányokat — enélkül a GC alól
#: kicsúszna a QML-fa, még mielőtt a teszt végigfutna
_KEEPALIVE: list[object] = []


def epits_ablakot(qml_dir, context_props: dict, width: int = 1024):
    """A `BackupHost` valódi, kirajzolt ablakban.

    `context_props`: a QML gyökér-kontextusnak adandó tulajdonságok
    (pl. `backupController`). Visszaadja a `(view, root)` párt — a
    kattintás célja a `view`, a tulajdonságoké/jelzéseké a `root`.

    ⚠️ A gazda MAGASSÁGÁHOZ nem nyúlunk: az a saját kötéséből jön (a mért
    panel + a mappalista sávja), és a nézet ahhoz igazodik. Egy korábbi
    változat `root.setHeight(250)`-nel felülírta a kötést, így a tesztek
    egy nem létező, magasabb panelt néztek — a lelógó gombokat nem látták
    (#3673 átnézése).

    #3696: a `qml_functional/conftest.py` teljes-app kiszolgálója a
    #901/#3279 óta a PicasaStyle-t és a csomagolt Open Sans betűt állítja
    be, MIELŐTT a motor létrejön — enélkül a vezérlők (natív stílus) és a
    feliratok (rendszerbetű) mérete GÉPENKÉNT/PLATFORMONKÉNT más. Ez a
    kiszolgáló ezt kihagyta, és a Windows-láb natív stílusa/betűje a mért
    panelnél csonkolt feliratot, a mentés-párbeszéd lábléc-gombjánál pedig
    a natív stílus nagyobb sormagasságai miatt eltolt kattintási célpontot
    adott (#3696). A sorrend itt is kötött: a motor létrejötte ELŐTT kell
    futnia.
    """
    _app_module.allitsd_be_a_stilust()
    app = QGuiApplication.instance()
    if app is not None:
        _app_module._install_ui_font(app)
    view = QQuickView()
    engine = view.engine()
    engine.addImportPath(str(qml_dir))
    for nev, ertek in context_props.items():
        engine.rootContext().setContextProperty(nev, ertek)

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
    root.setWidth(width)
    view.resize(width, round(root.height()))
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
