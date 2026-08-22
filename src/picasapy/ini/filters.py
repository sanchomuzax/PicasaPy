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

Két serialize-út van (#695):

- `serialize_filters` — megengedő és bájtra pontos. A bélyegkép-kulcshoz és
  a belső round-triphez való; idegen/sérült láncra sem dob (#301).
- `serialize_filters_for_write` — az ÍRÓ kapu a `.picasa.ini` felé:
  kanonizálja a regiszterbeli szűrőneveket, és visszautasítja a néma
  elejtésbe futó paraméterszámot (ld. `picasapy.ini.filter_registry` és
  `docs/specs/picasa-ini-format.md`).
"""

from __future__ import annotations

from .filter_registry import canonical_filter_name, is_exact_filter_name

from dataclasses import dataclass

from picasapy.ini.filter_registry import (
    FilterWriteError,
    canonicalize_filter_name,
    max_param_count,
)


@dataclass(frozen=True)
class FilterOp:
    """Egyetlen szűrő a láncban; params[0] az engedélyező flag (`1`)."""

    name: str
    params: tuple[str, ...]

    def matches(self, name: str) -> bool:
        """Bájtra PONTOS név-illesztés (#1141).

        ⚠️ Korábban `casefold()`-dal illesztettünk. Az eredeti Picasa
        viszont kis-nagybetű-ÉRZÉKENY: hat mért képen (`merokit-2`
        export) a `Tint` / `TINT` / `tInT` / `vignette` / `VIGNETTE` /
        `Sepia` alak NEM futott le, a kanonikus `tint` / `Vignette` /
        `sepia` igen. A három család mintázata más — tehát tényleg a
        regiszterbeli alakhoz kell illeszteni, nem „csupa kisbetűhöz".

        A #1140-nel együtt teljes a viselkedés: a fel nem ismert tag nem
        „kimarad", hanem elvágja a lánc maradékát.
        """
        return self.name == name

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


def parse_filters_prefix(value: str) -> tuple[FilterOp, ...]:
    """A lánc ÉP ELŐTAGJA — az első hibás tagnál elvágva (#1140).

    ⚠️ Az eredeti Picasa lánc-bejárója **az első hibás tagnál megáll**, és
    ami előtte volt, azt alkalmazza. Két dolog tér el ettől a szigorú
    `parse_filters`-től, és mindkettő MÉRT:

    * a hibás tagot NEM elejtjük, hanem **elvágjuk a láncot** — a mögötte
      állók sem futnak. Mérve: `nincsilyen=1;bw=1;` esetén a Picasa a
      FORRÁST adja vissza, a `bw` nem fut le;
    * az `=` nélküli tagra **nem dobunk kivételt**. Nálunk ettől a kép
      EGYÁLTALÁN NEM exportálódott — nem romlott kép, hanem hiányzó kép.

    A szigorú `parse_filters` megmarad: az ÍRÓ ágnak (szerkesztő, vágólap,
    napló) tudnia kell a hibáról, mert ott a hibás lánc a mi hibánk. Ez a
    változat az OLVASÓ ágé, ahol egy idegen `.picasa.ini` tartalmát kell
    értelmeznünk — azt nem mi írtuk, és nem hiúsíthatja meg a műveletet.
    """
    ops: list[FilterOp] = []
    for entry in value.split(";"):
        if not entry:
            continue
        name, sep, rest = entry.partition("=")
        if not sep or not name:
            break
        # #1141: a NEM kanonikus írásmód is hibás tag — az eredeti
        # kis-nagybetű-érzékeny, és a bejáró az első hibás tagnál megáll
        # (#1140). Mérve: `Sepia=1;bw=1;` esetén a `bw` sem fut le.
        # Az ismeretlen (idegen/jövőbeli) nevet változatlanul beengedjük:
        # azt a renderelő hagyja ki, a round-trip pedig megőrzi.
        if canonical_filter_name(name) is not None and not is_exact_filter_name(name):
            break
        ops.append(FilterOp(name, tuple(rest.split(",")) if rest else ()))
    return tuple(ops)


def serialize_filters(ops: tuple[FilterOp, ...]) -> str:
    return "".join(f"{op.name}={','.join(op.params)};" for op in ops)


def canonicalize_op(op: FilterOp) -> FilterOp:
    """A szűrő nevét a regiszterbeli (Picasa által várt) alakra hozza (#695).

    Ismeretlen nevet érintetlenül hagy — a round-trip elv szerint amit nem
    ismerünk, ahhoz nem nyúlunk. Immutábilis: mindig ÚJ `FilterOp`-ot ad.

    Args:
        op: A lánc egy eleme.

    Returns:
        A kanonikus nevű `FilterOp` (vagy maga `op`, ha már az).
    """
    canonical = canonicalize_filter_name(op.name)
    if canonical == op.name:
        return op
    return FilterOp(canonical, op.params)


def validate_op_for_write(op: FilterOp) -> None:
    """Az ini-be írás előtti ellenőrzés: nem lóg-e ki a paraméterszám (#695).

    Mérve (#685): a FÖLÖSLEGES paramétert az eredeti Picasa néma elejtéssel
    bünteti (`grain2=1,0.500000;`), a hiányzót viszont az alapértékkel
    pótolja (`unsharp=1`), a záró üres mezőt (`grain=1,;`) pedig tolerálja.
    Ezért csak a felső korlátot kérjük számon, és a záró üres mezőt nem
    számoljuk paraméternek.

    Args:
        op: A lánc egy eleme (a `params[0]` az engedélyező flag).

    Raises:
        FilterWriteError: Ha a paraméterszám meghaladja a regiszterbelit.
    """
    limit = max_param_count(op.name)
    if limit is None:
        return
    count = _effective_param_count(op.params)
    if count > limit:
        canonical = canonicalize_filter_name(op.name)
        raise FilterWriteError(
            f"A(z) {canonical!r} szűrő legfeljebb {limit} paramétert vár az "
            f"engedélyező flag után, de {count} érkezett "
            f"({serialize_filters((op,))!r}). Az eredeti Picasa a fölös "
            f"paraméterű bejegyzést NÉMÁN elejti (#685), ezért nem írjuk ki."
        )


def serialize_filters_for_write(ops: tuple[FilterOp, ...]) -> str:
    """A `.picasa.ini`-be szánt `filters=` érték: kanonizálva és ellenőrizve.

    A sima `serialize_filters` bájtra pontos, de megengedő — az marad a
    bélyegkép-kulcs és a belső round-trip útja. Ez a változat az ÍRÓ kapu:
    a regiszterbeli szűrők nevét a Picasa által várt alakra hozza, és
    visszautasítja a néma elejtésbe futó paraméterszámot.

    Args:
        ops: A kiírandó lánc.

    Returns:
        A `filters=` érték stringje.

    Raises:
        FilterWriteError: Ha valamelyik elem paraméterszáma kilóg.
    """
    canonical_ops = tuple(canonicalize_op(op) for op in ops)
    for op in canonical_ops:
        validate_op_for_write(op)
    return serialize_filters(canonical_ops)


def _effective_param_count(params: tuple[str, ...]) -> int:
    """A flag utáni ÉRDEMI paraméterek száma.

    A záró üres mező (`grain=1,;`) mérten tolerált, tehát nem paraméter."""
    rest = list(params[1:])
    while rest and rest[-1] == "":
        rest.pop()
    return len(rest)
