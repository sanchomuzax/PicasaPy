"""Google Photos Library API feltöltés és asztali OAuth (#5976).

A REST-réteg szándékosan szállítható saját HTTP-transzporttal: a tesztek
hamis szervert adnak át, ezért sem Google-fiók, sem hálózati socket nem kell.
"""

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


ProgressCallback = Callable[[str, int, int], None]


class GooglePhotosApiClient:
    """Képfeltöltés a Photos Library API `uploads` + `batchCreate` hívásaival."""

    def __init__(
        self,
        *,
        transport: HttpTransport | None = None,
        api_base_url: str = GOOGLE_PHOTOS_API_BASE_URL,
        max_side: int = DEFAULT_UPLOAD_MAX_SIDE,
        timeout: float = 60.0,
    ) -> None:
        if max_side < 1:
            raise ValueError("A hosszabbik oldal korlátja legalább 1 legyen.")
        self._transport = transport or UrllibTransport()
        self._api_base_url = api_base_url.rstrip("/")
        self._max_side = max_side
        self._timeout = timeout
        self._access_token = ""
        self._refresh_access_token: Callable[[], str] | None = None
        self._already_refreshed = False
        self._cancel_event: threading.Event | None = None

    def upload_paths(
        self,
        paths: Sequence[str | Path],
        *,
        access_token: str,
        progress: ProgressCallback | None = None,
        cancel_event: threading.Event | None = None,
        refresh_access_token: Callable[[], str] | None = None,
    ) -> int:
        """A fájlokat a megadott sorrendben tölti fel, majd 50-esével rögzíti."""
        total = len(paths)
        if not total:
            raise GooglePhotosError("empty_tray")
        self._access_token = access_token
        self._refresh_access_token = refresh_access_token
        self._already_refreshed = False
        self._cancel_event = cancel_event
        token_and_name: list[tuple[str, str]] = []

        for index, raw_path in enumerate(paths, start=1):
            self._check_cancelled()
            path = Path(raw_path)
            if progress is not None:
                progress("preparing", index, total)
            data, mime_type = _prepare_photo(path, self._max_side)
            if progress is not None:
                progress("uploading", index, total)
            response = self._authorized_request(
                "POST",
                f"{self._api_base_url}/uploads",
                {
                    "Content-Type": "application/octet-stream",
                    "X-Goog-Upload-Content-Type": mime_type,
                    "X-Goog-Upload-Protocol": "raw",
                },
                data,
            )
            token = response.body.decode("utf-8", errors="strict").strip()
            if not token:
                raise GooglePhotosError("api_error")
            token_and_name.append((token, _safe_filename(path.name)))
            if progress is not None:
                progress("uploaded", index, total)

        for offset in range(0, len(token_and_name), MAX_BATCH_SIZE):
            self._check_cancelled()
            batch = token_and_name[offset : offset + MAX_BATCH_SIZE]
            payload = {
                "newMediaItems": [
                    {
                        "simpleMediaItem": {
                            "uploadToken": token,
                            "fileName": filename,
                        }
                    }
                    for token, filename in batch
                ]
            }
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            response = self._authorized_request(
                "POST",
                f"{self._api_base_url}/mediaItems:batchCreate",
                {"Content-Type": "application/json; charset=utf-8"},
                body,
            )
            self._check_batch_result(response.body, len(batch))
            if progress is not None:
                progress("creating", min(offset + len(batch), total), total)

        if progress is not None:
            progress("completed", total, total)
        return total

    def _authorized_request(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: bytes,
    ) -> HttpResponse:
        self._check_cancelled()
        request_headers = {**headers, "Authorization": f"Bearer {self._access_token}"}
        response = self._request(method, url, request_headers, body)
        if response.status == 401 and self._refresh_access_token and not self._already_refreshed:
            self._already_refreshed = True
            try:
                self._access_token = self._refresh_access_token()
            except GooglePhotosError:
                raise
            except Exception:
                raise GooglePhotosError("token_expired") from None
            request_headers["Authorization"] = f"Bearer {self._access_token}"
            response = self._request(method, url, request_headers, body)
        self._raise_for_status(response)
        return response

    def _request(
        self, method: str, url: str, headers: Mapping[str, str], body: bytes
    ) -> HttpResponse:
        try:
            return self._transport.request(
                method,
                url,
                headers=headers,
                body=body,
                timeout=self._timeout,
                cancel_event=self._cancel_event,
            )
        except GooglePhotosError:
            raise
        except Exception:
            raise GooglePhotosError("network") from None

    def _raise_for_status(self, response: HttpResponse) -> None:
        if 200 <= response.status < 300:
            return
        if response.status == 401:
            raise GooglePhotosError("token_expired")
        if response.status == 429 or _response_has_quota_error(response.body):
            raise GooglePhotosError("quota")
        if response.status >= 500:
            raise GooglePhotosError("service_unavailable")
        raise GooglePhotosError("api_error")

    def _check_batch_result(self, body: bytes, expected: int) -> None:
        try:
            results = json.loads(body.decode("utf-8"))["newMediaItemResults"]
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError):
            raise GooglePhotosError("api_error") from None
        if len(results) != expected:
            raise GooglePhotosError("api_error")
        for result in results:
            status = result.get("status") or {}
            if status.get("code", 0) != 0:
                if _response_has_quota_error(json.dumps(status).encode()):
                    raise GooglePhotosError("quota")
                raise GooglePhotosError("api_error")

    def _check_cancelled(self) -> None:
        if self._cancel_event is not None and self._cancel_event.is_set():
            raise GooglePhotosError("cancelled")


class OAuthClient:
    """Google OAuth 2.0 installed-app token requests."""

    def __init__(
        self,
        *,
        transport: HttpTransport | None = None,
        authorization_endpoint: str = GOOGLE_OAUTH_AUTH_URL,
        token_endpoint: str = GOOGLE_OAUTH_TOKEN_URL,
        revocation_endpoint: str = GOOGLE_OAUTH_REVOKE_URL,
        timeout: float = 30.0,
    ) -> None:
        self._transport = transport or UrllibTransport()
        self._authorization_endpoint = authorization_endpoint
        self._token_endpoint = token_endpoint
        self._revocation_endpoint = revocation_endpoint
        self._timeout = timeout

    def authorization_url(
        self,
        *,
        client_id: str,
        redirect_uri: str,
        state: str,
        code_verifier: str,
    ) -> str:
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode("ascii")).digest()
        ).decode("ascii").rstrip("=")
        query = urlencode(
            {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "response_type": "code",
                "scope": GOOGLE_PHOTOS_SCOPE,
                "access_type": "offline",
                "prompt": "consent",
                "state": state,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            }
        )
        return f"{self._authorization_endpoint}?{query}"

    def exchange_code(
        self,
        *,
        client_id: str,
        client_secret: str,
        code: str,
        redirect_uri: str,
        code_verifier: str,
    ) -> dict:
        return self._token_request(
            {
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "code_verifier": code_verifier,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            }
        )

    def refresh_access_token(
        self, client_id: str, client_secret: str, refresh_token: str
    ) -> dict:
        return self._token_request(
            {
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            }
        )

    def revoke(self, token: str) -> None:
        body = urlencode({"token": token}).encode("ascii")
        try:
            response = self._transport.request(
                "POST",
                self._revocation_endpoint,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                body=body,
                timeout=self._timeout,
            )
        except Exception:
            return
        if response.status >= 500:
            return

    def _token_request(self, form: Mapping[str, str]) -> dict:
        try:
            response = self._transport.request(
                "POST",
                self._token_endpoint,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                body=urlencode(form).encode("ascii"),
                timeout=self._timeout,
            )
        except GooglePhotosError:
            raise
        except Exception:
            raise GooglePhotosError("network") from None
        error = _oauth_error(response.body)
        if error == "invalid_grant":
            raise GooglePhotosError("token_expired")
        if response.status == 429:
            raise GooglePhotosError("quota")
        if not 200 <= response.status < 300:
            if response.status >= 500:
                raise GooglePhotosError("service_unavailable")
            raise GooglePhotosError("auth_failed")
        try:
            data = json.loads(response.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise GooglePhotosError("auth_failed") from None
        if not isinstance(data, dict) or not data.get("access_token"):
            raise GooglePhotosError("auth_failed")
        return data


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


def _prepare_photo(path: Path, max_side: int) -> tuple[bytes, str]:
    try:
        original = path.read_bytes()
        image = Image.open(BytesIO(original))
        image_format = (image.format or path.suffix.lstrip(".")).upper()
        image.load()
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError):
        raise GooglePhotosError("invalid_image") from None
    mime_type = Image.MIME.get(image_format) or mimetypes.guess_type(path.name)[0]
    if not mime_type or not mime_type.startswith("image/"):
        raise GooglePhotosError("invalid_image")
    if max(image.size) <= max_side:
        if len(original) > MAX_PHOTO_BYTES:
            raise GooglePhotosError("file_too_large")
        return original, mime_type

    try:
        image = ImageOps.exif_transpose(image)
        scale = max_side / max(image.size)
        size = (
            max(1, round(image.width * scale)),
            max(1, round(image.height * scale)),
        )
        resized = image.resize(size, Image.Resampling.LANCZOS)
        output = BytesIO()
        save_format = image_format
        save_kwargs = {}
        if save_format in {"JPG", "JPEG"}:
            save_format = "JPEG"
            if resized.mode not in {"RGB", "L", "CMYK"}:
                resized = resized.convert("RGB")
            save_kwargs["quality"] = 95
            exif = image.getexif().tobytes()
            if exif:
                save_kwargs["exif"] = exif
        icc_profile = image.info.get("icc_profile")
        if icc_profile:
            save_kwargs["icc_profile"] = icc_profile
        resized.save(output, format=save_format, **save_kwargs)
    except (OSError, ValueError, KeyError):
        raise GooglePhotosError("invalid_image") from None
    data = output.getvalue()
    if len(data) > MAX_PHOTO_BYTES:
        raise GooglePhotosError("file_too_large")
    output_mime = Image.MIME.get(save_format, mime_type)
    return data, output_mime


def _safe_filename(filename: str) -> str:
    clean = Path(filename).name.replace("\r", "").replace("\n", "").strip()
    if not clean or len(clean) > 255:
        raise GooglePhotosError("invalid_filename")
    return clean


def _response_has_quota_error(body: bytes) -> bool:
    try:
        decoded = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    text = json.dumps(decoded).lower()
    return any(
        marker in text
        for marker in ("quota", "ratelimit", "rate_limit", "resource_exhausted", "daily_limit")
    )


def _oauth_error(body: bytes) -> str:
    try:
        value = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return ""
    return str(value.get("error", "")) if isinstance(value, dict) else ""
