"""Az EditSession effektműveleteinek változatlan forrású mixinje."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from picasapy.ini.filters import FilterOp

from .session_core import (
    FinetuneValues,
    _FINETUNE_CANONICAL,
    _FINETUNE_NAMES,
    _NEUTRAL_DEFAULT,
    _new_op,
)

if TYPE_CHECKING:
    from .session import EditSession

class _SessionEffectsMixin:
    def set_tilt(self, param: float, scale: float) -> EditSession:
        """Tilt beállítása vagy cseréje (a láncban legfeljebb egy lehet).

        Args:
            param: A szög paraméter (6 tizedesre formázva).
            scale: A skála paraméter (6 tizedesre formázva).

        Returns:
            Új EditSession.
        """
        new_op = _new_op("tilt", ("1", f"{param:.6f}", f"{scale:.6f}"))
        return self._with_single_layer(lambda op: op.matches("tilt"), new_op)

    def clear_tilt(self) -> EditSession:
        """Tilt eltávolítása."""
        new_ops = [op for op in self.ops if not op.matches("tilt")]
        return EditSession(ops=tuple(new_ops))

    def tilt_param(self) -> float | None:
        """A tilt szög paramétere.

        Hibás/nem numerikus paraméternél is `None`-t ad (nem dob), a `crop()`
        mintájára (#301).

        Returns:
            A float param, vagy None ha nincs (érvényes) tilt.
        """
        for op in self.ops:
            if op.matches("tilt"):
                if len(op.params) >= 2:
                    try:
                        return float(op.params[1])
                    except ValueError:
                        return None
        return None

    def set_finetune(
        self,
        *,
        fill: float,
        highlights: float,
        shadows: float,
        temperature: float,
        neutral: str | None = None,
    ) -> EditSession:
        """A finomhangolás (finetune2) réteg beállítása vagy cseréje (#20).

        A tilt/crop mintájára a láncban EGY finetune2 lehet: ha már van
        (finetune vagy finetune2), a helyén cserélődik, különben a végére
        fűződik. A négy csúszka p1..p3,p5, a pipetta-szín p4 — utóbbit, ha
        a hívó nem ad meg (`neutral=None`), a meglévő értékből őrizzük meg
        (round-trip elv), különben `00000000`.

        Args:
            fill: Derítőfény (0..1).
            highlights: Csúcsfények (0..1).
            shadows: Árnyékok (0..1).
            temperature: Színhőmérséklet (-1..1).
            neutral: A pipetta AARRGGBB hex-e; None = a meglévőt megőrzi.

        Returns:
            Új EditSession.
        """
        if neutral is None:
            existing = self.finetune_values()
            neutral = existing.neutral if existing is not None else _NEUTRAL_DEFAULT
        new_op = _new_op(
            _FINETUNE_CANONICAL,
            (
                "1",
                f"{fill:.6f}",
                f"{highlights:.6f}",
                f"{shadows:.6f}",
                neutral,
                f"{temperature:.6f}",
            ),
        )
        return self._with_single_layer(
            lambda op: op.name.casefold() in _FINETUNE_NAMES, new_op
        )

    def clear_finetune(self) -> EditSession:
        """A finomhangolás (finetune/finetune2) réteg eltávolítása."""
        new_ops = [
            op for op in self.ops if op.name.casefold() not in _FINETUNE_NAMES
        ]
        return EditSession(ops=tuple(new_ops))

    def finetune_values(self) -> FinetuneValues | None:
        """A mentett finetune2 csúszka-értékei, vagy None ha nincs finetune.

        A hiányzó paramétereket semlegesnek (0) vesszük; a p4 (pipetta)
        érvénytelen/hiányzó esetén az alapértékre esik vissza. A csúszkák
        ezzel állnak be az eszköz megnyitásakor a MENTETT értékre (#20).
        """
        for op in self.ops:
            if op.name.casefold() in _FINETUNE_NAMES:
                return FinetuneValues(
                    fill=_finetune_float(op, 1),
                    highlights=_finetune_float(op, 2),
                    shadows=_finetune_float(op, 3),
                    temperature=_finetune_float(op, 5),
                    neutral=(
                        op.params[4]
                        if len(op.params) > 4 and op.params[4]
                        else _NEUTRAL_DEFAULT
                    ),
                )
        return None

    def has_finetune(self) -> bool:
        """Van-e finomhangolás (finetune/finetune2) réteg a láncban."""
        return any(op.name.casefold() in _FINETUNE_NAMES for op in self.ops)

    def gpu_finetune_prefix(self) -> tuple[FilterOp, ...] | None:
        """A finetune2 réteg ELŐTTI lánc-előtag — a GPU élő-előnézet (#22)
        feltétele.

        A `GpuPointFilterPreview.qml` a finomhangolás-csúszkák húzása alatt
        a LUT-ot GPU-n alkalmazza egy előre kirenderelt köztes képen
        (`sourceItem`); ez csak akkor ad HELYES eredményt, ha a finetune2
        UTÁN a láncban nincs semmi — különben az utána következő effektek
        (pl. `grain2`, `vignette`) hiányoznának az élő-előnézetből. Ezért:

        - ha van finetune2/finetune réteg és az a lánc UTOLSÓ eleme: az
          ELŐTTE álló ops-ot adjuk vissza (ez az, amit a GPU `sourceItem`-je
          megjelenít, a shader csak a LUT-ot teszi rá);
        - ha nincs finetune2/finetune réteg egyáltalán: a TELJES láncot
          adjuk vissza (a `set_finetune` ilyenkor a végére fűzné az új
          réteget, tehát ez felel meg ugyanannak a helyzetnek);
        - egyébként (finetune2 a lánc közepén) `None` — a hívó ilyenkor a
          normál CPU-előnézetre esik vissza, GPU-gyorsítás nélkül.

        **#551: nem nulla Derítőfénynél is `None`.** A mérés kimondta, hogy
        a Derítőfény a pixel VILÁGOSSÁGÁTÓL függő hozzáadás, nem
        csatornánkénti tónusgörbe — a GPU pontonkénti (LUT-textúrás) útja
        ilyenkor a CPU-tól eltérő képet adna, ezért nem alkalmazható.
        """
        for index, op in enumerate(self.ops):
            if op.name.casefold() in _FINETUNE_NAMES:
                if index == len(self.ops) - 1 and _finetune_float(op, 1) == 0.0:
                    return self.ops[:index]
                return None
        return self.ops

    def append_effect(self, name: str, params: tuple[str, ...] = ("1",)) -> EditSession:
        """Effekt réteg a lánc VÉGÉRE fűzése (append-only, #20).

        Picasa-minta (a #116 egygombos javításaival azonos elv): az effekt-
        gomb mindig új réteget tesz a láncra — a levétel kizárólag a
        Visszavonással történik. Az ismeretlen render-op nélküli effektek is
        a láncba kerülnek (round-trip elv), az előnézeten csak kimaradnak.

        Args:
            name: Az effekt szűrő-neve (pl. "sepia", "grain2").
            params: A szűrő paraméterei; alapból az engedélyező flag ("1",).

        Returns:
            Új EditSession.

        Raises:
            ValueError: Ha a név üres.
        """
        if not name:
            raise ValueError("Az effekt neve nem lehet üres")
        return EditSession(ops=self.ops + (_new_op(name, params),))

    def apply(self, name: str) -> EditSession:
        """Egygombos javítás rétegként a lánc VÉGÉRE fűzése (append-only, #116).

        Picasa-minta: a gomb sosem távolít el — mindig új réteget tesz a
        láncra, akkor is, ha a szűrő korábban már szerepel benne (A→B→A
        rétegezés). A levétel kizárólag a Visszavonással történik.

        Érvényes nevek: "enhance", "autolight", "autocolor".

        Args:
            name: A szűrő neve.

        Returns:
            Új EditSession.

        Raises:
            ValueError: Ha a név nem érvényes egygombos javítás.
        """
        valid_one_shots = {"enhance", "autolight", "autocolor"}
        if name.casefold() not in valid_one_shots:
            raise ValueError(
                f"Érvénytelen egygombos javítás: {name!r}. "
                f"Érvényes: {valid_one_shots}"
            )
        return EditSession(ops=self.ops + (_new_op(name, ("1",)),))

    def last_is(self, name: str) -> bool:
        """Az utolsó lánc-elem a megadott szűrő-e (case-insensitive, #116)."""
        return bool(self.ops) and self.ops[-1].matches(name)

    def toggle(self, name: str) -> EditSession:
        """Toggle paraméter nélküli kapcsoló-szűrő.

        Érvényes név jelenleg csak a "redeye": teljes képes kapcsolóként
        működik a régió-alapú vörösszem-eszköz elkészültéig (#116). Ha a
        láncban van (case-insensitive), MINDEN előfordulását eltávolítja
        (nem csak az elsőt — a set_*-ek egy-példányos cseréjétől eltérően);
        különben a végére fűz. Az egygombos javításokra (enhance/autolight/
        autocolor) az append-only `apply()` való.

        Args:
            name: A szűrő neve.

        Returns:
            Új EditSession.

        Raises:
            ValueError: Ha a név nem érvényes.
        """
        valid_toggles = {"redeye"}
        if name.casefold() not in valid_toggles:
            raise ValueError(
                f"Érvénytelen toggle szűrő: {name!r}. "
                f"Érvényes: {valid_toggles}"
            )
        if self.has(name):
            new_ops = tuple(op for op in self.ops if not op.matches(name))
        else:
            new_ops = self.ops + (_new_op(name, ("1",)),)
        return EditSession(ops=new_ops)

    def has(self, name: str) -> bool:
        """Van-e a szűrő a láncban (case-insensitive)."""
        return any(op.matches(name) for op in self.ops)

    def is_empty(self) -> bool:
        """Üres-e a lánc."""
        return not self.ops

    def _with_single_layer(
        self, matches: Callable[[FilterOp], bool], new_op: FilterOp
    ) -> EditSession:
        """Egy-példányos réteg beállítása: a `matches`-re illő ELSŐ tag
        helyén cserélődik, a további egyezők eldobódnak; ha nincs egyező
        tag, `new_op` a lánc végére kerül.

        Közös implementáció a tilt/finetune/retouch „legfeljebb egy réteg,
        a helyén cserélve" szabályához (#302) — a `toggle()` ettől eltérően
        MINDEN egyezőt eltávolít, ezért nem ezt a helpert használja. A
        `crop64` 2026-08-27 óta NEM tartozik ide: az eredeti Picasa halmozza
        a vágásokat, ld. `append_crop` (#1553)."""
        new_ops = []
        replaced = False
        for op in self.ops:
            if matches(op):
                if not replaced:
                    new_ops.append(new_op)
                    replaced = True
            else:
                new_ops.append(op)
        if not replaced:
            new_ops.append(new_op)
        return EditSession(ops=tuple(new_ops))

def _finetune_float(op: FilterOp, index: int) -> float:
    """A finetune-op adott indexű paramétere számként; hiányzáskor 0.0.

    A hiányzó/üres paraméter semleges (0) — a részleges vagy idegen láncok is
    biztonságosan olvashatók (round-trip elv)."""
    if len(op.params) <= index or not op.params[index]:
        return 0.0
    try:
        return float(op.params[index])
    except ValueError:
        return 0.0
