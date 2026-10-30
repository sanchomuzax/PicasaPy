"""A Picasa-kollázs beállításai és lap-előkészítése."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .render import _decode, fit_to_frame
from .shadow import ShadowParams, shadow_params
from .themes import (
    BORDER_THEMES,
    COLLAGE_THEMES,
    THEME_CAPABILITIES,
    NOBORDER,
    PICTUREGRID,
)

_DEFAULT_WIDTH = 1600
_DEFAULT_HEIGHT = 1200
BACKGROUND_DIM_ALPHA = 0x26
BACKGROUND_DIM_FACTOR = (255 - BACKGROUND_DIM_ALPHA) / 255
logger = logging.getLogger("picasapy.collage.picasa_render")

@dataclass(frozen=True)
class PicasaCollageSettings:
    """A Picasa kollázs-panel beállításai.

    `theme` a `themes.COLLAGE_THEMES` egyike, `border` a
    `themes.BORDER_THEMES` egyike. A `spacing` a „Rács vastagsága" csúszka
    **0…1** értéke (nem képpont) — a `rects.to_pixel_rects` így várja.
    `background` BGR hármas.
    """

    theme: str = PICTUREGRID
    border: str = NOBORDER
    width: int = _DEFAULT_WIDTH
    height: int = _DEFAULT_HEIGHT
    background: tuple[int, int, int] = (255, 255, 255)
    spacing: float = 0.0
    seed: int = 0
    caption: str = ""
    #: Az Indexkép két fejlécsorának forrása (#1273). A mezők a `.cxf`
    #: `albumTitle` / `albumDate` értékei; a darabszámot a rajzoló ismeri.
    album_title: str = ""
    album_date: str = ""
    #: A „Beállítás képkockaközéppontként" gomb eredménye: melyik kép kapja
    #: a hangsúlyos középső helyet a Képkockamozaikban. `None` esetén NINCS
    #: rögzített kép — és ilyenkor az eredeti is az alap (Mozaik-)pakolóra
    #: esik vissza (spec 1.9.14: „a `CLocationTree` nem helyettesíti, hanem
    #: kiegészíti az alap algoritmust").
    frame_center: int | None = None
    #: #978: a felület „képfeliratok" kapcsolója (`collage/showcaptions`).
    #: Az eredetiben a Polaroid-felirat KÉT feltételhez kötött — a kapcsoló
    #: BE **és** a keret `polaroid` (`0x00839830`). Nálunk a rajzolási úton
    #: eddig csak a keret szerepelt, tehát a kapcsoló NÉMA volt: kikapcsolva
    #: is ott maradt a felirat a mentett képen.
    captions: bool = True
    #: Rajzoljunk-e árnyékot. `None` = a téma alapértelmezése (a maszk
    #: 14. bitje) — ez az eredeti viselkedése, ld. `effective_shadow`.
    shadow: bool | None = None
    #: A HÁTTÉRKÉP útvonala (#1015). Üresen a `background` szín marad. A
    #: kép a lapot KITÖLTI (arányt tartva, középről vágva) — a golden
    #: háttere a teljes lapot fedi, élesen, effekt nélkül.
    background_image: str = ""

    @property
    def effective_border(self) -> str:
        """A ténylegesen alkalmazott képkeret — a téma képességével szűrve.

        #923: a Picasában a keretválasztó CSAK a Képkupacnál és az
        Indexképnél látszik (a maszk 9. bitje). A többi témánál a beállítás
        elő sem állítható a felületen, ezért itt **figyelmen kívül marad**.

        Miért nem hiba, hanem elhagyás: a `.cxf` projektfájl tartalmazhat
        sávon kívüli értéket (kézzel szerkesztve, vagy régebbi verzióból),
        és a round-trip elv szerint azt MEGŐRIZZÜK — csak nem rajzoljuk ki.
        A tárolt `border` ezért változatlan marad; a renderelő ezt a
        property-t használja.
        """
        return self.border if THEME_CAPABILITIES[self.theme].borders else NOBORDER

    @property
    def effective_spacing(self) -> float:
        """A ténylegesen alkalmazott térköz — a téma képességével szűrve.

        A térköz-csúszka a három rácsos témánál látszik (10. bit); a
        Képkupacnál, az Indexképnél és a Többszörös exponálásnál nincs
        értelmezve. Ld. `effective_border` a megőrzés indoklásáért.
        """
        return self.spacing if THEME_CAPABILITIES[self.theme].spacing else 0.0

    @property
    def effective_shadow(self) -> bool:
        """Rajzolunk-e árnyékot. A 11. bit engedélyezi, a 14. az ALAPÉRTÉKE.

        A Többszörös exponálásnál az árnyék tiltott (a maszk 11. bitje 0),
        a Képkupacnál és az Indexképnél alapból BE, a többinél KI.
        """
        képesség = THEME_CAPABILITIES[self.theme]
        if not képesség.shadow:
            return False
        return képesség.shadow_default if self.shadow is None else self.shadow

    def __post_init__(self) -> None:
        if self.theme not in COLLAGE_THEMES:
            raise ValueError(f"Ismeretlen kollázs-téma: {self.theme!r}")
        if self.border not in BORDER_THEMES:
            raise ValueError(f"Ismeretlen képkeret: {self.border!r}")
        if self.width < 16 or self.height < 16:
            raise ValueError(f"Érvénytelen lapméret: {self.width}×{self.height}")
        if not 0.0 <= self.spacing <= 1.0:
            raise ValueError(f"A rács vastagsága 0..1 közé esik: {self.spacing}")
        if len(self.background) != 3 or not all(0 <= c <= 255 for c in self.background):
            raise ValueError(f"Érvénytelen háttérszín: {self.background}")

_DEFAULT_SETTINGS = PicasaCollageSettings()

def _canvas(settings: PicasaCollageSettings) -> np.ndarray:
    """A lap alapja: a beállított szín, vagy a HÁTTÉRKÉP (#1015).

    ⚠️ A háttérkép baja SOHA nem viheti el a kollázst. Hiányzó, olvashatatlan
    vagy sérült fájlnál a szín marad — a felhasználó képei fontosabbak, mint
    a háttér, és egy elszálló mentés sokkal rosszabb egy egyszínű háttérnél.

    A kép a lapot KITÖLTI (`fill=True`): arányt tartva nagyít, a túllógó részt
    középről vágja. A kitöltés-vagy-nyújtás kérdés nincs lemérve — a döntés
    indoklása a `tests/collage/test_kephatter_1015.py` modul-docstringjében.

    A háttér **TOMPÍTVA** kerül a lapra (`BACKGROUND_DIM_FACTOR`) — ez nem
    stílus, hanem mérés: a golden háttere a forráskép 85,1%-án áll."""
    canvas = np.empty((settings.height, settings.width, 3), dtype=np.uint8)
    canvas[:, :] = settings.background
    if not settings.background_image:
        return canvas
    try:
        hatter = _decode(Path(settings.background_image))
    except (ValueError, OSError) as hiba:
        logger.info(
            "A kollázs háttérképe nem olvasható (%s): %s",
            settings.background_image,
            hiba,
        )
        return canvas
    illesztett = fit_to_frame(hatter, settings.width, settings.height, fill=True)
    canvas[:, :] = np.rint(
        illesztett.astype(np.float32) * BACKGROUND_DIM_FACTOR
    ).astype(np.uint8)
    return canvas


def shadow_for_settings(
    settings: PicasaCollageSettings, count: int
) -> ShadowParams | None:
    """A téma árnyék-paraméterei, vagy `None`, ha nem kell árnyék (#977).

    Két kapu van, és MINDKETTŐ a képesség-maszkból jön: az
    `effective_shadow` (11. bit engedélyez, 14. bit az alapérték), és a
    `shadow.shadow_params` maga is a 11. bitet nézi. Így a Többszörös
    exponálás tiltása egyetlen forrásból származik — témanév-hasonlítás
    sehol nem születik.

    ⚠️ **Nyilvános** (#1021): az élő vászon UGYANEZT hívja, ugyanazzal a
    `render_settings()`-szel, amivel a mentés dolgozik. Enélkül a vászon
    egy párhuzamos számítást tartana, ami előbb-utóbb elválna — és a
    felhasználó azt látná, hogy a mentett kép mást mutat, mint az
    előnézet."""
    if not settings.effective_shadow:
        return None
    return shadow_params(
        settings.theme,
        page_width=settings.width,
        page_height=settings.height,
        count=max(1, count),
    )
