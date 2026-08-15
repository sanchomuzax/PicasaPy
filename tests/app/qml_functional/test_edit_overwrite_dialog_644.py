"""A külső felülírás figyelmeztetése — felület (#644).

A párbeszéd ÖNÁLLÓAN betöltve. A `visible`-t szándékosan nem vizsgáljuk (az
öröklődik a szülőtől); viselkedést tesztelünk.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

_KEEPALIVE = []


@pytest.fixture
def dialogus(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    engine.rootContext().setContextProperty("controller", None)
    component = QQmlComponent(engine)
    component.setData(
        b"import QtQuick\nimport PicasaPy 1.0\n"
        b'EditOverwriteDialog { objectName: "dlg" }\n',
        QUrl(),
    )
    obj = component.create()
    assert [e.toString() for e in component.errors()] == []
    assert obj is not None
    QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.extend((component, obj, engine))
    yield obj


def _tetelek(dialogus) -> list:
    """A `items` property Python-listaként.

    QML-ből visszakapva `QJSValue`, Pythonból beállítva sima lista — a
    `toVariant()` mindkettőt kezeli. (A projekt QML-tanulsága: a Qt-ből
    visszakapott érték típusa nem magától értetődő.)"""
    ertek = dialogus.property("items")
    if hasattr(ertek, "toVariant"):
        ertek = ertek.toVariant()
    return list(ertek or [])


VESZTESEG = [
    {"path": str(Path("/k/a.jpg")), "name": "a.jpg", "chain": "holga=1;"},
    {"path": "/k/b.jpg", "name": "b.jpg", "chain": "lomo=1;"},
]


class TestMegjelenes:
    def test_a_veszteseg_listat_atveszi(self, dialogus, qt_app) -> None:
        dialogus.show(VESZTESEG)
        qt_app.processEvents()

        assert len(_tetelek(dialogus)) == 2

    def test_ures_listara_nem_nyilik(self, dialogus, qt_app) -> None:
        """Ne ugorjon fel üres párbeszéd, ha nincs mit jelenteni."""
        dialogus.show([])
        qt_app.processEvents()

        assert dialogus.property("opened") is not True

    def test_van_visszaallito_es_bezaro_gomb(self, dialogus) -> None:
        assert dialogus.findChild(QObject, "editOverwriteRestoreButton") is not None
        assert dialogus.findChild(QObject, "editOverwriteCloseButton") is not None

    def test_a_szoveg_kimondja_a_korlatot(self, dialogus) -> None:
        """A jegy 4. teendője: a felhasználót ELŐRE tájékoztatni kell, hogy
        a Picasa írása nyer, amíg a kétirányú átjárás nincs meg (#643)."""
        szoveg = " ".join(
            (t.property("text") or "")
            for t in dialogus.findChildren(QObject)
            if t.property("text") is not None
        )

        assert "Picasa" in szoveg


class TestLezaras:
    def test_a_bezaras_uriti_a_listat(self, dialogus, qt_app) -> None:
        dialogus.show(VESZTESEG)
        qt_app.processEvents()

        dialogus.rejected.emit()
        qt_app.processEvents()

        assert _tetelek(dialogus) == []
