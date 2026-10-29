"""A diavetítés hangsávjának felismerése és illesztése (#6173)."""

from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


def _ffmpeg_exe() -> str | None:
    """FFmpeg útvonal: beágyazott kerék, majd a rendszer PATH-ja."""
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, RuntimeError):
        return shutil.which("ffmpeg")


def _hang_hossza(ffmpeg: str, hang: Path) -> float:
    """A hangsáv hosszát az FFmpeg bemeneti fejlécéből olvassa ki."""
    if not hang.is_file():
        raise FileNotFoundError(f"A kiválasztott hangsáv nem található: {hang}")
    eredmeny = subprocess.run(
        [ffmpeg, "-i", str(hang), "-f", "null", "-"],
        capture_output=True,
        text=True,
        check=False,
    )
    talalat = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", eredmeny.stderr)
    if talalat is None:
        raise RuntimeError("A hangsáv időtartamát nem sikerült beolvasni.")
    ora, perc, masodperc = talalat.groups()
    return int(ora) * 3600 + int(perc) * 60 + float(masodperc)


def _hanggal_osszeilleszt(ffmpeg: str, video: Path, hang: Path, cel: Path, mod: int) -> None:
    """A kész képsávhoz AAC hangsávot illeszt, a választott három mód egyikével."""
    handle, atmeneti_cel = tempfile.mkstemp(
        prefix=f".{cel.stem}-", suffix=cel.suffix or ".mp4", dir=cel.parent
    )
    os.close(handle)
    try:
        parancs = [ffmpeg, "-y"]
        if mod == 2:
            parancs.extend(["-stream_loop", "-1"])
        parancs.extend(
            [
                "-i",
                str(video),
                "-i",
                str(hang),
                "-map",
                "0:v:0",
                "-map",
                "1:a:0",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-shortest",
                atmeneti_cel,
            ]
        )
        eredmeny = subprocess.run(parancs, capture_output=True, text=True, check=False)
        if eredmeny.returncode:
            raise RuntimeError("A hangsávot nem sikerült a filmhez illeszteni.")
        os.replace(atmeneti_cel, cel)
    finally:
        Path(atmeneti_cel).unlink(missing_ok=True)
