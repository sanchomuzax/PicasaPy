"""A Google Fotók közös típusai és HTTPS-transportja."""

from __future__ import annotations

import threading
import time
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

GOOGLE_PHOTOS_SCOPE = "https://www.googleapis.com/auth/photoslibrary.appendonly"


GOOGLE_PHOTOS_API_BASE_URL = "https://photoslibrary.googleapis.com/v1"


GOOGLE_OAUTH_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"


GOOGLE_OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"


GOOGLE_OAUTH_REVOKE_URL = "https://oauth2.googleapis.com/revoke"


DEFAULT_UPLOAD_MAX_SIDE = 1600


MAX_BATCH_SIZE = 50


MAX_PHOTO_BYTES = 200 * 1024 * 1024


_OAUTH_CALLBACK_TIMEOUT_SECONDS = 300.0


_OAUTH_CALLBACK_POLL_SECONDS = 0.25


_monotonic = time.monotonic


_KEYRING_SERVICE = "PicasaPy Google Photos"


class GooglePhotosError(Exception):
    """A felületre fordítható, titokmentes hibakód."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class HttpResponse:
    status: int
    body: bytes
    headers: Mapping[str, str] | None = None


class HttpTransport(Protocol):
    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str],
        body: bytes,
        timeout: float,
        cancel_event: threading.Event | None = None,
    ) -> HttpResponse: ...


class UrllibTransport:
    """A szabványos HTTPS-transport; minden hiba titokmentes kódra fordul."""

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: Mapping[str, str],
        body: bytes,
        timeout: float,
        cancel_event: threading.Event | None = None,
    ) -> HttpResponse:
        if cancel_event is not None and cancel_event.is_set():
            raise GooglePhotosError("cancelled")
        request = Request(url, data=body, headers=dict(headers), method=method)
        try:
            with urlopen(request, timeout=timeout) as response:  # noqa: S310
                return HttpResponse(
                    response.status,
                    response.read(),
                    dict(response.headers.items()),
                )
        except HTTPError as error:
            try:
                body_bytes = error.read()
            except OSError:
                body_bytes = b""
            return HttpResponse(error.code, body_bytes, dict(error.headers.items()))
        except (TimeoutError, URLError, OSError):
            raise GooglePhotosError("network") from None
