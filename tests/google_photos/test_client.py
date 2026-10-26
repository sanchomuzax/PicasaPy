"""Google Fotók feltöltés és OAuth (#5976) — fake transporttal, socket nélkül."""

from __future__ import annotations

import base64
import hashlib
import json
import threading
from urllib.parse import parse_qs, urlparse

import pytest
from PIL import Image

from picasapy.google_photos import (
    GOOGLE_PHOTOS_SCOPE,
    GooglePhotosApiClient,
    GooglePhotosError,
    HttpResponse,
    LoopbackOAuthSession,
    OAuthClient,
)


class FakePhotosServer:
    """Hálózati rétegként viselkedő hamis szerver, helyi socket nélkül."""

    def __init__(self):
        self.requests = []
        self.upload_number = 0
        self.batch_sizes = []
        self.status_override: int | None = None

    def request(self, method, url, *, headers, body, timeout, cancel_event=None):
        self.requests.append((method, url, dict(headers), body))
        if self.status_override is not None:
            return HttpResponse(self.status_override, b'{"error":{"status":"RESOURCE_EXHAUSTED"}}')
        if url.endswith("/uploads"):
            self.upload_number += 1
            return HttpResponse(200, f"upload-{self.upload_number}".encode())
        if url.endswith("/mediaItems:batchCreate"):
            payload = json.loads(body)
            media = payload["newMediaItems"]
            self.batch_sizes.append(len(media))
            return HttpResponse(
                200,
                json.dumps(
                    {
                        "newMediaItemResults": [
                            {"uploadToken": item["simpleMediaItem"]["uploadToken"],
                             "status": {"code": 0}}
                            for item in media
                        ]
                    }
                ).encode(),
            )
        raise AssertionError(f"Ismeretlen kérés: {method} {url}")


def _make_image(path, size, color=(40, 90, 130)):
    Image.new("RGB", size, color).save(path, format="JPEG")
    return path


def test_talcakepek_merete_sorrendje_es_api_keresei(tmp_path):
    server = FakePhotosServer()
    api = GooglePhotosApiClient(
        transport=server,
        api_base_url="https://photos.test/v1",
        max_side=1600,
    )
    elso = _make_image(tmp_path / "zeta.jpg", (2400, 1200))
    masodik = _make_image(tmp_path / "alpha.jpg", (1200, 2400), color=(90, 30, 20))
    progress = []

    eredmeny = api.upload_paths(
        [str(elso), str(masodik)],
        access_token="access-token",
        progress=lambda phase, done, total: progress.append((phase, done, total)),
        cancel_event=threading.Event(),
    )

    assert eredmeny == 2
    feltoltesek = [request for request in server.requests if request[1].endswith("/uploads")]
    assert len(feltoltesek) == 2
    assert [request[2]["Authorization"] for request in feltoltesek] == [
        "Bearer access-token",
        "Bearer access-token",
    ]
    assert [request[2]["X-Goog-Upload-Protocol"] for request in feltoltesek] == [
        "raw",
        "raw",
    ]
    assert [Image.open(__import__("io").BytesIO(request[3])).size for request in feltoltesek] == [
        (1600, 800),
        (800, 1600),
    ]

    batch = [request for request in server.requests if request[1].endswith("/mediaItems:batchCreate")]
    assert len(batch) == 1
    payload = json.loads(batch[0][3])
    assert [item["simpleMediaItem"]["fileName"] for item in payload["newMediaItems"]] == [
        "zeta.jpg",
        "alpha.jpg",
    ]
    assert [item["simpleMediaItem"]["uploadToken"] for item in payload["newMediaItems"]] == [
        "upload-1",
        "upload-2",
    ]
    assert progress[-1] == ("completed", 2, 2)


def test_batchcreate_legfeljebb_otven_kepet_tartalmaz(tmp_path):
    # Rontás-kontroll: MAX_BATCH_SIZE=49 esetén a várt [50, 1] helyett [49, 2] jön.
    server = FakePhotosServer()
    api = GooglePhotosApiClient(transport=server, api_base_url="https://photos.test/v1")
    kep = _make_image(tmp_path / "egy.jpg", (32, 16))

    assert api.upload_paths(
        [str(kep)] * 51,
        access_token="access-token",
        cancel_event=threading.Event(),
    ) == 51

    assert server.batch_sizes == [50, 1]


def test_kvotahiba_olvashato_hibatipusra_fordul(tmp_path):
    server = FakePhotosServer()
    server.status_override = 429
    api = GooglePhotosApiClient(transport=server, api_base_url="https://photos.test/v1")
    kep = _make_image(tmp_path / "egy.jpg", (32, 16))

    with pytest.raises(GooglePhotosError) as error:
        api.upload_paths(
            [str(kep)], access_token="access-token", cancel_event=threading.Event()
        )

    assert error.value.code == "quota"
    assert "access-token" not in str(error.value)


def test_megszakitas_utan_nem_kezdodik_el_a_batchcreate(tmp_path):
    server = FakePhotosServer()
    api = GooglePhotosApiClient(transport=server, api_base_url="https://photos.test/v1")
    kepek = [
        _make_image(tmp_path / "egy.jpg", (32, 16)),
        _make_image(tmp_path / "ketto.jpg", (16, 32)),
    ]
    cancel = threading.Event()

    def progress(phase, done, _total):
        if phase == "uploaded" and done == 1:
            cancel.set()

    with pytest.raises(GooglePhotosError) as error:
        api.upload_paths(
            [str(path) for path in kepek],
            access_token="access-token",
            progress=progress,
            cancel_event=cancel,
        )

    assert error.value.code == "cancelled"
    assert not any(url.endswith("/mediaItems:batchCreate") for _, url, _, _ in server.requests)


def test_asztali_oauth_url_loopback_pkce_es_appendonly_jogosultsag():
    oauth = OAuthClient(transport=FakePhotosServer())
    verifier = "test-verifier-1234567890"
    url = oauth.authorization_url(
        client_id="client-id.apps.googleusercontent.com",
        redirect_uri="http://127.0.0.1:49152",
        state="random-state",
        code_verifier=verifier,
    )

    params = parse_qs(urlparse(url).query)
    expected_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).decode().rstrip("=")
    assert params["redirect_uri"] == ["http://127.0.0.1:49152"]
    assert params["scope"] == [GOOGLE_PHOTOS_SCOPE]
    assert params["access_type"] == ["offline"]
    assert params["code_challenge_method"] == ["S256"]
    assert params["code_challenge"] == [expected_challenge]
    assert params["state"] == ["random-state"]


def test_loopback_session_redirect_uri_a_root_url(monkeypatch):
    class FakeLoopbackServer:
        server_address = ("127.0.0.1", 49152)
        timeout = 0

        def handle_request(self):
            threading.Event().wait(0.005)

        def server_close(self):
            pass

    server = FakeLoopbackServer()
    monkeypatch.setattr(LoopbackOAuthSession, "_create_server", lambda _self: server)
    session = LoopbackOAuthSession(
        OAuthClient(transport=FakePhotosServer()),
        client_id="client-id.apps.googleusercontent.com",
        client_secret="client-secret",
    )
    try:
        assert session.redirect_uri == "http://127.0.0.1:49152"
    finally:
        session.cancel()


def test_oauth_refresh_invalid_grant_lejart_munkamenetkent_jelenik_meg():
    class InvalidGrantServer:
        def request(self, method, url, *, headers, body, timeout, cancel_event=None):
            return HttpResponse(400, b'{"error":"invalid_grant"}')

    oauth = OAuthClient(transport=InvalidGrantServer())
    with pytest.raises(GooglePhotosError) as error:
        oauth.refresh_access_token("client-id", "client-secret", "refresh-token")

    assert error.value.code == "token_expired"
    assert "client-secret" not in str(error.value)
    assert "refresh-token" not in str(error.value)
