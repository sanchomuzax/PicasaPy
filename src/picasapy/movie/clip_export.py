"""Egy videó vágott szakaszának exportja MP4-fájlba (#4564)."""

from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

_INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _ffmpeg_executable() -> str | None:
    """A csomagolt FFmpeg-et részesíti előnyben, a PATH a tartalék."""
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, RuntimeError):
        return shutil.which("ffmpeg")


def _safe_stem(source: Path) -> str:
    stem = _INVALID_FILENAME_CHARS.sub("", source.stem).strip().strip(".")
    return stem or "video"


def _reserve_output(folder: Path, stem: str) -> Path:
    """Ütközésmentesen lefoglal egy fájlnevet, felülírás nélkül."""
    for number in range(10_000):
        suffix = "" if number == 0 else str(number)
        target = folder / f"{stem}{suffix}.mp4"
        try:
            descriptor = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o666)
        except FileExistsError:
            continue
        os.close(descriptor)
        return target
    raise ValueError(f"Nem található szabad klipnév ebben a mappában: {folder}")


def export_clip(
    source: str | Path,
    destination_dir: str | Path,
    *,
    start_ms: int = -1,
    end_ms: int = -1,
) -> Path:
    """A megadott vágáspontok közötti szakaszt MP4-be kódolja.

    A ``-1`` az adott oldalon vágás nélküli határt jelöl. A videó kódolása
    háttérből hívható szinkron művelet; a felületet a vezérlő külön szálon
    indítja. Az újrakódolás képkockapontos kezdést és befejezést ad.
    """
    source = Path(source)
    if not source.is_file():
        raise FileNotFoundError(f"A forrásvideó nem található: {source}")

    start = int(start_ms)
    end = int(end_ms)
    if start < -1 or end < -1:
        raise ValueError("A vágáspont −1 vagy nemnegatív ezredmásodperc lehet.")
    start_at = max(0, start)
    end_at = None if end < 0 else end
    if end_at is not None and end_at <= start_at:
        raise ValueError("A klip befejezőpontja legyen a kezdőpont után.")

    ffmpeg = _ffmpeg_executable()
    if ffmpeg is None:
        raise RuntimeError("A klip exportjához nem található FFmpeg.")

    folder = Path(destination_dir)
    folder.mkdir(parents=True, exist_ok=True)
    target = _reserve_output(folder, _safe_stem(source))
    temporary: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{target.stem}.", suffix=".mp4", dir=folder
        )
        os.close(descriptor)
        temporary = Path(temporary_name)

        command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y"]
        if start_at > 0:
            command.extend(["-ss", f"{start_at / 1000:.3f}"])
        command.extend(["-i", str(source)])
        if end_at is not None:
            command.extend(["-t", f"{(end_at - start_at) / 1000:.3f}"])
        command.extend(
            [
                "-map",
                "0:v:0",
                "-map",
                "0:a?",
                "-c:v",
                "mpeg4",
                "-q:v",
                "3",
                "-c:a",
                "aac",
                "-b:a",
                "128k",
                "-movflags",
                "+faststart",
                str(temporary),
            ]
        )

        result = subprocess.run(
            command, capture_output=True, text=True, errors="replace", check=False
        )
        if (
            result.returncode != 0
            or not temporary.is_file()
            or temporary.stat().st_size == 0
        ):
            details = result.stderr.strip() or "Az FFmpeg nem készített kimeneti fájlt."
            raise RuntimeError(f"A klip exportja nem sikerült: {details}")
        temporary.replace(target)
        return target
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


__all__ = ["export_clip"]
