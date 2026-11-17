"""A lassú thumbnail olvasása nem foghatja meg a rács görgetését (#7086)."""

from __future__ import annotations

import os
import threading
import time
from dataclasses import replace

import pytest
from PySide6.QtCore import QPoint, QPointF, QTimer, Qt, QUrl
from PySide6.QtGui import QGuiApplication, QWheelEvent
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg


_ABLAKMAGASSAG_ELTERESEK = (-5, 0, 5)
_CEL_INDEX = 15
_KEPEK_SZAMA = 24
_KESLELTETES_MP = 1.5

_QML = """
import QtQuick
import QtQuick.Window
import PicasaPy 1.0
import "."

Window {
    id: root
    objectName: "thumbnailScrollWindow"
    visible: false
    width: 360
    height: 240
    property int selectedIndex: -1
    property int menuOpenCount: 0

    GridView {
        id: grid
        objectName: "thumbnailScrollGrid"
        anchors.fill: parent
        cellWidth: 120
        cellHeight: 80
        interactive: true
        model: photoCount
        function wheelStep(delta) {
            contentY = Math.max(0, contentY - delta / 120 * cellHeight)
        }
        delegate: Item {
            id: photoCell
            required property int index
            width: grid.cellWidth
            height: grid.cellHeight
            // A termelési LightboxFeedGroup ugyanígy olvassa a Python
            // PhotoGridModel.itemAt() eredményét a QML-kötésben.
            property var info: photoGridModel
                ? (photoGridModel.revision, photoGridModel.itemAt(index))
                : ({})
            AsyncThumbDelegate {
                anchors.fill: parent
                name: photoCell.info.name || ""
                thumbUrl: photoCell.info.thumbUrl || ""
                star: photoCell.info.star === true
                caption: photoCell.info.caption || ""
                isVideo: photoCell.info.isVideo === true
                index: photoCell.index
                keywords: photoCell.info.keywords || ""
                resolution: photoCell.info.resolution || ""
                onChosen: function(row, modifiers) {
                    root.selectedIndex = row
                }
                onContextMenuRequested: {
                    root.menuOpenCount += 1
                }
            }
        }
        LightboxFeedWheelArea { feed: grid }
    }
}
"""


def _make_library(tmp_path, id_offset):
    from picasapy.index import open_index, photos_in_folder, sync_tree

    library = tmp_path / "library"
    library.mkdir()
    for index in range(_KEPEK_SZAMA):
        make_jpeg(library / f"photo_{index:02d}.jpg", size=(160, 120))

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
        photos = photos_in_folder(conn, library)

    # A Qt pixmap cache process-wide megőrizheti az image:// URL-eket több
    # QML-engine között is; minden ablakmagasság saját provider-ID-t kap.
    photos = tuple(
        replace(photo, id=id_offset + index)
        for index, photo in enumerate(photos)
    )
    return library, photos


def _make_window(qt_app, tmp_path, photos, provider):
    import picasapy.app.application as app_module
    from picasapy.app.photo_grid_model import PhotoGridModel

    thumb_delegate_path = app_module._APP_DIR / "qml" / "PicasaPy" / "ThumbDelegate.qml"
    thumb_delegate_source = thumb_delegate_path.read_text(encoding="utf-8")
    async_binding = 'asynchronous: Qt.platform.pluginName !== "offscreen"'
    assert async_binding in thumb_delegate_source
    thumb_delegate_source = thumb_delegate_source.replace(
        "import QtQuick\n", "import QtQuick\nimport PicasaPy 1.0\n", 1
    ).replace(async_binding, "asynchronous: true", 1)
    thumb_delegate_source = thumb_delegate_source.replace(
        "        PressFeedbackOverlay { pressSource: parent }\n", "", 1
    )
    (tmp_path / "AsyncThumbDelegate.qml").write_text(
        thumb_delegate_source, encoding="utf-8"
    )

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    photo_model = PhotoGridModel()
    photo_model.set_photos(photos)
    engine.rootContext().setContextProperty("photoGridModel", photo_model)
    engine.rootContext().setContextProperty("photoCount", len(photos))
    engine.addImageProvider("thumbs", provider)
    component = QQmlComponent(engine)
    component.setData(
        _QML.encode("utf-8"),
        QUrl.fromLocalFile(str(tmp_path / "thumbnail-scroll-test.qml")),
    )
    window = component.create()
    assert not component.errors(), [error.toString() for error in component.errors()]
    assert window is not None, "a thumbnail görgetőablak nem épült fel"
    QQmlEngine.setObjectOwnership(window, QQmlEngine.ObjectOwnership.CppOwnership)
    window.resize(360, 240)
    window.show()
    QTest.qWait(50)
    assert window.isVisible(), "az ablak nem lett látható"
    return engine, component, window, photo_model


def _wait_until(predicate, timeout_ms=10_000):
    hatarido = time.monotonic() + timeout_ms / 1000
    while not predicate() and time.monotonic() < hatarido:
        QTest.qWait(20)
    return bool(predicate())


def _item_at(grid, index):
    from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QMetaObject

    return QMetaObject.invokeMethod(
        grid,
        "itemAtIndex",
        Qt.ConnectionType.DirectConnection,
        Q_RETURN_ARG(QQuickItem),
        Q_ARG(int, index),
    )


def _walk(item):
    yield item
    for child in item.childItems():
        yield from _walk(child)


def _named_item(parent, name):
    return next((item for item in _walk(parent) if item.objectName() == name), None)


def _send_wheel(window, grid, delta=-120):
    center = grid.mapToScene(QPointF(grid.width() / 2, grid.height() / 2))
    event = QWheelEvent(
        center,
        center,
        QPoint(0, 0),
        QPoint(0, delta),
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
        Qt.ScrollPhase.NoScrollPhase,
        False,
    )
    QGuiApplication.sendEvent(window, event)


def _image_for_delegate(delegate):
    image = _named_item(delegate, "thumbImage")
    assert image is not None, "a ThumbDelegate képe nem található"
    assert image.property("asynchronous") is True, (
        "a regressziós próba nem az aszinkron Image-utat használja"
    )
    return image


@pytest.mark.skipif(os.name != "posix", reason="a lassú fájlolvasó FIFO csak POSIX-on van")
def test_gorgetes_es_gombok_mukodnek_lassu_fajlolvasas_kozben(
    qt_app, tmp_path, monkeypatch
):
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.thumbs import ThumbnailCache
    from picasapy.thumbs import cache, cache_generation

    library, photos = _make_library(tmp_path, 10_000)
    target = photos[_CEL_INDEX]
    target_path = library / target.name
    jpeg_bytes = target_path.read_bytes()
    thumb_cache = ThumbnailCache(tmp_path / "thumbs", size=64)
    for photo in photos:
        if photo.id == target.id:
            continue
        thumb_cache.get_or_create(
            library / photo.name, photo.mtime_ns, photo.size
        )
    target_path.unlink()
    os.mkfifo(target_path)

    provider = ThumbnailProvider(
        thumb_cache, max_threads=2
    )
    provider.register_photos(photos)

    olvasas_elindult = threading.Event()
    kepkesz = threading.Event()
    iro_kesz = threading.Event()
    olvasas_befejezodott = threading.Event()
    olvasas_elengedheto = threading.Event()
    iro_megnyilt = threading.Event()
    olvasasi_idok = {}
    igazi_olvaso = cache.read_image_bytes
    igazi_request = provider.requestImage

    def megfigyelt_request(photo_id, size, requested_size):
        image = igazi_request(photo_id, size, requested_size)
        photo_id = int(str(photo_id).split("?", 1)[0])
        if photo_id == target.id:
            kepkesz.set()
        return image

    monkeypatch.setattr(provider, "requestImage", megfigyelt_request)

    def lassu_olvaso(path):
        if str(path) == str(target_path):
            olvasasi_idok["kezdet"] = time.monotonic()

            def irj_kesobb():
                with open(target_path, "wb") as stream:
                    iro_megnyilt.set()
                    olvasas_elengedheto.wait(timeout=10)
                    stream.write(jpeg_bytes)
                iro_kesz.set()

            threading.Thread(target=irj_kesobb, daemon=True).start()
            olvasas_elindult.set()
        adat = igazi_olvaso(path)
        if str(path) == str(target_path):
            olvasasi_idok["vege"] = time.monotonic()
            olvasas_befejezodott.set()
        return adat

    monkeypatch.setattr(cache, "read_image_bytes", lassu_olvaso)
    monkeypatch.setattr(cache_generation, "read_image_bytes", lassu_olvaso)

    engine, component, window, _photo_model = _make_window(
        qt_app, tmp_path, photos, provider
    )
    timer = None
    try:
        grid = window.findChild(QQuickItem, "thumbnailScrollGrid")
        assert grid is not None, "a görgethető rács nem található"
        assert grid.width() > 0 and grid.height() > 0, (
            "a görgethető rács geometriája nem épült fel"
        )
        ticks = []
        phase = ["a bélyegkép látótérbe görgetése"]
        last_tick = [time.monotonic()]
        timer = QTimer(window)
        timer.setInterval(10)

        def tick():
            now = time.monotonic()
            ticks.append((now - last_tick[0], phase[0]))
            last_tick[0] = now

        timer.timeout.connect(tick)
        timer.start()

        max_scroll_duration = []
        window.setHeight(240 + _ABLAKMAGASSAG_ELTERESEK[0])
        assert window.height() == 240 + _ABLAKMAGASSAG_ELTERESEK[0], (
            "az ablak magasságának módosítása nem érvényesült"
        )
        assert not olvasas_elindult.is_set(), (
            "a célkép a valódi görgetés előtt elkezdett betöltődni"
        )
        row_center_y = (_CEL_INDEX // 3) * 80 + 40
        desired_y = max(0, row_center_y - window.height() * 0.85)
        scroll_count = 0
        while float(grid.property("contentY")) < desired_y - 1:
            before = float(grid.property("contentY"))
            scroll_started = time.monotonic()
            _send_wheel(window, grid)
            duration = time.monotonic() - scroll_started
            max_scroll_duration.append(duration)
            scroll_count += 1
            assert duration < 0.3, f"a görgetőesemény {duration:.3f} s-ig tartott"
            assert float(grid.property("contentY")) > before, (
                "a valódi görgő-esemény nem mozdította el a rácsot"
            )
            assert scroll_count < 30, "a céldelegált nem került a látótérbe"

        phase[0] = "a cél bélyegkép látótérbe görgetése"
        assert _wait_until(olvasas_elindult.is_set), (
            "a görgetés után nem indult el az aszinkron fájlolvasás"
        )
        delegate = _item_at(grid, _CEL_INDEX)
        assert delegate is not None, "a látótérbe görgetett delegált nem épült fel"
        kep = _image_for_delegate(delegate)
        assert not kepkesz.is_set() and not iro_kesz.is_set(), (
            "a lassított fájlolvasás a mérés előtt véget ért"
        )
        assert _wait_until(iro_megnyilt.is_set), "az író nem kapcsolódott a FIFO-hoz"

        frame = _named_item(delegate, "thumbFrame")
        placeholder = _named_item(delegate, "thumbPlaceholder")
        assert frame is not None
        assert placeholder is not None, "betöltés közben nincs helykitöltő"
        assert float(frame.width()) >= float(kep.width()), (
            "a kártya betöltés közben a kép területénél kisebbre zsugorodott"
        )
        assert placeholder.isVisible(), "a betöltés alatti helykitöltő nem látszik"

        ticks.clear()
        last_tick[0] = time.monotonic()
        for stage, window_height_delta in enumerate(_ABLAKMAGASSAG_ELTERESEK, start=1):
            window.setHeight(240 + window_height_delta)
            assert window.height() == 240 + window_height_delta, (
                "az ablak magasságának módosítása nem érvényesült"
            )
            phase[0] = "görgetés a lassú olvasás alatt"
            before = float(grid.property("contentY"))
            scroll_started = time.monotonic()
            _send_wheel(window, grid)
            duration = time.monotonic() - scroll_started
            max_scroll_duration.append(duration)
            assert duration < 0.3, (
                f"a görgetés {duration:.3f} s-ig tartott olvasás közben"
            )
            assert float(grid.property("contentY")) > before, (
                "a görgetés megállt a bélyegkép lassú olvasása alatt"
            )
            center = delegate.mapToScene(
                QPointF(delegate.width() / 2, delegate.height() / 2)
            )
            assert 0 <= center.y() <= window.height(), (
                f"a céldelegált nincs a látótérben: y={center.y()}, "
                f"contentY={grid.property('contentY')}"
            )
            phase[0] = "bal kattintás / kijelölés"
            QTest.mouseClick(
                window,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier,
                center.toPoint(),
            )
            assert int(window.property("selectedIndex")) == _CEL_INDEX, (
                "a kijelölés nem reagált a lassú bélyegkép olvasása alatt"
            )
            phase[0] = "jobb kattintás / helyi menü"
            QTest.mouseClick(
                window,
                Qt.MouseButton.RightButton,
                Qt.KeyboardModifier.NoModifier,
                center.toPoint(),
            )
            assert int(window.property("menuOpenCount")) == (
                stage
            ), (
                "a jobb kattintás nem jutott el a fotó helyi menüjéig"
            )
            scroll_started = time.monotonic()
            _send_wheel(window, grid, delta=120)
            duration = time.monotonic() - scroll_started
            max_scroll_duration.append(duration)
            assert duration < 0.3

        phase[0] = "a fő eseményhurok mérése lassú olvasás alatt"
        maradek_ms = max(
            0,
            round(
                _KESLELTETES_MP * 1000
                - (time.monotonic() - olvasasi_idok["kezdet"]) * 1000
            ),
        )
        assert _wait_until(
            lambda: time.monotonic() - olvasasi_idok["kezdet"] >= _KESLELTETES_MP,
            maradek_ms + 10_000,
        ), "a lassított olvasási idő nem telt le"
        assert not kepkesz.is_set(), "a thumbnail az olvasás felengedése előtt elkészült"
        olvasas_elengedheto.set()
        assert _wait_until(
            lambda: iro_kesz.is_set()
            and olvasas_befejezodott.is_set()
            and kepkesz.is_set(),
            10_000,
        ), "a bélyegkép nem készült el a FIFO olvasás felengedése után"
        assert olvasasi_idok["vege"] - olvasasi_idok["kezdet"] >= _KESLELTETES_MP * 0.8, (
            "a próba nem tartotta nyitva elég sokáig a lassú fájlolvasást"
        )
        assert len(ticks) >= 20, f"az eseményhurok csak {len(ticks)} ütemet kapott"
        max_gap = max(tick[0] for tick in ticks)
        assert max_gap < 0.3, (
            f"a fő eseményhurok {max(ticks, key=lambda tick: tick[0])} s-ra "
            "megállt olvasás közben"
        )
        assert _wait_until(lambda: not placeholder.isVisible()), (
            "a helykitöltő a kész kép fölött maradt"
        )

        timer.stop()
        print(
            "#7086 mért max főszál-szünet: "
            f"{max_gap:.6f} s; görgetések max ideje: "
            f"{max(max_scroll_duration):.6f} s"
        )
    finally:
        olvasas_elengedheto.set()
        if timer is not None:
            timer.stop()
        provider.wait_for_done(1000)
        window.close()
        component.deleteLater()
        engine.deleteLater()
        qt_app.processEvents()
