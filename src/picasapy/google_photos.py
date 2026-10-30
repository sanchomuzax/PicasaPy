"""Google Fotók-kompatibilitási homlokzat (#5976, #6256)."""

# A történeti importneveket is újraexportáljuk erről a homlokzatról.
# ruff: noqa: F401

from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import secrets
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, HTTPServer
from io import BytesIO
from pathlib import Path
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen

from PIL import Image, ImageOps, UnidentifiedImageError

try:
    import keyring
except ImportError:  # pragma: no cover - a futási függőség telepítéskor jelen van
    keyring = None

from .google_photos_common import (
    DEFAULT_UPLOAD_MAX_SIDE,
    GOOGLE_OAUTH_AUTH_URL,
    GOOGLE_OAUTH_REVOKE_URL,
    GOOGLE_OAUTH_TOKEN_URL,
    GOOGLE_PHOTOS_API_BASE_URL,
    GOOGLE_PHOTOS_SCOPE,
    MAX_BATCH_SIZE,
    MAX_PHOTO_BYTES,
    _KEYRING_SERVICE,
    _OAUTH_CALLBACK_POLL_SECONDS,
    _OAUTH_CALLBACK_TIMEOUT_SECONDS,
    _monotonic,
    GooglePhotosError,
    HttpResponse,
    HttpTransport,
    UrllibTransport,
)
from .google_photos_api import (
    GooglePhotosApiClient,
    ProgressCallback,
    _prepare_photo,
    _response_has_quota_error,
    _safe_filename,
)
from .google_photos_oauth import OAuthClient, _oauth_error

# A régi importútvonal a típusok és kliensek történeti __module__ értéke is.
for _compat_type in (
    GooglePhotosError,
    HttpResponse,
    HttpTransport,
    UrllibTransport,
    GooglePhotosApiClient,
    OAuthClient,
):
    _compat_type.__module__ = __name__

class CredentialStore:
    """Titok a rendszerkulcstartóban, annak hibája esetén QSettingsben."""

    def __init__(self, settings, *, keyring_module=None) -> None:
        self._settings = settings
        self._keyring = keyring if keyring_module is None else keyring_module

    def get_secret(self, name: str) -> str:
        fallback = str(self._settings.value(f"googlePhotos/secrets/{name}", "") or "")
        if fallback:
            return fallback
        if self._keyring is not None:
            try:
                value = self._keyring.get_password(_KEYRING_SERVICE, name)
                if value:
                    return str(value)
            except Exception:
                pass
        return ""

    def set_secret(self, name: str, value: str) -> None:
        if self._keyring is not None:
            try:
                self._keyring.set_password(_KEYRING_SERVICE, name, value)
                self._settings.remove(f"googlePhotos/secrets/{name}")
                return
            except Exception:
                pass
        self._settings.setValue(f"googlePhotos/secrets/{name}", value)

    def delete_secret(self, name: str) -> None:
        if self._keyring is not None:
            try:
                self._keyring.delete_password(_KEYRING_SERVICE, name)
            except Exception:
                pass
        self._settings.remove(f"googlePhotos/secrets/{name}")


class LoopbackOAuthSession:
    """Egyszer használatos, state-védett localhost OAuth callback."""

    def __init__(
        self,
        oauth: OAuthClient,
        *,
        client_id: str,
        client_secret: str,
    ) -> None:
        self._oauth = oauth
        self._client_id = client_id
        self._client_secret = client_secret
        self._state = secrets.token_urlsafe(32)
        self._code_verifier = secrets.token_urlsafe(64)
        self._cancelled = threading.Event()
        self._result_ready = threading.Event()
        self._result: tuple[str, str] | None = None
        self._server = self._create_server()
        port = self._server.server_address[1]
        self.redirect_uri = f"http://127.0.0.1:{port}"
        self.authorization_url = oauth.authorization_url(
            client_id=client_id,
            redirect_uri=self.redirect_uri,
            state=self._state,
            code_verifier=self._code_verifier,
        )
        self._server.timeout = _OAUTH_CALLBACK_POLL_SECONDS
        self._listener = threading.Thread(
            target=self._listen, name="picasapy-google-photos-oauth", daemon=True
        )
        self._listener.start()

    def wait_for_tokens(
        self, timeout: float = _OAUTH_CALLBACK_TIMEOUT_SECONDS
    ) -> dict:
        deadline = _monotonic() + timeout
        while not self._result_ready.wait(0.1):
            if self._cancelled.is_set():
                raise GooglePhotosError("cancelled")
            if _monotonic() >= deadline:
                self.cancel()
                raise GooglePhotosError("auth_timeout")
        if self._cancelled.is_set():
            raise GooglePhotosError("cancelled")
        code, error = self._result or ("", "auth_failed")
        if error:
            raise GooglePhotosError(error)
        return self._oauth.exchange_code(
            client_id=self._client_id,
            client_secret=self._client_secret,
            code=code,
            redirect_uri=self.redirect_uri,
            code_verifier=self._code_verifier,
        )

    def cancel(self) -> None:
        self._cancelled.set()
        self._server.server_close()

    def _create_server(self) -> HTTPServer:
        session = self

        class CallbackHandler(BaseHTTPRequestHandler):
            def _respond(self, status: int, content: bytes) -> None:
                self.send_response(status)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                try:
                    self.wfile.write(content)
                except OSError:
                    pass

            def do_GET(self):  # noqa: N802 — http.server callback API
                parsed = urlparse(self.path)
                query = parse_qs(parsed.query)
                valid_state = secrets.compare_digest(
                    (query.get("state") or [""])[0], session._state
                )
                if parsed.path not in {"", "/"} or not valid_state:
                    self._respond(400, b"Invalid authorization callback.")
                    return

                if query.get("error"):
                    raw_error = (query.get("error") or [""])[0]
                    error = "cancelled" if raw_error == "access_denied" else "auth_failed"
                    code = ""
                else:
                    code = (query.get("code") or [""])[0]
                    error = "" if code else "auth_failed"
                session._result = (code, error)
                session._result_ready.set()
                content = b"Authorization complete. You can close this window."
                self._respond(200 if not error else 400, content)

            def log_message(self, _format, *args):
                # A kérés URL-je OAuth `state` értéket és authorization code-ot tartalmaz.
                return

        # ADR-011 kivétel: kizárólag a 127.0.0.1-re, véletlen szabad portra
        # kötött, egyszeri Google OAuth callback (#5976).
        server = HTTPServer(("127.0.0.1", 0), CallbackHandler)
        if server.server_address[0] != "127.0.0.1":
            server.server_close()
            raise GooglePhotosError("auth_failed")
        return server

    def _listen(self) -> None:
        deadline = _monotonic() + _OAUTH_CALLBACK_TIMEOUT_SECONDS
        try:
            while not self._cancelled.is_set() and not self._result_ready.is_set():
                if _monotonic() >= deadline:
                    self._result = ("", "auth_timeout")
                    self._result_ready.set()
                    return
                self._server.handle_request()
        except OSError:
            if not self._cancelled.is_set() and not self._result_ready.is_set():
                self._result = ("", "auth_failed")
                self._result_ready.set()
        finally:
            self._server.server_close()


__all__ = tuple(nev for nev in globals() if not nev.startswith("_"))
