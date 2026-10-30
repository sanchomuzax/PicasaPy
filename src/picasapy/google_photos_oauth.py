"""Google OAuth 2.0 tokenkliens."""

from __future__ import annotations

import base64
import hashlib
import json
from collections.abc import Mapping
from urllib.parse import urlencode

from .google_photos_common import (
    GOOGLE_OAUTH_AUTH_URL,
    GOOGLE_OAUTH_REVOKE_URL,
    GOOGLE_OAUTH_TOKEN_URL,
    GOOGLE_PHOTOS_SCOPE,
    GooglePhotosError,
    HttpTransport,
    UrllibTransport,
)

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


def _oauth_error(body: bytes) -> str:
    try:
        value = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return ""
    return str(value.get("error", "")) if isinstance(value, dict) else ""

