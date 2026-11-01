"""A csomag részeként előre fordított QML-cache előkészítése induláskor."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from collections.abc import MutableMapping
from pathlib import Path
from pathlib import PurePosixPath

_MANIFEST = "manifest.json"
_MARKER = ".picasapy-qml-cache-id"
_CACHE_SUFFIXES = {".qml": ".qmlc", ".js": ".jsc"}


def _qt_cache_file_name(local_source_path: str, suffix: str) -> str:
    """A Qt cache-neve a normalizált, helyi forrásútvonal SHA-1 lenyomata."""
    qt_path = local_source_path.replace("\\", "/")
    digest = hashlib.sha1(qt_path.encode("utf-8")).hexdigest()
    return digest + suffix


def _seed_packaged_qml_cache(
    qml_root: Path,
    *,
    bundle_dir: Path | None = None,
    cache_dir: Path | None = None,
    environ: MutableMapping[str, str] | None = None,
) -> int:
    """A beépített cache-t bemásolja a Qt lemez-cache-ébe a QML-motor előtt.

    A cache-fájl neve a QML forrás abszolút útvonalának SHA-1 lenyomata.
    Ezért csomagtelepítésenként az aktuális QML-útvonalhoz nevezzük át a
    build közben előállított, útvonalfüggetlen cache-egységeket.
    """
    env = os.environ if environ is None else environ
    bundle = (
        Path(bundle_dir)
        if bundle_dir is not None
        else Path(__file__).with_name("qmlcache")
    )
    manifest_path = bundle / _MANIFEST
    if not manifest_path.is_file() or env.get("QML_DISABLE_DISK_CACHE"):
        return 0

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        cache_id = str(manifest["cache_id"])
        entries = manifest["files"]
        if (
            manifest.get("format") != 1
            or not cache_id
            or not isinstance(entries, list)
        ):
            return 0
    except (OSError, ValueError, KeyError, TypeError):
        return 0

    if cache_dir is None:
        cache_path = env.get("QML_DISK_CACHE_PATH")
        if cache_path:
            cache_dir = Path(cache_path)
        else:
            from PySide6.QtCore import QStandardPaths

            cache_location = QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.CacheLocation
            )
            if not cache_location:
                return 0
            cache_dir = Path(cache_location) / "qmlcache"
    else:
        cache_dir = Path(cache_dir)
    env["QML_DISK_CACHE_PATH"] = str(cache_dir)

    qml_root = Path(qml_root)
    normalized_entries: list[tuple[Path, Path, Path]] = []
    for entry in entries:
        try:
            source_relative = PurePosixPath(entry["source"])
            cache_relative = PurePosixPath(entry["cache"])
            if (
                source_relative.is_absolute()
                or cache_relative.is_absolute()
                or ".." in source_relative.parts
                or ".." in cache_relative.parts
            ):
                return 0
            cache_suffix = _CACHE_SUFFIXES[source_relative.suffix]
            if cache_relative.suffix != cache_suffix:
                return 0
            source = qml_root.joinpath(*source_relative.parts)
            packaged_cache = bundle.joinpath(*cache_relative.parts)
            if not source.is_file() or not packaged_cache.is_file():
                return 0
            cache_name = _qt_cache_file_name(str(source.absolute()), cache_suffix)
            normalized_entries.append(
                (source, packaged_cache, Path(cache_name))
            )
        except (KeyError, TypeError, ValueError):
            return 0

    root_identity = str(qml_root.absolute())
    marker_value = f"{cache_id}\n{root_identity}\n"
    marker_path = cache_dir / _MARKER
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        if marker_path.read_text(encoding="utf-8") == marker_value and all(
            (cache_dir / target_name).is_file()
            for _source, _compiled, target_name in normalized_entries
        ):
            return 0
    except OSError:
        pass

    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        for _source, packaged_cache, target_name in normalized_entries:
            shutil.copyfile(packaged_cache, cache_dir / target_name)
        marker_path.write_text(marker_value, encoding="utf-8")
    except OSError:
        return 0
    return len(normalized_entries)
