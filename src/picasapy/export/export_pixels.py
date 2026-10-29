"""Képpont-dekódolás, szűrőlánc és geometriai exportműveletek."""

from __future__ import annotations

from pathlib import Path

from picasapy.lazy_cv2 import cv2
import numpy as np

from picasapy.cvimage import dekodolj_forrast
from picasapy.ini.filters import FilterOp
from picasapy.render import apply_filters, normalize_crop_ops
from picasapy.render.flip import apply_flip


# #1611: FÜGGVÉNY, nem modulszintű konstans — modulszinten a `cv2.ROTATE_*`
# olvasása a BETÖLTÉSKOR behozná az OpenCV-t, és az `export` az indulási
# láncban van (`app/controller` → `app/export_controller` → `export`).
def _rotations() -> dict[int, int]:
    return {
        1: cv2.ROTATE_90_CLOCKWISE,
        2: cv2.ROTATE_180,
        3: cv2.ROTATE_90_COUNTERCLOCKWISE,
    }

def _apply_filter_chain(image: np.ndarray, ops: tuple[FilterOp, ...]) -> np.ndarray:
    """A szűrőlánc és az aktuális crop kulcs beleégetése — a meglévő
    render-lánccal (RGB-térben, mint a bélyegkép-gyorsítótár,
    ld. `thumbs/cache.py`).

    A `_export_filter_ops` a forrás képszekciójának `crop=` mezőjét az
    utolsó `crop64` tételen érvényesíti, annak láncbeli helyét megtartva.

    Hibás/idegen lánc-bejegyzésnél (#73-elv) a szűretlen kép a helyes
    visszaesés, nem az export teljes meghiúsulása — ezt a #301 óta maga az
    apply_filters garantálja (a hibás op kimarad, kivétel nem szökik ki)."""
    if not ops:
        return image
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    rendered, _skipped = apply_filters(rgb, ops)
    return cv2.cvtColor(rendered, cv2.COLOR_RGB2BGR)


def _export_filter_ops(
    ops: tuple[FilterOp, ...],
    crop: str | None,
    *,
    crop_ini_readable: bool = True,
    warning_key: str | None = None,
) -> tuple[FilterOp, ...]:
    """Az export közös render-előkészítője (#4008, #4013)."""
    return normalize_crop_ops(
        ops,
        crop,
        crop_ini_readable=crop_ini_readable,
        warning_key=warning_key,
    )


def _decode_image(source: Path) -> np.ndarray:
    """Bájt-alapú dekódolás a közös helperrel (`picasapy.cvimage`, #151/7).
    EXIF-forgatással dekódol; hibánál emberi olvasásra szánt kivétel.

    #3120: a közös belépőn megy, tehát a **nyers (RAW)** fájlok is
    exportálhatók — korábban a puszta `cv2.imdecode` némán `None`-t adott
    rájuk, és az export „nem dekódolható kép" hibával állt meg."""
    image = dekodolj_forrast(source)
    if image is None:
        raise ValueError(f"Nem dekódolható kép: {source}")
    return image


def _apply_rotation(image: np.ndarray, rotate_steps: int) -> np.ndarray:
    """90°-os órairányú lépések beégetése (a Picasa/Qt konvenciója szerint)."""
    steps = rotate_steps % 4
    if steps == 0:
        return image
    return cv2.rotate(image, _rotations()[steps])


def render_photo_pixels(
    source: Path,
    ops: tuple[FilterOp, ...],
    *,
    rotate_steps: int = 0,
    flip_flags: int = 0,
) -> np.ndarray:
    """Teljes felbontású, szerkesztett kép BGR-ben (#4602).

    A közös belépő az export és a nyomtatás számára: `_decode_image` EXIF-
    tájolással és RAW-dekóderrel olvas, utána a filters-lánc, a tükrözés és
    az órairányú negyedfordulat kerül a képpontokba. A `ops`-nak a hívó már
    érvényesítette a külön tárolt `crop=` kulcsot.
    """
    image = _decode_image(source)
    image = _apply_filter_chain(image, ops)
    # #3065: előbb a tükrözés, utána a forgatás — a mért sorrend.
    image = apply_flip(image, flip_flags)
    return _apply_rotation(image, rotate_steps)
