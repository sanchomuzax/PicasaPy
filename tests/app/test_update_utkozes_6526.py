"""#6526: a már elindított frissítést egy később érkező ellenőrzés nem ütheti ki."""

from __future__ import annotations

import hashlib

from picasapy.app.update_manager import (
    SHA256SUMS_NAME,
    WINDOWS_ASSET_NAME,
    ReleaseAsset,
    ReleaseInfo,
    UpdateController,
)


class _MemorySettings:
    def __init__(self):
        self.values = {}

    def value(self, key, default=None):
        return self.values.get(key, default)

    def setValue(self, key, value):
        self.values[key] = value

    def remove(self, key):
        self.values.pop(key, None)

    def sync(self):
        pass


class _QueuedPool:
    """A háttérmunkák sorrendjét a teszt dönti el (a valóságban párhuzamosak)."""

    def __init__(self):
        self.workers = []

    def start(self, worker):
        self.workers.append(worker)


def _windows_release(version: str) -> ReleaseInfo:
    return ReleaseInfo(
        version,
        "Notes",
        "https://example.test/release",
        (
            ReleaseAsset(WINDOWS_ASSET_NAME, "https://example.test/zip"),
            ReleaseAsset(SHA256SUMS_NAME, "https://example.test/sums"),
        ),
    )


class _Client:
    def __init__(self, release, payload: bytes = b"PK-uj-verzio"):
        self.release = release
        self.payload = payload

    def latest_release(self):
        return self.release

    def download(self, asset, *, progress=None):
        digest = hashlib.sha256(self.payload).hexdigest()
        return f"{digest}  {WINDOWS_ASSET_NAME}\n".encode("utf-8")

    def download_to(self, asset, destination, *, progress=None):
        if progress:
            progress(len(self.payload) // 2, len(self.payload))
        destination.write_bytes(self.payload)
        if progress:
            progress(len(self.payload), len(self.payload))
        return hashlib.sha256(self.payload).hexdigest()


def _vezerlo(client, pool):
    return UpdateController(
        "1.0.0",
        settings=_MemorySettings(),
        client=client,
        pool=pool,
        schedule=False,
        install_kind="windows",
    )


def _letoltes_folyamatban(qt_app):
    pool = _QueuedPool()
    client = _Client(_windows_release("1.0.1"))
    controller = _vezerlo(client, pool)
    controller.checkForUpdates()
    pool.workers.pop(0).run()
    assert controller.updateAvailable
    controller.downloadUpdate()
    assert controller.downloadState == "downloading"
    return controller, client, pool


def test_letoltes_kozben_erkezo_ellenorzes_nem_allitja_meg_a_haladas_jelzeset(qt_app):
    controller, _client, pool = _letoltes_folyamatban(qt_app)
    letoltes = pool.workers.pop(0)
    controller._check_latest(manual=False)
    pool.workers.pop(0).run()
    haladas = []
    controller.progressChanged.connect(lambda: haladas.append(controller.downloadProgress))

    letoltes.run()

    assert 50 in haladas
    assert controller.downloadState == "ready"
    controller._download_path.unlink()


def test_futo_letoltest_masodik_inditas_nem_kezdi_ujra(qt_app):
    controller, _client, pool = _letoltes_folyamatban(qt_app)

    controller.downloadUpdate()

    assert len(pool.workers) == 1
    assert controller.downloadState == "downloading"


def test_letoltes_kozbeni_ures_ellenorzes_nem_torli_a_letoltott_kiadast(qt_app):
    controller, client, pool = _letoltes_folyamatban(qt_app)
    letoltes = pool.workers.pop(0)
    client.release = None
    controller._check_latest(manual=False)
    pool.workers.pop(0).run()

    assert controller.updateAvailable
    assert controller.availableVersion == "1.0.1"
    letoltes.run()
    assert controller.downloadState == "ready"
    assert controller.availableVersion == "1.0.1"
    controller._download_path.unlink()


def test_letoltes_kozben_ujabb_kiadas_sem_cseréli_a_letoltes_alatti_verziot(qt_app):
    controller, client, pool = _letoltes_folyamatban(qt_app)
    letoltes = pool.workers.pop(0)
    client.release = _windows_release("1.0.2")
    jelzesek = []
    controller.notificationRequested.connect(lambda: jelzesek.append(True))
    controller._check_latest(manual=False)
    pool.workers.pop(0).run()

    assert controller.availableVersion == "1.0.1"
    assert jelzesek == []
    letoltes.run()
    assert controller._download_path.name == "PicasaPy-1.0.1.zip"
    controller._download_path.unlink()


def test_futo_automatikus_ellenorzes_alatt_inditott_kezi_ellenorzes_is_valaszt_kap(qt_app):
    pool = _QueuedPool()
    controller = _vezerlo(_Client(_windows_release("1.0.1")), pool)
    eredmenyek = []
    controller.manualCheckFinished.connect(lambda ok, ok_ok: eredmenyek.append((ok, ok_ok)))
    controller._check_latest(manual=False)

    controller.checkForUpdates()
    assert len(pool.workers) == 1
    pool.workers.pop(0).run()

    assert eredmenyek == [(True, "available")]
