"""#1721 — a kézi sorrend a RÁCSON: az ejtés a helyes kép elé rendez.

A húzás indítása a #455 óta megvan (kijelölt képről indul, a „teste" a
`thumbDragProxy`); ez a modul azt méri, hogy az EJTÉS a rácson

1. kiszámolja, MELYIK kép elé kerül a blokk (`ejtesiCelSor`),
2. és a vezérlő `reorderPhotos`-át hívja a kijelöléssel.

A #3053 MÉRÉSE szerint az eredeti a lenyomáskor dönt: kép fölött módosító
nélkül húzás indul, módosítóval csak a kijelölés változik, üres területen
lasszó. A lasszó a mi rácsunkon MŰKÖDŐ funkció — ezért a próbák azt is
kimondják, hogy az ejtési terület nem fogyaszt egéresemenyt (`DropArea`),
tehát a lasszó útja érintetlen.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject

from support.jpeg_factory import make_jpeg


def _kepekkel(qml_app, qt_app, darab=6):
    """`darab` kép egy mappában — a csoport-futam (és vele a lasszó- meg az
    ejtési terület) csak KÉPEKKEL épül fel (a `test_lasszo_1148.py` mintája)."""
    window, controller, _ = qml_app
    lib = Path(controller.watchedFolders[0])
    (lib / "sok").mkdir(exist_ok=True)
    for i in range(darab):
        make_jpeg(lib / "sok" / f"k{i}.jpg", size=(80, 60))
    controller.rescan()
    for _ in range(200):
        qt_app.processEvents()
        if controller.waitForBackgroundWorkers(0.05):
            break
    qt_app.processEvents()
    return window, controller


def _bejar(item):
    """A jelenet ELEM-fája — a `findChild` itt nem elég: a QML-elemek
    gyerekei nem QObject-gyerekek az ablak alatt (a `test_lasszo_1148.py`
    ugyanezért jár be)."""
    for gyerek in item.childItems():
        yield gyerek
        yield from _bejar(gyerek)


def _elem(window, nev):
    for elem in _bejar(window.contentItem()):
        if elem.objectName() == nev:
            return elem
    return None


def _pitch(feed, flow_w: float) -> int:
    """A cella-osztásköz UGYANAZZAL a számítással, amit a lasszó használ
    (#85): az oszlopszám a NÉVLEGES cellaméretből, a bucketelés a
    tényleges, kitöltő szélességből."""
    nevleges = int(feed.property("nominalCellWidth"))
    oszlopok = max(1, int(flow_w // nevleges))
    return max(1, int(flow_w // oszlopok))


def _feed(window) -> QObject:
    feed = window.findChild(QObject, "photoGrid") or _elem(window, "photoGrid")
    assert feed is not None, "a képfolyam nincs a jelenetben"
    return feed


def _hivd(elem, nev, *argok):
    from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QMetaObject, Qt

    args = [Q_ARG("QVariant", a) for a in argok]
    return QMetaObject.invokeMethod(
        elem,
        nev,
        Qt.ConnectionType.DirectConnection,
        Q_RETURN_ARG("QVariant"),
        *args,
    )


class TestAzEjtesiCelSor:
    """A geometria: hányadik kép elé kerül a blokk."""

    def test_az_elso_cella_fole_ejtve_a_csoport_elso_sora(self, qml_app, qt_app):
        window, _c, _e = qml_app
        feed = _feed(window)

        assert _hivd(feed, "ejtesiCelSor", 0, 6, 600, 5, 5) == 0

    def test_a_masodik_cellara_ejtve_a_kovetkezo_sor(self, qml_app, qt_app):
        window, _c, _e = qml_app
        feed = _feed(window)
        assert _hivd(feed, "ejtesiCelSor", 0, 6, 600,
                     _pitch(feed, 600) + 5, 5) == 1

    def test_a_csoport_kezdete_beleszamit(self, qml_app, qt_app):
        """A második mappa-futam sorindexei a `start`-tól nőnek — az ejtés
        ezt nem kerülheti meg, különben más mappába rendezne."""
        window, _c, _e = qml_app
        feed = _feed(window)

        assert _hivd(feed, "ejtesiCelSor", 10, 6, 600, 5, 5) == 10

    def test_az_utolso_cella_utan_a_mappa_vege(self, qml_app, qt_app):
        """A cellákon túlra ejtve `-1` — a vezérlő ezt „a mappa végére"
        jelentésben érti."""
        window, _c, _e = qml_app
        feed = _feed(window)

        assert _hivd(feed, "ejtesiCelSor", 0, 2, 600, 5, 10_000) == -1


class TestAzEjtesiTerulet:
    def test_a_dropArea_a_jelenetben_van(self, qml_app, qt_app):
        window, _controller = _kepekkel(qml_app, qt_app)

        assert _elem(window, "feedReorderDropArea") is not None

    def test_a_lasszo_terulete_megmaradt(self, qml_app, qt_app):
        """A lasszó MŰKÖDŐ funkció — az ejtési terület nem veheti el."""
        window, _controller = _kepekkel(qml_app, qt_app)

        assert _elem(window, "feedFlowLasso") is not None

    def test_a_forrasban_a_DropArea_nem_MouseArea(self):
        """Forrás-őr: egy `MouseArea` elvenné a lasszó lenyomásait; a
        `DropArea` csak húzás-eseményt kap."""
        import picasapy.app

        forras = (
            Path(picasapy.app.__file__).parent
            / "qml"
            / "PicasaPy"
            / "LightboxFeed.qml"
        ).read_text(encoding="utf-8")
        kezd = forras.index('objectName: "feedReorderDropArea"')
        blokk = forras[max(0, kezd - 200):kezd]

        assert "DropArea {" in blokk
        assert "MouseArea" not in blokk


class TestAFotoHuzasSzerzodese:
    """A húzás „teste" és a hasznos teher — az album-ejtéssel KÖZÖS."""

    def test_a_payload_fotokat_jelent(self, qml_app, qt_app):
        window, _controller = _kepekkel(qml_app, qt_app)
        proxy = _elem(window, "thumbDragProxy")

        assert proxy is not None, "a húzás teste nincs a jelenetben"
        assert proxy.property("payload") == "photos"
