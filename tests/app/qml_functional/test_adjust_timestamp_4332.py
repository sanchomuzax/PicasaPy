"""#4332: az Eszközök dátummódosítása a valódi menüből és párbeszédből."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import piexif
import pytest
from PySide6.QtCore import QDateTime, QLocale, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg, make_minta_jpeg
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.varakozas import var_feltetelre


DATUMOK = ("2020:01:01 12:00:00", "2020:01:03 12:00:00")


def _kepek(lib: Path) -> None:
    for nev, taken_at, datetime_0th in (
        ("a.jpg", DATUMOK[0], "2020:01:01 12:00:00"),
        ("b.jpg", DATUMOK[1], "2020:01:03 12:00:00"),
        ("c.jpg", "2020:01:04 12:00:00", "2020:01:04 12:00:00"),
    ):
        make_jpeg(lib / nev, taken_at=taken_at, datetime_0th=datetime_0th)


def _ns(value: str) -> int:
    return round(datetime.fromisoformat(value).timestamp() * 1_000_000_000)


@pytest.fixture
def timestamp_app(qt_app, tmp_path):
    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_kepek)


def _var(qt_app, feltetel, leiras: str, ido: float = 10.0) -> None:
    assert var_feltetelre(qt_app, feltetel, ido), f"időtúllépés: {leiras}"


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
def test_valodi_eszközmenüvel_mindket_mod_az_exifet_irja_es_fajlidot_megoriz(
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
    assert controller.sortFolderBy(controller.currentFolder, "date")
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
    assert _elem(window, "adjustTimestampCurrentDate").property("text") == (
        "Current photo date"
    )
    assert _elem(window, "adjustTimestampCurrentDateField").property("text") == (
        "2020-01-01"
    )
    assert _elem(window, "adjustTimestampCurrentTimeField").property(
        "displayText"
    ) == "12:00:00"
    assert not _elem(window, "adjustTimestampCurrentDateField").property("enabled")
    assert not _elem(window, "adjustTimestampCurrentTimeField").property("enabled")
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
    # Az atime-ot itt nem mérjük: a módosítás után a nézet újratölti a képet
    # (bélyegkép-dekódolás), és relatime alatt ez a valódi olvasás frissíti.
    # A visszaállítás sorrendjét a test_timestamp_fajlidok_sorrend_4646.py méri.
    for path in forrasok:
        most = path.stat()
        assert most.st_mtime_ns == regi_fajlidok[path.name].st_mtime_ns
        if os.name == "nt":
            assert most.st_ctime_ns == regi_fajlidok[path.name].st_ctime_ns
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
        assert path.read_bytes() != elotte[path.name]

    kijeloltek = {
        photo.name: photo
        for photo in controller.photos.photos
        if photo.name in kijelolt_nevek
    }
    assert all(photo.taken_at_override is None for photo in kijeloltek.values())

    # A modell dátummezője az EXIF-ből szinkronizált értéket adja. A korábban
    # egyszer elmentett mappasorrend a dátummódosítás után is változatlan marad.
    rows = {photo.name: row for row, photo in enumerate(controller.photos.photos)}
    assert controller.photos.itemAt(rows["a.jpg"])["takenAt"] == vart["a.jpg"]
    assert tuple(photo.name for photo in controller.photos.photos) == (
        "a.jpg",
        "b.jpg",
        "c.jpg",
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


def _egy_fenykep(lib: Path) -> None:
    kep = lib / "foto.jpg"
    make_minta_jpeg(kep, size=(320, 240), seed=7)
    piexif.insert(
        piexif.dump(
            {
                "0th": {piexif.ImageIFD.DateTime: "2020:01:01 12:00:00"},
                "Exif": {
                    piexif.ExifIFD.DateTimeOriginal: "2020:01:01 12:00:00"
                },
            }
        ),
        str(kep),
    )


@pytest.fixture
def egykepes_timestamp_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_egy_fenykep,
        valodi_belyegkep=True,
    )


@pytest.mark.parametrize("ablakmagassag_eltolas", (-5, 0, 5))
def test_eszközmenüből_a_jelenlegi_dátum_két_olvasható_letiltott_mezőben_látszik(
    egykepes_timestamp_app, qt_app, ablakmagassag_eltolas
):
    window, controller, _engine = egykepes_timestamp_app
    window.setHeight(window.height() + ablakmagassag_eltolas)
    assert controller.sortFolderBy(controller.currentFolder, "date")
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    window.show()
    qt_app.processEvents()

    tools_menu = _elem(window, "menuTools")
    tools_menu.open()
    _var(qt_app, lambda: tools_menu.property("visible"), "az Eszközök menü")
    menu_item = _elem(window, "menuToolsAdjustTimestamp")
    assert menu_item.property("enabled")
    _kattints(menu_item, qt_app, window)

    dialog = _elem(window, "adjustTimestampDialog")
    _var(qt_app, lambda: dialog.property("visible"), "a dátummódosító ablak")
    thumbnail = _elem(window, "adjustTimestampThumbnail")
    assert thumbnail.property("source").toString().startswith("image://thumbs/")
    _var(qt_app, lambda: dialog.property("thumbnailLoaded"), "a valódi bélyegkép")
    thumbnail_ratio = thumbnail.property("paintedWidth") / thumbnail.property(
        "paintedHeight"
    )
    assert thumbnail_ratio == pytest.approx(4 / 3, abs=0.05)

    datum_felirat = _elem(window, "adjustTimestampCurrentDate")
    datum_mezo = _elem(window, "adjustTimestampCurrentDateField")
    ido_mezo = _elem(window, "adjustTimestampCurrentTimeField")
    uj_datum_mezo = _elem(window, "adjustTimestampNewDate")
    uj_ido_mezo = _elem(window, "adjustTimestampTime")

    assert datum_felirat.property("text") == "Current photo date"
    assert datum_mezo.property("text") == "2020-01-01"
    assert datum_mezo.property("text") == uj_datum_mezo.property("text")
    assert ido_mezo.property("displayText") == "12:00:00"
    assert ido_mezo.property("displayText") == uj_ido_mezo.property("displayText")
    assert datum_mezo.property("enabled") is False
    assert ido_mezo.property("enabled") is False
    assert ido_mezo.property("editable") is False

    _kattints(datum_mezo, qt_app, window)
    _kattints(ido_mezo, qt_app, window)
    QTest.keyClick(window, Qt.Key.Key_9)
    qt_app.processEvents()
    assert datum_mezo.property("text") == "2020-01-01"
    assert ido_mezo.property("displayText") == "12:00:00"

    kepmappa = os.environ.get("PICASAPY_KIADASKEP_MAPPA")
    if kepmappa and ablakmagassag_eltolas == 0:
        cel = Path(kepmappa) / "adjust-photo-date-5869.png"
        kep = window.grabWindow()
        assert not kep.isNull(), "a párbeszéd képernyőképe üres"
        assert kep.save(str(cel)), f"nem menthető a kiadáskép: {cel}"
