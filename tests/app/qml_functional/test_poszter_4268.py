"""#4268 — a Poszter párbeszéd és fájlkimenet valódi menükattintással."""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from PySide6.QtCore import QLocale, QObject, QPoint, QPointF, Qt, QMetaObject
from PySide6.QtTest import QSignalSpy, QTest

from picasapy.lazy_cv2 import cv2
from tests.app.qml_functional.conftest import _build_qml_app

_DIALOG_PARENTS: list[QObject] = []


def _chart(lib):
    yy, xx = np.indices((800, 800), dtype=np.uint16)
    rgb = np.empty((800, 800, 3), dtype=np.uint8)
    rgb[..., 0] = (xx // 40 * 31 + yy // 40 * 17) % 256
    rgb[..., 1] = xx % 256
    rgb[..., 2] = yy % 256
    Image.fromarray(rgb, "RGB").save(
        lib / "color_patches.jpg", format="JPEG", quality=100, subsampling=0
    )


@pytest.fixture(autouse=True)
def _amerikai_papirbeallitas():
    old = QLocale()
    QLocale.setDefault(QLocale("en_US"))
    try:
        yield
    finally:
        QLocale.setDefault(old)


@pytest.fixture(scope="module")
def poster_app(
    qt_app,
    tmp_path_factory,
    _module_qml_warnings,
    _module_user_folder_guard,
):
    """A teljes QML-ablakot egyszer építi fel a tíz ellenőrzéshez."""
    old_locale = QLocale()
    QLocale.setDefault(QLocale("en_US"))
    app = _build_qml_app(
        qt_app,
        tmp_path_factory.mktemp("poster-4268"),
        kepeket_keszit=_chart,
    )
    try:
        window, controller, engine = next(app)
        window.setProperty("posterTestBaseHeight", int(window.height()))
        yield window, controller, engine
    finally:
        try:
            next(app, None)
        finally:
            QLocale.setDefault(old_locale)


def _var(qt_app, condition, message: str, seconds: float = 5.0):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if condition():
            return
        time.sleep(0.01)
    raise AssertionError(message)


def _elem(root, name: str):
    item = root.findChild(QObject, name)
    assert item is not None, f"nem található a kirajzolt {name} vezérlő"
    return item


def _kattintas(item):
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        item.window(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )


def _ellenorizd_dialog_szuloterulethez_igazitas(dialog, window):
    """A Dialog saját geometriáját az aktuális szülőterülethez méri."""
    parent = dialog.property("parent")
    assert parent is not None, "a Poszter párbeszédnek nincs vizuális szülőterülete"
    # A QML `parent` vizuális szülő nem mindig QObject-szülő; a PySide wrapper
    # felszabadítása a dialógus felépült vizuális fáját is elengedheti.
    _DIALOG_PARENTS.append(parent)
    assert parent.window() == window, "a Poszter párbeszéd másik ablakhoz tartozik"
    x = float(dialog.property("x"))
    y = float(dialog.property("y"))
    width = float(dialog.property("width"))
    height = float(dialog.property("height"))
    parent_width = float(parent.width())
    parent_height = float(parent.height())
    assert parent_width >= width - 3 and parent_height >= height - 3, (
        f"a Poszter párbeszéd szülőterülete túl kicsi: "
        f"{parent_width}×{parent_height}, párbeszéd={width}×{height}"
    )
    expected_x = (parent_width - width) / 2
    expected_y = (parent_height - height) / 2
    assert abs(x - expected_x) <= 3, (
        f"a Poszter párbeszéd vízszintesen nincs középre igazítva: "
        f"x={x}, várt={expected_x}"
    )
    assert abs(y - expected_y) <= 3, (
        f"a Poszter párbeszéd függőlegesen nincs középre igazítva: "
        f"y={y}, várt={expected_y}"
    )


def _nyisd_meg_valodi_menu_kattintassal(window, controller, qt_app):
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()

    create_menu = _elem(window, "menuCreateRoot")
    assert QMetaObject.invokeMethod(create_menu, "open", Qt.ConnectionType.DirectConnection)
    poster = _elem(window, "menuCreatePoster")
    _var(
        qt_app,
        lambda: create_menu.property("opened") is True and poster.isVisible(),
        "a Poszter menüpont nem jelent meg teljesen",
    )
    assert poster.property("enabled") is True
    _kattintas(poster)
    _var(
        qt_app,
        lambda: (
            window.findChild(QObject, "posterDialog") is not None
            and _elem(window, "posterDialog").property("opened") is True
        ),
        "a valódi menükattintás nem nyitotta meg teljesen a Poszter párbeszédet",
    )
    dialog = _elem(window, "posterDialog")
    _ellenorizd_dialog_szuloterulethez_igazitas(dialog, window)
    return dialog


def _inditsd_a_kimenetet(
    window, controller, qt_app, *, overlap: bool, height_delta: int
):
    original_height = int(window.property("posterTestBaseHeight"))
    target_height = original_height + height_delta
    window.resize(window.width(), target_height)
    _var(
        qt_app,
        lambda: int(window.height()) == target_height,
        f"a főablak nem vette fel a {height_delta:+d} px-es magasságváltozást",
    )

    dialog = _nyisd_meg_valodi_menu_kattintassal(window, controller, qt_app)
    assert dialog.property("title") == "Poster Settings"
    assert _elem(dialog, "posterSizeLabel").property("text") == "Poster size:"
    assert _elem(dialog, "posterPaperLabel").property("text") == "Paper size:"
    assert _elem(dialog, "posterOverlapCheck").property("text") == "Overlap tiles"
    assert _elem(dialog, "posterSizeBox").property("currentIndex") == 0
    assert _elem(dialog, "posterPaperBox").property("currentText") == "4x6"

    check = _elem(dialog, "posterOverlapCheck")
    if overlap:
        _kattintas(check)
    assert check.property("checked") is overlap

    # A befejező jel csak azután érkezik, hogy a háttérszál minden lapot kiírt.
    finished = QSignalSpy(controller.posterFinished)
    failed = QSignalSpy(controller.posterFailed)
    _kattintas(_elem(dialog, "posterAcceptButton"))
    _var(
        qt_app,
        lambda: dialog.property("opened") is not True,
        "a Poszter párbeszéd elfogadása nem zárta be a párbeszédet",
    )

    source = controller.photos.filePathAt(0)
    source_folder = source.rsplit("/", 1)[0]
    names = [
        f"{row}-{column}-color_patches.jpg"
        for row in range(2)
        for column in range(2)
    ]
    _var(
        qt_app,
        lambda: finished.count() > 0 or failed.count() > 0,
        "a Poszter háttérmunkája nem jelzett befejezést vagy hibát",
        seconds=20.0,
    )
    assert failed.count() == 0, (
        "a Poszter háttérmunkája hibát jelzett: "
        f"{failed.at(0)[0] if failed.count() else ''}"
    )
    assert finished.count() == 1, "a Poszter háttérmunkája többször fejeződött be"
    _var(
        qt_app,
        lambda: all(Path(source_folder, name).is_file() for name in names),
        "a Poszter befejező jelzése után nem jelent meg mind a négy lap",
    )
    source_bytes = np.frombuffer(Path(source).read_bytes(), dtype=np.uint8)
    original_pixels = cv2.imdecode(source_bytes, cv2.IMREAD_COLOR)

    overlap_range = (0, 440) if overlap else (0, 400)
    inner_range = (360, 800) if overlap else (400, 800)
    expected = {
        "0-0-color_patches.jpg": original_pixels[
            overlap_range[0] : overlap_range[1], overlap_range[0] : overlap_range[1]
        ],
        "0-1-color_patches.jpg": original_pixels[
            overlap_range[0] : overlap_range[1], inner_range[0] : inner_range[1]
        ],
        "1-0-color_patches.jpg": original_pixels[
            inner_range[0] : inner_range[1], overlap_range[0] : overlap_range[1]
        ],
        "1-1-color_patches.jpg": original_pixels[
            inner_range[0] : inner_range[1], inner_range[0] : inner_range[1]
        ],
    }
    for name, pixels in expected.items():
        encoded_ok, encoded_expected = cv2.imencode(".jpg", pixels)
        assert encoded_ok
        jpeg_expected = cv2.imdecode(encoded_expected, cv2.IMREAD_COLOR)
        with Image.open(Path(source_folder, name)) as page:
            actual = np.asarray(page.convert("RGB"))[..., ::-1]
        assert actual.shape == jpeg_expected.shape, name
        assert np.array_equal(actual, jpeg_expected), (
            f"{name}: a kimenet pixeladata nem a mért forrástartományból jött"
        )


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_valodi_kattintas_megnyitja_a_hivatalos_parbeszedet(
    poster_app, qt_app, height_delta
):
    window, controller, _engine = poster_app
    original_height = int(window.property("posterTestBaseHeight"))
    window.resize(window.width(), original_height + height_delta)
    _var(
        qt_app,
        lambda: int(window.height()) == original_height + height_delta,
        f"a főablak nem vette fel a {height_delta:+d} px-es magasságváltozást",
    )

    dialog = _nyisd_meg_valodi_menu_kattintassal(window, controller, qt_app)

    assert dialog.property("visible") is True
    assert _elem(dialog, "posterTip").property("text").startswith("Tip:")
    assert len(controller.posterPaperSizes()) == 2
    _kattintas(_elem(dialog, "posterCancelButton"))
    _var(
        qt_app,
        lambda: dialog.property("opened") is not True,
        "a Poszter párbeszéd nem zárult be a Mégse gombbal",
    )


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_kattintasbol_negy_400x400as_lap_kesz_atfedes_nelkul(
    poster_app, qt_app, height_delta
):
    window, controller, _engine = poster_app
    _inditsd_a_kimenetet(
        window, controller, qt_app, overlap=False, height_delta=height_delta
    )


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_kattintasbol_negy_440x440as_lap_kesz_atfedessel(
    poster_app, qt_app, height_delta
):
    window, controller, _engine = poster_app
    _inditsd_a_kimenetet(
        window, controller, qt_app, overlap=True, height_delta=height_delta
    )


def test_papirmeret_a_legutobbi_valasztast_es_a_teruleti_listat_megorzi(
    poster_app, qt_app
):
    _window, controller, _engine = poster_app

    assert controller.posterPaperSizes() == ["4x6", "8.5x11"]
    assert controller.posterPaperSize() == "4x6"
    controller.setPosterPaperSize("8.5x11")
    assert controller.posterPaperSize() == "8.5x11"
    assert controller._get_settings().value("paper") == "8.5x11"
    window, _controller, _engine = poster_app
    dialog = _nyisd_meg_valodi_menu_kattintassal(window, controller, qt_app)
    assert _elem(dialog, "posterPaperBox").property("currentText") == "8.5x11"
    _kattintas(_elem(dialog, "posterCancelButton"))
    _var(
        qt_app,
        lambda: dialog.property("opened") is not True,
        "a Poszter párbeszéd nem zárult be a Mégse gombbal",
    )

    QLocale.setDefault(QLocale("hu_HU"))
    assert controller.posterPaperSizes() == ["10x15", "20x25"]
    assert controller.posterPaperSize() == "10x15"
    controller.setPosterPaperSize("20x25")
    assert controller.posterPaperSize() == "20x25"
