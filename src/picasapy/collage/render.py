"""Kollázs-renderelés OpenCV-vel (#29).

A `layout.py` megmondja, MELYIK kép HOVÁ kerül; itt csak a képfeldolgozás
történik: dekódolás, keretre illesztés (kitöltő vágás vagy arányos
beillesztés), opcionális fehér paszpartu, és forgatás a képhalomnál.

Elvek:

- **Egy rossz kép nem viheti el a kollázst** — a hibás forrás kimarad, a
  többi rendben elkészül (az exporter `ExportReport` mintája szerint a
  hívó megkapja, mi maradt ki és miért).
- **Bájt-alapú beolvasás** (`picasapy.cvimage.read_image_bytes`) — a
  `cv2.imread` Windowson ékezetes útvonalon némán None-t ad (#65).
- **Immutábilis beállítás-objektum**, a kimenet új tömb; a bemeneti
  képeket sosem módosítjuk.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from picasapy.cvimage import read_image_bytes

from .layout import GRID, Placement, layout_for

# A vászon (és a képkeretek) alapértelmezett mérete — a Picasa kollázsai
# is nagy felbontású, nyomtatható képek.
_DEFAULT_WIDTH = 1600
_DEFAULT_HEIGHT = 1200

# A képhalom fehér paszpartuja a keret rövidebb oldalának ennyied része.
_MAT_RATIO = 0.04


@dataclass(frozen=True)
class CollageSettings:
    """Kollázs-beállítások: típus, vászonméret, háttér, keret és rés.

    `background` BGR hármas (az OpenCV sorrendje). A `seed` csak a
    képhalomnál számít — azonos maggal ugyanaz a kollázs áll elő."""

    kind: str = GRID
    width: int = _DEFAULT_WIDTH
    height: int = _DEFAULT_HEIGHT
    background: tuple[int, int, int] = (255, 255, 255)
    spacing: int = 8
    columns: int = 4
    seed: int = 0
    matted: bool = True  # fehér paszpartu a képek körül (Picasa-hatás)

    def __post_init__(self) -> None:
        if self.width < 16 or self.height < 16:
            raise ValueError(f"Érvénytelen vászonméret: {self.width}×{self.height}")
        if self.spacing < 0:
            raise ValueError(f"Érvénytelen rés: {self.spacing}")
        if len(self.background) != 3 or not all(
            0 <= c <= 255 for c in self.background
        ):
            raise ValueError(f"Érvénytelen háttérszín: {self.background}")


@dataclass(frozen=True)
class CollageReport:
    """A kollázs eredménye: a kész kép + a kihagyott források és okaik."""

    image: np.ndarray
    used: tuple[Path, ...]
    skipped: tuple[Path, ...] = ()
    reasons: tuple[str, ...] = ()


_DEFAULT_SETTINGS = CollageSettings()


def _decode(source: Path) -> np.ndarray:
    payload = read_image_bytes(source)
    if payload is None:
        raise ValueError("üres vagy nem olvasható fájl")
    image = cv2.imdecode(payload, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("nem dekódolható kép")
    return image


def fit_to_frame(
    image: np.ndarray, width: int, height: int, *, fill: bool
) -> np.ndarray:
    """A kép keretre igazítása.

    `fill=True`: a keretet hézag nélkül kitölti, a túllógó rész középről
    vágva (rács, mozaik, halom). `fill=False`: a teljes kép látszik, a
    maradék hely átlátszatlanul üresen marad — a hívó tölti ki háttérrel
    (kontaktmásolat)."""
    if width < 1 or height < 1:
        raise ValueError(f"Érvénytelen keret: {width}×{height}")
    src_h, src_w = image.shape[:2]
    if src_h < 1 or src_w < 1:
        raise ValueError("Üres kép")
    scale = (
        max(width / src_w, height / src_h)
        if fill
        else min(width / src_w, height / src_h)
    )
    new_w = max(1, round(src_w * scale))
    new_h = max(1, round(src_h * scale))
    interpolation = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
    resized = cv2.resize(image, (new_w, new_h), interpolation=interpolation)
    if not fill:
        return resized
    x0 = max(0, (new_w - width) // 2)
    y0 = max(0, (new_h - height) // 2)
    return resized[y0 : y0 + height, x0 : x0 + width]


def _paste(canvas: np.ndarray, tile: np.ndarray, x: int, y: int) -> None:
    """Csempe a vászonra, a vászon szélein levágva (a halom kilóghat)."""
    ch, cw = canvas.shape[:2]
    th, tw = tile.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(cw, x + tw), min(ch, y + th)
    if x0 >= x1 or y0 >= y1:
        return
    canvas[y0:y1, x0:x1] = tile[y0 - y : y1 - y, x0 - x : x1 - x]


def _matted(tile: np.ndarray, mat: int) -> np.ndarray:
    """Fehér paszpartu a csempe köré (a Picasa kollázsainak jellegzetessége)."""
    if mat < 1:
        return tile
    return cv2.copyMakeBorder(
        tile, mat, mat, mat, mat, cv2.BORDER_CONSTANT, value=(255, 255, 255)
    )


def _rotated_paste(
    canvas: np.ndarray, tile: np.ndarray, place: Placement
) -> None:
    """Elforgatott csempe beillesztése maszkkal (a halom lapjai)."""
    th, tw = tile.shape[:2]
    center = (tw / 2, th / 2)
    matrix = cv2.getRotationMatrix2D(center, place.angle, 1.0)
    cos, sin = abs(matrix[0, 0]), abs(matrix[0, 1])
    out_w = int(th * sin + tw * cos)
    out_h = int(th * cos + tw * sin)
    matrix[0, 2] += out_w / 2 - center[0]
    matrix[1, 2] += out_h / 2 - center[1]
    rotated = cv2.warpAffine(tile, matrix, (out_w, out_h))
    mask = cv2.warpAffine(
        np.full((th, tw), 255, dtype=np.uint8), matrix, (out_w, out_h)
    )
    x = place.x - (out_w - tw) // 2
    y = place.y - (out_h - th) // 2
    ch, cw = canvas.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(cw, x + out_w), min(ch, y + out_h)
    if x0 >= x1 or y0 >= y1:
        return
    region = canvas[y0:y1, x0:x1]
    sub_mask = mask[y0 - y : y1 - y, x0 - x : x1 - x] > 0
    region[sub_mask] = rotated[y0 - y : y1 - y, x0 - x : x1 - x][sub_mask]


def make_collage(
    sources, settings: CollageSettings = _DEFAULT_SETTINGS
) -> CollageReport:
    """Kollázs a megadott forrásokból; a hibás képek kimaradnak, nem
    állítják meg a munkát.

    Ha egyetlen kép sem dekódolható, a vászon a háttérszínnel áll elő —
    a hívó a `used` üres voltából látja, hogy nincs mit menteni."""
    paths = [Path(s) for s in sources]
    if not paths:
        raise ValueError("Kollázshoz legalább egy kép kell.")

    decoded: list[tuple[Path, np.ndarray]] = []
    skipped: list[Path] = []
    reasons: list[str] = []
    for path in paths:
        try:
            decoded.append((path, _decode(path)))
        except (ValueError, OSError) as error:
            skipped.append(path)
            reasons.append(str(error))

    canvas = np.full(
        (settings.height, settings.width, 3),
        np.array(settings.background, dtype=np.uint8),
        dtype=np.uint8,
    )
    if not decoded:
        return CollageReport(
            image=canvas, used=(), skipped=tuple(skipped), reasons=tuple(reasons)
        )

    places = layout_for(
        settings.kind,
        len(decoded),
        settings.width,
        settings.height,
        spacing=settings.spacing,
        columns=settings.columns,
        seed=settings.seed,
    )
    for (_path, image), place in zip(decoded, places, strict=True):
        mat = int(min(place.width, place.height) * _MAT_RATIO) if settings.matted else 0
        inner_w = max(1, place.width - 2 * mat)
        inner_h = max(1, place.height - 2 * mat)
        tile = fit_to_frame(image, inner_w, inner_h, fill=place.fill)
        tile = _matted(tile, mat)
        if place.angle:
            _rotated_paste(canvas, tile, place)
        else:
            # arányos illesztésnél (kontaktmásolat) a csempe kisebb lehet
            # a keretnél — középre igazítjuk, a maradék a háttéré
            tile_h, tile_w = tile.shape[:2]
            offset_x = place.x + (place.width - tile_w) // 2
            offset_y = place.y + (place.height - tile_h) // 2
            _paste(canvas, tile, offset_x, offset_y)

    return CollageReport(
        image=canvas,
        used=tuple(path for path, _ in decoded),
        skipped=tuple(skipped),
        reasons=tuple(reasons),
    )


def write_collage(target: Path, image: np.ndarray, quality: int = 92) -> Path:
    """A kész kollázs kiírása JPEG-ként (bájt-alapon, ékezetes útvonalon is).

    A `cv2.imwrite` Windowson ékezetes útvonalon némán nem ír (#190) —
    ezért `imencode` + Python-IO, és hangos hiba néma elnyelés helyett."""
    if not 1 <= quality <= 100:
        raise ValueError(f"Érvénytelen JPEG-minőség: {quality}")
    ok, encoded = cv2.imencode(
        ".jpg", image, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)]
    )
    if not ok:
        raise ValueError("A kollázs kódolása nem sikerült.")
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(encoded.tobytes())
    return target
