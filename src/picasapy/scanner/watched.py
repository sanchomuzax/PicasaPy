"""WatchedFolders.txt olvasás — soronként egy abszolút útvonal (Scan Always).

Az eredeti (Windows-os) Picasa fájlját is olvassuk importnál: CRLF, BOM és
backslash-útvonalak tűrése kötelező. A hiányzó fájl üres listát jelent
(nincs figyelt mappa), nem hibát.
"""

from __future__ import annotations

from pathlib import Path


def read_watched_folders(path: str | Path) -> tuple[str, ...]:
    file_path = Path(path)
    if not file_path.exists():
        return ()
    text = file_path.read_text(encoding="utf-8-sig")
    return tuple(line.strip() for line in text.splitlines() if line.strip())
