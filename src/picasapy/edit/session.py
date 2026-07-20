"""EditSession — immutábilis szerkesztési-lánc (filters=) állapotkezelő."""

from __future__ import annotations

from dataclasses import dataclass

from picasapy.ini.filters import FilterOp, parse_filters, serialize_filters
from picasapy.ini.rect64 import Rect64, decode_rect64, encode_rect64

# A finomhangolás (#20) egyetlen finetune2 réteg, a tilt/crop mintájára a
# láncban a helyén cserélődik (nem rétegződik). A v1 "finetune"-t is ez
# kezeli (mindkét nevet ugyanaz a réteg jelenti).
_FINETUNE_NAMES = ("finetune2", "finetune")
_FINETUNE_CANONICAL = "finetune2"
# p4 (semleges-szín pipetta) alapértéke: nulla alfa = nincs kijelölt szín.
_NEUTRAL_DEFAULT = "00000000"


@dataclass(frozen=True)
class FinetuneValues:
    """A finetune2 négy csúszkája + a pipetta-szín (round-triphez megőrzött).

    fill/highlights/shadows ∈ [0..1], temperature ∈ [-1..1]; neutral az
    AARRGGBB hex (p4), változatlanul visszaírva."""

    fill: float
    highlights: float
    shadows: float
    temperature: float
    neutral: str = _NEUTRAL_DEFAULT


@dataclass(frozen=True)
class EditSession:
    """Immutábilis szerkesztési-lánc; a filters= érték objektum-reprezentációja.

    Minden metódus új EditSession-t ad vissza — mutáció tilos.
    """

    ops: tuple[FilterOp, ...] = ()

    @classmethod
    def from_value(cls, value: str | None) -> EditSession:
        """Parse a `filters=` érték stringből.

        Args:
            value: A filters= érték; None vagy üres string üres láncot ad.

        Returns:
            Új EditSession.
        """
        if not value:
            return cls()
        ops = parse_filters(value)
        return cls(ops=ops)

    def to_value(self) -> str:
        """Stringgé konvertál (serialize).

        Returns:
            A filters= érték stringje.
        """
        return serialize_filters(self.ops)

    def set_crop(self, rect: Rect64) -> EditSession:
        """Crop64 beállítása vagy cseréje.

        Ha a láncban már van crop64, azt lecseréli a helyén. Különben a végére fűzi.

        Args:
            rect: Az új Rect64 téglalap.

        Returns:
            Új EditSession.
        """
        encoded = encode_rect64(rect)
        new_op = FilterOp("crop64", ("1", encoded))

        # Keressük az első crop64-et (case-insensitive)
        new_ops = []
        replaced = False
        for op in self.ops:
            if op.matches("crop64"):
                if not replaced:
                    new_ops.append(new_op)
                    replaced = True
                # Többit eltávolítjuk (csak egy crop64 lehet)
            else:
                new_ops.append(op)

        # Ha nem volt crop64, a végére fűzzük
        if not replaced:
            new_ops.append(new_op)

        return EditSession(ops=tuple(new_ops))

    def clear_crop(self) -> EditSession:
        """Crop64 eltávolítása.

        Returns:
            Új EditSession, crop64 nélkül.
        """
        new_ops = [op for op in self.ops if not op.matches("crop64")]
        return EditSession(ops=tuple(new_ops))

    def crop(self) -> Rect64 | None:
        """Az aktuális crop64 téglalap.

        Returns:
            Rect64 a dekódolt értékkel, vagy None ha nincs crop64.
        """
        for op in self.ops:
            if op.matches("crop64"):
                if len(op.params) >= 2:
                    return decode_rect64(op.params[1])
        return None

    def set_tilt(self, param: float, scale: float) -> EditSession:
        """Tilt beállítása vagy cseréje.

        Az szög és skála paraméterek 6 tizedes helyre formázódnak.

        Args:
            param: A szög paraméter.
            scale: A skála paraméter.

        Returns:
            Új EditSession.
        """
        # Formázás: 6 tizedes
        formatted_param = f"{param:.6f}"
        formatted_scale = f"{scale:.6f}"
        new_op = FilterOp("tilt", ("1", formatted_param, formatted_scale))

        # Keressük az első tilt-et
        new_ops = []
        replaced = False
        for op in self.ops:
            if op.matches("tilt"):
                if not replaced:
                    new_ops.append(new_op)
                    replaced = True
                # Többit eltávolítjuk
            else:
                new_ops.append(op)

        # Ha nem volt tilt, a végére fűzzük
        if not replaced:
            new_ops.append(new_op)

        return EditSession(ops=tuple(new_ops))

    def clear_tilt(self) -> EditSession:
        """Tilt eltávolítása.

        Returns:
            Új EditSession, tilt nélkül.
        """
        new_ops = [op for op in self.ops if not op.matches("tilt")]
        return EditSession(ops=tuple(new_ops))

    def tilt_param(self) -> float | None:
        """A tilt szög paramétere.

        Returns:
            A float param, vagy None ha nincs tilt.
        """
        for op in self.ops:
            if op.matches("tilt"):
                if len(op.params) >= 2:
                    return float(op.params[1])
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
        new_op = FilterOp(
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
        new_ops = []
        replaced = False
        for op in self.ops:
            if op.name.casefold() in _FINETUNE_NAMES:
                if not replaced:
                    new_ops.append(new_op)
                    replaced = True
                # a további finetune-rétegeket eltávolítjuk (csak egy lehet)
            else:
                new_ops.append(op)
        if not replaced:
            new_ops.append(new_op)
        return EditSession(ops=tuple(new_ops))

    def clear_finetune(self) -> EditSession:
        """A finomhangolás (finetune/finetune2) réteg eltávolítása.

        Returns:
            Új EditSession, finetune nélkül.
        """
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
        return EditSession(ops=self.ops + (FilterOp(name, params),))

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
        return EditSession(ops=self.ops + (FilterOp(name, ("1",)),))

    def last_is(self, name: str) -> bool:
        """Az utolsó lánc-elem a megadott szűrő-e (case-insensitive, #116).

        A gomb-tiltási szabály alapja: az egygombos javítás gombja tiltott,
        ha ugyanez a szűrő a lánc utolsó eleme (kétszer egymás után nincs
        értelme).

        Args:
            name: A szűrő neve.

        Returns:
            True ha a lánc nem üres és az utolsó eleme a szűrő.
        """
        return bool(self.ops) and self.ops[-1].matches(name)

    def toggle(self, name: str) -> EditSession:
        """Toggle paraméter nélküli kapcsoló-szűrő.

        Érvényes név jelenleg csak a "redeye": teljes képes kapcsolóként
        működik a régió-alapú vörösszem-eszköz elkészültéig (#116). Ha a
        láncban van (case-insensitive), MINDEN előfordulását eltávolítja;
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

        # Keressük, van-e már
        new_ops = []
        found = False
        for op in self.ops:
            if op.matches(name):
                found = True
                # Eltávolítunk
            else:
                new_ops.append(op)

        # Ha nem volt, a végére fűzzük
        if not found:
            new_ops.append(FilterOp(name, ("1",)))

        return EditSession(ops=tuple(new_ops))

    def has(self, name: str) -> bool:
        """Van-e a szűrő a láncban (case-insensitive).

        Args:
            name: A szűrő neve.

        Returns:
            True ha van.
        """
        for op in self.ops:
            if op.matches(name):
                return True
        return False

    def is_empty(self) -> bool:
        """Üres-e a lánc.

        Returns:
            True ha nincs szűrő.
        """
        return not self.ops


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
