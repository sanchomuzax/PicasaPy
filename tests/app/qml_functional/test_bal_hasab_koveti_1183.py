"""A bal hasáb a feedben MUTATOTT kép mappáját jelölje (#1183).

## A tulajdonos jelentése (v0.8.29)

> „A feedben egy index képre állok, a bal hasábban nem kerül kiválasztásra
> a nézett mappa."

## Az eredeti — bizonyíték

`docs/specs/picasa-eger-es-kijeloles.md` 10.2 (utasításszinten, két
kódútból megerősítve): a `CThumbUI` `+0xeac` mezője **a fókuszban lévő
mappa kijelölés-csomópontja**, és a váltó (`0x0056bc10`) pontosan akkor
fut, amikor a fókusz másik mappára kerül:

```asm
0x0056bc3e  call 0x718a50      ; az ELŐZŐ mappa kijelölése teljesen le
0x0056bca4  mov esi, [ebx + 0x3c0]
0x0056bcac  call 0x56b910      ; „a jelenlegi album megváltozott"
0x0056bd43  mov [edi + 0xeac], ebx
0x0056bd8c  call 0x537fb0      ; a helyi menük újraépítése
```

Tehát a **jelenlegi mappa a rács fókuszát követi** — nem fordítva —, és a
váltáskor az előző mappa kijelölése elengedődik (#1145).

## Nálunk mi hiányzott

A `currentFolder` csak a bal hasáb kattintására (`selectFolder`) változott;
a rács fókusza nem mozdította. A bal hasáb ezért a legutóbb KATTINTOTT
mappát emelte ki, nem a nézettet.
"""

from pathlib import Path

from PySide6.QtCore import Q_ARG, QMetaObject, Qt

from support.jpeg_factory import make_jpeg


def _ujraolvas(controller, qt_app) -> None:
    controller.rescan()
    for _ in range(200):
        qt_app.processEvents()
        if controller.waitForBackgroundWorkers(0.05):
            break
    qt_app.processEvents()


def _ket_mappas_feed(qml_app, qt_app):
    window, controller, _ = qml_app
    lib = Path(controller.watchedFolders[0])
    for mappa in ("alma", "korte"):
        (lib / mappa).mkdir(exist_ok=True)
        for i in range(3):
            make_jpeg(lib / mappa / f"{mappa}{i}.jpg", size=(80, 60))
    _ujraolvas(controller, qt_app)
    csoportok = controller.feedGroups
    assert len(csoportok) >= 2
    return window, controller, csoportok


def _kattints(window, index, mods=0):
    QMetaObject.invokeMethod(
        window,
        "handleThumbClick",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", index),
        Q_ARG("QVariant", mods),
    )


def _kijelolt(window):
    ertek = window.property("selectedIndexes")
    if hasattr(ertek, "toVariant"):
        ertek = ertek.toVariant()
    return sorted(int(i) for i in (ertek or []))


class TestBalHasabKoveti:
    def test_masik_mappa_kepere_kattintva_valt_a_mappa(self, qml_app, qt_app):
        """⚠️ A jegy magja: eddig a bal hasáb a régi mappán maradt."""
        window, controller, csoportok = _ket_mappas_feed(qml_app, qt_app)
        elso, masodik = csoportok[0], csoportok[1]
        controller.selectFolder(elso["path"])
        qt_app.processEvents()
        assert controller.currentFolder == elso["path"]

        _kattints(window, int(masodik["start"]))
        qt_app.processEvents()

        assert controller.currentFolder == masodik["path"], (
            "a bal hasáb nem követte a rács fókuszát"
        )

    def test_a_kijeloles_tuleli_a_kovetest(self, qml_app, qt_app):
        """A #1145 mappaváltás-törlése nem viheti el az imént tett
        kijelölést: az előző mappáé szűnik meg, nem az újé."""
        window, controller, csoportok = _ket_mappas_feed(qml_app, qt_app)
        controller.selectFolder(csoportok[0]["path"])
        qt_app.processEvents()
        cel = int(csoportok[1]["start"])

        _kattints(window, cel)
        qt_app.processEvents()

        assert _kijelolt(window) == [cel], "a kijelölés eltűnt a mappaváltással"
        assert window.property("selectedIndex") == cel

    def test_a_mappan_beluli_kattintas_nem_valt(self, qml_app, qt_app):
        """Megőrző: azonos mappán belül nincs se váltás, se törlés."""
        window, controller, csoportok = _ket_mappas_feed(qml_app, qt_app)
        elso = csoportok[0]
        controller.selectFolder(elso["path"])
        qt_app.processEvents()

        _kattints(window, int(elso["start"]))
        qt_app.processEvents()
        _kattints(window, int(elso["start"]) + 1)
        qt_app.processEvents()

        assert controller.currentFolder == elso["path"]
        assert _kijelolt(window) == [int(elso["start"]) + 1]
