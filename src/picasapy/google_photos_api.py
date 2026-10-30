"""Google Photos Library API feltöltési kliens és képfeldolgozó."""

from __future__ import annotations

import json
import mimetypes
import threading
from collections.abc import Callable, Mapping, Sequence
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

from .google_photos_common import (
    DEFAULT_UPLOAD_MAX_SIDE,
    GOOGLE_PHOTOS_API_BASE_URL,
    MAX_BATCH_SIZE,
    MAX_PHOTO_BYTES,
    GooglePhotosError,
    HttpResponse,
    HttpTransport,
    UrllibTransport,
)

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

