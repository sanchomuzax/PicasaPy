"""Elrendezés-invariánsok a KIRAJZOLT QML-fán — a #656 terv 1. fázisa.

Ez a modul **nem** az eredeti Picasához hasonlít: tiszta önellenőrzés a saját
felületünkön. Két olyan állítást vizsgál, ami minden felületre igaz kell
legyen, referencia nélkül is:

- **túlcsordulás** — egy vezérlő kilóg a szülője dobozából;
- **átfedés** — két testvér ugyanazt a képpontot foglalja.

Miért invariáns, és miért nem konkrét elvárás: a meglévő tesztjeink azt
ellenőrzik, amire valaki előre gondolt. A felhasználó által jelzett hibák
(az effekt-csúszkák nem férnek a bal oszlopba, gombok rossz helyre csúsznak)
pont azért csúsztak át, mert senki nem írt rájuk külön elvárást. Egy
invariáns viszont **az összes** vezérlőre egyszerre néz rá.

A bejárás a VIZUÁLIS fát követi (`childItems()`), mert a
`Repeater`/`ListView` delegáltjait a `findChild` nem találja meg — a
csúszkasorok pedig pontosan ilyenek.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Iterable, Iterator

#: Alapértelmezett tűrés képpontban. A QML geometriája tört szám lehet
#: (`implicitWidth` + skálázás), ezért a fél képpont körüli kilógás nem hiba.
DEFAULT_TOLERANCE = 1.0

#: Az ismert, még nem javított sértések listája. Azért van, hogy az őr
#: bevezethető legyen anélkül, hogy a meglévő hibákat ebben a körben
#: javítanánk — a hatókör-szabály szerint azokra külön jegy nyílik.
ALLOWLIST_PATH = Path(__file__).with_name("uiaudit_ismert_sertesek.json")


@dataclass(frozen=True)
class Violation:
    """Egy elrendezés-sértés. Fagyasztott: a leletet nem írjuk felül."""

    kind: str
    item: str
    parent: str
    detail: str
    other: str | None = None

    def key(self) -> tuple[str, str, str, str]:
        """Az azonosság kulcsa — a `detail` szándékosan NEM része.

        A kilógás mértéke ablakmérettől függ; ha a kulcs része lenne, az
        engedélyezési lista minden szélességnél új bejegyzést kívánna.
        """
        return (self.kind, self.item, self.parent, self.other or "")


def walk(item) -> Iterator:
    """A vizuális fa bejárása, mélységi sorrendben."""
    for child in item.childItems():
        yield child
        yield from walk(child)


def _name(item) -> str:
    """Beszédes név a riporthoz: `objectName`, ha van; különben a típus."""
    name = item.objectName()
    if name:
        return name
    meta = item.metaObject()
    return f"<{meta.className()}>" if meta is not None else "<ismeretlen>"


def _merheto(item) -> bool:
    """Csak látható, nem nulla méretű elemet mérünk.

    A láthatatlan elemek geometriája gyakran még nincs beállítva (a layout
    nem futott le rájuk), és a nulla méretű helyőrzők zajt adnának.
    """
    return bool(item.isVisible()) and item.width() > 0 and item.height() > 0


def find_overflows(root, tolerance: float = DEFAULT_TOLERANCE) -> list[Violation]:
    """Kilóg-e valamelyik gyerek a szülője dobozából?

    A `clip` tulajdonságú szülőt kihagyjuk: ott a kilógás **szándékos**, a
    tartalom vágása a cél (görgethető listák). Ez nem kényelmi kivétel — e
    nélkül minden `ListView` hamis riasztást adna.
    """
    sertesek: list[Violation] = []
    for parent in walk(root):
        if not _merheto(parent) or parent.clip():
            continue
        szeles = parent.width()
        magas = parent.height()
        for child in parent.childItems():
            if not _merheto(child):
                continue
            tul_jobb = (child.x() + child.width()) - szeles
            tul_also = (child.y() + child.height()) - magas
            tul_bal = -child.x()
            tul_felso = -child.y()
            mertek = max(tul_jobb, tul_also, tul_bal, tul_felso)
            if mertek > tolerance:
                irany = _irany(tul_jobb, tul_also, tul_bal, tul_felso)
                sertesek.append(
                    Violation(
                        kind="overflow",
                        item=_name(child),
                        parent=_name(parent),
                        detail=f"{mertek:.1f} képponttal lóg ki ({irany})",
                    )
                )
    return sertesek


def _irany(jobb: float, also: float, bal: float, felso: float) -> str:
    parok = (("jobbra", jobb), ("lefelé", also), ("balra", bal), ("felfelé", felso))
    return max(parok, key=lambda par: par[1])[0]


def find_overlaps(root, tolerance: float = DEFAULT_TOLERANCE) -> list[Violation]:
    """Fedi-e egymást két testvér?

    Csak **testvéreket** hasonlítunk: a szülő-gyerek átfedés természetes.
    A `z` szerint szándékosan egymásra tett elemeket (pl. overlay) a hívó az
    engedélyezési listával zárja ki — automatikusan nem tudjuk megítélni,
    mi szándékos.
    """
    sertesek: list[Violation] = []
    for parent in walk(root):
        if not _merheto(parent):
            continue
        gyerekek = [child for child in parent.childItems() if _merheto(child)]
        for i, elso in enumerate(gyerekek):
            for masodik in gyerekek[i + 1:]:
                atfedes = _atfedes(elso, masodik)
                if atfedes > tolerance:
                    nevek = sorted((_name(elso), _name(masodik)))
                    sertesek.append(
                        Violation(
                            kind="overlap",
                            item=nevek[0],
                            parent=_name(parent),
                            detail=f"{atfedes:.1f} képpont átfedés",
                            other=nevek[1],
                        )
                    )
    return sertesek


def _atfedes(a, b) -> float:
    """A közös terület kisebbik oldala képpontban (0, ha nincs átfedés)."""
    vizszintes = min(a.x() + a.width(), b.x() + b.width()) - max(a.x(), b.x())
    fuggoleges = min(a.y() + a.height(), b.y() + b.height()) - max(a.y(), b.y())
    if vizszintes <= 0 or fuggoleges <= 0:
        return 0.0
    return float(min(vizszintes, fuggoleges))


def load_allowlist(path: Path | None = None) -> frozenset[tuple[str, str, str, str]]:
    """Az ismert sértések kulcsai. Hiányzó fájl esetén üres — ez nem hiba."""
    target = path or ALLOWLIST_PATH
    if not target.exists():
        return frozenset()
    try:
        adat = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as hiba:
        raise ValueError(f"az ismert-sértés lista nem olvasható: {target}") from hiba
    return frozenset(
        (bejegyzes["kind"], bejegyzes["item"], bejegyzes["parent"], bejegyzes.get("other") or "")
        for bejegyzes in adat.get("sertesek", [])
    )


def subtract_allowlist(
    sertesek: Iterable[Violation],
    engedelyezett: frozenset[tuple[str, str, str, str]],
) -> list[Violation]:
    """Csak az ÚJ sértések — a már ismerteket kiszűrjük."""
    return [sertes for sertes in sertesek if sertes.key() not in engedelyezett]


def format_report(sertesek: Iterable[Violation]) -> str:
    """Emberi olvasásra szánt riport; üres listára beszédes mondat."""
    tetelek = list(sertesek)
    if not tetelek:
        return "nincs elrendezés-sértés"
    sorok = [f"{len(tetelek)} elrendezés-sértés:"]
    for sertes in sorted(tetelek, key=lambda s: (s.kind, s.parent, s.item)):
        cel = f"{sertes.item}+{sertes.other}" if sertes.other else sertes.item
        sorok.append(f"  [{sertes.kind}] {sertes.parent} › {cel}: {sertes.detail}")
    return "\n".join(sorok)


def to_allowlist_json(sertesek: Iterable[Violation]) -> str:
    """A talált sértések engedélyezési listává alakítva (kézi átnézésre)."""
    egyedi = {sertes.key(): sertes for sertes in sertesek}
    bejegyzesek = [
        {
            "kind": sertes.kind,
            "item": sertes.item,
            "parent": sertes.parent,
            "other": sertes.other,
            "megjegyzes": sertes.detail,
        }
        for sertes in sorted(egyedi.values(), key=lambda s: s.key())
    ]
    return json.dumps({"sertesek": bejegyzesek}, indent=1, ensure_ascii=False)


def with_detail(sertes: Violation, detail: str) -> Violation:
    """Új példány más leírással — a fagyasztott leletet nem írjuk felül."""
    return replace(sertes, detail=detail)
