"""A szöveges diák képkockáinak renderelése (#6173)."""

from __future__ import annotations

from typing import Any

from picasapy.lazy_cv2 import cv2
import numpy as np
from PIL import Image, ImageColor, ImageDraw


def render_text_frame(
    slide: dict[str, object],
    settings: Any,
    skala: float = 1.0,
    *,
    ido: float | None = None,
    font_loader,
) -> np.ndarray:
    """Képkockát készít a Szöveg fülön felvett dia beállításaiból.

    A `settings` már a TÉNYLEGES vászonméretet hordozza; a `skala` (a teljes
    filmmérethez képesti arány, export: 1.0) a betűméretet és a margót
    arányosan igazítja (a körvonal legalább 1 px), hogy a kis kocka ugyanazt mutassa kicsiben.
    """

    def szin(ertek: object, tartalek: str) -> tuple[int, int, int]:
        try:
            return ImageColor.getrgb(str(ertek))[:3]
        except (ValueError, TypeError):
            return ImageColor.getrgb(tartalek)

    hatter = szin(slide.get("backgroundColor"), "#000000")
    betuszín = szin(slide.get("textColor"), "#ffffff")
    kep = Image.new("RGB", (settings.width, settings.height), hatter)
    rajz = ImageDraw.Draw(kep, "RGBA")
    meret = max(8, int(slide.get("size", 16)))
    if skala != 1.0:
        meret = max(1, round(meret * skala))
    betu = str(slide.get("font", "DejaVuSans"))
    fontfajlok = [betu, f"{betu}.ttf"]
    if slide.get("italic"):
        fontfajlok.append("DejaVuSans-Oblique.ttf")
    if slide.get("bold"):
        fontfajlok.append("DejaVuSans-Bold.ttf")
    fontfajlok.append("DejaVuSans.ttf")
    font = font_loader(tuple(fontfajlok), meret)

    szoveg = str(slide.get("text", ""))
    if not szoveg:
        return cv2.cvtColor(np.asarray(kep), cv2.COLOR_RGB2BGR)
    stilus = int(slide.get("style", 0))
    if skala == 1.0:
        marg = max(16, settings.width // 18)
    else:
        marg = max(1, round(max(16, round(settings.width / skala) // 18) * skala))
    keret = rajz.multiline_textbbox((0, 0), szoveg, font=font)
    szoveg_szeles = keret[2] - keret[0]
    szoveg_magas = keret[3] - keret[1]
    if stilus in (2, 3, 11):
        x = max(marg, (settings.width - szoveg_szeles) // 2)
        y = settings.height - szoveg_magas - marg
    elif stilus == 9:
        x, y = marg, (settings.height - szoveg_magas) // 2
    elif stilus == 10:
        x, y = settings.width - szoveg_szeles - marg, (settings.height - szoveg_magas) // 2
    else:
        x, y = (settings.width - szoveg_szeles) // 2, (settings.height - szoveg_magas) // 2

    rajzolando_szoveg = szoveg
    alfa = 255
    if ido is not None and stilus in (1, 8, 11):
        # A felületről létrehozott MXF-dia blacktime és extra időeltolása 0.
        # Az időtengely a helyi filmrenderelésé: kockaindex / fps.
        kezdet = 0.0
        if stilus == 8:
            idotartam = settings.seconds_per_photo
        else:
            idotartam = settings.transition_seconds
            if idotartam == 0:
                idotartam = settings.seconds_per_photo / 3
        if idotartam > 0:
            arany = max(0.0, min(1.0, (ido + 0.02 - kezdet) / idotartam))
            simitott = 3 * arany**2 - 2 * arany**3
            if stilus == 1:
                # A TextFadeMove X-eltolása 0-ról -M-re tart; M a saját
                # render geometriájából számolt szövegdoboz-balél.
                x = round(x - simitott * x)
                alfa = round(255 * arany)
            elif stilus == 8:
                # B a vászon alsó éle, A a középre igazított szövegdoboz.
                also = settings.height
                kozep = 0.5 * (settings.height - szoveg_magas)
                y = round(also + simitott * (kozep - also))
            else:
                # A timeline a szöveg UTF-8 bájthosszát lépteti. Csak a
                # teljes karakterek rajzolhatók, a fél UTF-8 karakter nem.
                hossz = len(szoveg.encode("utf-8"))
                bajtlimit = max(1, int(hossz * arany + 0.5))
                lathato = []
                felhasznalt = 0
                for karakter in szoveg:
                    karakterbajtok = len(karakter.encode("utf-8"))
                    if felhasznalt + karakterbajtok > bajtlimit:
                        break
                    lathato.append(karakter)
                    felhasznalt += karakterbajtok
                rajzolando_szoveg = "".join(lathato)
                if not rajzolando_szoveg:
                    return cv2.cvtColor(np.asarray(kep), cv2.COLOR_RGB2BGR)

    if stilus in (4, 5, 6, 7):
        sav = (0, 0, 0, 180) if stilus in (4, 6) else (255, 255, 255, 180)
        rajz.rectangle((0, y - marg // 2, settings.width, y + szoveg_magas + marg // 2), fill=sav)
        betuszín = (255, 255, 255) if stilus in (4, 6) else (0, 0, 0)
    kontur = bool(slide.get("outline")) or stilus in (3, 11)
    kitoltes = (*betuszín, alfa) if alfa < 255 else betuszín
    kontur_szin = (0, 0, 0) if betuszín != (0, 0, 0) else (255, 255, 255)
    kontur_kitoltes = (*kontur_szin, alfa) if alfa < 255 else kontur_szin
    szoveg_reteg = Image.new("RGBA", kep.size, (0, 0, 0, 0)) if alfa < 255 else None
    szoveg_rajz = ImageDraw.Draw(szoveg_reteg) if szoveg_reteg is not None else rajz
    szoveg_rajz.multiline_text(
        (x, y),
        rajzolando_szoveg,
        font=font,
        fill=kitoltes,
        stroke_width=max(1, meret // 18) if kontur or slide.get("bold") else 0,
        stroke_fill=kontur_kitoltes,
    )
    if szoveg_reteg is not None:
        kep = Image.alpha_composite(kep.convert("RGBA"), szoveg_reteg).convert("RGB")
    return cv2.cvtColor(np.asarray(kep), cv2.COLOR_RGB2BGR)
