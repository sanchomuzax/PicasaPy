#!/usr/bin/env python3
"""A PyInstaller-csomag QML- és JavaScript-cache fájljainak előállítása."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

_FORRAS_KITERJESZTESEK = {".qml": ".qmlc", ".js": ".jsc"}


def _qmlcachegen() -> str:
    for nev in ("pyside6-qmlcachegen", "qmlcachegen"):
        talalat = shutil.which(nev)
        if talalat:
            return talalat

    try:
        from PySide6.QtCore import QLibraryInfo

        for hely in (
            QLibraryInfo.LibraryPath.LibraryExecutablesPath,
            QLibraryInfo.LibraryPath.BinariesPath,
        ):
            gyoker = Path(QLibraryInfo.path(hely))
            for nev in ("qmlcachegen", "qmlcachegen.exe"):
                talalat = gyoker / nev
                if talalat.is_file():
                    return str(talalat)
    except (ImportError, AttributeError):
        pass
    raise SystemExit("A PySide6 qmlcachegen eszköze nem található.")


def _compile(qml_root: Path, output: Path, compiler: str) -> dict:
    qml_root = qml_root.resolve()
    output.mkdir(parents=True, exist_ok=True)
    for korabbi in output.rglob("*"):
        if korabbi.is_file() and (
            korabbi.name == "manifest.json" or korabbi.suffix in {".qmlc", ".jsc"}
        ):
            korabbi.unlink()

    forrasok = sorted(
        path
        for path in qml_root.rglob("*")
        if path.is_file() and path.suffix in _FORRAS_KITERJESZTESEK
    )
    if not forrasok:
        raise SystemExit(f"Nem található QML/JS fájl: {qml_root}")

    entries = []
    fingerprint = hashlib.sha256()
    for forras in forrasok:
        relative = forras.relative_to(qml_root)
        cache_suffix = _FORRAS_KITERJESZTESEK[forras.suffix]
        cache_relative = relative.with_name(relative.name + cache_suffix)
        cel = output / cache_relative
        cel.parent.mkdir(parents=True, exist_ok=True)
        eredmeny = subprocess.run(
            [compiler, "--only-bytecode", "-o", str(cel), str(forras)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
            check=False,
        )
        if eredmeny.returncode != 0 or not cel.is_file():
            raise SystemExit(
                f"A QML-cache fordítása nem sikerült: {relative}\n"
                f"{eredmeny.stdout}{eredmeny.stderr}"
            )

        relative_text = relative.as_posix()
        cache_text = cache_relative.as_posix()
        source_bytes = forras.read_bytes()
        cache_bytes = cel.read_bytes()
        fingerprint.update(relative_text.encode("utf-8"))
        fingerprint.update(source_bytes)
        fingerprint.update(cache_bytes)
        entries.append({"source": relative_text, "cache": cache_text})

    manifest = {
        "format": 1,
        "cache_id": fingerprint.hexdigest(),
        "files": entries,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--qml-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    manifest = _compile(args.qml_root, args.output, _qmlcachegen())
    print(f"QML/JS cache kész: {len(manifest['files'])} fájl")
    return 0


if __name__ == "__main__":
    sys.exit(main())
