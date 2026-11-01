"""A PyInstaller Windows-verzióerőforrásának előállítása."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path


def _negyreszes_verzio(verzio: str) -> tuple[int, int, int, int]:
    """A három vagy négy tagú kiadási verziót Windows-verzióvá alakítja."""
    reszek = verzio.split(".")
    if len(reszek) not in (3, 4) or any(
        not re.fullmatch(r"\d+", resz) for resz in reszek
    ):
        raise ValueError(
            f"A Windows-verzióadat nem tudja értelmezni ezt a verziót: {verzio}"
        )
    szamok = [int(resz) for resz in reszek]
    return tuple((szamok + [0] * (4 - len(szamok)))[:4])


def write_version_info(
    pyproject_path: Path,
    output_path: Path,
    original_filename: str,
) -> str:
    """A PyInstaller által olvasható verziófájlt írja a megadott build mappába."""
    projekt = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    verzio = projekt["project"]["version"]
    negyreszes = _negyreszes_verzio(verzio)
    fajlnev = repr(original_filename)

    tartalom = f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={negyreszes},
    prodvers={negyreszes},
    mask=0x3f,
    flags=0x0,
    OS=0x4,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0),
  ),
  kids=[
    StringFileInfo([
      StringTable('040904B0', [
        StringStruct('CompanyName', 'PicasaPy'),
        StringStruct('FileDescription', 'PicasaPy'),
        StringStruct('FileVersion', {verzio!r}),
        StringStruct('InternalName', {fajlnev}),
        StringStruct('OriginalFilename', {fajlnev}),
        StringStruct('ProductName', 'PicasaPy'),
        StringStruct('ProductVersion', {verzio!r}),
      ])
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])]),
  ],
)
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(tartalom, encoding="utf-8")
    return verzio
