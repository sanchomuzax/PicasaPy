"""`picasapy.app.email_controller.EmailController` (#32, RÉSZLEGES kör) —
a `subprocess`/tényleges küldés mockolva; a képelőkészítés és a
parancs-összeállítás valódi, determinisztikus logikával."""

from __future__ import annotations

from pathlib import Path

import os
import tempfile
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtGui import QGuiApplication
from PIL import Image, ImageDraw

from picasapy.app import email_controller as email_controller_module
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
    #: #2902: a valódi `PhotoRecord`-nak is van tükrözés-jelzője, és a
    #: melléklet-készítés beégeti — a hasonmásnak is tudnia kell róla
    flip_flags: int = 0
    filters: str | None = None


def _settings(tmp_path):
    return QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)


def _controller(photos, tmp_path):
    return EmailController(
        photo_source=lambda: photos, settings=_settings(tmp_path)
    )


@pytest.fixture(autouse=True)
def _email_temp_directory_in_worktree(tmp_path, monkeypatch):
    """A vezérlő minden ideiglenes exportja a közös pytest-basetempbe kerüljön."""
    target = tmp_path / "email-temp"
    target.mkdir()
    real_mkdtemp = tempfile.mkdtemp
    monkeypatch.setattr(
        email_controller_module,
        "tempfile",
        SimpleNamespace(
            mkdtemp=lambda prefix: real_mkdtemp(prefix=prefix, dir=target)
        ),
    )


def _make_quadrant_jpeg(path):
    colors = {
        "red": (255, 0, 0),
        "green": (0, 255, 0),
        "blue": (0, 0, 255),
        "yellow": (255, 255, 0),
    }
    image = Image.new("RGB", (80, 48))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 39, 23), fill=colors["red"])
    draw.rectangle((40, 0, 79, 23), fill=colors["green"])
    draw.rectangle((0, 24, 39, 47), fill=colors["blue"])
    draw.rectangle((40, 24, 79, 47), fill=colors["yellow"])
    image.save(path, "JPEG", quality=100, subsampling=0)
    return colors


def _quadrant_pixels(image):
    width, height = image.size
    return (
        image.getpixel((width // 4, height // 4)),
        image.getpixel((3 * width // 4, height // 4)),
        image.getpixel((width // 4, 3 * height // 4)),
        image.getpixel((3 * width // 4, 3 * height // 4)),
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

    def test_default_KERDEZ_friss_profilon(self, qt_app, tmp_path):
        """#2184: MEGFORDULT. Az eredetiben a `DoNotPromptForEmailPref`
        alapértéke 0, vagyis az első küldéskor a választó párbeszéd
        MEGJELENIK (`0x00742154`/`0x00742168`, mérve). Korábban nálunk
        alapból az alapértelmezett kliens ment, és a párbeszéd
        elérhetetlen volt annak, aki sosem nyitja meg az Opciókat."""
        controller = _controller([], tmp_path)
        assert controller.useDefaultClient is False


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


class TestMovieSettings:
    def test_video_kuldes_alapertelmezettje_elsokocka_es_mentodik(
        self, qt_app, tmp_path
    ):
        settings = _settings(tmp_path)
        first = EmailController(photo_source=lambda: [], settings=settings)

        assert first.movieFull is False

        first.setMovieFull(True)
        settings.sync()
        second = EmailController(
            photo_source=lambda: [], settings=_settings(tmp_path)
        )

        assert second.movieFull is True

    def test_elso_kocka_modban_a_belyegkep_dekodolasa_keszit_jpeget(
        self, qt_app, tmp_path, monkeypatch
    ):
        import numpy as np
        from picasapy.thumbs import cache as thumbnail_cache

        source = tmp_path / "felvetel.mp4"
        source.write_bytes(b"tesztvideo")
        frame = np.zeros((48, 80, 3), dtype=np.uint8)
        frame[:, :] = (0, 0, 255)  # BGR: piros képkocka
        dekodolt = []

        def _dekodol(utvonal):
            dekodolt.append(Path(utvonal))
            return frame.copy()

        monkeypatch.setattr(
            thumbnail_cache, "_decode_video_frame_isolated", _dekodol
        )
        photo = _FakePhoto(folder_path=str(tmp_path), name=source.name)
        controller = _controller([photo], tmp_path)

        attachments = controller.prepareAttachments([0], True)

        assert dekodolt == [source]
        assert len(attachments) == 1
        attachment = Path(attachments[0])
        assert attachment.suffix == ".jpg"
        with Image.open(attachment) as image:
            assert image.format == "JPEG"
            assert image.size == (80, 48)
            red, green, blue = image.convert("RGB").getpixel((40, 24))
        assert red > 220 and green < 35 and blue < 35

    def test_teljes_film_modban_a_video_teljes_masolatban_csatalodik(
        self, qt_app, tmp_path
    ):
        source = tmp_path / "felvetel.mp4"
        tartalom = b"a teljes film bytejai"
        source.write_bytes(tartalom)
        photo = _FakePhoto(folder_path=str(tmp_path), name=source.name)
        controller = _controller([photo], tmp_path)
        controller.setMovieFull(True)

        attachments = controller.prepareAttachments([0], True)

        assert len(attachments) == 1
        attachment = Path(attachments[0])
        assert attachment.suffix == ".mp4"
        assert attachment.read_bytes() == tartalom


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
    @pytest.mark.parametrize(
        "rotate_steps,flip_flags,filters,expected_size,expected_quadrants,grayscale",
        [
            (0, 1, None, (80, 48), ("green", "red", "yellow", "blue"), False),
            (1, 0, None, (48, 80), ("blue", "red", "yellow", "green"), False),
            (3, 0, None, (48, 80), ("green", "yellow", "red", "blue"), False),
            (0, 0, "bw=1;", (80, 48), None, True),
            (0, 0, None, (80, 48), ("red", "green", "blue", "yellow"), False),
        ],
        ids=(
            "tukrozes",
            "90-fok-jobbra",
            "90-fok-balra",
            "fekete-feher",
            "valtozatlan",
        ),
    )
    def test_original_size_attachment_contains_rendered_jpeg_pixels(
        self,
        qt_app,
        tmp_path,
        rotate_steps,
        flip_flags,
        filters,
        expected_size,
        expected_quadrants,
        grayscale,
    ):
        """Eredeti méretnél is a beégetett változat megy csatolmányként."""
        source = tmp_path / "negynegyed.jpg"
        colors = _make_quadrant_jpeg(source)
        photo = _FakePhoto(
            folder_path=str(tmp_path),
            name=source.name,
            rotate_steps=rotate_steps,
            flip_flags=flip_flags,
            filters=filters,
        )
        controller = _controller([photo], tmp_path)
        controller.setSinglePictureOriginal(True)  # #2020: KAPCSOLÓ
        attachments = controller.prepareAttachments([0], False)

        # rontás-kontroll: javítás nélkül mind az öt eset a forrás útvonalát
        # kapja vissza, ezért ez az állítás minden parametrizált tesztben piros.
        assert len(attachments) == 1
        attachment = Path(attachments[0])

        with Image.open(attachment) as exported:
            assert exported.format == "JPEG"
            assert exported.size == expected_size
            rendered = exported.convert("RGB")

        if grayscale:
            assert all(max(pixel) - min(pixel) <= 8 for pixel in rendered.getdata())
        else:
            expected_colors = [colors[name] for name in expected_quadrants]
            for actual, expected in zip(
                _quadrant_pixels(rendered), expected_colors, strict=True
            ):
                assert all(
                    abs(channel - target) <= 35
                    for channel, target in zip(actual, expected, strict=True)
                )

        if filters is None and not rotate_steps and not flip_flags:
            with Image.open(source) as original:
                assert list(rendered.getdata()) == list(original.convert("RGB").getdata())

        assert attachment != source

    def test_smaller_preset_creates_a_resized_copy(self, qt_app, tmp_path):
        source = make_jpeg(tmp_path / "kép.jpg", size=(2000, 1000))
        photo = _FakePhoto(folder_path=str(tmp_path), name=source.name)
        controller = _controller([photo], tmp_path)
        controller.setEmailSize(640)  # #2020: KÉPPONT, nem index
        result = controller.prepareAttachments([0], True)
        assert len(result) == 1
        assert result[0] != str(source)
        with Image.open(result[0]) as image:
            assert max(image.size) <= 640

    def test_no_selection_returns_empty_list(self, qt_app, tmp_path):
        controller = _controller([], tmp_path)
        assert controller.prepareAttachments([], True) == []

    def test_out_of_range_row_is_skipped(self, qt_app, tmp_path):
        controller = _controller([], tmp_path)
        assert controller.prepareAttachments([5], True) == []


def _kuldo_controller(photos, tmp_path):
    """Vezérlő, amelyik AZONNAL küld — a választó párbeszéd nélkül.

    #2184 óta friss profilon a `sendRows()` előbb megkérdezi, mivel
    küldjön (ez az eredeti viselkedése). Ezek a próbák viszont magát a
    KÜLDÉST mérik, ezért itt előre eldöntjük a kérdést — ugyanúgy, ahogy
    a felhasználó teszi, ha bepipálja a „ne kérdezz többé"-t."""
    controller = _controller(photos, tmp_path)
    controller.setUseDefaultClient(True)
    return controller


class TestSendRows:
    def test_uses_xdg_email_when_available(self, qt_app, tmp_path):
        controller = _kuldo_controller([], tmp_path)
        with patch(
            "picasapy.app.email_controller._which", return_value="/usr/bin/xdg-email"
        ), patch("picasapy.app.email_controller._popen") as popen:
            popen.return_value.wait.return_value = 0
            ok = controller.sendWithDefaultClient(
                ["/tmp/a.jpg"], "Tárgy", "Szöveg", False
            )
        assert ok is True
        popen.assert_called_once()
        argv = popen.call_args[0][0]
        assert argv[0] == "xdg-email"
        assert "--attach" in argv
        # Windowson a Path backslash-formát ad — az elvárás is azzal számol
        assert str(Path("/tmp/a.jpg")) in argv

    def test_nonzero_xdg_email_exit_emits_failure(self, qt_app, tmp_path):
        controller = _kuldo_controller([], tmp_path)
        events = []
        controller.emailFailed.connect(events.append)
        with patch(
            "picasapy.app.email_controller._which", return_value="/usr/bin/xdg-email"
        ), patch("picasapy.app.email_controller._popen") as popen:
            popen.return_value.wait.return_value = 3
            ok = controller.sendWithDefaultClient(
                ["/tmp/a.jpg"], "Tárgy", "Szöveg", False
            )

        assert ok is False
        assert events == [controller.tr("No email program was found.")]
        popen.return_value.wait.assert_called_once_with(
            timeout=email_controller_module._XDG_EMAIL_VARAKOZAS_S
        )

    def test_popen_failure_emits_email_failed(self, qt_app, tmp_path):
        controller = _kuldo_controller([], tmp_path)
        events = []
        controller.emailFailed.connect(events.append)
        with patch(
            "picasapy.app.email_controller._which", return_value="/usr/bin/xdg-email"
        ), patch(
            "picasapy.app.email_controller._popen",
            side_effect=OSError("boom"),
        ):
            ok = controller.sendWithDefaultClient(["/tmp/a.jpg"], "s", "b", False)
        assert ok is False
        assert events

    def test_falls_back_to_mailto_without_xdg_email(self, qt_app, tmp_path):
        controller = _kuldo_controller([], tmp_path)
        with patch(
            "picasapy.app.email_controller._which", return_value=None
        ), patch(
            "picasapy.app.email_controller.QDesktopServices.openUrl",
            return_value=True,
        ) as open_url:
            ok = controller.sendWithDefaultClient(
                ["/tmp/a.jpg"], "Tárgy", "Szöveg", False
            )
        assert ok is True
        open_url.assert_called_once()
        url = open_url.call_args[0][0].toString()
        assert url.startswith("mailto:")

    def test_mailto_fallback_with_attachments_warns(self, qt_app, tmp_path):
        controller = _kuldo_controller([], tmp_path)
        events = []
        controller.emailFailed.connect(events.append)
        with patch(
            "picasapy.app.email_controller._which", return_value=None
        ), patch(
            "picasapy.app.email_controller.QDesktopServices.openUrl",
            return_value=True,
        ):
            controller.sendWithDefaultClient(["/tmp/a.jpg"], "s", "b", False)
        assert events  # figyelmeztetés: a csatolmány elveszik

    def test_mailto_fallback_without_attachments_is_silent(self, qt_app, tmp_path):
        controller = _kuldo_controller([], tmp_path)
        events = []
        controller.emailFailed.connect(events.append)
        with patch(
            "picasapy.app.email_controller._which", return_value=None
        ), patch(
            "picasapy.app.email_controller.QDesktopServices.openUrl",
            return_value=True,
        ):
            controller.sendWithDefaultClient([], "s", "b", False)
        assert events == []

    def test_no_mail_program_found_emits_failure(self, qt_app, tmp_path):
        controller = _kuldo_controller([], tmp_path)
        events = []
        controller.emailFailed.connect(events.append)
        with patch(
            "picasapy.app.email_controller._which", return_value=None
        ), patch(
            "picasapy.app.email_controller.QDesktopServices.openUrl",
            return_value=False,
        ):
            ok = controller.sendWithDefaultClient([], "s", "b", False)
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
