"""Fiktív Google-fiók adatai a belépési tesztekhez (#6446).

Személyes cím SEHOL: a teszt csak ezt a példacímet használja.
"""

from __future__ import annotations

import base64
import json

PROBA_EMAIL = "proba.fiok@example.com"
PROBA_REFRESH = "test-refresh-token"


def _kodol(resz: bytes) -> str:
    return base64.urlsafe_b64encode(resz).decode("ascii").rstrip("=")


def id_token(torzs) -> str:
    """Próba-id_token: a fejléc és az aláírás a teszthez nem számít."""
    fejlec = _kodol(json.dumps({"alg": "RS256", "typ": "JWT"}).encode("utf-8"))
    return f"{fejlec}.{_kodol(json.dumps(torzs).encode('utf-8'))}.aláírás"
