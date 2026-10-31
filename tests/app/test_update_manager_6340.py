"""#6340: frissítés-ellenőrzés, letöltés és biztonságos csere."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError

import pytest

from picasapy.app.update_manager import (
    GitHubReleaseClient,
    AUTO_CHECK_KEY,
    LAST_AUTO_CHECK_KEY,
    ReleaseInfo,
    SKIPPED_VERSION_KEY,
    UpdateController,
    automatic_check_is_due,
    installation_kind,
    parse_sha256sums,
    release_is_newer,
    should_offer_release,
    verify_sha256,
)
from picasapy.app import update_swap_helper
from picasapy.app.update_swap_helper import swap_update_directory


@pytest.mark.parametrize(
    ("current", "latest", "expected"),
    [
        ("1.0.0", "1.0.1", True),
        ("1.0.0", "1.0.0", False),
        ("1.0.2", "1.0.1", False),
        ("1.9.9", "1.10.0", True),
        ("1.0.0-rc.1", "1.0.0", True),
        ("1.0.0", "1.1.0-rc.1", True),
    ],
)
def test_release_verziot_teljes_verziokent_hasonlitja_ossze(current, latest, expected):
    assert release_is_newer(latest, current) is expected


def test_napi_automatikus_korlat_utc_naptari_nap_alapjan():
    today = datetime(2026, 10, 31, 15, tzinfo=timezone.utc)
    assert automatic_check_is_due(None, today)
    assert not automatic_check_is_due("2026-10-31", today)
    assert automatic_check_is_due("2026-10-30", today)


def test_kikapcsolt_automatikus_ellenorzes_nem_indit_napi_ellenorzest():
    today = datetime(2026, 10, 31, 15, tzinfo=timezone.utc)
    assert not automatic_check_is_due(None, today, enabled=False)


def test_kihagyott_verziot_tobbe_nem_ajanl_fel():
    assert should_offer_release("1.2.0", skipped_version="1.2.0") is False
    assert should_offer_release("1.2.1", skipped_version="1.2.0") is True


def test_a_futtatasi_hely_alapjan_megkulonbozteti_a_windows_deb_es_pip_modot():
    assert installation_kind(
        frozen=True, platform="nt", executable="C:/PicasaPy/PicasaPy.exe"
    ) == "windows"
    assert installation_kind(
        frozen=False,
        platform="posix",
        executable="/usr/bin/python3",
        package_path="/usr/lib/python3/dist-packages/picasapy/app/update_manager.py",
    ) == "deb"
    assert installation_kind(
        frozen=False,
        platform="posix",
        executable="/usr/bin/python3",
        package_path="/home/user/.local/lib/python3.12/site-packages/picasapy/app/update_manager.py",
    ) == "pip"


def test_a_github_kiadasi_kliens_helyettesitheto_es_a_latest_api_utvonalat_keri():
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'{"tag_name":"v1.2.0","body":"Notes","assets":[]}'

    requested = []

    def opener(request, timeout):
        requested.append((request.full_url, timeout))
        return Response()

    release = GitHubReleaseClient(opener=opener).latest_release()

    assert release.version == "1.2.0"
    assert release.notes == "Notes"
    assert requested[0][0].endswith("/repos/sanchomuzax/PicasaPy/releases/latest")


def test_sha256sum_manifestbol_a_celzott_asset_hasha_olvashato():
    manifest = "a" * 64 + "  PicasaPy-windows-x64.zip\n" + "b" * 64 + "  other.zip\n"
    assert parse_sha256sums(manifest)["PicasaPy-windows-x64.zip"] == "a" * 64


def test_sha256_elteres_hibaval_megallitja_a_telepitest():
    payload = b"new app"
    actual = hashlib.sha256(payload).hexdigest()
    assert verify_sha256(payload, actual)
    with pytest.raises(ValueError, match="SHA-256"):
        verify_sha256(payload, "0" * 64)


def _app(path: Path, text: str) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "app.txt").write_text(text, encoding="utf-8")


def test_sikeres_csere_megtartja_az_elozo_verziot_es_ujraindit(tmp_path):
    app = tmp_path / "PicasaPy"
    stage = tmp_path / "staged"
    _app(app, "old")
    _app(stage, "new")
    started = []

    assert swap_update_directory(
        stage,
        app,
        launch=lambda: started.append((app / "app.txt").read_text(encoding="utf-8")) or True,
    )

    assert (app / "app.txt").read_text(encoding="utf-8") == "new"
    assert (tmp_path / "PicasaPy.previous" / "app.txt").read_text(encoding="utf-8") == "old"
    assert started == ["new"]


def test_uj_verzio_inditasi_hibaja_visszaallitja_az_elsozot(tmp_path):
    app = tmp_path / "PicasaPy"
    stage = tmp_path / "staged"
    _app(app, "old")
    _app(stage, "new")

    assert not swap_update_directory(stage, app, launch=lambda: False)

    assert (app / "app.txt").read_text(encoding="utf-8") == "old"
    assert not (tmp_path / "PicasaPy.previous").exists()


def test_windows_varakozas_helyettesitheto_folyamatkezelo_fogantyuval(monkeypatch):
    waited = []
    monkeypatch.setattr(update_swap_helper, "_platform", lambda: "win32")
    monkeypatch.setattr(update_swap_helper, "_wait_for_windows_process", waited.append)
    monkeypatch.setattr(
        update_swap_helper,
        "_kill",
        lambda *_args: pytest.fail("Windows alatt nem használható az os.kill-os próba"),
    )

    update_swap_helper.wait_for_process(1234)

    assert waited == [1234]


def test_zip_kicsomagolas_kozbeni_hiba_utan_nincs_reszleges_programcsere(tmp_path):
    app = tmp_path / "PicasaPy"
    stage = tmp_path / "staged"
    _app(app, "old")
    _app(stage, "new")
    (stage / "broken.txt").write_text("partial", encoding="utf-8")

    with pytest.raises(ValueError, match="stage"):
        swap_update_directory(
            stage,
            app,
            launch=lambda: (_ for _ in ()).throw(ValueError("stage is incomplete")),
        )

    assert (app / "app.txt").read_text(encoding="utf-8") == "old"


class _MemorySettings:
    def __init__(self, values=None):
        self.values = dict(values or {})

    def value(self, key, default=None):
        return self.values.get(key, default)

    def setValue(self, key, value):
        self.values[key] = value

    def sync(self):
        pass


class _InlinePool:
    def start(self, worker):
        worker.run()


class _ReleaseClient:
    def __init__(self, release=None, error=None):
        self.release = release
        self.error = error
        self.checks = 0

    def latest_release(self):
        self.checks += 1
        if self.error:
            raise self.error
        return self.release


def _release(version: str) -> ReleaseInfo:
    return ReleaseInfo(version, "Notes", "https://example.test/release", ())


def test_offline_automatikus_hiba_csendben_marad_es_a_napi_korlatot_rogziti(qt_app):
    settings = _MemorySettings()
    client = _ReleaseClient(error=URLError("offline"))
    controller = UpdateController(
        "1.0.0", settings=settings, client=client, pool=_InlinePool(), schedule=False
    )
    notices = []
    controller.notificationRequested.connect(lambda: notices.append(True))

    controller._automatic_check_if_due()

    assert client.checks == 1
    assert notices == []
    assert settings.value(LAST_AUTO_CHECK_KEY) == datetime.now(timezone.utc).date().isoformat()
    assert controller.autoCheckEnabled is True


def test_kezi_ellenorzes_uj_verziot_jelez_de_a_kihagyottat_nem_ajanlja_fel(qt_app):
    settings = _MemorySettings({SKIPPED_VERSION_KEY: "1.2.0"})
    client = _ReleaseClient(_release("1.2.0"))
    controller = UpdateController(
        "1.0.0", settings=settings, client=client, pool=_InlinePool(), schedule=False
    )
    outcomes = []
    controller.manualCheckFinished.connect(
        lambda available, result: outcomes.append((available, result))
    )

    controller.checkForUpdates()

    assert outcomes == [(False, "up-to-date")]
    assert not controller.updateAvailable


def test_automatikus_ellenorzes_alapbol_engedelyezett_es_naponta_egyszer_fut(qt_app):
    settings = _MemorySettings({AUTO_CHECK_KEY: True})
    client = _ReleaseClient(_release("1.1.0"))
    controller = UpdateController(
        "1.0.0", settings=settings, client=client, pool=_InlinePool(), schedule=False
    )
    notices = []
    controller.notificationRequested.connect(lambda: notices.append(True))

    controller._automatic_check_if_due()
    controller._automatic_check_if_due()

    assert client.checks == 1
    assert controller.updateAvailable
    assert notices == [True]
