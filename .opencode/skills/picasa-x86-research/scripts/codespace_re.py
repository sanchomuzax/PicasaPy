#!/usr/bin/env python3
"""Picasa profile for the pinned public Codespace x86 RE toolkit."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sys
from typing import Callable
from urllib.request import Request, urlopen


TOOLKIT_VERSION = "v0.1.0"
TOOLKIT_SHA256 = (
    "92f9bf53e528ec3e873d020a40bc0363de416166ce7a2e939e0626ce1d969e50"
)
TOOLKIT_URL = (
    "https://raw.githubusercontent.com/sanchomuzax/"
    f"codespace-x86-re-toolkit/{TOOLKIT_VERSION}/"
    "skills/codespace-x86-re/scripts/codespace_re.py"
)
DEFAULT_MACHINE = "standardLinux32gb"
MAX_TOOLKIT_BYTES = 1024 * 1024


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def ensure_toolkit(
    destination: Path,
    expected_sha256: str = TOOLKIT_SHA256,
    opener: Callable = urlopen,
) -> Path:
    """Return a verified cached toolkit, downloading the pinned file if needed."""
    if destination.is_file() and sha256_file(destination) == expected_sha256:
        return destination

    destination.unlink(missing_ok=True)
    request = Request(TOOLKIT_URL, headers={"User-Agent": "picasa-x86-research"})
    with opener(request, timeout=30) as response:
        payload = response.read(MAX_TOOLKIT_BYTES + 1)
    if len(payload) > MAX_TOOLKIT_BYTES:
        raise SystemExit("A letöltött Codespace toolkit váratlanul túl nagy.")
    actual_sha256 = sha256_bytes(payload)
    if actual_sha256 != expected_sha256:
        raise SystemExit(
            "A letöltött Codespace toolkit SHA-256 értéke eltér: "
            f"{actual_sha256} != {expected_sha256}"
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(f"{destination.suffix}.part")
    try:
        partial.write_bytes(payload)
        partial.replace(destination)
    finally:
        partial.unlink(missing_ok=True)
    return destination


def cache_destination() -> Path:
    cache_root = Path(
        os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))
    )
    return cache_root / "picasa-x86-research" / TOOLKIT_VERSION / "codespace_re.py"


def resolve_toolkit() -> Path:
    """Resolve an optional local pinned copy or the verified user cache."""
    override = os.environ.get("PICASA_X86_RE_TOOLKIT")
    if not override:
        return ensure_toolkit(cache_destination())

    path = Path(override).expanduser().resolve()
    if path.is_dir():
        path = path / "skills" / "codespace-x86-re" / "scripts" / "codespace_re.py"
    if not path.is_file():
        raise SystemExit(f"A megadott publikus toolkit nem található: {path}")
    actual_sha256 = sha256_file(path)
    if actual_sha256 != TOOLKIT_SHA256:
        raise SystemExit(
            "A helyi Codespace toolkit nem a pinnelt release: "
            f"{actual_sha256} != {TOOLKIT_SHA256}"
        )
    return path


def forwarded_args(arguments: list[str]) -> list[str]:
    """Apply only the Picasa workload's measured machine-size default."""
    forwarded = list(arguments)
    if forwarded and forwarded[0] in {"doctor", "create"}:
        if "--machine" not in forwarded:
            forwarded[1:1] = ["--machine", DEFAULT_MACHINE]
    return forwarded


def main() -> None:
    toolkit = resolve_toolkit()
    arguments = forwarded_args(sys.argv[1:])
    os.execv(sys.executable, [sys.executable, str(toolkit), *arguments])


if __name__ == "__main__":
    main()
