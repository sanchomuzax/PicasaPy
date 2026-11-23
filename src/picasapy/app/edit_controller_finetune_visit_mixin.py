"""A Hangolás-látogatás: egy új `finetune2` réteg, egyetlen visszavonási lépés (#7383).

Az eredeti Picasában (J3d, J4a, J6c) a Hangolás fül csúszkái mindig
alaphelyzetben indulnak, a kép viszont a láncot mutatja. A látogatás első
húzása új `finetune2` réteget fűz a lánc végére (a betöltött réteg mellé), a
további húzások és a pipetta ugyanazt a réteget módosítják, és az egész
látogatás EGY visszavonási lépés.

A látogatás a saját visszavonási bejegyzésének azonosságán él: addig nyitott,
amíg ez a bejegyzés a verem teteje. Minden más lépés (másik művelet, Undo,
Redo, képváltás, a verem újratöltése) új bejegyzést vagy új vermet hoz, így a
látogatás magától lezárul, külön nyilvántartás nélkül.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from picasapy.edit.session_core import _FINETUNE_NAMES
from picasapy.edit.session_core import _NEUTRAL_DEFAULT as _NEUTRAL_ALAP
from picasapy.ini.filters import FilterOp

from .edit_controller_shared import EditSession, Slot

if TYPE_CHECKING:
    from picasapy.edit.session_core import FinetuneValues


@dataclass(frozen=True)
class FinetuneVisit:
    """Egy nyitott Hangolás-látogatás pillanatképe."""

    entry: tuple[str, str]
    """A látogatás visszavonási bejegyzése (azonosság szerint hasonlítjuk)."""

    base_length: int
    """A látogatás ELŐTTI lánc elemszáma: a látogatás rétege ezen az indexen áll."""


class EditControllerFinetuneVisitMixin:
    """A Hangolás-látogatás állapota és a réteg írása (#7383)."""

    _finetune_visit: FinetuneVisit | None = None

    @Slot()
    def closeFinetuneVisit(self) -> None:  # noqa: N802
        """A Hangolás fül elhagyása (és az újra-belépés): a következő húzás
        ÚJ réteget kezd. A csúszkák alaphelyzetét a panel maga állítja."""
        self._finetune_visit = None

    def _end_finetune_visit(self) -> None:
        """A látogatás vége: a csúszkák alaphelyzetbe állnak (jelből)."""
        self._finetune_visit = None
        self.finetuneSlidersReset.emit()

    def _finetune_visit_open(self) -> bool:
        visit = self._finetune_visit
        return (
            visit is not None
            and bool(self._undo_stack)
            and self._undo_stack[-1] is visit.entry
        )

    def _visit_layer(self, session: EditSession) -> FilterOp | None:
        """A látogatás rétege a `session` láncában, ha már van ilyen."""
        visit = self._finetune_visit
        if not self._finetune_visit_open() or len(session.ops) <= visit.base_length:
            return None
        return session.ops[visit.base_length]

    def _visit_values(self, session: EditSession | None = None) -> FinetuneValues | None:
        """A látogatás rétegének értékei (`FinetuneValues`), vagy None."""
        layer = self._visit_layer(self._session if session is None else session)
        return None if layer is None else EditSession(ops=(layer,)).finetune_values()

    def _finetune_visit_session(
        self,
        session: EditSession,
        *,
        fill: float,
        highlights: float,
        shadows: float,
        temperature: float,
        neutral: str | None = None,
    ) -> EditSession:
        """A `session` lánca a látogatás rétegével: a látogatás ELŐTTI lánc
        + EGY új `finetune2`. A pipetta színét (`neutral=None`) a látogatás
        meglévő rétegéből őrizzük meg, különben `00000000`. Négy nulla érték és
        pipetta-szín nélkül nem kerül réteg a láncba (alaphelyzet)."""
        if neutral is None:
            values = self._visit_values(session)
            neutral = values.neutral if values is not None else _NEUTRAL_ALAP
        visit = self._finetune_visit
        base = session.ops[: visit.base_length] if self._finetune_visit_open() else session.ops
        if (
            fill == 0.0
            and highlights == 0.0
            and shadows == 0.0
            and temperature == 0.0
            and neutral == _NEUTRAL_ALAP
        ):
            # alaphelyzeti jelölt: nincs fantom réteg (a mentés is eldobná), a
            # lánc a látogatás előtti - így a lánc-nézet sem számol rá egy lépést
            return EditSession(ops=base)
        return EditSession(ops=base).append_finetune(
            fill=fill,
            highlights=highlights,
            shadows=shadows,
            temperature=temperature,
            neutral=neutral,
        )

    def _commit_finetune_layer(
        self,
        *,
        fill: float,
        highlights: float,
        shadows: float,
        temperature: float,
        neutral: str | None = None,
    ) -> bool:
        """A látogatás rétegének mentése a láncba; `False`, ha nincs mit.

        A látogatás első mentése visszavonási lépést tol és új réteget fűz a
        lánc végére; a többi ugyanazt a réteget írja felül, lépés nélkül. Ha
        mind a négy érték 0 és nincs pipetta-szín, a réteg nem kell: a lánc a
        látogatás előtti állapotra áll vissza (a látogatás nyitva marad); még
        nyitatlan látogatásnál az üres húzás semmit sem változtat."""
        is_open = self._finetune_visit_open()
        layer_values = self._visit_values()
        effective_neutral = (
            neutral
            if neutral is not None
            else (layer_values.neutral if layer_values is not None else _NEUTRAL_ALAP)
        )
        is_noop = (
            fill == 0.0
            and highlights == 0.0
            and shadows == 0.0
            and temperature == 0.0
            and effective_neutral == _NEUTRAL_ALAP
        )
        if not is_open:
            if is_noop:
                return False
            base_length = len(self._session.ops)
            self._push_undo("finetune")
            self._finetune_visit = FinetuneVisit(
                entry=self._undo_stack[-1], base_length=base_length
            )
        visit = self._finetune_visit
        if is_noop:
            self._session = EditSession(ops=self._session.ops[: visit.base_length])
            return True
        self._session = self._finetune_visit_session(
            self._session,
            fill=fill,
            highlights=highlights,
            shadows=shadows,
            temperature=temperature,
            neutral=effective_neutral,
        )
        return True

    def _commit_neutral_color(self, neutral: str) -> None:
        """A pipetta (és a szín-varázspálca) színe a látogatás rétegébe: a
        négy csúszka értéke megmarad; nyitatlan látogatásnál a pipetta kezdi
        a látogatást, tehát új, csúszka-nélküli réteget fűz a lánc végére."""
        values = self._visit_values()
        self._commit_finetune_layer(
            fill=values.fill if values else 0.0,
            highlights=values.highlights if values else 0.0,
            shadows=values.shadows if values else 0.0,
            temperature=values.temperature if values else 0.0,
            neutral=neutral,
        )
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()

    def _loaded_finetune_present(self) -> bool:
        """Van-e a láncban a látogatás rétegén KÍVÜL finetune-réteg (betöltött
        vagy korábbi látogatásból való)?"""
        visit = self._finetune_visit
        visit_index = visit.base_length if self._finetune_visit_open() else None
        return any(
            op.name.casefold() in _FINETUNE_NAMES and index != visit_index
            for index, op in enumerate(self._session.ops)
        )

    def _gpu_finetune_prefix(self, session: EditSession | None = None):
        """A GPU élő-előnézet (#22) prefixe, vagy None, ha az nem alkalmazható.

        A GPU-út a látogatás rétegét a KÉSZ prefix-képre teszi (LUT-tal). Ha a
        láncban a látogatás rétegén kívül is van finetune-réteg, a prefix nem
        állítható elő a régi, egyetlen-réteges szabállyal (a betöltött réteg
        kimaradna belőle): ilyenkor a rendes CPU-előnézet fut, ugyanazt a
        képet adva. Egyébként a `session` (alapból a mostani lánc) régi
        szabálya érvényes: a finetune2 a lánc végén áll, vagy nincs."""
        if self._loaded_finetune_present():
            return None
        active = self._session if session is None else session
        return active.gpu_finetune_prefix()

