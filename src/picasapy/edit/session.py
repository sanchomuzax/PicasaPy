"""EditSession — immutábilis szerkesztési-lánc (filters=) állapotkezelő."""

from __future__ import annotations

from dataclasses import dataclass

from picasapy.ini.filters import FilterOp, parse_filters, serialize_filters
from picasapy.ini.rect64 import Rect64, decode_rect64, encode_rect64


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
