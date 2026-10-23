"""#5639: Print Screen rögzítés, mentés és projekt-besorolás."""

from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QSettings
from PySide6.QtGui import QImage, QColor

from picasapy.app.screen_capture import (
    CaptureMode,
    CaptureTarget,
    ScreenCaptureController,
    capture_once,
    print_screen_pressed,
    save_screenshot,
    screen_capture_folder,
    select_capture_target,
)
from picasapy.ini.folder_category import (
    PROJECTS_CATEGORY,
    read_folder_category,
)
from picasapy.ini.io import load_document
from picasapy.ini.names import INI_NAME


class FakeCaptureSource:
    """Windows-képernyőforrás helyett injektált cél- és képforrás."""

    supported = True

    def __init__(self, *, foreground=101, cursor=202):
        self.foreground = foreground
        self.cursor = cursor
        self.pressed_keys = set()
        self.captured_targets = []
        self.image = QImage(3, 2, QImage.Format.Format_RGB32)
        self.image.fill(QColor(25, 80, 140))

    def is_key_down(self, virtual_key):
        return virtual_key in self.pressed_keys

    def foreground_window(self):
        return self.foreground

    def cursor_window(self):
        return self.cursor

    def capture(self, target):
        self.captured_targets.append(target)
        return self.image

    def window_title(self, target):
        if target.mode is CaptureMode.DESKTOP:
            return ""
        return "Editor: Photo"


def test_beallitas_alapertelmezetten_be_es_kikapcsolva_nem_indit_figyelot(
    tmp_path, qt_app,
):
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    source = FakeCaptureSource()

    alap = ScreenCaptureController(settings=settings, source=source)
    try:
        assert alap.enabled is True
        assert alap.isListening is True
    finally:
        alap.shutdown()

    settings.setValue("Preferences/EnableScreenCap", False)
    kikapcsolt_forras = FakeCaptureSource()
    kikapcsolt = ScreenCaptureController(settings=settings, source=kikapcsolt_forras)
    try:
        assert kikapcsolt.enabled is False
        assert kikapcsolt.isListening is False
        assert kikapcsolt_forras.captured_targets == []
    finally:
        kikapcsolt.shutdown()


def test_globalis_figyeles_nelkul_hiba_uzenet_nelkul_kimarad(tmp_path, caplog):
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    source = FakeCaptureSource()
    source.supported = False

    controller = ScreenCaptureController(settings=settings, source=source)
    try:
        assert controller.enabled is True
        assert controller.isListening is False
        assert not [record for record in caplog.records if record.levelname == "ERROR"]
    finally:
        controller.shutdown()


def test_a_harom_celmod_es_az_alt_elvezeti_a_ctrlt(tmp_path):
    assert select_capture_target(False, False, foreground=101, cursor=202) == (
        CaptureTarget(CaptureMode.DESKTOP)
    )
    assert select_capture_target(True, False, foreground=101, cursor=202) == (
        CaptureTarget(CaptureMode.FOREGROUND_WINDOW, 101)
    )
    assert select_capture_target(False, True, foreground=101, cursor=202) == (
        CaptureTarget(CaptureMode.CURSOR_WINDOW, 202)
    )
    assert select_capture_target(True, True, foreground=101, cursor=202) == (
        CaptureTarget(CaptureMode.CURSOR_WINDOW, 202)
    )

    source = FakeCaptureSource()
    for index, (ctrl, alt) in enumerate(
        ((False, False), (True, False), (False, True))
    ):
        capture_once(
            source,
            tmp_path / f"screen-capture-mode-{index}",
            ctrl_pressed=ctrl,
            alt_pressed=alt,
            now=datetime(2026, 10, 23, 9, 8, 7),
            date_time_text="09.08.07",
        )
    assert source.captured_targets == [
        CaptureTarget(CaptureMode.DESKTOP),
        CaptureTarget(CaptureMode.FOREGROUND_WINDOW, 101),
        CaptureTarget(CaptureMode.CURSOR_WINDOW, 202),
    ]


def test_a_print_screen_es_a_print_is_inditja_a_figyelot():
    source = FakeCaptureSource()
    source.pressed_keys.add(0x2C)
    assert print_screen_pressed(source) is True

    source.pressed_keys.clear()
    source.pressed_keys.add(0x2A)
    assert print_screen_pressed(source) is True

    source.pressed_keys.clear()
    assert print_screen_pressed(source) is False


def test_a_kepforras_injektalhato_es_a_mentett_kep_utja_visszater(tmp_path):
    source = FakeCaptureSource()
    when = datetime(2026, 10, 23, 9, 8, 7)
    folder = tmp_path / "Picasa" / "Screen Captures"

    saved = capture_once(
        source,
        folder,
        ctrl_pressed=True,
        alt_pressed=False,
        now=when,
        date_time_text="2026. 10. 23. 09.08.07",
    )

    assert source.captured_targets == [
        CaptureTarget(CaptureMode.FOREGROUND_WINDOW, 101)
    ]
    assert saved == folder / "Editor_ Photo 2026. 10. 23. 09.08.07.bmp"
    assert saved.is_file()


def test_hianyzik_ablakcimnel_tartaleknev_es_utkozesnel_kotott_sorszam(tmp_path):
    folder = tmp_path / "Screen Captures"
    image = QImage(2, 2, QImage.Format.Format_RGB32)
    image.fill(QColor("red"))
    when = datetime(2026, 10, 23, 9, 8, 7)

    first = save_screenshot(
        image, folder, "", when, date_time_text="2026. 10. 23. 09.08.07"
    )
    second = save_screenshot(
        image, folder, "", when, date_time_text="2026. 10. 23. 09.08.07"
    )
    third = save_screenshot(
        image, folder, "", when, date_time_text="2026. 10. 23. 09.08.07"
    )

    assert first.name == "Fullscreen capture 2026. 10. 23. 09.08.07.bmp"
    assert second.name == "Fullscreen capture 2026. 10. 23. 09.08.07-001.bmp"
    assert third.name == "Fullscreen capture 2026. 10. 23. 09.08.07-002.bmp"


def test_bmp_24_bites_tomoritetlen_es_a_mappa_a_projektekhez_tartozik(tmp_path):
    image = QImage(3, 2, QImage.Format.Format_RGB32)
    image.fill(QColor(25, 80, 140))
    folder = tmp_path / "Picasa" / "Screen Captures"

    saved = save_screenshot(
        image,
        folder,
        "Window",
        datetime(2026, 10, 23, 9, 8, 7),
        date_time_text="2026. 10. 23. 09.08.07",
    )

    raw = saved.read_bytes()
    assert raw[:2] == b"BM"
    assert int.from_bytes(raw[28:30], "little") == 24
    assert int.from_bytes(raw[30:34], "little") == 0
    assert raw[54:57]  # BMP-képpontadat is van a fejléc után.
    document = load_document(folder / INI_NAME)
    assert read_folder_category(document) == PROJECTS_CATEGORY


def test_screen_captures_mappa_neve_a_meglevo_honositast_hasznalja(tmp_path):
    pictures = tmp_path / "Pictures"
    (pictures / "Picasa" / "Képernyőfelvételek").mkdir(parents=True)

    assert screen_capture_folder(pictures, "en") == (
        pictures / "Picasa" / "Képernyőfelvételek"
    )
