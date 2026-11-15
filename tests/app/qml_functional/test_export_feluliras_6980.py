"""A felülírás elutasítása megszakítja az exportot (#6980)."""

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.halasztott_parbeszed import epitsd_fel
from support.qt_wait import varj_feltetelre


def _elem(window, nev):
    epitsd_fel(window, "exportDialog")
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _kattint(window, parbeszed, felirat, qt_app):
    gombok = [
        item
        for item in parbeszed.findChildren(QQuickItem)
        if "Button" in item.metaObject().className()
        and item.property("text") == felirat
        and item.isVisible()
        and item.isEnabled()
        and item.width() > 0
        and item.height() > 0
    ]
    assert gombok, f"A látható {felirat!r} gomb nem található"
    gomb = gombok[-1]
    pont = gomb.mapToScene(QPointF(gomb.width() / 2, gomb.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        pont.toPoint(),
    )
    qt_app.processEvents()


@pytest.mark.parametrize("magassag_elteres", [-5, 0, 5])
def test_nem_megszakit_igen_pedig_exportal(
    qml_app, qt_app, tmp_path, monkeypatch, magassag_elteres
):
    window, _controller, _engine = qml_app
    celmagassag = window.height() + magassag_elteres
    window.resize(window.width(), celmagassag)
    assert varj_feltetelre(qt_app, lambda: window.height() == celmagassag, 3.0)

    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    parbeszed = _elem(window, "exportDialog")

    assert QMetaObject.invokeMethod(
        parbeszed, "openForSelection", Qt.ConnectionType.DirectConnection
    )
    celgyoker = tmp_path / "cel"
    celgyoker.mkdir()
    mappanev = str(_elem(window, "exportFolderNameField").property("text"))
    cel = celgyoker / mappanev
    cel.mkdir()
    regi = cel / "regi.txt"
    regi.write_text("régi tartalom", encoding="utf-8")
    parbeszed.setProperty("targetFolder", celgyoker.as_uri())
    qt_app.processEvents()

    import picasapy.app.export_controller as export_controller

    eredeti_export = export_controller.export_photos
    inditasok = []

    def export_figyelo(*args, **kwargs):
        inditasok.append(True)
        return eredeti_export(*args, **kwargs)

    monkeypatch.setattr(export_controller, "export_photos", export_figyelo)

    _kattint(window, parbeszed, "Export", qt_app)
    feluliras = _elem(window, "exportOverwriteDialog")
    assert varj_feltetelre(qt_app, lambda: feluliras.property("visible"), 3.0)
    _kattint(window, feluliras, "No", qt_app)

    assert varj_feltetelre(
        qt_app, lambda: not feluliras.property("visible"), 3.0
    )
    assert not parbeszed.property("visible"), "a Nem nem a Mégse szerint zárta be az exportot"
    assert inditasok == [], "a Nem válasz exportot indított"
    assert regi.read_text(encoding="utf-8") == "régi tartalom"
    assert list(cel.iterdir()) == [regi], "a Nem válasz új fájlt hozott létre"

    assert QMetaObject.invokeMethod(
        parbeszed, "openForSelection", Qt.ConnectionType.DirectConnection
    )
    parbeszed.setProperty("targetFolder", celgyoker.as_uri())
    qt_app.processEvents()
    _kattint(window, parbeszed, "Export", qt_app)
    assert varj_feltetelre(qt_app, lambda: feluliras.property("visible"), 3.0)
    _kattint(window, feluliras, "Yes", qt_app)

    assert varj_feltetelre(
        qt_app,
        lambda: len(inditasok) == 1
        and not regi.exists()
        and any(path.is_file() for path in cel.iterdir()),
        3.0,
    ), "az Igen nem törölte a korábbi fájlt és nem készített exportot"
