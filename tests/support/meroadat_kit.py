"""A kiválasztott mérőképek kinyerése a helyi meroadat-archívumból."""

from __future__ import annotations

import shutil
import tarfile
from pathlib import Path, PurePosixPath


_ARCHIVE = Path.home() / ".local" / "share" / "picasapy-meroadat" / "meroadat.tar"


def extract_meroadat_files(
    members: tuple[str, ...], destination: Path
) -> dict[str, Path] | None:
    """Csak a név szerint kért archívumtagokat bontja ki a teszt BT-jébe.

    Hiányzó archívum vagy tag esetén `None`-t ad vissza, így a golden-próba
    más gépen kihagyható. Kizárólag a megnevezett archívumtagokat olvassa.
    """
    if not _ARCHIVE.is_file():
        return None

    with tarfile.open(_ARCHIVE, mode="r:*") as archive:
        try:
            selected = [archive.getmember(name) for name in members]
        except KeyError:
            return None
        if not all(member.isfile() for member in selected):
            return None

        extracted: dict[str, Path] = {}
        for member in selected:
            relative = PurePosixPath(member.name)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError(f"Nem biztonságos mérőadat-útvonal: {member.name!r}")
            target = destination.joinpath(*relative.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                return None
            with source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
            extracted[member.name] = target
    return extracted
