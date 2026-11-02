"""#6383: a kiadási API csak helyi tesztkiszolgálóra irányítható át."""

from __future__ import annotations

import pytest

from picasapy.app.update_manager import (
    LATEST_RELEASE_API,
    GitHubReleaseClient,
    _latest_release_api_url,
)


def test_alapertelmezetten_a_github_kiadasi_api_marad(monkeypatch):
    monkeypatch.delenv("PICASAPY_UPDATE_API", raising=False)

    assert _latest_release_api_url() == LATEST_RELEASE_API


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:43127/repos/sanchomuzax/PicasaPy/releases/latest",
        "http://localhost:43127/repos/sanchomuzax/PicasaPy/releases/latest",
    ],
)
def test_helyi_kiadasi_api_url_felulirhato(monkeypatch, url):
    monkeypatch.setenv("PICASAPY_UPDATE_API", url)

    assert _latest_release_api_url() == url


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/releases/latest",
        "http://127.0.0.2/releases/latest",
        "http://localhost.evil.test/releases/latest",
        "file:///tmp/releases.json",
    ],
)
def test_nem_loopback_api_url_elutasitott(monkeypatch, url):
    monkeypatch.setenv("PICASAPY_UPDATE_API", url)

    with pytest.raises(ValueError, match="127.0.0.1.*localhost"):
        _latest_release_api_url()


def test_a_kliens_a_helyi_api_urlt_keri(monkeypatch):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'{"tag_name":"v1.2.0","assets":[]}'

    requested = []
    monkeypatch.setenv(
        "PICASAPY_UPDATE_API",
        "http://127.0.0.1:43127/repos/sanchomuzax/PicasaPy/releases/latest",
    )

    release = GitHubReleaseClient(
        opener=lambda request, timeout: requested.append(request.full_url) or Response()
    ).latest_release()

    assert release.version == "1.2.0"
    assert requested == [
        "http://127.0.0.1:43127/repos/sanchomuzax/PicasaPy/releases/latest"
    ]
