"""Szintetikus tesztképek a dedup-tesztekhez: strukturált (nem egyszínű)
mintázatok, hogy a dHash-nek legyen mit megkülönböztetnie."""

import io

import numpy as np
from PIL import Image


def gradient_jpeg(path, size=(64, 64), quality=90):
    """Átlós szürkeárnyalatos színátmenet — folytonos, alacsony-frekvenciás
    mintázat."""
    width, height = size
    xs = np.linspace(0, 255, width, dtype=np.uint8)
    ys = np.linspace(0, 255, height, dtype=np.uint8)
    ramp = (xs[np.newaxis, :].astype(np.uint16) + ys[:, np.newaxis]) // 2
    rgb = np.stack([ramp] * 3, axis=-1).astype(np.uint8)
    Image.fromarray(rgb, "RGB").save(path, "JPEG", quality=quality)
    return path


def checkerboard_jpeg(path, size=(64, 64), tile=8, quality=90):
    """Sakktábla-mintázat — magas-frekvenciás, a gradienstől jól
    megkülönböztethető."""
    width, height = size
    tiles = np.indices((height, width)).sum(axis=0) // tile % 2
    board = (tiles * 255).astype(np.uint8)
    rgb = np.stack([board] * 3, axis=-1)
    Image.fromarray(rgb, "RGB").save(path, "JPEG", quality=quality)
    return path


def photo_like_jpeg(path, size=(64, 64), quality=90):
    """Fotószerű, ALACSONY frekvenciás mintázat (néhány lassú szinusz
    összege, csatornánként eltolva) — ez az a tartomány, amit a dHash
    ténylegesen megfog, és amin a redukált dekódolás stabil (#294).
    A sakktáblával ellentétben nincs benne Nyquist fölötti részlet."""
    width, height = size
    xs = np.linspace(0, 1, width)[np.newaxis, :]
    ys = np.linspace(0, 1, height)[:, np.newaxis]
    channels = []
    for phase in (0.0, 0.7, 1.4):
        wave = (
            np.sin(2 * np.pi * (xs + phase))
            + np.sin(2 * np.pi * 1.5 * (ys + phase))
            + np.sin(2 * np.pi * (xs + ys))
        )
        wave = np.broadcast_to(wave, (height, width))
        normalized = (wave - wave.min()) / (wave.max() - wave.min())
        channels.append((normalized * 255).astype(np.uint8))
    rgb = np.stack(channels, axis=-1)
    Image.fromarray(rgb, "RGB").save(path, "JPEG", quality=quality)
    return path


def resave_as_jpeg(source_path, target_path, size=None, quality=60):
    """Egy meglévő kép átméretezve és/vagy alacsonyabb minőséggel
    újratömörítve — a "hasonló, de nem bitre azonos" eset szimulálása."""
    with Image.open(source_path) as image:
        image = image.convert("RGB")
        if size is not None:
            image = image.resize(size, Image.BICUBIC)
        buffer = io.BytesIO()
        image.save(buffer, "JPEG", quality=quality)
        target_path.write_bytes(buffer.getvalue())
    return target_path
