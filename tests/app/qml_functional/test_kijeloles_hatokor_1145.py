"""A kijelölés hatóköre a JELENLEGI MAPPA, nem a teljes könyvtár (#1145).

## A tulajdonos jelentése (#1184)

> „A »Kiválasztás megfordítása« és az »Összes kép kijelölése« funkció
> tévesen az összes indexképet kiválasztja, nem csak a mappájét, amit
> nézünk."

## Az eredeti — bizonyíték

Az „Az összes kijelölése" parancs (`0x9cb8`) kezelője (`0x005e5070`)
EGYETLEN csomóponton dolgozik:

```asm
0x005e5078  mov edi, [ebx + 0xeac]   ; a JELENLEGI mappa kijelölés-csomópontja
0x005e5084  call 0x716f40            ; „mindent kijelöl" EBBEN a csomópontban
```

A csomópont EGY mappához tartozik (`CSelectionNode + 0x3c0`), és
mappaváltáskor az előzőé TÖRLŐDIK (`0x0056bc10` → `0x718a50`).

⚠️ Vagyis a Picasában **egyáltalán nem létezik mappákon átnyúló
kijelölés** — nálunk viszont a Ctrl+A tízezres nagyságrendű sort jelölt
ki, és ettől „majdnem lefagyott az app".
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


def _ket_mappas_feed(qml_app, qt_app, tmp_path):
    """A `qml_app` könyvtára alá KÉT almappa — így két feed-csoport lesz."""
    window, controller, _ = qml_app
    lib = Path(controller.watchedFolders[0])
    for mappa, darab in (("alma", 2), ("korte", 3)):
        (lib / mappa).mkdir(exist_ok=True)
        for i in range(darab):
            make_jpeg(lib / mappa / f"{mappa}{i}.jpg", size=(80, 60))
    _ujraolvas(controller, qt_app)
    csoportok = controller.feedGroups
    assert len(csoportok) >= 2, f"kevés csoport: {[c['name'] for c in csoportok]}"
    return window, controller, csoportok


def _kijelolt(window) -> list[int]:
    """A `selectedIndexes` PYTHON-listaként.

    ⚠️ A QML-tulajdonság `QJSValue`-ként jön vissza — a nyers
    összehasonlítás (`== []`) mindig hamis lenne, és a teszt a saját
    típushibáját mérné, nem a terméket."""
    ertek = window.property("selectedIndexes")
    if hasattr(ertek, "toVariant"):
        ertek = ertek.toVariant()
    return sorted(int(i) for i in (ertek or []))


def _hivd(window, nev):
    QMetaObject.invokeMethod(window, nev, Qt.ConnectionType.DirectConnection)


def _kattints(window, index, mods=0):
    QMetaObject.invokeMethod(
        window,
        "handleThumbClick",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", index),
        Q_ARG("QVariant", mods),
    )


class TestOsszesKijelolese:
    def test_a_Ctrl_A_CSAK_a_jelenlegi_mappat_jeloli(
        self, qml_app, qt_app, tmp_path
    ):
        """⚠️ A jegy magja: eddig a TELJES feedet jelölte ki."""
        window, _controller, csoportok = _ket_mappas_feed(qml_app, qt_app, tmp_path)
        cel = csoportok[1]
        # a második csoport egyik képére állunk
        _kattints(window, cel["start"])
        qt_app.processEvents()

        _hivd(window, "selectAll")
        qt_app.processEvents()

        kijelolt = _kijelolt(window)
        vart = list(range(cel["start"], cel["start"] + cel["count"]))
        assert kijelolt == vart, (
            f"a kijelölés átnyúlt a mappahatáron: {kijelolt} != {vart}"
        )

    def test_a_megforditas_is_a_jelenlegi_mappara_szukul(
        self, qml_app, qt_app, tmp_path
    ):
        window, _controller, csoportok = _ket_mappas_feed(qml_app, qt_app, tmp_path)
        cel = csoportok[1]
        _kattints(window, cel["start"])
        qt_app.processEvents()

        _hivd(window, "invertSelection")
        qt_app.processEvents()

        kijelolt = _kijelolt(window)
        assert kijelolt, "a megfordítás semmit nem jelölt ki"
        assert all(
            cel["start"] <= i < cel["start"] + cel["count"] for i in kijelolt
        ), f"a megfordítás átnyúlt a mappahatáron: {kijelolt}"


class TestMappavaltas:
    def test_mappavaltaskor_TORLODIK_a_kijeloles(self, qml_app, qt_app, tmp_path):
        """Az eredetiben az előző mappa csomópontja törlődik (`0x0056bc10`)."""
        window, controller, csoportok = _ket_mappas_feed(qml_app, qt_app, tmp_path)
        _kattints(window, csoportok[1]["start"])
        _hivd(window, "selectAll")
        qt_app.processEvents()
        assert _kijelolt(window), "nem sikerült kijelölni"

        controller.selectFolder(csoportok[0]["path"])
        qt_app.processEvents()

        assert _kijelolt(window) == [], (
            "a kijelölés túlélte a mappaváltást"
        )
