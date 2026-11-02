"""A belépett Google-fiók e-mail-címe a belépési válaszból (#6446).

Az `id_token` közvetlenül a tokenvégpontról érkezik, TLS-en, a saját
kódcserénk válaszaként. Ezért az aláírását nem ellenőrizzük. Az adatot
CSAK megjelenítésre használjuk (a menüsorban), azonosításra vagy
jogosultság-döntésre soha.
"""

from __future__ import annotations

import base64
import json
from collections.abc import Mapping


def account_email_from_tokens(tokens: Mapping[str, object]) -> str:
    """Az `id_token` törzséből az e-mail-cím; hiányzó vagy hibás esetén üres."""
    if not isinstance(tokens, Mapping):
        return ""
    token = tokens.get("id_token")
    if not isinstance(token, str):
        return ""
    fejlec_torzs_alairas = token.split(".")
    if len(fejlec_torzs_alairas) != 3:
        return ""
    torzs = _jwt_torzs(fejlec_torzs_alairas[1])
    email = torzs.get("email")
    return email.strip() if isinstance(email, str) else ""


def _jwt_torzs(resz: str) -> dict:
    try:
        bajtok = base64.urlsafe_b64decode(resz + "=" * (-len(resz) % 4))
        adat = json.loads(bajtok.decode("utf-8"))
    except ValueError:
        return {}
    return adat if isinstance(adat, dict) else {}
