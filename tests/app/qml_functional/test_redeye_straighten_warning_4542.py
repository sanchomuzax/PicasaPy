"""#4542: a Vörösszem panel a kiegyenesített képen figyelmeztet."""

from __future__ import annotations

import time

from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest


def _varj(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.05)
    qt_app.processEvents()
    return bool(feltetel())


def _kattints(window, elem, qt_app) -> None:
    assert elem.width() > 0 and elem.height() > 0, "a Vörösszem csempe nem látható"
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    qt_app.processEvents()


def test_redeye_figyelmeztetese_kattintas_utan_a_kiegyenesitestol_fugg(
    qml_app, qt_app, tmp_path
):
    window, _controller, engine = qml_app
    alapmagassag = window.height()
    ini = tmp_path / "kepek" / ".picasa.ini"
    ini.write_text(
        "[a.jpg]\nfilters=tilt=1,0.250000,0.000000;\n[b.jpg]\n",
        encoding="utf-8",
    )

    window.setHeight(alapmagassag - 5)
    assert _varj(qt_app, lambda: window.height() == alapmagassag - 5)
    window.setProperty("viewerOpen", True)
    viewer = window.findChild(QObject, "photoViewer")
    assert viewer is not None
    viewer.setProperty("currentIndex", 0)
    edit = engine.rootContext().contextProperty("editController")
    assert _varj(qt_app, lambda: edit.property("tiltParam") == 0.25)

    panel = window.findChild(QObject, "viewerEditorPanel")
    csempe = window.findChild(QObject, "editToolRedeyeIcon")
    figyelmeztetes = window.findChild(QObject, "redeyeStraightenWarning")
    assert panel is not None and csempe is not None
    assert figyelmeztetes is not None, "a vörösszem-panel figyelmeztetése hiányzik"

    _kattints(window, csempe, qt_app)
    assert _varj(qt_app, lambda: panel.property("redeyeActive"))
    assert _varj(qt_app, lambda: figyelmeztetes.property("visible")), (
        "kiegyenesített képen a vörösszem-panel nem figyelmeztet"
    )
    assert figyelmeztetes.property("text") == (
        "This image's orientation has been modified by the Straighten tool, "
        "which can cause inaccuracies when selecting red eye  rectangles.\n"
        "If your redeye fixes appear to be misaligned (or non-existent), try "
        "undoing the Straighten fix, then reapply red eye fixes, and "
        "Straighten again if necessary."
    )

    window.setHeight(alapmagassag + 5)
    assert _varj(qt_app, lambda: window.height() == alapmagassag + 5)
    viewer.setProperty("currentIndex", 1)
    assert _varj(qt_app, lambda: edit.property("tiltParam") == 0)
    assert _varj(qt_app, lambda: not figyelmeztetes.property("visible")), (
        "kiegyenesítetlen képen is látható maradt a vörösszem-figyelmeztetés"
    )
