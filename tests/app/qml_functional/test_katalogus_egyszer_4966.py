"""#4966: a betűcsalád-katalógust a szerkesztő-panel EGYSZER kapja meg.

A `beginEdit` kibocsátja a `toolsChanged` jelet, amire a néző
`syncPanelFromController` fut. Korábban ez minden szerkesztés-megnyitáskor
újra kiolvasta a `textFontFamilies`-t (~340 elemű lista), pedig az állandó.

A próba a Python-oldali `family_labels()` hívásait számolja: a getter minden
QML-olvasáskor lefut, tehát a szám a tényleges olvasásokat méri, nem egy
belső gyorsítótárat.
"""

from __future__ import annotations

from PySide6.QtCore import QObject

from picasapy.app import edit_controller as edit_controller_module


def test_masodik_szerkesztes_megnyitas_nem_olvassa_ujra_a_betucsaladokat(
    qml_app, qt_app, tmp_path, monkeypatch,
):
    window, _app_controller, engine = qml_app
    window.setProperty("viewerOpen", True)
    viewer = window.findChild(QObject, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    qt_app.processEvents()

    edit = engine.rootContext().contextProperty("editController")
    kep = str(tmp_path / "kepek" / "a.jpg")
    edit.endEdit()
    edit.beginEdit("1", kep)
    qt_app.processEvents()

    olvasasok = []
    eredeti = edit_controller_module.family_labels

    def szamlalo():
        olvasasok.append(1)
        return eredeti()

    monkeypatch.setattr(edit_controller_module, "family_labels", szamlalo)

    edit.endEdit()
    edit.beginEdit("1", kep)
    qt_app.processEvents()

    assert olvasasok == [], (
        f"szerkesztés-megnyitáskor {len(olvasasok)}-szer olvasódott a "
        "betűcsalád-katalógus, pedig állandó"
    )
