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
    def test_az_alapertek_480_keppont(self, qt_app, tmp_path):
        """#2020: MÉRVE — az `EmailExportSize` alapértéke 480 (`0x1e0`),
        három független helyen a binárisban. A #350 becsült listájában ez
        az érték elő sem fordult."""
        controller = _controller([], tmp_path)
        assert controller.emailSize == 480

    def test_egy_kep_alapbol_a_KOZOS_meretet_kapja(self, qt_app, tmp_path):
        """#2020: az `EmailSinglePicture` alapértéke 0.

        ⚠️ Ez MEGVÁLTOZTATJA a #350 viselkedését, ahol egy kép alapból
        eredeti méretben ment."""
        controller = _controller([], tmp_path)
        assert controller.singlePictureOriginal is False

    def test_default_uses_default_mail_client(self, qt_app, tmp_path):
        controller = _controller([], tmp_path)
        assert controller.useDefaultClient is True


class TestSizeSettingsPersistence:
    def test_a_meret_tullel_egy_ujrainditast(self, qt_app, tmp_path):
        settings = _settings(tmp_path)
        first = EmailController(photo_source=lambda: [], settings=settings)
        first.setEmailSize(1200)
        second = EmailController(photo_source=lambda: [], settings=settings)
        assert second.emailSize == 1200

    def test_a_negativ_meret_nem_ir_felul(self, qt_app, tmp_path):
        controller = _controller([], tmp_path)
        before = controller.emailSize
        controller.setEmailSize(-5)
        assert controller.emailSize == before

    def test_a_fokozatlistan_kivuli_meret_ELFOGADOTT(self, qt_app, tmp_path):
        """A mező képpontszám, nem fokozat-sorszám (#2020).

        Fog: ha valaki visszateszi a nyolc fokozatra szűkítést, ez bukik —
        egy másik Picasa-verzióból örökölt 900 érvényes méret."""
        controller = _controller([], tmp_path)
        controller.setEmailSize(900)
        assert controller.emailSize == 900

    def test_setting_same_value_does_not_emit_signal(self, qt_app, tmp_path):
        controller = _controller([], tmp_path)
        events = []
        controller.singlePictureOriginalChanged.connect(lambda: events.append(1))
        controller.setSinglePictureOriginal(controller.singlePictureOriginal)
        assert events == []

    def test_toggle_use_default_client(self, qt_app, tmp_path):
        controller = _controller([], tmp_path)
        controller.setUseDefaultClient(False)
        assert controller.useDefaultClient is False


class TestRegiBeallitasAtvetele:
    """#2020: a #350 INDEX-alapú kulcsát képponttá kell alakítani.

    Enélkül a meglévő felhasználó `mail/multiSizeIndex=2` beállítása
    2 KÉPPONTOS méretként olvasódna — némán, észrevehetetlenül.
    """

    def _regi_indexszel(self, tmp_path, index):
        settings = _settings(tmp_path)
        settings.setValue("mail/multiSizeIndex", index)
        settings.sync()
        return EmailController(photo_source=lambda: [], settings=settings)

    @pytest.mark.parametrize(
        "index,varhato", [(0, 640), (1, 800), (2, 1024), (3, 1600), (4, 0)]
    )
    def test_a_regi_index_a_REGI_listan_oldodik_fel(
        self, qt_app, tmp_path, index, varhato
    ):
        controller = self._regi_indexszel(tmp_path, index)
        assert controller.emailSize == varhato

    def test_az_atvett_ertek_KIIRODIK_az_uj_kulcsba(self, qt_app, tmp_path):
        settings = _settings(tmp_path)
        settings.setValue("mail/multiSizeIndex", 1)
        settings.sync()
        EmailController(photo_source=lambda: [], settings=settings)
        assert int(settings.value("mail/exportSize")) == 800

    def test_az_UJ_kulcs_eroesebb_a_reginel(self, qt_app, tmp_path):
        settings = _settings(tmp_path)
        settings.setValue("mail/multiSizeIndex", 0)
        settings.setValue("mail/exportSize", 480)
        settings.sync()
        controller = EmailController(photo_source=lambda: [], settings=settings)
        assert controller.emailSize == 480

    def test_ertelmetlen_regi_index_az_alapertekre_esik(self, qt_app, tmp_path):
        controller = self._regi_indexszel(tmp_path, 99)
        assert controller.emailSize == 480


class TestPrepareAttachments:
    def test_original_size_returns_source_path_unchanged(self, qt_app, tmp_path):
        source = make_jpeg(tmp_path / "kép.jpg", size=(300, 200))
        photo = _FakePhoto(folder_path=str(tmp_path), name=source.name)
        controller = _controller([photo], tmp_path)
        controller.setSinglePictureOriginal(True)  # #2020: KAPCSOLÓ
        result = controller.prepareAttachments([0], False)
        assert result == [str(source)]

    def test_smaller_preset_creates_a_resized_copy(self, qt_app, tmp_path):
        source = make_jpeg(tmp_path / "kép.jpg", size=(2000, 1000))
        photo = _FakePhoto(folder_path=str(tmp_path), name=source.name)
        controller = _controller([photo], tmp_path)
        controller.setEmailSize(640)  # #2020: KÉPPONT, nem index
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
            "picasapy.app.email_controller._which", return_value="/usr/bin/xdg-email"
        ), patch("picasapy.app.email_controller._popen") as popen:
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
            "picasapy.app.email_controller._which", return_value="/usr/bin/xdg-email"
        ), patch(
            "picasapy.app.email_controller._popen",
            side_effect=OSError("boom"),
        ):
            ok = controller.sendRows(["/tmp/a.jpg"], "s", "b")
        assert ok is False
        assert events

    def test_falls_back_to_mailto_without_xdg_email(self, qt_app, tmp_path):
        controller = _controller([], tmp_path)
        with patch(
            "picasapy.app.email_controller._which", return_value=None
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
            "picasapy.app.email_controller._which", return_value=None
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
            "picasapy.app.email_controller._which", return_value=None
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
            "picasapy.app.email_controller._which", return_value=None
        ), patch(
            "picasapy.app.email_controller.QDesktopServices.openUrl",
            return_value=False,
        ):
            ok = controller.sendRows([], "s", "b")
        assert ok is False
        assert events


class TestRegiEgyKepBeallitasAtvetele:
    """#2020: a régi MÁSODIK méret-csúszka átvétele kapcsolóvá.

    Az új alapérték („ugyanakkora, mint a többi") a réginek az
    ELLENTÉTE — átvétel nélkül a meglévő felhasználó némán mást küldene,
    mint eddig.
    """

    def _regi_indexszel(self, tmp_path, index):
        settings = _settings(tmp_path)
        settings.setValue("mail/singleSizeIndex", index)
        settings.sync()
        return EmailController(photo_source=lambda: [], settings=settings)

    def test_a_regi_EREDETI_MERET_fokozat_bekapcsolja(self, qt_app, tmp_path):
        controller = self._regi_indexszel(tmp_path, 4)  # a régi lista vége
        assert controller.singlePictureOriginal is True

    @pytest.mark.parametrize("index", [0, 1, 2, 3])
    def test_a_tobbi_regi_fokozat_KIkapcsolva_hagyja(
        self, qt_app, tmp_path, index
    ):
        controller = self._regi_indexszel(tmp_path, index)
        assert controller.singlePictureOriginal is False

    def test_az_atvett_ertek_KIIRODIK(self, qt_app, tmp_path):
        settings = _settings(tmp_path)
        settings.setValue("mail/singleSizeIndex", 4)
        settings.sync()
        EmailController(photo_source=lambda: [], settings=settings)
        assert _coerce(settings.value("mail/singlePictureOriginal")) is True

    def test_beallitas_nelkul_az_UJ_alapertek_ervenyes(self, qt_app, tmp_path):
        controller = _controller([], tmp_path)
        assert controller.singlePictureOriginal is False


def _coerce(value):
    """A QSettings platformonként bool-t vagy szöveget ad ugyanarra az írásra."""
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("true", "1")
