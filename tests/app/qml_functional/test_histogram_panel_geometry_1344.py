"""#1344: a `nerdview` panel MÉRT geometriája, képpontban.

**Az őr egysége.** Minden állítás QML-elrendezési egységben (device-
independent pixel, `devicePixelRatio = 1`) mér, a `HistogramBox` gyökerét
**pontosan 238 × 144-re** kényszerítve — ugyanabban az ablakméretben,
amelyet a `PhotoViewer.qml` ad neki élesben. Ezek NEM betűmérettől függő
számok: a `respack.yt` rétegfejléceiből mért, platformfüggetlen
elrendezési koordináták (ld. `docs/specs/picasa-nerdview-panel.md`).

**A felirat két állítása külön él.** A „nem félkövér" és az „egy sorba
fér" két különböző hiba lehetősége, ezért két külön teszt őrzi őket —
együtt vizsgálva az egyik némán elveszhetne.

A betűmérethez tartozó egyetlen relatív állítás (elfér-e a magyar szöveg
egy sorban) szándékosan nem képpontszámot éget be: a szöveg tényleges
szélességét a futó platform betűjével, `QFontMetricsF`-fel méri.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QUrl
from PySide6.QtGui import QFontMetricsF
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickView
from PySide6.QtTest import QTest

# A magyar felirat (`picasapy_hu.ts`) — az angol forrásnál hosszabb, tehát
# ez a szűk keresztmetszet az egysorosságnál.
MAGYAR_FELIRAT = "Hisztogram és fényképezőgép-adatok"

_KEEPALIVE: list[object] = []


def _panel(qt_app, camera_summary: str = "Gép\t1/125 s") -> QQuickItem:
    """A valódi `HistogramBox` kirajzolva, 238 × 144-es gyökérrel."""
    import picasapy.app.application as app_module

    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    component = QQmlComponent(
        view.engine(),
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "HistogramBox.qml")
        ),
    )
    assert [error.toString() for error in component.errors()] == []

    root = component.createWithInitialProperties(
        {
            "histogramData": {"r": [0.5] * 256, "g": [0.4] * 256, "b": [0.3] * 256},
            "cameraSummary": camera_summary,
        }
    )
    assert root is not None
    root.setWidth(238)
    root.setHeight(144)
    root.setParentItem(view.contentItem())
    view.resize(238, 144)
    view.show()
    assert QTest.qWaitForWindowExposed(view)
    for _ in range(5):
        qt_app.processEvents()
        QTest.qWait(20)

    _KEEPALIVE.extend((view, root, component))
    return root


def _gyerek(root: QQuickItem, name: str) -> QQuickItem:
    """Névre keresett QML-elem, típusellenőrzéssel."""
    item = root.findChild(QObject, name)
    assert isinstance(item, QQuickItem), f"{name} nem található"
    return item


def _vizualis_gyerek(root: QQuickItem, name: str) -> QQuickItem:
    """Névre keresett elem a VIZUÁLIS fában.

    A `Repeater` delegate-jei nem QObject-gyerekei a gyökérnek (a
    `findChild` nem találja meg őket), ezért a `childItems()` fát járjuk
    be — ugyanaz a minta, mint a `test_histogram.py` kétoszlopos tesztjében.
    """

    def _walk(item: QQuickItem) -> QQuickItem | None:
        for child in item.childItems():
            if child.objectName() == name:
                return child
            found = _walk(child)
            if found is not None:
                return found
        return None

    item = _walk(root)
    assert item is not None, f"{name} nem található a vizuális fában"
    return item


def test_a_felirat_nem_felkover(qt_app):
    """A `.tre`-ben SEMMI nem jelöl félkövéret a `nerdview/nvhead`-en."""
    title = _gyerek(_panel(qt_app), "histogramTitle")
    assert title.property("font").bold() is False


def test_a_felirat_egy_sorban_marad(qt_app):
    """Egyetlen sor, tördelés nélkül — a magyar szöveg is elfér benne."""
    title = _gyerek(_panel(qt_app), "histogramTitle")

    # 1. nincs többsoros tördelés engedve (a #235 `maximumLineCount: 2`-je
    #    megdőlt: az eredeti doboz 11 képpont magas, egy sorra)
    assert title.property("lineCount") == 1

    # 2. a kirajzolt szöveg belefér a rendelkezésre álló szélességbe,
    #    tehát nem is vágódik `…`-ra (relatív állítás, nem képpontszám)
    assert title.property("contentWidth") <= title.width()

    # 3. a HOSSZABB magyar fordítás is elfér — a futó platform betűjével mérve
    metrics = QFontMetricsF(title.property("font"))
    assert metrics.horizontalAdvance(MAGYAR_FELIRAT) <= title.width()


def test_a_felirat_helye_es_sormagassaga(qt_app):
    """`static(...): nvhead` — x = 13, y = 4, sormagasság 11 képpont."""
    title = _gyerek(_panel(qt_app), "histogramTitle")
    assert (title.x(), title.y()) == (13, 4)
    assert title.height() == 11


def test_a_hisztogram_rajzterulete_valtozatlan(qt_app):
    """`rect: histoback` — 13, 25-től 213 × 59 (a #864 mérése, ne romoljon)."""
    plot = _gyerek(_panel(qt_app), "histogramPlot")
    assert (plot.x(), plot.y()) == (13, 25)
    assert (plot.width(), plot.height()) == (213, 59)


def test_a_ket_adatoszlop_szelessege_es_rese(qt_app):
    """`text: detail1` 138 széles, `detail2` 69 — 6 képpont réssel."""
    root = _panel(qt_app)
    area = _gyerek(root, "cameraSummaryArea")
    left = _vizualis_gyerek(root, "cameraCellLeft")
    right = _vizualis_gyerek(root, "cameraCellRight")

    # az oszlopok sávja a panel bal szélétől 13-nál kezdődik (13 … 226)
    assert (area.x(), area.y()) == (13, 82)
    assert (area.width(), area.height()) == (213, 41)

    assert left.width() == 138
    assert right.width() == 69
    # a rés: a bal oszlop jobb széle 138, a jobb oszlop x-e 144
    assert right.x() - (left.x() + left.width()) == 6


def test_a_panel_merete_fuggetlen_a_tartalomtol(qt_app):
    """Bőséges EXIF-blokk mellett sem nő a panel, és nem csúszik a tartalom."""
    hosszu = "\n".join(
        f"Nagyon hosszú fényképezőgép-adat sor {i}, ami több sorba törne\tÉrték {i}"
        for i in range(8)
    )
    root = _panel(qt_app, camera_summary=hosszu)

    assert (root.width(), root.height()) == (238, 144)
    plot = _gyerek(root, "histogramPlot")
    title = _gyerek(root, "histogramTitle")
    area = _gyerek(root, "cameraSummaryArea")
    assert (plot.x(), plot.y(), plot.width(), plot.height()) == (13, 25, 213, 59)
    assert (title.x(), title.y()) == (13, 4)
    assert (area.x(), area.y(), area.height()) == (13, 82, 41)
