"""A Gyakori javítások Derítőfény-látogatása: új `fill` réteg, egy Undo-lépés (#7397).

Az eredeti Picasában (E27, job-906) az 1. fül Derítőfény-csúszkájának húzása a
betöltött `fill` mellé ÚJ réteget fűz a lánc végére
(`fill=1,0.500000;fill=1,0.523364;`), a két réteg halmozódik. A látogatás a
Hangolás-látogatás (#7383) mintájára él: a saját visszavonási bejegyzésének
azonosságán, tehát addig nyitott, amíg ez a bejegyzés a verem teteje. A fül
elhagyása (`closeFinetuneVisit`), a képváltás, az Undo/Redo és minden másik
lépés lezárja. A látogatás további húzásai az új réteget írják felül; hogy az
eredetiben is így van-e, a B13 felvétel dönti el (nem mért).
"""

from __future__ import annotations

from dataclasses import dataclass

from .edit_controller_shared import EditSession


@dataclass(frozen=True)
class FillVisit:
    """Egy nyitott Derítőfény-látogatás pillanatképe."""

    entry: tuple[str, str]
    """A látogatás visszavonási bejegyzése (azonosság szerint hasonlítjuk)."""

    base_length: int
    """A látogatás ELŐTTI lánc elemszáma: a látogatás rétege ezen az indexen áll."""


class EditControllerFillVisitMixin:
    """A Derítőfény-látogatás állapota és a réteg írása (#7397)."""

    _fill_visit: FillVisit | None = None

    def _close_fill_visit(self) -> None:
        """A látogatás vége: a következő húzás új `fill` réteget fűz."""
        self._fill_visit = None

    def _fill_visit_open(self) -> bool:
        visit = self._fill_visit
        return (
            visit is not None
            and bool(self._undo_stack)
            and self._undo_stack[-1] is visit.entry
        )

    def _fill_visit_session(self, session: EditSession, value: float) -> EditSession:
        """A `session` lánca a Derítőfény-réteggel: a látogatás ELŐTTI lánc +
        EGY új `fill`; a betöltött `fill` rétegek érintetlenek (E27).

        A nulla érték a mai módon az összes `fill` réteget leveszi: a `fill`
        nullára húzásának viselkedése nem mért (#7397 nem része)."""
        if value == 0.0:
            return session.clear_fill()
        visit = self._fill_visit
        base = session.ops[: visit.base_length] if self._fill_visit_open() else session.ops
        return EditSession(ops=base).append_fill(value)

    def _commit_fixes_fill(self, value: float) -> None:
        """A Derítőfény mentése: a látogatás első mentése visszavonási lépést
        tol és új réteget fűz a lánc végére, a többi ugyanazt a réteget írja
        felül, lépés nélkül. A nulla érték mindig új lépés és nem nyit
        látogatást (a mai viselkedés)."""
        if value == 0.0 or not self._fill_visit_open():
            base_length = len(self._session.ops)
            self._push_undo("fill")
            self._fill_visit = (
                None
                if value == 0.0
                else FillVisit(entry=self._undo_stack[-1], base_length=base_length)
            )
        self._session = self._fill_visit_session(self._session, value)
