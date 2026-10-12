"""#4332: az Eszközök dátummódosítása a valódi menüből és párbeszédből."""

from __future__ import annotations

import os
import time
from datetime import datetime
from pathlib import Path

import piexif
import pytest
from PySide6.QtCore import QDateTime, QLocale, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg
from tests.app.qml_functional.conftest import _build_qml_app


DATUMOK = ("2020:01:01 12:00:00", "2020:01:03 12:00:00")


def _kepek(lib: Path) -> None:
    for nev, taken_at, datetime_0th, nap in (
        ("a.jpg", DATUMOK[0], "2020:01:01 12:00:00", 1),
        ("b.jpg", DATUMOK[1], "2020:01:03 12:00:00", 3),
        ("c.jpg", "2020:01:04 12:00:00", "2020:01:04 12:00:00", 4),
    ):
        path = make_jpeg(lib / nev, taken_at=taken_at, datetime_0th=datetime_0th)
        atime = datetime(2019, 12, nap, 1, 2, 3).timestamp()
        mtime = datetime(2019, 12, nap, 4, 5, 6).timestamp()
        os.utime(path, (atime, mtime))


def _ns(value: str) -> int:
    return round(datetime.fromisoformat(value).timestamp() * 1_000_000_000)


@pytest.fixture
def timestamp_app(qt_app, tmp_path):
    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_kepek)


def _var(qt_app, feltetel, leiras: str, ido: float = 3.0) -> None:
    hatarido = time.monotonic() + ido
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return
        time.sleep(0.05)
    assert feltetel(), f"időtúllépés: {leiras}"


def _elem(window, nev: str):
    from PySide6.QtCore import QObject

    elem = window.findChild(QObject, nev)
    assert elem is not None, f"nem található: {nev}"
    return elem


def _vizualis_elem(root, nev: str):
    """Popup belső vezérlőjét a QQuickItem gyerekfájában keresi meg."""
    verem = [root]
    while verem:
        elem = verem.pop()
        if elem.objectName() == nev:
            return elem
        verem.extend(elem.childItems())
    return None


def _kattints(elem, qt_app, window=None) -> None:
    """A tényleges vezérlő helyére kattint, a QML elem saját ablakában."""
    pont = elem.mapToScene(
        QPointF(float(elem.property("width")) / 2, float(elem.property("height")) / 2)
    ).toPoint()
    ablak = window if window is not None else elem.window()
    assert ablak is not None, f"{elem.objectName()} nem látható ablakban"
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(pont.x(), pont.y()),
    )
    qt_app.processEvents()


def _datum_kivalasztasa(window, qt_app, iso_date: str) -> None:
    _kattints(_elem(window, "adjustTimestampNewDate"), qt_app, window)
    naptar = _elem(window, "adjustTimestampCalendar")
    _var(qt_app, lambda: naptar.property("visible"), "a dátumválasztó")
    ev, honap, _nap = (int(resz) for resz in iso_date.split("-"))
    cel_objektum = f"adjustTimestampCalendarDay_{iso_date}"
    for _ in range(12):
        nap = _vizualis_elem(
            _elem(window, "adjustTimestampMonthGrid"), cel_objektum
        )
        if nap is not None and nap.property("enabled"):
            _kattints(nap, qt_app, window)
            _var(
                qt_app,
                lambda: _elem(window, "adjustTimestampNewDate").property("text")
                == iso_date,
                "a kiválasztott naptári nap beállítása",
            )
            return
        honap_racs = _elem(window, "adjustTimestampMonthGrid")
        if honap_racs.property("year") > ev or (
            honap_racs.property("year") == ev
            and honap_racs.property("month") + 1 > honap
        ):
            elozo = _elem(window, "adjustTimestampPreviousMonth")
            _kattints(elozo, qt_app, window)
        else:
            kovetkezo = _elem(window, "adjustTimestampNextMonth")
            _kattints(kovetkezo, qt_app, window)
    raise AssertionError(f"a dátumválasztóban nem található: {iso_date}")


def _ido_beallitasa(window, qt_app, ertek: str) -> None:
    mezo = _elem(window, "adjustTimestampTime")
    _kattints(mezo, qt_app, window)
    QTest.keyClick(
        window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier
    )
    for karakter in ertek:
        billentyu = (
            Qt.Key.Key_Colon
            if karakter == ":"
            else getattr(Qt.Key, f"Key_{karakter}")
        )
        QTest.keyClick(window, billentyu)
    QTest.keyClick(window, Qt.Key.Key_Return)
    qt_app.processEvents()


@pytest.mark.parametrize("ablakmagassag_eltolas", (-5, 0, 5))
@pytest.mark.parametrize(
    ("mod", "cel_datum", "cel_ido", "vart"),
    [
        (
            "relative",
            "2020-01-05",
            "12:00:00",
            {
                "a.jpg": "2020-01-05T12:00:00",
                "b.jpg": "2020-01-03T12:00:00",
                "c.jpg": "2020-01-08T12:00:00",
            },
        ),
        (
            "absolute",
            "2020-02-02",
            "08:30:00",
            {
                "a.jpg": "2020-02-02T08:30:00",
                "b.jpg": "2020-01-03T12:00:00",
                "c.jpg": "2020-02-02T08:30:00",
            },
        ),
    ],
)
def test_valodi_eszközmenüvel_mindket_mod_az_exifet_es_fajlidot_irja(
    timestamp_app,
    qt_app,
    tmp_path,
    mod,
    cel_datum,
    cel_ido,
    vart,
    ablakmagassag_eltolas,
):
    window, controller, _engine = timestamp_app
    window.setHeight(window.height() + ablakmagassag_eltolas)
    controller.setFolderPhotoSort("date")
    qt_app.processEvents()
    window.setProperty("selectedIndexes", [0, 2])
    window.setProperty("selectedIndex", 0)
    window.show()
    qt_app.processEvents()

    eszkozok = _elem(window, "menuTools")
    eszkozok.open()
    _var(
        qt_app,
        lambda: eszkozok.property("visible"),
        "az Eszközök menü megnyitása",
    )
    menu_item = _elem(window, "menuToolsAdjustTimestamp")
    assert menu_item.property("enabled"), "kijelölt képeknél a parancs szürke"
    assert not menu_item.property("placeholder"), "a parancs helyfoglaló maradt"
    _kattints(menu_item, qt_app, window)

    dialog = _elem(window, "adjustTimestampDialog")
    _var(
        qt_app,
        lambda: dialog.property("visible"),
        "a dátummódosító párbeszéd",
    )
    assert dialog.property("title") == "Adjust Photo Date - 2 items"
    thumbnail = _elem(window, "adjustTimestampThumbnail")
    assert thumbnail.property("source").toString().startswith("image://thumbs/")
    _var(
        qt_app,
        lambda: dialog.property("thumbnailLoaded"),
        "a párbeszéd előnézeti bélyegképe betöltődik",
    )
    assert _elem(window, "adjustTimestampCurrentDate").property("text").endswith(
        "2020-01-01 12:00:00"
    )
    assert _elem(window, "adjustTimestampNewDate").property("text") == "2020-01-01"
    assert _elem(window, "adjustTimestampTime").property("value") == 12 * 3600
    assert _elem(window, "adjustTimestampRelative").property("checked")

    if mod == "absolute":
        _kattints(_elem(window, "adjustTimestampAbsolute"), qt_app, window)
        _var(
            qt_app,
            lambda: _elem(window, "adjustTimestampAbsolute").property("checked"),
            "az abszolút dátummód kiválasztása",
        )
    _datum_kivalasztasa(window, qt_app, cel_datum)
    _ido_beallitasa(window, qt_app, cel_ido)

    kijelolt_nevek = {"a.jpg", "c.jpg"}
    forrasok = [
        Path(photo.folder_path) / photo.name
        for photo in controller.photos.photos
        if photo.name in kijelolt_nevek
    ]
    elotte = {path.name: path.read_bytes() for path in forrasok}
    regi_fajlidok = {
        path.name: path.stat() for path in forrasok
    }
    forras_ini = forrasok[0].parent / ".picasa.ini"
    ini_elotte = forras_ini.read_bytes() if forras_ini.exists() else None
    _kattints(_elem(window, "adjustTimestampAccept"), qt_app, window)

    _var(
        qt_app,
        lambda: {
            photo.name: photo.taken_at for photo in controller.photos.photos
        }
        == vart,
        "az indexben a két új dátum",
    )
    assert (forras_ini.read_bytes() if forras_ini.exists() else None) == ini_elotte
    assert {
        path.name: piexif.load(str(path))["Exif"][piexif.ExifIFD.DateTimeOriginal]
        for path in forrasok
    } == {
        name: value.encode().replace(b"-", b":", 2).replace(b"T", b" ")
        for name, value in vart.items()
        if name in kijelolt_nevek
    }
    for path in forrasok:
        regi_exif = datetime.strptime(
            {"a.jpg": "2020:01:01 12:00:00", "c.jpg": "2020:01:04 12:00:00"}[
                path.name
            ],
            "%Y:%m:%d %H:%M:%S",
        )
        uj_exif = datetime.fromisoformat(vart[path.name])
        delta_ns = round((uj_exif - regi_exif).total_seconds() * 1_000_000_000)
        most = path.stat()
        assert most.st_atime_ns == regi_fajlidok[path.name].st_atime_ns + delta_ns
        assert most.st_mtime_ns == regi_fajlidok[path.name].st_mtime_ns + delta_ns
        if os.name == "nt":
            assert most.st_ctime_ns == regi_fajlidok[path.name].st_ctime_ns
        assert path.read_bytes() != elotte[path.name]

    kijeloltek = {
        photo.name: photo
        for photo in controller.photos.photos
        if photo.name in kijelolt_nevek
    }
    assert all(photo.taken_at_override is None for photo in kijeloltek.values())

    # A modell dátummezője is az EXIF-ből szinkronizált értéket adja, és az aktív
    # dátumrendezés a befejezett köteg után a módosított képekhez igazodik.
    rows = {photo.name: row for row, photo in enumerate(controller.photos.photos)}
    assert controller.photos.itemAt(rows["a.jpg"])["takenAt"] == vart["a.jpg"]
    assert tuple(photo.name for photo in controller.photos.photos) == (
        ("b.jpg", "a.jpg", "c.jpg")
        if mod == "relative"
        else ("b.jpg", "a.jpg", "c.jpg")
    )

    tulajdonsagok = controller.propertiesOf(rows["a.jpg"])
    elvart_camera_datum = QLocale().toString(
        QDateTime.fromString(vart["a.jpg"], "yyyy-MM-ddTHH:mm:ss"),
        QLocale.FormatType.ShortFormat,
    )
    assert elvart_camera_datum in [str(entry["value"]) for entry in tulajdonsagok]

    from picasapy.app.export_controller import _export_item
    from picasapy.export import ExportSettings, export_photos

    records = [
        photo for photo in controller.photos.photos if photo.name in kijelolt_nevek
    ]
    report = export_photos(
        [_export_item(record) for record in records],
        tmp_path / "export",
        ExportSettings(),
    )
    assert len(report.exported) == 2 and not report.failed
    assert {
        path.name: piexif.load(str(path))["Exif"][piexif.ExifIFD.DateTimeOriginal]
        for path in report.exported
    } == {
        name: value.encode().replace(b"-", b":", 2).replace(b"T", b" ")
        for name, value in vart.items()
        if name in kijelolt_nevek
    }
