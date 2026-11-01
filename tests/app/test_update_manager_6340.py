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
    AUTO_CHECK_INTERVAL_MS,
    UpdateController,
    automatic_check_is_due,
    installation_kind,
    parse_sha256sums,
    release_is_newer,
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


def test_az_automatikus_kereses_nem_napi_korlathoz_kotott():
    """#6379: a mai korábbi keresés nem tiltja le a következőt."""
    assert automatic_check_is_due()
    assert automatic_check_is_due(enabled=True)


def test_kikapcsolt_automatikus_ellenorzes_nem_indit_ellenorzest():
    assert not automatic_check_is_due(enabled=False)


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


def test_sikeres_csere_eltavolitja_a_regi_mappat_es_ujraindit(tmp_path):
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
    assert not (tmp_path / "PicasaPy.previous").exists()
    assert started == ["new"]


def test_sikeres_csere_atviszi_az_eltavolitot_es_torli_a_regi_mappat(tmp_path):
    app = tmp_path / "PicasaPy"
    stage = tmp_path / "staged"
    _app(app, "old")
    (app / "unins000.exe").write_bytes(b"uninstaller")
    (app / "unins000.dat").write_bytes(b"uninstaller data")
    _app(stage, "new")

    assert swap_update_directory(stage, app, launch=lambda: True)

    assert (app / "unins000.exe").read_bytes() == b"uninstaller"
    assert (app / "unins000.dat").read_bytes() == b"uninstaller data"
    assert not (tmp_path / "PicasaPy.previous").exists()


def test_uj_verzio_inditasi_hibaja_visszaallitja_az_elsozot(tmp_path):
    app = tmp_path / "PicasaPy"
    stage = tmp_path / "staged"
    _app(app, "old")
    (app / "unins000.exe").write_bytes(b"old uninstaller")
    _app(stage, "new")

    assert not swap_update_directory(stage, app, launch=lambda: False)

    assert (app / "app.txt").read_text(encoding="utf-8") == "old"
    assert (app / "unins000.exe").read_bytes() == b"old uninstaller"
    assert not (tmp_path / "PicasaPy.previous").exists()


def test_indulaskori_takaritas_hatterben_atviszi_a_hianyzo_eltavolitot(
    tmp_path, monkeypatch
):
    from picasapy.app import update_cleanup

    app = tmp_path / "PicasaPy"
    previous = tmp_path / "PicasaPy.previous"
    app.mkdir()
    previous.mkdir()
    executable = app / "PicasaPy.exe"
    (app / "unins000.exe").write_bytes(b"uj, mar meglevo")
    (previous / "unins000.exe").write_bytes(b"regi exe")
    (previous / "unins000.dat").write_bytes(b"regi adat")
    monkeypatch.setattr(update_cleanup, "_platform", lambda: "win32")
    monkeypatch.setattr(update_cleanup, "_frozen", lambda: True)
    monkeypatch.setattr(update_cleanup, "_executable_path", lambda: executable)
    szalak = []

    class _HatterSzala:
        def __init__(self, *, target, name, daemon):
            szalak.append((target, name, daemon))

        def start(self):
            pass

    monkeypatch.setattr(update_cleanup, "_thread", _HatterSzala)

    update_cleanup.start_startup_cleanup()

    assert len(szalak) == 1
    cel, nev, daemon = szalak[0]
    assert nev
    assert daemon is True
    cel()
    assert (app / "unins000.exe").read_bytes() == b"uj, mar meglevo"
    assert (app / "unins000.dat").read_bytes() == b"regi adat"
    assert not previous.exists()


def test_indulaskori_takaritas_nem_frozen_futasnal_nem_indit_szalat(
    tmp_path, monkeypatch
):
    from picasapy.app import update_cleanup

    app = tmp_path / "PicasaPy"
    previous = tmp_path / "PicasaPy.previous"
    app.mkdir()
    previous.mkdir()
    (previous / "unins000.exe").write_bytes(b"uninstaller")
    monkeypatch.setattr(update_cleanup, "_platform", lambda: "win32")
    monkeypatch.setattr(update_cleanup, "_frozen", lambda: False)
    monkeypatch.setattr(update_cleanup, "_executable_path", lambda: app / "PicasaPy.exe")

    class _TiltottSzala:
        def __init__(self, **_kwargs):
            pytest.fail("nem frozen futásnál nem indulhat takarító szál")

    monkeypatch.setattr(update_cleanup, "_thread", _TiltottSzala)

    update_cleanup.start_startup_cleanup()

    assert previous.exists()
    assert (previous / "unins000.exe").is_file()


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

    def remove(self, key):
        self.values.pop(key, None)

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


def test_offline_automatikus_hiba_csendben_marad_es_a_keresest_rogziti(qt_app):
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
    assert str(settings.value(LAST_AUTO_CHECK_KEY)).startswith(
        datetime.now(timezone.utc).date().isoformat()
    )
    assert controller.autoCheckEnabled is True


def test_kezi_ellenorzes_a_regi_kihagyas_utan_is_felajanlja_a_legujabbat(qt_app):
    """#6394: a korábban kihagyott verzió induláskor újra felkínálható."""
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

    assert outcomes == [(True, "available")]
    assert controller.updateAvailable


def test_induláskor_a_korabbi_kihagyas_torlodik(qt_app):
    """#6394: a „Verzió kihagyása” már nincs; a régi beállítás induláskor törlődik."""
    settings = _MemorySettings({SKIPPED_VERSION_KEY: "1.2.0"})
    UpdateController(
        "1.0.0", settings=settings, client=_ReleaseClient(), pool=_InlinePool(), schedule=False
    )

    assert SKIPPED_VERSION_KEY not in settings.values


def test_automatikus_ellenorzes_minden_alkalommal_fut_de_csak_egyszer_ertesit(qt_app):
    """#6379: a napi korlát megszűnt; az értesítés verziónként egyszer jön."""
    today = datetime.now(timezone.utc).date().isoformat()
    settings = _MemorySettings({AUTO_CHECK_KEY: True, LAST_AUTO_CHECK_KEY: today})
    client = _ReleaseClient(_release("1.1.0"))
    controller = UpdateController(
        "1.0.0", settings=settings, client=client, pool=_InlinePool(), schedule=False
    )
    notices = []
    controller.notificationRequested.connect(lambda: notices.append(True))

    controller._automatic_check_if_due()
    controller._automatic_check_if_due()

    assert client.checks == 2
    assert controller.updateAvailable
    assert notices == [True]


def test_kikapcsolt_automatikus_kereses_nem_fordul_a_klienshez(qt_app):
    settings = _MemorySettings({AUTO_CHECK_KEY: False})
    client = _ReleaseClient(_release("1.1.0"))
    controller = UpdateController(
        "1.0.0", settings=settings, client=client, pool=_InlinePool(), schedule=False
    )

    controller._automatic_check_if_due()

    assert client.checks == 0


def test_futas_kozben_hat_orankent_ujra_keres(qt_app):
    """#6379: a napokig nyitva hagyott program is észreveszi az új verziót."""
    client = _ReleaseClient(_release("1.1.0"))
    controller = UpdateController(
        "1.0.0",
        settings=_MemorySettings({AUTO_CHECK_KEY: True}),
        client=client,
        pool=_InlinePool(),
        schedule=False,
    )

    controller.start_automatic_check()
    timer = controller._periodic_check_timer

    assert AUTO_CHECK_INTERVAL_MS == 6 * 60 * 60 * 1000
    assert timer.interval() == AUTO_CHECK_INTERVAL_MS
    assert not timer.isSingleShot()
    assert timer.isActive()
    timer.timeout.emit()
    assert client.checks == 1


def _windows_release(version: str = "1.1.0") -> ReleaseInfo:
    from picasapy.app.update_manager import (
        SHA256SUMS_NAME,
        WINDOWS_ASSET_NAME,
        ReleaseAsset,
    )

    return ReleaseInfo(
        version,
        "Notes",
        "https://example.test/release",
        (
            ReleaseAsset(WINDOWS_ASSET_NAME, "https://example.test/zip"),
            ReleaseAsset(SHA256SUMS_NAME, "https://example.test/sums"),
        ),
    )


def _letolto_vezerlo(payload: bytes, manifest_hash: str):
    from picasapy.app.update_manager import WINDOWS_ASSET_NAME

    client = _AssetClient(
        _windows_release(), payload, f"{manifest_hash}  {WINDOWS_ASSET_NAME}\n"
    )
    controller = UpdateController(
        "1.0.0",
        settings=_MemorySettings(),
        client=client,
        pool=_InlinePool(),
        schedule=False,
        install_kind="windows",
    )
    controller.checkForUpdates()
    assert controller.updateAvailable
    return controller


class _AssetClient(_ReleaseClient):
    """Letöltést is tudó kliens: a manifeszt és a csomag bájtjait adja."""

    def __init__(self, release, payload: bytes, manifest: str):
        super().__init__(release)
        self.payload = payload
        self.manifest = manifest

    def download(self, asset, *, progress=None):
        return self.manifest.encode("utf-8")

    def download_to(self, asset, destination, *, progress=None):
        destination.write_bytes(self.payload)
        if progress:
            progress(len(self.payload), len(self.payload))
        return hashlib.sha256(self.payload).hexdigest()


def test_a_letoltes_fajlba_megy_es_az_ujjlenyomat_egyezik(qt_app):
    payload = b"PK-zip-tartalom"
    controller = _letolto_vezerlo(payload, hashlib.sha256(payload).hexdigest())
    eredmenyek = []
    controller.downloadFinished.connect(lambda ok, ok_ok: eredmenyek.append((ok, ok_ok)))

    controller.downloadUpdate()

    assert eredmenyek == [(True, "ready")]
    assert controller._download_path.read_bytes() == payload
    controller._download_path.unlink()


def test_eltero_ujjlenyomatnal_a_letoltott_fajl_torlodik(qt_app):
    controller = _letolto_vezerlo(b"hamisitott", "0" * 64)
    eredmenyek = []
    controller.downloadFinished.connect(lambda ok, ok_ok: eredmenyek.append((ok, ok_ok)))

    controller.downloadUpdate()

    assert eredmenyek == [(False, "integrity-error")]
    assert controller._download_path is None
    import tempfile

    assert not (Path(tempfile.gettempdir()) / "picasapy-update" / "PicasaPy-1.1.0.zip").exists()


def test_a_github_kliens_fajlba_tolt_es_hasht_szamol(tmp_path):
    from picasapy.app.update_manager import ReleaseAsset

    adat = b"x" * 300_000

    class _Valasz:
        headers = {"Content-Length": str(len(adat))}

        def __init__(self):
            self._maradek = adat

        def read(self, n):
            darab, self._maradek = self._maradek[:n], self._maradek[n:]
            return darab

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    kliens = GitHubReleaseClient(opener=lambda request, timeout: _Valasz())
    cel = tmp_path / "csomag.zip"
    lepesek = []
    digest = kliens.download_to(
        ReleaseAsset("csomag.zip", "https://example.test/zip"),
        cel,
        progress=lambda kapott, osszes: lepesek.append(kapott),
    )
    assert cel.read_bytes() == adat
    assert digest == hashlib.sha256(adat).hexdigest()
    assert lepesek[-1] == len(adat)


def test_irhato_telepitesi_mappanal_nem_ker_uac_ot(tmp_path):
    from picasapy.app import update_manager

    assert update_manager.mappa_irhato(tmp_path) is True
    assert update_manager.mappa_irhato(tmp_path / "nincs-ilyen") is False


def test_a_segedet_csak_irhatatlan_mappanal_inditja_rendszergazdakent(
    qt_app, tmp_path, monkeypatch
):
    from picasapy.app import update_manager

    telepites = tmp_path / "PicasaPy"
    telepites.mkdir()
    (telepites / "PicasaPyUpdateHelper.exe").write_bytes(b"seged")
    from types import SimpleNamespace

    monkeypatch.setattr(
        update_manager, "_futtato", SimpleNamespace(executable=str(telepites / "PicasaPy.exe"))
    )
    hivasok = []
    monkeypatch.setattr(
        update_manager,
        "_inditsd_a_segedet",
        lambda args, *, emelt: hivasok.append(emelt) or True,
    )
    controller = UpdateController(
        "1.0.0",
        settings=_MemorySettings(),
        client=_ReleaseClient(),
        pool=_InlinePool(),
        schedule=False,
        install_kind="windows",
    )
    controller._download_path = tmp_path / "csomag.zip"

    monkeypatch.setattr(update_manager, "mappa_irhato", lambda _m: True)
    assert controller.installWhenExiting(False) is True
    monkeypatch.setattr(update_manager, "mappa_irhato", lambda _m: False)
    assert controller.installWhenExiting(False) is True
    assert hivasok == [False, True]


def test_rendszergazdai_segedbol_a_program_normal_jogokkal_indul(monkeypatch, tmp_path):
    inditasok = []
    monkeypatch.setattr(update_swap_helper, "_popen", lambda args, **k: inditasok.append(args))
    exe = tmp_path / "PicasaPy.exe"

    monkeypatch.setattr(update_swap_helper, "_rendszergazda", lambda: True)
    update_swap_helper.inditsd_a_felhasznalonak(exe)
    monkeypatch.setattr(update_swap_helper, "_rendszergazda", lambda: False)
    update_swap_helper.inditsd_a_felhasznalonak(exe)

    assert inditasok[0][0] == "explorer.exe"
    assert Path(inditasok[0][1]) == exe
    assert [Path(elem) for elem in inditasok[1]] == [exe]


def test_sikertelen_kicsomagolas_utan_is_elindul_a_regi_program(monkeypatch, tmp_path):
    telepites = tmp_path / "PicasaPy"
    telepites.mkdir()
    (telepites / "PicasaPy.exe").write_bytes(b"regi")
    hibas_zip = tmp_path / "hibas.zip"
    hibas_zip.write_bytes(b"nem zip")
    inditasok = []
    monkeypatch.setattr(update_swap_helper, "wait_for_process", lambda pid: None)
    monkeypatch.setattr(
        update_swap_helper, "inditsd_a_felhasznalonak", lambda exe: inditasok.append(exe)
    )

    import zipfile

    with pytest.raises(zipfile.BadZipFile):
        update_swap_helper.install_after_exit(123, hibas_zip, telepites, "PicasaPy.exe")

    assert inditasok == [telepites.resolve() / "PicasaPy.exe"]
    assert (telepites / "PicasaPy.exe").read_bytes() == b"regi"


def test_a_korabbi_regi_mappa_eltavolitoja_a_csere_elott_visszakerul(tmp_path):
    """#6354: Program Files-ba telepítve az induláskori pótlás nem írhat a
    mappába; a következő (emelt jogú) csere a régi mappa törlése előtt menti."""
    app = tmp_path / "PicasaPy"
    previous = tmp_path / "PicasaPy.previous"
    stage = tmp_path / "staged"
    _app(app, "kozbenso")
    _app(previous, "legregebbi")
    (previous / "unins000.exe").write_bytes(b"uninstaller")
    (previous / "unins000.dat").write_bytes(b"uninstaller data")
    _app(stage, "new")

    assert swap_update_directory(stage, app, launch=lambda: True)

    assert (app / "app.txt").read_text(encoding="utf-8") == "new"
    assert (app / "unins000.exe").read_bytes() == b"uninstaller"
    assert (app / "unins000.dat").read_bytes() == b"uninstaller data"
    assert not previous.exists()


class _AllóPool:
    """A munkát elfogadja, de nem futtatja: a letöltés még "úton van"."""

    def __init__(self):
        self.workers = []

    def start(self, worker):
        self.workers.append(worker)


def test_frissites_most_utan_azonnal_letoltes_allapot(qt_app):
    """#6380: a kattintás pillanatától látszik, hogy dolgozik."""
    pool = _AllóPool()
    controller = UpdateController(
        "1.0.0",
        settings=_MemorySettings(),
        client=_ReleaseClient(_windows_release("1.1.0")),
        pool=pool,
        schedule=False,
        install_kind="windows",
    )
    controller._release = _windows_release("1.1.0")
    allapotok = []
    controller.progressChanged.connect(lambda: allapotok.append(controller.downloadState))

    controller.downloadUpdate()

    assert pool.workers, "a letöltés nem indult el"
    assert controller.downloadState == "downloading"
    assert controller.downloadProgress == 0
    assert allapotok == ["downloading"]


def test_sikertelen_letoltes_utan_visszaall_tetlenre(qt_app):
    client = _ReleaseClient(_windows_release("1.1.0"))
    client.download = lambda asset, *, progress=None: (_ for _ in ()).throw(URLError("offline"))
    controller = UpdateController(
        "1.0.0",
        settings=_MemorySettings(),
        client=client,
        pool=_InlinePool(),
        schedule=False,
        install_kind="windows",
    )
    controller._release = _windows_release("1.1.0")
    eredmeny = []
    controller.downloadFinished.connect(lambda ok, ok_ok: eredmeny.append((ok, ok_ok)))

    controller.downloadUpdate()

    assert eredmeny == [(False, "download-error")]
    assert controller.downloadState == "idle"


class _ManifestesKliens(_ReleaseClient):
    """A kiadás mellé `SHA256SUMS`-t is ad (vagy hibát, ha nincs)."""

    def __init__(self, release, manifest: str | None):
        super().__init__(release)
        self.manifest = manifest

    def download(self, asset, *, progress=None):
        if self.manifest is None:
            raise URLError("nincs SHA256SUMS")
        return self.manifest.encode("utf-8")


def _windows_vezerlo(client):
    from picasapy.app.update_manager import UpdateController as _Vezerlo

    return _Vezerlo(
        "1.0.0",
        settings=_MemorySettings({AUTO_CHECK_KEY: True}),
        client=client,
        pool=_InlinePool(),
        schedule=False,
        install_kind="windows",
    )


def test_hianyzo_windows_csomagnal_nem_ajanl_fel_kiadast(qt_app):
    """#6389: a kiadási lap már kint, a windowsos zip még nincs fent."""
    controller = _windows_vezerlo(_ManifestesKliens(_release("1.1.0"), "abc  x.whl\n"))
    controller._automatic_check_if_due()
    assert not controller.updateAvailable


def test_zip_nelkuli_sha256sumsnal_nem_ajanl_fel_kiadast(qt_app):
    from picasapy.app.update_manager import WINDOWS_ASSET_NAME

    assert WINDOWS_ASSET_NAME == "PicasaPy-windows-x64.zip"
    controller = _windows_vezerlo(
        _ManifestesKliens(_windows_release("1.1.0"), "abc  picasapy-1.1.0.tar.gz\n")
    )
    controller._automatic_check_if_due()
    assert not controller.updateAvailable


def test_teljes_windows_kiadast_felajanl(qt_app):
    from picasapy.app.update_manager import WINDOWS_ASSET_NAME

    controller = _windows_vezerlo(
        _ManifestesKliens(_windows_release("1.1.0"), f"{'a' * 64}  {WINDOWS_ASSET_NAME}\n")
    )
    controller._automatic_check_if_due()
    assert controller.updateAvailable


def test_restart_now_utan_beragadt_lezarasnal_a_folyamat_kilep(qt_app, tmp_path, monkeypatch):
    """#6383: a frissítősegéd a folyamat kilépésére vár; beragadt lezárásnál
    a határidő után kényszerített kilépés jön, különben a csere sosem indul."""
    from types import SimpleNamespace

    from picasapy.app import update_manager

    telepites = tmp_path / "PicasaPy"
    telepites.mkdir()
    (telepites / "PicasaPyUpdateHelper.exe").write_bytes(b"seged")
    monkeypatch.setattr(
        update_manager, "_futtato", SimpleNamespace(executable=str(telepites / "PicasaPy.exe"))
    )
    monkeypatch.setattr(update_manager, "_inditsd_a_segedet", lambda args, *, emelt: True)
    monkeypatch.setattr(update_manager, "mappa_irhato", lambda _m: True)
    halok = []
    monkeypatch.setattr(
        update_manager, "_kenyszeritett_kilepes_ha_beragad", lambda: halok.append("felhuzva")
    )
    from PySide6.QtCore import QCoreApplication

    monkeypatch.setattr(QCoreApplication, "quit", staticmethod(lambda: halok.append("quit")))
    controller = UpdateController(
        "1.0.0",
        settings=_MemorySettings(),
        client=_ReleaseClient(),
        pool=_InlinePool(),
        schedule=False,
        install_kind="windows",
    )
    controller._download_path = tmp_path / "csomag.zip"

    assert controller.installWhenExiting(True) is True
    assert halok == ["felhuzva", "quit"]


def test_a_kenyszeritett_kilepes_a_hatarido_utan_os_exit(monkeypatch):
    import threading

    from picasapy.app import update_manager

    kilepett = threading.Event()
    kodok = []
    monkeypatch.setattr(
        update_manager, "_azonnali_kilepes", lambda kod: (kodok.append(kod), kilepett.set())
    )
    update_manager._kenyszeritett_kilepes_ha_beragad(0.05)
    assert kilepett.wait(2.0)
    assert kodok == [0]
