"""Közös segédfüggvények Picasa-stílusú konfigfájlokhoz.

A `WatchedFolders.txt` és a `FRExcludeFolders.txt` közös tulajdonságai:
- kis-nagybetű-független fájlnév-keresés kell (élesben, pl. Samba/NAS
  megosztáson, `watchedfolders.txt` / `frexcludefolders.txt` néven is
  előfordulnak — ld. MEMORY 2026-07-16),
- tartalmuk azonos formátumú: soronként egy abszolút útvonal, CRLF/BOM és
  backslash-útvonalak tűrésével (az eredeti, Windows-os Picasa fájlját is
  be kell tudni olvasni importnál).
"""

from __future__ import annotations

from pathlib import Path


def find_config_file(directory: str | Path, filename: str) -> Path | None:
    """Az adott könyvtárban a `filename` nevű fájl kis-nagybetű-független
    megkeresése. Ha a könyvtár nem létezik, vagy nincs egyező nevű fájl,
    `None` — ez nem hibaeset (hiányzó konfigfájl = üres lista)."""
    dir_path = Path(directory)
    if not dir_path.is_dir():
        return None
    target = filename.lower()
    for entry in sorted(dir_path.iterdir()):
        if entry.is_file() and entry.name.lower() == target:
            return entry
    return None


def read_path_list(path: str | Path) -> tuple[str, ...]:
    """Soronként egy útvonal olvasása. A hiányzó fájl üres listát jelent."""
    file_path = Path(path)
    if not file_path.exists():
        return ()
    text = file_path.read_text(encoding="utf-8-sig")
    return tuple(line.strip() for line in text.splitlines() if line.strip())
