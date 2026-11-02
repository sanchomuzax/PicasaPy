"""SHA256SUMS-manifeszt feldolgozása és payload-ellenőrzés."""

from __future__ import annotations

import hashlib
import hmac
import re

SHA256SUMS_NAME = "SHA256SUMS"


def parse_sha256sums(manifest: str) -> dict[str, str]:
    """GNU sha256sum formátumú manifesztből fájlnév → hex digest térképet ad."""
    result: dict[str, str] = {}
    for line in manifest.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"([0-9a-fA-F]{64})\s+\*?(.+)", line)
        if not match:
            raise ValueError("Érvénytelen SHA256SUMS sor")
        result[match.group(2).strip()] = match.group(1).lower()
    return result


def verify_sha256(payload: bytes, expected: str) -> bool:
    """Eltérésnél kivételt dob, hogy hibás fájl ne juthasson telepítésig."""
    actual = hashlib.sha256(payload).hexdigest()
    if not hmac.compare_digest(actual, expected.lower()):
        raise ValueError("A letöltött fájl SHA-256 ujjlenyomata nem egyezik")
    return True
