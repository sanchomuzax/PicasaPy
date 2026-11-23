"""A Hangolás pipettájának mintavétele a réteg ELŐTTI lánc képéből (#7385).

Az eredetiben (J5a, E10, E11, E23) a pipetta p4-e a kép FORRÁSÁNAK színe, és
nem egy képpont, hanem TERÜLETÁTLAG: a bézs folt határán (x=782) a p4 a bézs és
a kék 8 bites csatornánkénti átlaga, a bézs súlya 2/5; 10 képpontra a határtól
már a tiszta folt.

A réteg előtti lánc képe az előnézet léptékében készül, ugyanazon az úton, mint
a megjelenített előnézet (`EditPreviewProvider._render_at_preview_scale`), és
fotónként EGY bejegyzésként tárolódik:

- az aláírás (fájl és mérete, színkezelés, lánc, festés) minden változásnál
  érvényteleníti, így a tárolt kép sosem elavult;
- az ismételt kattintás nem renderel újra (a nehéz láncon ez 10 másodperces
  fagyás volt a GUI-szálon);
- a háttér-render ingyen feltölti, ha a megjelenített lánc maga a pipetta
  lánca (nem megnyitott látogatás): az első kattintás is azonnali.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from picasapy.lazy_import import lazy_callable
from picasapy.scanner import PICASA_INI_NAME

from .edit_preview_cache import _LRU_CAPACITY, gyors_elonezet_aktiv

if TYPE_CHECKING:
    from picasapy.ini.filters import FilterOp

# #6688: a render csomag az első előnézeti rendereléskor töltődik be
normalize_crop_ops = lazy_callable("picasapy.render", "normalize_crop_ops")

#: A mintaterület oldala FORRÁS-képpontban. KIMONDOTT FELTEVÉS (#7385, B14): a
#: mért négy pont (x=782, 772, 762, 742) a kattintott képpontra középre
#: igazított páratlan négyzetek közül csak az 5x5-ösre illik (3x3: 1/3, 7x7:
#: 3/7 a bézs súlya a határon, a mért 2/5 helyett). A pontos méretet a
#: 7345-B14 mérés dönti el: ha az más, EZ az egyetlen szám változik.
MINTA_FORRAS_KEPPONT = 5


def mintaablak_oldala(arany: float) -> int:
    """A mintaablak oldala az előnézet léptékű képen: az 5 forrás-képpontnak
    megfelelő, legközelebbi PÁRATLAN szám (legalább 1).

    Az `arany` az előnézeti kép és a teljes felbontású forrás aránya
    (`_elonezeti_arany`); 1-nél nagyobb vagy érvénytelen értéknél 1 (a kép
    teljes felbontású, az ablak 5x5). Páratlan, hogy a kattintott képpontra
    középre igazítható legyen."""
    if not math.isfinite(arany) or arany <= 0:
        arany = 1.0
    kivant = MINTA_FORRAS_KEPPONT * min(1.0, arany)
    return 2 * math.floor((kivant - 1) / 2 + 0.5) + 1


def teruletatlag(kep: np.ndarray, nx: float, ny: float, oldal: int) -> tuple[int, int, int] | None:
    """A (nx, ny) normált pontra középre igazított `oldal` x `oldal` négyzet
    8 bites csatornánkénti EGYSZERŰ átlaga (nem fényesség-lineáris), a
    legközelebbi egészre kerekítve.

    A képről lelógó ablak a képre vágódik (a sarokban kevesebb képpont
    átlagolódik). `None`, ha a pont a képen kívülre esik."""
    magassag, szelesseg = kep.shape[:2]
    x = int(round(nx * (szelesseg - 1)))
    y = int(round(ny * (magassag - 1)))
    if not (0 <= x < szelesseg and 0 <= y < magassag):
        return None
    fel = oldal // 2
    resz = kep[max(0, y - fel) : y + fel + 1, max(0, x - fel) : x + fel + 1, :3]
    darab = resz.shape[0] * resz.shape[1]
    osszeg = resz.reshape(-1, 3).sum(axis=0, dtype=np.int64)
    atlag = (2 * osszeg + darab) // (2 * darab)
    return int(atlag[0]), int(atlag[1]), int(atlag[2])


class EditPreviewSampleMixin:
    """A pipetta mintája: a réteg előtti lánc képe, tárolva (#7385)."""

    def sample_prefix_color(
        self,
        photo_id: str,
        path: Path,
        ops: tuple[FilterOp, ...],
        nx: float,
        ny: float,
        *,
        paint_strokes: tuple = (),
        crop: str | None = None,
        crop_ini_readable: bool | None = None,
    ) -> tuple[int, int, int] | None:
        """Az `ops` láncból renderelt kép színe a (nx, ny) normált ponton.

        A Hangolás pipettája (`pickNeutralColor`) ezt kérdezi az eredetiben
        mért módon (J5a, E23): a p4 a KÉP FORRÁSÁNAK színe, nem a már
        szerkesztett előnézeté, és a kattintott pont körüli területé (5x5
        forrás-képpont, ld. `MINTA_FORRAS_KEPPONT`). A hívó a lánc `finetune2`
        réteg ELŐTTI részét adja (`ops`), így a réteg saját hatása
        (Színhőmérséklet, korábbi semleges szín) nem szűrődik vissza a mintába,
        a korábbi effektek viszont igen.

        A lánc előkészítése és futtatása ugyanaz, mint a `register()`-é (dekód,
        `crop=` normalizálás, előnézeti arány, ecset-maszk), így a normált pont
        ugyanarra a képpontra esik, mint a megjelenített képen: a vágás
        kezelése változatlan. A szövegréteg nem tartozik a láncba, kimarad.

        A kép aláírás szerint tárolt: ha az aláírás egyezik (a háttér-render
        vagy egy korábbi kattintás készítette), a hívás nem renderel. Hiányzó
        bejegyzésnél a render a hívás szálán fut (GUI-szál), legfeljebb egy
        előnézeti képkocka idejéig, és a bejegyzés a következő kattintásokra
        megmarad. `None`, ha a kép nem dekódolható vagy a pont a képen
        kívülre esik."""
        key = str(photo_id)
        path = Path(path)
        if crop_ini_readable is None:
            crop, crop_ini_readable = self._crop_reader.read(
                path.parent / PICASA_INI_NAME, path.name
            )
        ops = normalize_crop_ops(
            tuple(ops),
            crop,
            crop_ini_readable=crop_ini_readable,
            warning_key=str(path),
        )
        try:
            fajl_adat = path.stat()
        except OSError:
            mtime = None
            meret = None
        else:
            mtime, meret = fajl_adat.st_mtime, fajl_adat.st_size
        signature = self._sample_signature(path, meret, ops, paint_strokes)
        entry = self._recall_sample_prefix(key, signature)
        if entry is None:
            # a dekódolt forrás gyorsítótárazott (a következő kép-művelet is
            # használja), a lánc-prefix gyorsítótár nem: a kész képet a saját
            # bejegyzésünk tartja, a prefix másolata csak memória lenne
            render = self._render_at_preview_scale(
                key, path, mtime, ops, True, False, paint_strokes
            )
            if render.image is None or render.image.size == 0:
                return None
            entry = (signature, render.image, render.scale)
            if not gyors_elonezet_aktiv():
                with self._lock:
                    self._store_sample_prefix(key, *entry)
        _alairas, kep, arany = entry
        return teruletatlag(kep, nx, ny, mintaablak_oldala(arany))

    def _sample_signature(
        self,
        path: Path,
        meret: int | None,
        ops: tuple[FilterOp, ...],
        paint_strokes: tuple,
    ) -> tuple:
        """Mindaz, ami a réteg előtti lánc képét meghatározza: a fájl és a
        mérete, a színkezelés (a dekódra hat), a (crop-pal normalizált) lánc és
        a festés. A `_lock` alatt NEM hívható (a `color_management` maga is
        zárol).

        Az időbélyeg SZÁNDÉKOSAN nincs benne: az alkalmazás maga léptet a kép
        mtime-ján minden `.picasa.ini`-mentéskor (`photo_touch`, #2491), tehát
        minden pipetta-mentés érvénytelenítené a bejegyzést, és a látogatás
        további kattintásai újra renderelnének. A méret a tartalom cseréjét
        jelzi (a lecserélt fájl szinte mindig más méretű), az érintés viszont
        nem változtatja. A bejegyzés a szerkesztés végén (`unregister`) úgyis
        felszabadul."""
        return (path, meret, self.color_management, tuple(ops), tuple(paint_strokes))

    def _recall_sample_prefix(self, key: str, signature: tuple) -> tuple | None:
        """A fotó bejegyzése, ha az aláírása egyezik; különben `None`."""
        with self._lock:
            entry = self._sample_prefixes.get(key)
            if entry is None or entry[0] != signature:
                return None
            self._sample_prefixes.move_to_end(key)
            return entry

    def _store_sample_prefix(
        self, key: str, signature: tuple, image: np.ndarray, scale: float
    ) -> None:
        """A fotó bejegyzése (LRU, mint a képtár). A `_lock` alatt hívandó."""
        self._sample_prefixes[key] = (signature, image, scale)
        self._sample_prefixes.move_to_end(key)
        while len(self._sample_prefixes) > _LRU_CAPACITY:
            self._sample_prefixes.popitem(last=False)
