"""A teljes gyűjteménysor görbehelye és folyamatos léptetése (#6595)."""

from pathlib import Path
import time

import piexif

from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtGui import QColor
from PySide6.QtTest import QTest
import pytest

from picasapy.timeline_motion import CARD_STEP
from support.jpeg_factory import make_minta_jpeg
from support.varakozas import var_feltetelre
from tests.app.qml_functional.conftest import _build_qml_app


_EVEK = tuple(range(2008, 2027))[::1][:14]


def _make_dated_collections(root: Path) -> None:
    """Szintetikus, múltbeli dátumú gyűjtemények (tulajdonosi kérés, #6595).

    Tizennégy mappa 2008-tól évente, mappánként három eltérő színű és
    mintázatú kép EXIF-felvételi dátummal, hogy a kötegek és a háttérváltás
    megkülönböztethető legyen. Kész kép nem kerül a repóba.
    """
    for index, ev in enumerate(_EVEK):
        folder = root / f"Kirandulas {ev}"
        folder.mkdir()
        for kep in range(3):
            path = folder / f"kep-{ev}-{kep}.jpg"
            make_minta_jpeg(path, size=(320, 240), seed=17 * index + 5 * kep + 3)
            datum = f"{ev}:{index % 12 + 1:02d}:{10 + kep:02d} 12:00:00"
            piexif.insert(
                piexif.dump({"Exif": {piexif.ExifIFD.DateTimeOriginal: datum}}),
                str(path),
            )


@pytest.fixture
def qml_app_carousel_6595(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_make_dated_collections,
        belyegkep_meret=256,
        valodi_belyegkep=True,
    )


def _child(parent, name):
    child = parent.findChild(QObject, name)
    assert child is not None, f"{name} nem található"
    return child


def _visual_child(parent, name):
    if parent.objectName() == name:
        return parent
    for child in parent.childItems():
        found = _visual_child(child, name)
        if found is not None:
            return found
    return None


def _wait(qt_app, predicate, message, seconds=10.0):
    assert var_feltetelre(qt_app, predicate, seconds), message


def _open_carousel(qml_app_carousel_6595, qt_app, height):
    window, _controller, engine = qml_app_carousel_6595
    window.setProperty("selectedIndexes", [])
    window.requestActivate()
    _wait(qt_app, window.isActive, "a főablak nem lett aktív")
    QTest.keyClick(window, Qt.Key.Key_5, Qt.KeyboardModifier.ControlModifier)
    _wait(
        qt_app,
        lambda: window.property("timelineOpen") is True,
        "a Ctrl+5 nem nyitotta meg az Időrendet",
    )
    timeline = _child(window, "timelineView")
    _wait(qt_app, timeline.isVisible, "az Időrendablak nem látszik")
    timeline.requestActivate()
    _wait(qt_app, timeline.isActive, "az Időrend nem kapott fókuszt")
    timeline.setProperty("visibility", timeline.property("windowedVisibility"))
    timeline.resize(1280, height)
    _wait(qt_app, lambda: timeline.width() == 1280, "az ablak szélessége nem állt be")
    _wait(qt_app, lambda: timeline.height() == height, "az ablakmagasság nem állt be")

    controller = engine.rootContext().contextProperty("timelineController")
    source = [
        dict(item) for item in controller.collections
        if str(item.get("name", "")).startswith("Kirandulas")
    ]
    assert len(source) >= 12, [item.get("name") for item in controller.collections]
    collections = []
    for index in range(12):
        collection = dict(source[index])
        collection.update(
            collectionId=f"fixture:{index}",
            name=f"Collection {index:02d}",
            dateLabel=f"Date {index:02d}",
            sliderPosition=index / 11,
            photos=[dict(photo) for photo in source[index]["photos"]],
        )
        collections.append(collection)
    timeline.setProperty("collectionsModel", collections)
    timeline.setProperty("currentIndex", 0)
    timeline.setProperty("carouselOffset", controller.focusParameter())
    if not var_feltetelre(
        qt_app,
        lambda: _visual_child(
            _child(timeline, "timelinePanel"), "timelineCarouselCard11"
        ) is not None,
        10.0,
    ):
        raise AssertionError("nem épült fel mind a 12 gyűjteményköteg")
    return timeline, controller, collections


@pytest.mark.parametrize("height", [795, 800, 805])
def test_fullscreen_scaled_carousel_renders_twelve_cards_and_moves_smoothly(
    qml_app_carousel_6595, qt_app, height
):
    timeline, controller, _collections = _open_carousel(
        qml_app_carousel_6595, qt_app, height
    )
    panel = _child(timeline, "timelinePanel")
    focus = controller.focusParameter()
    layout = controller.carouselLayout(focus, 12)

    assert abs(panel.property("width") - 480 * 1280 / height) <= 0.01
    assert panel.property("height") == 480
    assert abs(panel.property("scale") - height / 480) <= 0.001
    top_left = panel.mapToItem(timeline.contentItem(), QPointF(0, 0))
    assert abs(top_left.x()) <= 3
    assert abs(top_left.y()) <= 3
    _wait(
        qt_app,
        lambda: timeline.property("currentCardsLoaded"),
        "a fókuszban levő köteg bélyegképei nem töltődtek be",
    )

    for index, item in enumerate(layout):
        card = _visual_child(panel, f"timelineCarouselCard{index}")
        assert card is not None, f"timelineCarouselCard{index} nem látható a vizuális fában"
        assert card.property("visible") is item["visible"]
        actual_center = card.mapToItem(
            timeline.contentItem(),
            QPointF(card.property("width") / 2, card.property("height") / 2),
        )
        expected_center = panel.mapToItem(
            timeline.contentItem(),
            QPointF(item["x"] * panel.property("width"),
                    item["y"] * panel.property("height")),
        )
        assert abs(actual_center.x() - expected_center.x()) <= 2
        assert abs(actual_center.y() - expected_center.y()) <= 2

    frame = timeline.grabWindow()
    assert not frame.isNull(), "az Időrend renderelt képkockája üres"
    card_zero = _visual_child(panel, "timelineCarouselCard0")
    assert card_zero is not None
    rendered_center = card_zero.mapToItem(
        timeline.contentItem(),
        QPointF(card_zero.property("width") / 2, card_zero.property("height") / 2),
    ).toPoint()
    samples = {
        frame.pixelColor(rendered_center.x() + dx, rendered_center.y() + dy).rgba()
        for dx, dy in ((-4, -4), (0, -4), (4, -4), (-4, 0), (0, 0), (4, 0),
                       (-4, 4), (0, 4), (4, 4))
    }
    assert len(samples) >= 4, "a fókuszköteg nem rajzol bélyegképet"

    initial_center = QPointF(
        card_zero.mapToItem(
            panel,
            QPointF(card_zero.property("width") / 2, card_zero.property("height") / 2),
        )
    )
    target_offset = controller.clampOffset(focus - 2 * CARD_STEP, 12)
    target = controller.carouselLayout(target_offset, 12)[0]
    QTest.keyClick(timeline, Qt.Key.Key_Right)
    QTest.keyClick(timeline, Qt.Key.Key_Right)
    _wait(qt_app, lambda: timeline.property("animating"), "a léptetés nem indult el")
    assert timeline.property("currentIndex") == 0

    intermediate = {}

    def has_intermediate_render():
        elapsed = time.time() * 1000 - timeline.property("animationStartedAt")
        if not 800 <= elapsed <= 1200:
            return False
        point = card_zero.mapToItem(
            panel,
            QPointF(card_zero.property("width") / 2, card_zero.property("height") / 2),
        )
        target_distance = abs(point.x() - target["x"] * panel.property("width"))
        start_distance = abs(point.x() - initial_center.x())
        if start_distance <= 2 or target_distance <= 2:
            return False
        output = timeline.grabWindow()
        actual = card_zero.mapToItem(timeline.contentItem(), point).toPoint()
        if output.isNull() or output.pixelColor(actual) == QColor("black"):
            return False
        intermediate["x"] = point.x()
        intermediate["start_distance"] = start_distance
        intermediate["target_distance"] = target_distance
        return True

    _wait(
        qt_app,
        has_intermediate_render,
        "egy másodpercnél nem volt látható köztes körhinta-állás",
        seconds=10.0,
    )
    assert intermediate["start_distance"] > 2
    assert intermediate["target_distance"] > 2
    _wait(
        qt_app,
        lambda: timeline.property("currentIndex") == 2
        and timeline.property("animating") is False,
        "a két összeadódó léptetés nem a harmadik gyűjteménynél állt meg",
        seconds=10.0,
    )
    assert _child(timeline, "timelineCollectionName").property("text") == "Collection 02"


def test_click_and_slider_animate_to_the_chosen_collection(
    qml_app_carousel_6595, qt_app
):
    timeline, controller, _collections = _open_carousel(
        qml_app_carousel_6595, qt_app, 800
    )
    panel = _child(timeline, "timelinePanel")
    card = _visual_child(panel, "timelineCarouselCard2")
    assert card is not None
    card_point = card.mapToItem(
        timeline.contentItem(),
        QPointF(card.property("width") / 2, card.property("height") / 2),
    ).toPoint()
    QTest.mouseClick(timeline, Qt.MouseButton.LeftButton, pos=card_point)
    _wait(
        qt_app,
        lambda: timeline.property("currentIndex") == 2
        and timeline.property("animating") is False,
        "a kötegre kattintás nem úszott a kiválasztott gyűjteményhez",
        seconds=10.0,
    )

    slider = _child(timeline, "timelineSliderArea")
    target_index = 5
    target_x = slider.property("width") * target_index / 11
    slider_point = slider.mapToItem(
        timeline.contentItem(), QPointF(target_x, slider.property("height") / 2)
    ).toPoint()
    QTest.mouseClick(timeline, Qt.MouseButton.LeftButton, pos=slider_point)
    _wait(
        qt_app,
        lambda: timeline.property("currentIndex") == target_index
        and timeline.property("animating") is False,
        "a csúszka nem úszott a választott gyűjteményhez",
        seconds=10.0,
    )
    assert _child(timeline, "timelineCollectionName").property("text") == "Collection 05"


def test_a_ferde_koteg_szele_elsimitott(qml_app_carousel_6595, qt_app):
    """Tulajdonosi kérés (#6595): a ferdén álló kép széle ne legyen recés.

    A fókuszköteg felső képének felső élén függőlegesen mintavételez: élsimítás
    nélkül a háttér és a keret között egyetlen lépcső van, élsimítással
    legalább egy köztes (kevert) képpont is.
    """
    timeline, _controller, _collections = _open_carousel(
        qml_app_carousel_6595, qt_app, 800
    )
    _wait(
        qt_app,
        lambda: timeline.property("currentCardsLoaded"),
        "a fókuszban levő köteg bélyegképei nem töltődtek be",
    )
    panel = _child(timeline, "timelinePanel")
    deck = _visual_child(panel, "timelineCarouselPhotoDeck0")
    assert deck is not None
    tetejen = None
    for child in _visual_child(panel, "timelineCarouselCard0").childItems():
        name = child.objectName()
        if name.startswith("timelineCarouselPhoto_0_"):
            if tetejen is None or child.property("z") > tetejen.property("z"):
                tetejen = child
    assert tetejen is not None
    assert abs(tetejen.property("rotation")) >= 4, "a köteg felső képe nem ferde"

    # A tesztkörnyezet szoftveres rajzolója a ferde élt mindig simítja, ezért
    # a képpont-próba ott élsimítás nélkül is zöld lenne. A programban futó
    # GPU-s rajzoló csak `antialiasing: true` mellett simít: ezt a kapcsolót
    # a ferde köteg minden rajzoló elemén külön ellenőrizzük.
    def rajzolo_elemek(item):
        for child in item.childItems():
            if child.metaObject().className().startswith(
                ("QQuickRectangle", "QQuickImage")
            ):
                yield child
            yield from rajzolo_elemek(child)

    elemek = list(rajzolo_elemek(tetejen))
    assert len(elemek) >= 4, "a köteg képének rajzoló elemei nem találhatók"
    simitatlan = [e.metaObject().className() for e in elemek
                  if e.property("antialiasing") is not True]
    assert simitatlan == [], f"élsimítás nélküli ferde elem: {simitatlan}"
    frame = timeline.grabWindow()
    kevert = 0
    for arany in (0.3, 0.5, 0.7):
        pont = tetejen.mapToItem(
            timeline.contentItem(), QPointF(tetejen.property("width") * arany, 0)
        ).toPoint()
        oszlop = [
            frame.pixelColor(pont.x(), pont.y() + dy).lightness()
            for dy in range(-6, 7)
        ]
        kint, bent = oszlop[0], max(oszlop)
        if bent - kint < 30:
            continue
        also, felso = kint + 0.15 * (bent - kint), bent - 0.15 * (bent - kint)
        kevert += sum(1 for v in oszlop if also < v < felso)
    assert kevert >= 2, "a ferde köteg széle recés: nincs kevert képpont az élen"
