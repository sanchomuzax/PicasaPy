"""A szerkesztési előnézet dekód- és renderlánc-gyorsítótára."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from picasapy.ini.filters import FilterOp
from picasapy.render import apply_filters
from picasapy.render.chain_geometry import TartalomHely
from picasapy.render.elonezeti_arany import gyors_elonezet_aktiv
from picasapy.render.op_geometry import LancHelyzet

from . import edit_preview_source

# LRU-kapacitás (#128): az aktuális és az előző fotó marad a gyorsítótárban.
_LRU_CAPACITY = 2


class EditPreviewCacheMixin:
    """A forrás-, renderlánc- és GPU-prefix gyorsítótár műveletei."""

    def _futtasd_a_lancot(
        self,
        key: str,
        source_array: np.ndarray | None,
        ops: tuple[FilterOp, ...],
        shared_cache: bool,
        paint_strokes: tuple,
    ) -> tuple[np.ndarray | None, TartalomHely | None]:
        """A lánc a `_register_impl` három ágán (#3377-ben kiemelve)."""
        # lánc-prefix gyorsítótár (#140): interakció közben csak az utolsó
        # op fut. A háttér-úton (#546) nincs gyorsítótár - cserébe nincs
        # megosztott állapot sem, amit sorosítani kellene.
        #: #3166: a keret-elhelyezés a render JELENTÉSÉBŐL jön - abból a
        #: hívásból, amelyik a kereteket tényleg alkalmazta (mind a három
        #: ágon: festett maszk, gyorsítótár, közvetlen).
        elhelyezes = None
        from .paint_mask import maszk_vonasokbol, van_mentett_ecsetvonas

        if (paint_strokes or van_mentett_ecsetvonas(ops)) and source_array is not None and ops:
            # #1908: festett ecset-maszk esetén a lánc-prefix gyorsítótár
            # KIMARAD. A maszk nem csak az utolsó opra hat (a festhető effekt
            # bárhol állhat a láncban), a prefix viszont épp azt tartja
            # változatlannak - a gyorsítótár tehát elavult képet adna. A
            # festés nem csúszka-húzás: egy vonás után egy teljes lánc
            # elfut, és ez a helyes, nem a gyors.
            maszk = maszk_vonasokbol(
                paint_strokes,
                source_array.shape[0],
                source_array.shape[1],
                filters=ops,
            )
            jelentes = apply_filters(source_array, tuple(ops), paint_mask=maszk)
            result_array = jelentes.image
            elhelyezes = jelentes.content_placement
        elif shared_cache:
            result_array, elhelyezes, _helyzet = self._render_cached_jelentes(
                key, source_array, tuple(ops)
            )
        elif source_array is None or not ops:
            result_array = source_array
        else:
            jelentes = apply_filters(source_array, tuple(ops))
            result_array = jelentes.image
            elhelyezes = jelentes.content_placement
        return result_array, elhelyezes

    def _resolve_source(
        self,
        key: str,
        path: Path,
        mtime: float | None,
        shared_cache: bool,
        full_res: bool = False,
    ) -> np.ndarray | None:
        """A dekódolt forráskép - a GUI-úton gyorsítótárazva, háttéren nem.

        #546: a `_sources` LRU-t KIZÁRÓLAG a GUI-szál írja. A háttér-render
        inkább újra dekódol (ez a lassú effektek mellett elhanyagolható),
        cserébe a két szál között nincs megosztott, zárral védendő állapot.
        """
        if not shared_cache:
            return edit_preview_source._decode_source(
                path, full_res=full_res, color_managed=self.color_management
            )
        cached = self._sources.get(key)
        #: #819: a kicsinyített és a teljes felbontású forrás NEM cserélhető
        #: fel - a negyedik mező mondja meg, melyik van a gyorsítótárban.
        if (
            cached is not None
            and cached[0] == path
            and cached[1] == mtime
            and (len(cached) < 4 or cached[3] == full_res)
        ):
            source_array = cached[2]
        else:
            source_array = edit_preview_source._decode_source(
                path, full_res=full_res, color_managed=self.color_management
            )
        # LRU-frissítés (#128): az aktuális kulcs a sor végére kerül, és a
        # kapacitáson túli legrégebbi bejegyzések felszabadulnak - az
        # előző kép még bent marad (gyors visszalapozás), a régebbiek nem.
        # A forrás-referencia (source_array) azonossága megmarad, így a
        # lánc-prefix gyorsítótár (#140) találata a re-store után is érvényes.
        self._sources[key] = (path, mtime, source_array, full_res)
        self._sources.move_to_end(key)
        while len(self._sources) > _LRU_CAPACITY:
            self._sources.popitem(last=False)
        return source_array

    def _render_cached_jelentes(
        self,
        key: str,
        source_array: np.ndarray | None,
        ops: tuple[FilterOp, ...],
    ) -> tuple[np.ndarray | None, TartalomHely | None, LancHelyzet | None]:
        """Renderelés lánc-prefix gyorsítótárral: interakció közben (azonos
        prefix, csak az utolsó op paramétere változik) csak az utolsó op fut.

        A visszaadott RGB-tömb a hisztogram (#25) és a QImage-konverzió közös
        forrása - így a hisztogram mindig a TÉNYLEGESEN megjelenített képet
        tükrözi, nem egy külön újraszámolt változatot.

        #301: hibás/idegen lánc-bejegyzésnél az apply_filters saját maga esik
        vissza a szűretlen köztes eredményre (kivétel nem szökik ki innen),
        a #73-elv (részleges előnézet a placeholder helyett) így is teljesül."""
        if source_array is None:
            return None, None, None
        if not ops:
            height, width = source_array.shape[:2]
            return source_array, None, LancHelyzet.kezdo(width, height)
        if any(op.name.casefold() in {"grain", "grain2"} for op in ops):
            # A szemcsemag sorszáma a teljes renderláncban értendő. A
            # prefix-cache kettévágása a záró grainnek újra 0-t adna, ezért
            # szemcsét tartalmazó láncnál egyben renderelünk.
            jelentes = apply_filters(source_array, ops)
            return jelentes.image, jelentes.content_placement, jelentes.helyzet
        # #3229: a lánc MÁR NEM rendez át - az `apply_filters` az ops
        # sorrendjében fut, és a `crop64` koordinátáit a leképezés vezeti át.
        # Ezért a prefix egyszerűen a lánc eleje, és a kettévágott futtatás
        # ugyanazt adja, mint az egészben futtatott. (A #3169 itt 18,2
        # átlagos eltérést mért a régi, halasztó ágon: a prefixbe került keret
        # után az utolsó op ARRA futott rá. A halasztás megszűnésével ez a
        # csapda is megszűnt - őr: `test_lanc_sorrend_elesben_3229.py`.)
        prefix_array, prefix_helyzet, prefix_alpha = self._cached_prefix(
            key, source_array, ops[:-1]
        )
        # #3166 + #3229: a keret-elhelyezés a FORRÁS helyét mondja meg a
        # kimenetben, tehát a TELJES láncra értendő - a záró hívás ezért
        # megkapja a prefix koordináta-állapotát (`bejovo`), különben a
        # prefixben lefutott vágás/keret elveszne belőle.
        jelentes = apply_filters(
            prefix_array,
            ops[-1:],
            bejovo=prefix_helyzet,
            input_alpha=prefix_alpha,
        )
        return jelentes.image, jelentes.content_placement, jelentes.helyzet

    def _render_cached(
        self,
        key: str,
        source_array: np.ndarray | None,
        ops: tuple[FilterOp, ...],
    ) -> np.ndarray | None:
        """Csak a kép - azoknak a hívóknak, akiknek a keret-elhelyezés
        (#3166) nem kell (pl. a vörösszem-számolás)."""
        return self._render_cached_jelentes(key, source_array, ops)[0]

    def _cached_prefix(
        self,
        key: str,
        source_array: np.ndarray,
        prefix_ops: tuple[FilterOp, ...],
    ) -> tuple[np.ndarray, LancHelyzet, int]:
        """Az utolsó op ELŐTTI köztes eredmény, gyorsítótárból ha lehet.

        A találat feltétele: azonos fotó-kulcs, azonos prefix-lánc és
        ugyanaz a (referencia szerint azonos) dekódolt forrás - a
        forrás-cache frissülésekor a prefix automatikusan érvénytelen.

        A köztes KÉP mellett a lánc koordináta-állapotát is visszaadja
        (#3229): a folytatásnak tudnia kell, hogy a kapott kép már nem az
        eredeti - a `crop64` koordinátái arra vonatkoznak (#330), és a
        keret-elhelyezés is a forrás helyét mondja meg a kimenetben. Az
        alfaállapot (#5299) a Polaroid folytatásához kell."""
        cached = self._prefix_cache
        gyors = gyors_elonezet_aktiv()
        if (
            cached is not None
            and cached[0] == key
            and cached[1] == prefix_ops
            and cached[2] is source_array
            and cached[5] == gyors
        ):
            return cached[3], cached[4], cached[6]
        if prefix_ops:
            jelentes = apply_filters(source_array, prefix_ops)
            prefix_array = jelentes.image
            helyzet = jelentes.helyzet
            alpha = jelentes.alpha
        else:
            prefix_array = source_array
            magassag, szelesseg = source_array.shape[:2]
            helyzet = LancHelyzet.kezdo(szelesseg, magassag)
            alpha = 255
        self._prefix_cache = (key, prefix_ops, source_array, prefix_array, helyzet, gyors, alpha)
        return prefix_array, helyzet, alpha

    def _cached_gpu_prefix(
        self,
        key: str,
        source_array: np.ndarray,
        prefix_ops: tuple[FilterOp, ...],
    ) -> np.ndarray:
        """A GPU-előnézet (#22) prefix-je, KÜLÖN gyorsítótár-rekeszben.

        Ugyanaz a találat-logika, mint `_cached_prefix`-nél, de saját
        `_gpu_prefix_cache` rekesszel - ld. a rekesz mellé írt docsztringet
        a cache-csörgés elkerüléséről. A gyakori esetben (finetune2 a lánc
        VÉGén, `prefix_ops == ops[:-1]`) ez a hívás olcsó: a tömb-tartalom
        MEGEGYEZIK a `_cached_prefix`-ben az imént kiszámolttal, csak a
        referencia más - az `apply_filters` itt is lefut, de a KÖVETKEZŐ,
        AZONOS prefixű hívásnál már ez a rekesz is talál."""
        cached = self._gpu_prefix_cache
        gyors = gyors_elonezet_aktiv()
        if (
            cached is not None
            and cached[0] == key
            and cached[1] == prefix_ops
            and cached[2] is source_array
            and cached[4] == gyors
        ):
            return cached[3]
        if prefix_ops:
            prefix_array, _skipped = apply_filters(source_array, prefix_ops)
        else:
            prefix_array = source_array
        self._gpu_prefix_cache = (key, prefix_ops, source_array, prefix_array, gyors)
        return prefix_array
