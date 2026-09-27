"""Az Útlevélkép (#1401) arc-központú négyzet-kivágása és döntési fája.

`docs/specs/picasa-menu-parancsok-viselkedes.md`, 24. szakasz — kimért
képlet (`0x00531c60` és a sikeres ág, `0x00531e50`-től):

1. az egy-arc feltétel: a felismerő pontosan EGY arcnál engedi tovább a
   parancsot, nulla vagy kettő-plusz arcnál hibaüzenet;
2. a kivágás **felül** az arcmagasság HARMADÁVAL, **alul** a HAT TIZEDÉVEL
   nagyobb a felismert arc-téglalapnál (fejtér fent, váll lent);
3. a kivágás **NÉGYZET**, az arc VÍZSZINTES közepére igazítva;
4. végül a kép HATÁRAIRA vágva — a bal/felső oldal legalább 0, a
   jobb/alsó legfeljebb a kép szélessége/magassága (FÜGGETLEN korlátok,
   nem újra-négyzetesítés: egy szélen lévő arc kivágása emiatt már nem
   feltétlenül négyzet — ez a mért viselkedés, nem hiba).

Ez a modul TISZTA: sem Qt-, sem OpenCV-függése nincs, csak arc-téglalapot
(pixelben) és képméretet kap — a `PassportPhotoController` hívja."""

from __future__ import annotations

import math
from dataclasses import dataclass

#: felül: az arcmagasság 1/3-a ráhagyás (fejtér)
TOP_MARGIN_RATIO = 1.0 / 3.0

#: alul: az arcmagasság 0,6-szorosa ráhagyás (váll)
BOTTOM_MARGIN_RATIO = 0.6

#: A három döntési kimenet (`0x00531c60`: `Passport0`/`Passport1`/siker).
NO_FACE = "no_face"
MULTIPLE_FACES = "multiple_faces"
SINGLE_FACE = "single_face"


def classify_face_count(face_count: int) -> str:
    """A talált arcok száma → a három kimenet egyike.

    Nulla arcnál `NO_FACE` („Nem találhatók arcok"), egynél többnél
    `MULTIPLE_FACES` („Úgy tűnik, több arc van a képen."), pontosan egynél
    `SINGLE_FACE` — ekkor mehet a kivágás."""
    if face_count <= 0:
        return NO_FACE
    if face_count > 1:
        return MULTIPLE_FACES
    return SINGLE_FACE


@dataclass(frozen=True)
class PixelRect:
    """Egy kivágási téglalap KÉPPIXELBEN, a kép bal felső sarkától mérve."""

    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top


def passport_crop_rect(
    face_left: float,
    face_top: float,
    face_right: float,
    face_bottom: float,
    image_width: int,
    image_height: int,
) -> PixelRect:
    """A 24. szakasz képlete szerinti kivágás, a modul fejlécében leírt
    négy lépésben.

    ⚠️ **Kerekítési egyszerűsítés.** A mért gép (`fistp` `∓0,5`-del) a
    kifelé kerekítést valósítja meg — ide `floor`/`ceil` került helyette
    (szélsőérték-mentesen ugyanaz az eredmény, csak a pontos FPU-kerekítés
    fél-egész eseteit nem replikáljuk bitpontosan). A képpont-szintű
    kivágásnál ennek legfeljebb egy képpontnyi hatása lehet — ld. az
    #1401 jegy jelentését.
    """
    # 2. kerekítés KIFELÉ — a felismert arc-téglalap sosem szűkül
    left = math.floor(face_left)
    top = math.floor(face_top)
    right = math.ceil(face_right)
    bottom = math.ceil(face_bottom)

    # 3. a függőleges ráhagyás (fejtér fent, váll lent)
    face_height = bottom - top
    crop_top = round(top - face_height * TOP_MARGIN_RATIO)
    crop_bottom = round(bottom + face_height * BOTTOM_MARGIN_RATIO)

    # 4. NÉGYZET, az arc vízszintes közepére igazítva
    center_x = (left + right) / 2.0
    half = (crop_bottom - crop_top) / 2.0
    crop_left = round(center_x - half)
    crop_right = round(center_x + half)

    # 5. levágás a kép határaira — FÜGGETLEN korlátok (ld. a docstringet)
    crop_left = max(0, crop_left)
    crop_top = max(0, crop_top)
    crop_right = min(int(image_width), crop_right)
    crop_bottom = min(int(image_height), crop_bottom)

    return PixelRect(
        left=crop_left, top=crop_top, right=crop_right, bottom=crop_bottom
    )


__all__ = [
    "MULTIPLE_FACES",
    "NO_FACE",
    "SINGLE_FACE",
    "PixelRect",
    "classify_face_count",
    "passport_crop_rect",
]
