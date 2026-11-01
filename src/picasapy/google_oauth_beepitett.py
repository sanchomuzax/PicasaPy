"""A PicasaPy beépített Google OAuth-kliensének betöltése."""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path

_CLIENT_ID_ENV = "PICASAPY_GOOGLE_CLIENT_ID"
_CLIENT_SECRET_ENV = "PICASAPY_GOOGLE_CLIENT_SECRET"
_CREDENTIALS_FILE = Path(__file__).with_name("_google_oauth.json")


def get_google_oauth_credentials(
    user_client_id: str = "",
    user_client_secret: str = "",
    *,
    environ: Mapping[str, str] | None = None,
    credentials_file: str | Path | None = None,
) -> tuple[str, str] | None:
    """Az első teljes klienspárt adja a felhasználói, környezeti és csomagforrásból."""
    sajat = (str(user_client_id or "").strip(), str(user_client_secret or "").strip())
    if all(sajat):
        return sajat

    kornyezet = os.environ if environ is None else environ
    kornyezeti = (
        str(kornyezet.get(_CLIENT_ID_ENV, "") or "").strip(),
        str(kornyezet.get(_CLIENT_SECRET_ENV, "") or "").strip(),
    )
    if all(kornyezeti):
        return kornyezeti

    fajl = _CREDENTIALS_FILE if credentials_file is None else Path(credentials_file)
    try:
        adat = json.loads(fajl.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(adat, dict):
        return None

    csomagolt = (
        str(adat.get("client_id", "") or "").strip(),
        str(adat.get("client_secret", "") or "").strip(),
    )
    return csomagolt if all(csomagolt) else None
