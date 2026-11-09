"""Diavetítés-képkockák méretezése és áttűnései (#6173)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from picasapy.lazy_cv2 import cv2
import numpy as np

from picasapy.cvimage import dekodolj_forrast


def letterbox(
    image: np.ndarray,
    width: int,
    height: int,
    background: tuple[int, int, int] = (0, 0, 0),
) -> np.ndarray:
    """A kép arányos beillesztése a vászonra, középre, háttérrel kitöltve."""
    if width < 1 or height < 1:
        raise ValueError(f"Érvénytelen vászon: {width}×{height}")
    src_h, src_w = image.shape[:2]
    if src_h < 1 or src_w < 1:
        raise ValueError("Üres kép")
    scale = min(width / src_w, height / src_h)
    new_w = max(1, min(width, round(src_w * scale)))
    new_h = max(1, min(height, round(src_h * scale)))
    interpolation = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
    resized = cv2.resize(image, (new_w, new_h), interpolation=interpolation)
    canvas = np.full((height, width, 3), np.array(background, dtype=np.uint8), dtype=np.uint8)
    x0 = (width - new_w) // 2
    y0 = (height - new_h) // 2
    canvas[y0 : y0 + new_h, x0 : x0 + new_w] = resized
    return canvas


def crop_to_fit(
    image: np.ndarray,
    width: int,
    height: int,
) -> np.ndarray:
    """A fotó kitölti a képkockát; a középre eső szélek levágódnak."""
    if width < 1 or height < 1:
        raise ValueError(f"Érvénytelen vászon: {width}×{height}")
    src_h, src_w = image.shape[:2]
    if src_h < 1 or src_w < 1:
        raise ValueError("Üres kép")
    scale = max(width / src_w, height / src_h)
    new_w = max(width, round(src_w * scale))
    new_h = max(height, round(src_h * scale))
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    x0 = (new_w - width) // 2
    y0 = (new_h - height) // 2
    return resized[y0 : y0 + height, x0 : x0 + width]


def _decode(source: Path) -> np.ndarray:
    #: #3120: a KÖZÖS belépőn megy — a `cv2.imdecode`-nak nincs nyers
    #: dekódere, tehát a RAW fájlokra némán `None`-t adott.
    image = dekodolj_forrast(source)
    if image is None:
        raise ValueError("nem dekódolható kép")
    return image


@lru_cache(maxsize=8)
def _atmenet_koordinatak(magassag: int, szelesseg: int) -> tuple[np.ndarray, np.ndarray]:
    """A maszkok normalizált sor- és oszlopkoordinátái méret szerint cache-elve."""
    # A korábbi np.mgrid-képlet float64 koordinátákat adott; a körmaszk
    # határán a float32 2–4 pixellel eltérő exportot eredményezett.
    xn = (np.arange(szelesseg, dtype=np.float64) + 0.5) / max(1, szelesseg)
    yn = (np.arange(magassag, dtype=np.float64) + 0.5) / max(1, magassag)
    xn.setflags(write=False)
    yn.setflags(write=False)
    return xn, yn


def _atmeneti_kocka(
    kilepo: np.ndarray, erkezo: np.ndarray, tipus: str, arany: float, *, koordinatak=None
) -> np.ndarray:
    """Egy áttűnés képkockája a kiválasztott Picasa-típus alapján.

    A teljes 22-es készletet a spec szerinti kulcsokkal kezeljük. Az eredeti
    program effekt-görbéi nem részei a 2.1-es leírásnak; itt a típus neve
    szerinti, kiszámítható geometriai változat készül.
    """
    p = min(1.0, max(0.0, arany))
    if tipus == "cut":
        return erkezo
    if tipus in {"dissolve", "timelapse"}:
        if tipus == "timelapse":
            p = round(p * 6) / 6
        return cv2.addWeighted(kilepo, 1.0 - p, erkezo, p, 0.0)
    if tipus in {"dissolveblack", "dissolvewhite"}:
        alapszin = 0 if tipus == "dissolveblack" else 255
        koztes = np.full_like(kilepo, alapszin)
        if p < 0.5:
            return cv2.addWeighted(kilepo, 1.0 - p * 2, koztes, p * 2, 0.0)
        return cv2.addWeighted(koztes, 1.0 - (p - 0.5) * 2, erkezo, (p - 0.5) * 2, 0.0)

    magassag, szelesseg = kilepo.shape[:2]
    if tipus in {"pushleft", "pushright", "pushtop", "pushdown"}:
        out = np.empty_like(kilepo)
        if tipus == "pushleft":
            offset = round(szelesseg * p)
            out[:, : szelesseg - offset] = kilepo[:, offset:]
            out[:, szelesseg - offset :] = erkezo[:, :offset]
        elif tipus == "pushright":
            offset = round(szelesseg * p)
            out[:, offset:] = kilepo[:, : szelesseg - offset]
            out[:, :offset] = erkezo[:, szelesseg - offset :]
        elif tipus == "pushtop":
            offset = round(magassag * p)
            out[: magassag - offset, :] = kilepo[offset:, :]
            out[magassag - offset :, :] = erkezo[:offset, :]
        else:
            offset = round(magassag * p)
            out[offset:, :] = kilepo[: magassag - offset, :]
            out[:offset, :] = erkezo[magassag - offset :, :]
        return out

    if tipus in {"kenburns", "kenburnsaoi"}:
        # Az arc fókuszpontja nem része a jelenlegi fotóadat-modellnek; a
        # középpontos pásztázás mindkét Ken Burns-változatnál stabil alap.
        scale = 1.12 - 0.12 * p
        uj_w = max(1, round(szelesseg * scale))
        uj_h = max(1, round(magassag * scale))
        nagy = cv2.resize(erkezo, (uj_w, uj_h), interpolation=cv2.INTER_LINEAR)
        x0 = max(0, (uj_w - szelesseg) // 2)
        y0 = max(0, (uj_h - magassag) // 2)
        mozgatott = nagy[y0 : y0 + magassag, x0 : x0 + szelesseg]
        return cv2.addWeighted(kilepo, 1.0 - p, mozgatott, p, 0.0)

    if tipus in {
        "wipeleft",
        "wiperight",
        "wipeup",
        "wipedown",
        "diagwipeul",
        "diagwipeur",
        "diagwipedl",
        "diagwipedr",
        "circlein",
        "circleout",
        "rect",
    }:
        koord_fuggveny = koordinatak or _atmenet_koordinatak
        xn, yn = koord_fuggveny(magassag, szelesseg)
        if tipus == "wipeleft":
            maszk = xn[None, :] < p
        elif tipus == "wiperight":
            maszk = xn[None, :] >= 1.0 - p
        elif tipus == "wipeup":
            maszk = yn[:, None] >= 1.0 - p
        elif tipus == "wipedown":
            maszk = yn[:, None] < p
        elif tipus == "diagwipeul":
            maszk = xn[None, :] + yn[:, None] < 2.0 * p
        elif tipus == "diagwipeur":
            maszk = (1.0 - xn[None, :]) + yn[:, None] < 2.0 * p
        elif tipus == "diagwipedl":
            maszk = xn[None, :] + (1.0 - yn[:, None]) < 2.0 * p
        elif tipus == "diagwipedr":
            maszk = (1.0 - xn[None, :]) + (1.0 - yn[:, None]) < 2.0 * p
        elif tipus in {"circlein", "circleout"}:
            tav = np.sqrt(((xn[None, :] - 0.5) * 2) ** 2 + ((yn[:, None] - 0.5) * 2) ** 2)
            maszk = tav <= p * np.sqrt(2)
            if tipus == "circleout":
                maszk = ~maszk
        else:
            maszk = (np.abs(xn[None, :] - 0.5) <= p * 0.5) & (np.abs(yn[:, None] - 0.5) <= p * 0.5)
        return np.where(maszk[..., None], erkezo, kilepo)

    return erkezo
