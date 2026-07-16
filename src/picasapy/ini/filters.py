"""A `filters=` szerkesztési lánc parse/serialize.

Formátum: `<név>=1[,<param>...];` bejegyzések pontosvesszővel, sorrend =
alkalmazási sorrend. A név kis-nagybetű-tűrően illesztendő (pl. `Vignette`),
de round-triphez az eredeti alak megőrzendő. A paraméterek tetszőleges
előjeles floatok lehetnek — nyers stringként tároljuk őket, hogy a
serialize bitre pontos legyen.

Figyelem: a parse→serialize normalizál (üres bejegyzéseket elhagy, záró `;`-t
pótol), ezért a byte-pontos round-trip garanciát a document-réteg nyers
értéktárolása adja — íráskor a nem módosított filters= értékhez nem szabad
ezen a modulon keresztülmenni.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FilterOp:
    """Egyetlen szűrő a láncban; params[0] az engedélyező flag (`1`)."""

    name: str
    params: tuple[str, ...]

    def matches(self, name: str) -> bool:
        return self.name.casefold() == name.casefold()

    def float_params(self) -> tuple[float, ...]:
        """A flag utáni paraméterek számként."""
        return tuple(float(param) for param in self.params[1:])


def parse_filters(value: str) -> tuple[FilterOp, ...]:
    ops = []
    for entry in value.split(";"):
        if not entry:
            continue
        name, sep, rest = entry.partition("=")
        if not sep or not name:
            raise ValueError(f"Érvénytelen filter-bejegyzés: {entry!r}")
        params = tuple(rest.split(",")) if rest else ()
        ops.append(FilterOp(name, params))
    return tuple(ops)


def serialize_filters(ops: tuple[FilterOp, ...]) -> str:
    return "".join(f"{op.name}={','.join(op.params)};" for op in ops)
