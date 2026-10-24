"""Az Időrend qshow-sorrendje, billentyűi és visszatérése (#5770)."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import piexif
import pytest
from PySide6.QtCore import QLocale, QObject, Qt
from PySide6.QtTest import QTest

from support.jpeg_factory import make_minta_jpeg
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.varakozas import var_feltetelre


ALBUM_TOKEN = "57705770577057705770577057705770"
KIADASKEP_KORNYEZET = "PICASAPY_5770_KIADASKEP_MAPPA"


def _fénykép(út: Path, dátum: str) -> None:
    make_minta_jpeg(út, size=(320, 240), seed=sum(út.name.encode("utf-8")))
    piexif.insert(
        piexif.dump(
            {
                "0th": {},
                "Exif": {
                    piexif.ExifIFD.DateTimeOriginal: dátum.encode("ascii")
                },
                "GPS": {},
            }
        ),
        str(út),
    )


def _job239_mintakészlet(könyvtár: Path) -> None:
    mappák = (
        ("2009_majus", ("2009:05:14 10:00:00",)),
        (
            "2014_november",
            (
                "2014:11:02 15:30:00",
                "2014:11:03 15:30:00",
                "2014:11:04 15:30:00",
            ),
        ),
        (
            "2019_marcius",
            tuple(f"2019:03:{day:02d} 09:15:00" for day in range(8, 15)),
        ),
        (
            "2021_eltero_fajlido",
            ("2021:08:20 12:00:00", "2021:08:20 13:00:00"),
        ),
    )
    for mappanév, dátumok in mappák:
        mappa = könyvtár / mappanév
        mappa.mkdir()
        for index, dátum in enumerate(dátumok, start=1):
            út = mappa / f"{mappanév}_{index:02d}.jpg"
            _fénykép(út, dátum)
            if mappanév == "2021_eltero_fajlido":
                os.utime(út, (datetime(2023, 1, 1, 12).timestamp(),) * 2)

    picasa_teszt = könyvtár / "PicasaTeszt"
    picasa_teszt.mkdir()
    album_sorok = []
    for index in range(1, 25):
        név = f"PicasaTeszt_{index:02d}.jpg"
        _fénykép(picasa_teszt / név, "2026:10:01 08:00:00")
        album_sorok.extend((f"[{név}]", f"albums={ALBUM_TOKEN}"))
    ini = [
        f"[.album:{ALBUM_TOKEN}]",
        "name=Recently Updated",
        f"token={ALBUM_TOKEN}",
        *album_sorok,
        "",
    ]
    (picasa_teszt / ".picasa.ini").write_text("\n".join(ini), encoding="utf-8")


@pytest.fixture
def locál_en_us():
    előző = QLocale()
    QLocale.setDefault(QLocale("en_US"))
    try:
        yield
    finally:
        QLocale.setDefault(előző)


def _child(parent, object_name):
    child = parent.findChild(QObject, object_name)
    assert child is not None, f"{object_name} nem található"
    return child


def _vár(qt_app, feltétel, üzenet: str, másodperc: float = 10.0) -> None:
    assert var_feltetelre(qt_app, feltétel, másodperc), üzenet


def _nyit_időrendet(window, qt_app):
    window.requestActivate()
    _vár(qt_app, window.isActive, "a főablak nem lett aktív")
    QTest.keyClick(window, Qt.Key.Key_5, Qt.KeyboardModifier.ControlModifier)
    _vár(
        qt_app,
        lambda: window.property("timelineOpen") is True,
        "a Ctrl+5 nem nyitotta meg az Időrend-bemutatót",
    )
    timeline = _child(window, "timelineView")
    timeline.requestActivate()
    _vár(qt_app, timeline.isActive, "az Időrend nem kapott billentyűfókuszt")
    return timeline


def _feliratok(timeline):
    return (
        _child(timeline, "timelineCollectionName").property("text"),
        _child(timeline, "timelineCollectionDate").property("text"),
    )


@pytest.fixture
def qml_app_5770(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_job239_mintakészlet,
        belyegkep_meret=256,
        valodi_belyegkep=True,
    )


def test_valodi_billentyuk_sorrend_felirat_escape_es_ujranyitas(
    qml_app_5770, qt_app, locál_en_us
):
    window, _controller, _engine = qml_app_5770
    timeline = _nyit_időrendet(window, qt_app)
    controller = _engine.rootContext().contextProperty("timelineController")
    collections = controller.collections
    assert [item["name"] for item in collections] == [
        "2009_majus",
        "2014_november",
        "2019_marcius",
        "2021_eltero_fajlido",
        "PicasaTeszt",
        "Recently Updated",
    ]
    assert [item["dateLabel"] for item in collections] == [
        "May 2009",
        "November 2014",
        "March 2019",
        "August 2021",
        "October 2026",
        "October 2026",
    ]
    assert collections[3]["count"] == 2

    if output_dir := os.environ.get(KIADASKEP_KORNYEZET):
        for _ in range(2):
            QTest.keyClick(timeline, Qt.Key.Key_Right)
        _vár(
            qt_app,
            lambda: timeline.property("currentIndex") == 2,
            "nem érte el a képköteges kártyát",
        )
        _vár(
            qt_app,
            lambda: timeline.property("currentCardsLoaded"),
            "a kártya bélyegképei nem töltődtek be",
        )
        image = timeline.grabWindow()
        assert not image.isNull(), "az Időrend kiadásképe üres"
        célmappa = Path(output_dir)
        célmappa.mkdir(parents=True, exist_ok=True)
        cél = célmappa / "idorend_bemutato_5770.png"
        assert image.save(str(cél), "PNG"), f"nem menthető a kiadáskép: {cél}"
        for _ in range(2):
            QTest.keyClick(timeline, Qt.Key.Key_Left)
        _vár(
            qt_app,
            lambda: timeline.property("currentIndex") == 0,
            "nem tért vissza az első kártyára",
        )

    QTest.keyClick(timeline, Qt.Key.Key_Right)
    _vár(qt_app, lambda: timeline.property("currentIndex") == 1, "Right nem lépett")
    assert _feliratok(timeline) == ("2014_november", "November 2014")
    QTest.keyClick(timeline, Qt.Key.Key_Left)
    _vár(qt_app, lambda: timeline.property("currentIndex") == 0, "Left nem lépett vissza")
    QTest.keyClick(timeline, Qt.Key.Key_Left)
    assert timeline.property("currentIndex") == 0

    QTest.keyClick(timeline, Qt.Key.Key_Right)
    QTest.keyClick(timeline, Qt.Key.Key_Right)
    QTest.keyClick(timeline, Qt.Key.Key_Right)
    _vár(
        qt_app,
        lambda: timeline.property("currentIndex") == 3,
        "Right nem érte el a 2021-es csoportot",
    )
    assert _feliratok(timeline) == ("2021_eltero_fajlido", "August 2021")
    QTest.keyClick(timeline, Qt.Key.Key_Escape)
    _vár(
        qt_app,
        lambda: window.property("timelineOpen") is False,
        "Escape nem zárta be az Időrendet",
    )
    első_út = collections[3]["firstPhotoPath"]
    assert _controller.currentFolder == str(Path(első_út).parent)
    első_sor = _controller.photos.rowOfPath(első_út)
    assert window.property("selectedIndex") == első_sor
    assert window.property("selectedIndexes").toVariant() == [első_sor]

    timeline = _nyit_időrendet(window, qt_app)
    _vár(
        qt_app,
        lambda: timeline.property("currentIndex") == 0,
        "újranyitáskor nem a legrégebbi kártya az első",
    )
    assert _feliratok(timeline) == ("2009_majus", "May 2009")


def test_space_album_elso_kepe_es_escape_utani_kijeloles(
    qml_app_5770, qt_app, locál_en_us
):
    window, controller, _engine = qml_app_5770
    timeline = _nyit_időrendet(window, qt_app)
    for _ in range(5):
        QTest.keyClick(timeline, Qt.Key.Key_Right)
    _vár(
        qt_app,
        lambda: timeline.property("currentIndex") == 5,
        "nem érte el az albumkártyát",
    )
    QTest.keyClick(timeline, Qt.Key.Key_Space)
    slideshow = _child(window, "slideshowView")
    _vár(
        qt_app,
        lambda: window.property("timelineSlideshowActive") is True
        and slideshow.property("visible") is True,
        "Space nem indította el az album diavetítését",
    )
    album_modell = window.property("timelineSlideshowModel")
    assert album_modell.rowCount() == 24
    assert slideshow.property("currentIndex") == 0
    első_út = album_modell.filePathAt(0)
    assert Path(első_út).name == "PicasaTeszt_01.jpg"

    QTest.keyClick(window, Qt.Key.Key_Escape)
    _vár(
        qt_app,
        lambda: slideshow.property("visible") is False,
        "Escape nem zárta be a diavetítést",
    )
    assert controller.currentAlbumToken == ALBUM_TOKEN
    első_sor = controller.photos.rowOfPath(első_út)
    assert window.property("selectedIndex") == első_sor
    assert window.property("selectedIndexes").toVariant() == [első_sor]
