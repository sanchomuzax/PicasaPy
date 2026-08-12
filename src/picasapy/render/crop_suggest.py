"""Automatikus vágás-JAVASLATOK (#448).

A Picasa vágás-panelén **három javaslat-gomb** ült, mindegyik saját
előnézettel — a mögöttük álló stratégiák a binárisban nevesítve vannak:

    „Close crop to faces"          — szoros vágás az arcokra
    „Compose picture around faces" — kompozíció az arcok köré
    „Crop by horizon line"         — vágás a horizontvonal mentén
    „Crop by Red/Green"            — szín-domináns terület alapján
    „Crop by variance"             — a legrészletgazdagabb terület alapján

A stratégiák BELSŐ működését a bináris nem adta meg — csak a nevüket. Az itt
következő megvalósítás tehát a NEVEK szerinti, dokumentált saját modell, nem
a Picasa algoritmusának rekonstrukciója; a különbség a docstringekben
végig ki van mondva, hogy egy későbbi mérés (valódi Picasa-kimenet) ne
tévessze össze a kettőt.

A modul TISZTA: numpy tömböt és arc-téglalapokat kap, relatív [0..1]
téglalapokat ad vissza — nincs Qt-függése, ezért önmagában tesztelhető.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from picasapy.ini.rect64 import Rect64

#: A javaslat-gombok száma a panelen (az eredetin is három).
SUGGESTION_COUNT = 3

#: „Close crop to faces": az arcok befoglalója köré tett ráhagyás, az arc-
#: befoglaló rövidebb oldalához mérve. A portré-vágás bevett aránya: az arc
#: ne érjen a képszélig, de a vágás szoros maradjon.
_FACE_TIGHT_MARGIN = 0.55

#: „Compose picture around faces": a vágás a kép ekkora hányadát tartja meg,
#: és az arcok súlypontját a harmadoló-vonalak metszéspontjához igazítja.
_COMPOSE_KEEP = 0.72
_THIRD = 1.0 / 3.0

#: A tartalom-alapú stratégiák (variancia, szín) ekkora ablakkal keresnek —
#: a kép rövidebb oldalának hányadában.
_CONTENT_KEEP = 0.75

#: A variancia-/szín-térkép felbontása. A keresés kis rácson fut (a nagy kép
#: pixelre pontos vizsgálata semmit nem adna hozzá, cserébe lassú lenne).
_ANALYSIS_EDGE = 128


@dataclass(frozen=True)
class CropSuggestion:
    """Egy javaslat: a stratégia kulcsa és a javasolt relatív téglalap.

    A `key` a felület felirat-kulcsa (a fordítás a QML dolga), a `rect`
    pedig közvetlenül az `EditController.applyCrop`-nak adható.
    """

    key: str
    rect: Rect64


def _clamped(left: float, top: float, width: float, height: float) -> Rect64:
    """[0..1]-be tolt (nem vágott!) téglalap.

    Tolás, nem vágás: a kért MÉRET megmarad, csak visszacsúszik a képbe —
    így a kért képarány nem torzul el a szélen.
    """
    width = min(max(width, 1e-3), 1.0)
    height = min(max(height, 1e-3), 1.0)
    left = min(max(left, 0.0), 1.0 - width)
    top = min(max(top, 0.0), 1.0 - height)
    return Rect64(left=left, top=top, right=left + width, bottom=top + height)


def _size_for_aspect(
    keep: float, image_aspect: float, aspect: float | None
) -> tuple[float, float]:
    """A vágás relatív szélessége/magassága a kért képaránynál.

    `aspect` a KÉPARÁNY (szélesség/magasság) a vágott képre; `None` esetén a
    forráskép arányát tartjuk. A `keep` a megtartott hányad — a nagyobbik
    oldalt ez adja, a másikat az arány.
    """
    if aspect is None or aspect <= 0:
        return keep, keep
    # relatív koordinátákban a kért arányhoz a képarány hányadosa kell
    ratio = aspect / image_aspect
    if ratio >= 1.0:
        return keep, keep / ratio
    return keep * ratio, keep


def _faces_bounds(faces) -> tuple[float, float, float, float] | None:
    """Az arc-téglalapok együttes befoglalója relatív koordinátákban."""
    rects = [f for f in faces if f is not None]
    if not rects:
        return None
    left = min(float(r.left) for r in rects)
    top = min(float(r.top) for r in rects)
    right = max(float(r.right) for r in rects)
    bottom = max(float(r.bottom) for r in rects)
    if right <= left or bottom <= top:
        return None
    return left, top, right, bottom


def close_crop_to_faces(faces, image_aspect: float, aspect: float | None) -> Rect64 | None:
    """„Close crop to faces" — szoros vágás az arcok köré.

    Az arcok befoglalója köré `_FACE_TIGHT_MARGIN` ráhagyás kerül (a
    befoglaló rövidebb oldalához mérve), majd a kért képarányra igazítjuk.
    Arc nélkül `None` — a hívó ilyenkor másik stratégiát kínál.
    """
    bounds = _faces_bounds(faces)
    if bounds is None:
        return None
    left, top, right, bottom = bounds
    margin = min(right - left, bottom - top) * _FACE_TIGHT_MARGIN
    left, top = left - margin, top - margin
    right, bottom = right + margin, bottom + margin
    width, height = right - left, bottom - top
    if aspect is not None and aspect > 0:
        ratio = aspect / image_aspect
        # a befoglalót NÖVELJÜK a kért arányra (sosem vágunk le arcot)
        if width / height < ratio:
            width = height * ratio
        else:
            height = width / ratio
    center_x, center_y = (left + right) / 2, (top + bottom) / 2
    return _clamped(center_x - width / 2, center_y - height / 2, width, height)


def compose_around_faces(
    faces, image_aspect: float, aspect: float | None
) -> Rect64 | None:
    """„Compose picture around faces" — kompozíció az arcok köré.

    A szoros vágással szemben itt a KÖRNYEZET is számít: a vágás a kép
    `_COMPOSE_KEEP` hányadát tartja meg, és az arcok súlypontját a felső
    harmadoló-vonalhoz igazítja (a portré-kompozíció bevett szabálya:
    a szem-vonal a felső harmadra esik). Arc nélkül `None`.
    """
    bounds = _faces_bounds(faces)
    if bounds is None:
        return None
    left, top, right, bottom = bounds
    center_x, center_y = (left + right) / 2, (top + bottom) / 2
    width, height = _size_for_aspect(_COMPOSE_KEEP, image_aspect, aspect)
    # vízszintesen középre, függőlegesen a FELSŐ harmadra igazítva
    return _clamped(
        center_x - width / 2, center_y - height * _THIRD, width, height
    )


def _analysis_gray(image: np.ndarray) -> np.ndarray:
    """Kis felbontású szürkeárnyalatos másolat az elemzéshez."""
    height, width = image.shape[:2]
    scale = _ANALYSIS_EDGE / max(height, width)
    if scale < 1.0:
        image = cv2.resize(
            image,
            (max(1, int(width * scale)), max(1, int(height * scale))),
            interpolation=cv2.INTER_AREA,
        )
    return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY).astype(np.float32)


def _best_window(weight: np.ndarray, width: float, height: float) -> Rect64:
    """A `weight` térkép legnagyobb összsúlyú, adott relatív méretű ablaka.

    Integrálkép (`cv2.integral`) — az összes ablak-pozíció egyetlen menetben
    kiértékelhető, tehát a keresés a rács méretétől függetlenül gyors.
    """
    rows, cols = weight.shape
    window_w = max(1, int(round(width * cols)))
    window_h = max(1, int(round(height * rows)))
    if window_w >= cols and window_h >= rows:
        return _clamped(0.0, 0.0, width, height)
    integral = cv2.integral(weight.astype(np.float64))
    sums = (
        integral[window_h:, window_w:]
        - integral[:-window_h, window_w:]
        - integral[window_h:, :-window_w]
        + integral[:-window_h, :-window_w]
    )
    index = int(np.argmax(sums))
    top_index, left_index = divmod(index, sums.shape[1])
    return _clamped(left_index / cols, top_index / rows, width, height)


def crop_by_variance(
    image: np.ndarray, image_aspect: float, aspect: float | None
) -> Rect64:
    """„Crop by variance" — a legrészletgazdagabb terület.

    A részletgazdagságot a helyi szórás adja (a Sobel-gradiens abszolút
    értéke): a legnagyobb összegű ablak nyer.
    """
    gray = _analysis_gray(image)
    detail = np.abs(cv2.Sobel(gray, cv2.CV_32F, 1, 0)) + np.abs(
        cv2.Sobel(gray, cv2.CV_32F, 0, 1)
    )
    width, height = _size_for_aspect(_CONTENT_KEEP, image_aspect, aspect)
    return _best_window(detail, width, height)


def crop_by_horizon(
    image: np.ndarray, image_aspect: float, aspect: float | None
) -> Rect64:
    """„Crop by horizon line" — vágás a horizontvonal mentén.

    A horizont a legerősebb VÍZSZINTES él sora (a függőleges gradiens
    soronkénti összege); a vágás úgy áll, hogy ez a sor a közelebbi
    harmadoló-vonalra essen — a tájkép-kompozíció bevett szabálya.
    """
    gray = _analysis_gray(image)
    horizontal_edges = np.abs(cv2.Sobel(gray, cv2.CV_32F, 0, 1)).sum(axis=1)
    horizon = float(np.argmax(horizontal_edges)) / max(1, gray.shape[0] - 1)
    width, height = _size_for_aspect(_CONTENT_KEEP, image_aspect, aspect)
    # a közelebbi harmadoló-vonalra igazítjuk (felső vagy alsó)
    target = _THIRD if horizon < 0.5 else 1.0 - _THIRD
    return _clamped(0.5 - width / 2, horizon - height * target, width, height)


def crop_by_red_green(
    image: np.ndarray, image_aspect: float, aspect: float | None
) -> Rect64:
    """„Crop by Red/Green" — a szín-domináns terület.

    Súlytérkép: mennyivel emelkedik a piros, illetve a zöld csatorna a másik
    kettő átlaga fölé. Ez emeli ki a virágot/lombot/bőrtónust a semleges
    háttérből; a legnagyobb összsúlyú ablak nyer.
    """
    height_px, width_px = image.shape[:2]
    scale = _ANALYSIS_EDGE / max(height_px, width_px)
    small = image
    if scale < 1.0:
        small = cv2.resize(
            image,
            (max(1, int(width_px * scale)), max(1, int(height_px * scale))),
            interpolation=cv2.INTER_AREA,
        )
    values = small.astype(np.float32)
    red, green, blue = values[..., 0], values[..., 1], values[..., 2]
    red_excess = np.maximum(red - (green + blue) / 2.0, 0.0)
    green_excess = np.maximum(green - (red + blue) / 2.0, 0.0)
    width, height = _size_for_aspect(_CONTENT_KEEP, image_aspect, aspect)
    return _best_window(red_excess + green_excess, width, height)


def suggest_crops(
    image: np.ndarray, faces=(), aspect: float | None = None
) -> tuple[CropSuggestion, ...]:
    """A panelen megjelenő HÁROM javaslat, sorrendben (#448).

    A választás determinisztikus, és az eredeti gombkészletet követi:

    * **arcokkal**: szoros arc-vágás · kompozíció az arcok köré · variancia,
    * **arcok nélkül**: variancia · horizont · szín-dominancia.

    Az arcos ág azért előzi meg a tartalom-alapút, mert az eredeti panelen is
    az arc-stratégiák állnak elöl, és mert ha van arc a képen, az a téma.

    Args:
        image: RGB `uint8` kép (H, W, 3).
        faces: relatív [0..1] arc-téglalapok (`Rect64`), üres is lehet.
        aspect: a kért képarány (szélesség/magasság), vagy `None` = a
            forráskép arányát tartjuk.

    Returns:
        Legfeljebb `SUGGESTION_COUNT` javaslat; üres, ha a kép érvénytelen.
    """
    if image is None or image.ndim != 3 or image.shape[2] != 3:
        return ()
    height_px, width_px = image.shape[:2]
    if height_px < 2 or width_px < 2:
        return ()
    image_aspect = width_px / height_px

    suggestions: list[CropSuggestion] = []
    tight = close_crop_to_faces(faces, image_aspect, aspect)
    if tight is not None:
        composed = compose_around_faces(faces, image_aspect, aspect)
        suggestions.append(CropSuggestion("faces_tight", tight))
        if composed is not None:
            suggestions.append(CropSuggestion("faces_compose", composed))
        suggestions.append(
            CropSuggestion("variance", crop_by_variance(image, image_aspect, aspect))
        )
    else:
        suggestions.append(
            CropSuggestion("variance", crop_by_variance(image, image_aspect, aspect))
        )
        suggestions.append(
            CropSuggestion("horizon", crop_by_horizon(image, image_aspect, aspect))
        )
        suggestions.append(
            CropSuggestion("red_green", crop_by_red_green(image, image_aspect, aspect))
        )
    return tuple(suggestions[:SUGGESTION_COUNT])
