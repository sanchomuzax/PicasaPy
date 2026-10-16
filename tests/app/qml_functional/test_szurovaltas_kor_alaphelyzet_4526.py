"""#4526 — a szűrősáv kattintásra egyetlen aktív szűrőt jelez.

A négy gombot valódi egérkattintással váltjuk egymás után. A kor-szűrő
felirata és fogantyúja nézetváltáskor, mappaváltáskor és a „Back to View All”
gombbal is visszaáll.
"""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree
from tests.support.jpeg_factory import make_jpeg


def _item(window, object_name: str) -> QQuickItem:
    item = window.findChild(QQuickItem, object_name)
    assert item is not None, f"a(z) {object_name} QML-elem nem található"
    return item


def _kattintas(window, item: QQuickItem, qt_app) -> None:
    """Valódi kattintás a felépült QML-elem aktuális közepére."""
    point = item.mapToScene(
        QPointF(float(item.width()) / 2, float(item.height()) / 2)
    )
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )
    qt_app.processEvents()


def _allapotok(window) -> dict[str, bool]:
    return {
        "starred": bool(_item(window, "starFilterButton").property("ctlFilterActive")),
        "faces": bool(_item(window, "faceFilter").property("aktiv")),
        "videos": bool(_item(window, "movieFilter").property("aktiv")),
        "geo": bool(_item(window, "geoFilter").property("aktiv")),
    }


def _view_all_gomb(window) -> QQuickItem:
    """A felirat szülőjét adja, amelyen a TapHandler ténylegesen ül."""

    def bejar(item):
        for child in item.childItems():
            yield child
            yield from bejar(child)

    felirat = next(
        (
            item
            for item in bejar(window.contentItem())
            if item.property("text") == "Back to View All"
        ),
        None,
    )
    assert felirat is not None, "a „Back to View All” felirat nem látható"
    return felirat.parentItem()


def _kor_szurese(controller, slider, qt_app) -> None:
    slider.setProperty("value", 0.5)
    assert QMetaObject.invokeMethod(
        slider, "moved", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()
    assert controller.viewModeName == "age"
    assert controller.ageFilterText


def test_szurovaltas_es_kor_alaphelyzet_minden_ablakmagassagon(
    qml_app, qt_app, tmp_path
):
    window, controller, _engine = qml_app
    assert controller.photos.photos

    # A geo-gomb csak meglévő helyjelölő mellett kattintható. A teszt a
    # saját ideiglenes könyvtárában ad helyet az egyik képnek.
    controller.setGeotagRows([0], 47.4979, 19.0402)
    assert controller.geoMarkerCount > 0

    masik_mappa = tmp_path / "kepek" / "masik"
    masik_mappa.mkdir()
    make_jpeg(masik_mappa / "c.jpg", size=(80, 60))
    with open_index(controller._db_path) as conn:
        sync_tree(conn, masik_mappa)

    slider = _item(window, "dateRangeFilterSlider")
    failures: list[str] = []
    alap_magassag = int(window.height())

    # A helyi ablakmagasság körüli két eltérés mellett is a vezérlők
    # tényleges, aktuális scene-koordinátájából kattintunk.
    for delta in (-5, 0, 5):
        window.resize(int(window.width()), alap_magassag + delta)
        qt_app.processEvents()
        assert int(window.height()) == alap_magassag + delta

        for object_name, mode in (
            ("starFilterButton", "starred"),
            ("faceFilter", "faces"),
            ("movieFilter", "videos"),
            ("geoFilter", "geo"),
            # A csillag másik aktív szűrőről is váltson át, ne kapcsoljon ki.
            ("starFilterButton", "starred"),
        ):
            _kattintas(window, _item(window, object_name), qt_app)
            if controller.viewModeName != mode:
                failures.append(
                    f"{object_name} kattintása után {controller.viewModeName!r}, "
                    f"nem {mode!r} nézet aktív (ablakmagasság-eltérés: {delta}px)"
                )
            vart = {name: name == mode for name in _allapotok(window)}
            tenyleges = _allapotok(window)
            if tenyleges != vart:
                failures.append(
                    f"nem csak a {mode!r} gomb aktív: {tenyleges!r} "
                    f"(ablakmagasság-eltérés: {delta}px)"
                )
            if mode == "geo":
                hatter = _item(window, "geoFilterBackground").property("color")
                if hatter.name().lower() != "#4e9258":
                    failures.append(
                        f"a hely-gomb aktív háttere nem zöld: {hatter.name()} "
                        f"(ablakmagasság-eltérés: {delta}px)"
                    )

        _kor_szurese(controller, slider, qt_app)
        _kattintas(window, _item(window, "faceFilter"), qt_app)
        if controller.ageFilterText:
            failures.append(
                f"a kor-felirat szűrőváltás után is megmaradt ({delta}px)"
            )
        if float(slider.property("value")) != 0.0:
            failures.append(
                f"a kor-csúszka szűrőváltás után {slider.property('value')!r} "
                f"értéken maradt ({delta}px)"
            )

        _kor_szurese(controller, slider, qt_app)
        controller.selectFolder(str(masik_mappa))
        qt_app.processEvents()
        if controller.viewModeName != "folder" or controller.ageFilterText:
            failures.append(
                f"mappaváltás után nem alaphelyzetű a kor-szűrő ({delta}px)"
            )
        if float(slider.property("value")) != 0.0:
            failures.append(
                f"a kor-csúszka mappaváltás után {slider.property('value')!r} "
                f"értéken maradt ({delta}px)"
            )

        _kor_szurese(controller, slider, qt_app)
        _kattintas(window, _view_all_gomb(window), qt_app)
        if controller.viewModeName != "folder" or controller.ageFilterText:
            failures.append(
                f"Back to View All után nem alaphelyzetű a kor-szűrő ({delta}px)"
            )
        if float(slider.property("value")) != 0.0:
            failures.append(
                f"a kor-csúszka Back to View All után "
                f"{slider.property('value')!r} értéken maradt ({delta}px)"
            )

    assert not failures, "\n".join(failures)
