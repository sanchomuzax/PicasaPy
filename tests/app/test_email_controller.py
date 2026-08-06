"""`picasapy.app.email_controller.EmailController` (#32, RÉSZLEGES kör) —
a `subprocess`/tényleges küldés mockolva; az átméretezés-előkészítés és a
parancs-összeállítás valódi, determinisztikus logikával."""

from __future__ import annotations

from pathlib import Path

import os
from dataclasses import dataclass
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtGui import QGuiApplication

from picasapy.app.email_controller import EmailController
from support.jpeg_factory import make_jpeg


@pytest.fixture(scope="module")
def qt_app():
    return QGuiApplication.instance() or QGuiApplication([])


@dataclass
class _FakePhoto:
    folder_path: str
    name: str
    rotate_steps: int = 0
    filters: str | None = None


def _settings(tmp_path):
    return QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)


def _controller(photos, tmp_path):
    return EmailController(
        photo_source=lambda: photos, settings=_settings(tmp_path)
    )


class TestSizeSettingsDefaults:
    def test_default_multi_size_is_not_original(self, qt_app, tmp_path):
        controller = _controller([], tmp_path)
        # a Picasa-mintát követve a többfotós küldés alapból nem az eredeti
        # méretet küldi (levélméret-korlát) — a pontos index a modul
        # dokumentált alapértéke
        assert 0 <= controller.multiSizeIndex <= 4

    def test_default_single_size_is_original(self, qt_app, tmp_path):
        controller = _controller([], tmp_path)
        assert controller.singleSizeIndex == 4  # utolsó fokozat = eredeti

    def test_default_uses_default_mail_client(self, qt_app, tmp_path):
        controller = _controller([], tmp_path)
        assert controller.useDefaultClient is True


class TestSizeSettingsPersistence:
    def test_setting_multi_size_persists_across_instances(self, qt_app, tmp_path):
        settings = _settings(tmp_path)
        first = EmailController(photo_source=lambda: [], settings=settings)
        first.setMultiSizeIndex(0)
        second = EmailController(photo_source=lambda: [], settings=settings)
        assert second.multiSizeIndex == 0

    def test_setting_out_of_range_index_is_ignored(self, qt_app, tmp_path):
        controller = _controller([], tmp_path)
        before = controller.multiSizeIndex
        controller.setMultiSizeIndex(99)
        assert controller.multiSizeIndex == before

    def test_setting_same_value_does_not_emit_signal(self, qt_app, tmp_path):
        controller = _controller([], tmp_path)
        controller.setSingleSizeIndex(controller.singleSizeIndex)
        events = []
        controller.singleSizeIndexChanged.connect(lambda: events.append(1))
        controller.setSingleSizeIndex(controller.singleSizeIndex)
        assert events == []

    def test_toggle_use_default_client(self, qt_app, tmp_path):
        controller = _controller([], tmp_path)
        controller.setUseDefaultClient(False)
        assert controller.useDefaultClient is False


class TestPrepareAttachments:
    def test_original_size_returns_source_path_unchanged(self, qt_app, tmp_path):
        source = make_jpeg(tmp_path / "kép.jpg", size=(300, 200))
        photo = _FakePhoto(folder_path=str(tmp_path), name=source.name)
        controller = _controller([photo], tmp_path)
        controller.setSingleSizeIndex(4)  # eredeti méret
        result = controller.prepareAttachments([0], False)
        assert result == [str(source)]

    def test_smaller_preset_creates_a_resized_copy(self, qt_app, tmp_path):
        source = make_jpeg(tmp_path / "kép.jpg", size=(2000, 1000))
        photo = _FakePhoto(folder_path=str(tmp_path), name=source.name)
        controller = _controller([photo], tmp_path)
        controller.setMultiSizeIndex(0)  # 640 px
        result = controller.prepareAttachments([0], True)
        assert len(result) == 1
        assert result[0] != str(source)
        from PIL import Image

        with Image.open(result[0]) as image:
            assert max(image.size) <= 640

    def test_no_selection_returns_empty_list(self, qt_app, tmp_path):
        controller = _controller([], tmp_path)
        assert controller.prepareAttachments([], True) == []

    def test_out_of_range_row_is_skipped(self, qt_app, tmp_path):
        controller = _controller([], tmp_path)
        assert controller.prepareAttachments([5], True) == []


class TestSendRows:
    def test_uses_xdg_email_when_available(self, qt_app, tmp_path):
        controller = _controller([], tmp_path)
        with patch(
            "picasapy.app.email_controller.shutil.which", return_value="/usr/bin/xdg-email"
        ), patch("picasapy.app.email_controller.subprocess.Popen") as popen:
            ok = controller.sendRows(["/tmp/a.jpg"], "Tárgy", "Szöveg")
        assert ok is True
        popen.assert_called_once()
        argv = popen.call_args[0][0]
        assert argv[0] == "xdg-email"
        assert "--attach" in argv
        # Windowson a Path backslash-formát ad — az elvárás is azzal számol
        assert str(Path("/tmp/a.jpg")) in argv

    def test_popen_failure_emits_email_failed(self, qt_app, tmp_path):
        controller = _controller([], tmp_path)
        events = []
        controller.emailFailed.connect(events.append)
        with patch(
            "picasapy.app.email_controller.shutil.which", return_value="/usr/bin/xdg-email"
        ), patch(
            "picasapy.app.email_controller.subprocess.Popen",
            side_effect=OSError("boom"),
        ):
            ok = controller.sendRows(["/tmp/a.jpg"], "s", "b")
        assert ok is False
        assert events

    def test_falls_back_to_mailto_without_xdg_email(self, qt_app, tmp_path):
        controller = _controller([], tmp_path)
        with patch(
            "picasapy.app.email_controller.shutil.which", return_value=None
        ), patch(
            "picasapy.app.email_controller.QDesktopServices.openUrl",
            return_value=True,
        ) as open_url:
            ok = controller.sendRows(["/tmp/a.jpg"], "Tárgy", "Szöveg")
        assert ok is True
        open_url.assert_called_once()
        url = open_url.call_args[0][0].toString()
        assert url.startswith("mailto:")

    def test_mailto_fallback_with_attachments_warns(self, qt_app, tmp_path):
        controller = _controller([], tmp_path)
        events = []
        controller.emailFailed.connect(events.append)
        with patch(
            "picasapy.app.email_controller.shutil.which", return_value=None
        ), patch(
            "picasapy.app.email_controller.QDesktopServices.openUrl",
            return_value=True,
        ):
            controller.sendRows(["/tmp/a.jpg"], "s", "b")
        assert events  # figyelmeztetés: a csatolmány elveszik

    def test_mailto_fallback_without_attachments_is_silent(self, qt_app, tmp_path):
        controller = _controller([], tmp_path)
        events = []
        controller.emailFailed.connect(events.append)
        with patch(
            "picasapy.app.email_controller.shutil.which", return_value=None
        ), patch(
            "picasapy.app.email_controller.QDesktopServices.openUrl",
            return_value=True,
        ):
            controller.sendRows([], "s", "b")
        assert events == []

    def test_no_mail_program_found_emits_failure(self, qt_app, tmp_path):
        controller = _controller([], tmp_path)
        events = []
        controller.emailFailed.connect(events.append)
        with patch(
            "picasapy.app.email_controller.shutil.which", return_value=None
        ), patch(
            "picasapy.app.email_controller.QDesktopServices.openUrl",
            return_value=False,
        ):
            ok = controller.sendRows([], "s", "b")
        assert ok is False
        assert events
