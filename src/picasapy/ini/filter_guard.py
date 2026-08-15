"""#643 — ROUND-TRIP ŐR: a Picasa által elvetett lánc nem juthat a lemezre.

## Amit a #643 kutatói szála bizonyított

Az eredeti Picasa `filters=` lánc-bejárója **az első hibás tagnál megáll**,
és onnantól a lánc hátralévő része **egyáltalán nem fut le**. Ez nem
elmélet: dekompilációból ÉS hét valódi Picasa-exporton mérve is megerősített
(ld. `docs/specs/picasa-ini-format.md`, „A lánc bejárója az ELSŐ hibás
tagnál megáll" szakasz mérési táblája). Három hibamód viselkedik **azonosan**:

| lánc | ΔE | mi történt |
|---|---|---|
| `sepia=1;bw=1;` | 17,238 | mindkettő lefutott (kontroll) |
| `nincsilyen=1;bw=1;` | 0,181 | **semmi** — ismeretlen név |
| `grain2=1,0.5;bw=1;` | 0,181 | **semmi** — rossz paraméterszám |
| `sepia;bw=1;` | 0,181 | **semmi** — hiányzó `=` |
| `sepia=1;nincsilyen=1;` | 21,251 | csak a `sepia` (a ZÁRÓ hibás tag ártalmatlan) |

Ez magyarázza a hibajelentést: a lánc SZÖVEGE hiánytalanul átmegy (ezért
helyes a Picasa gombfelirata), de a FELDOLGOZÁS megáll, ezért a kép nem
mutatja az effekteket.

## Miért kell ŐR, ha a #695 már ellenőriz?

A #695 az író kaput ott zárja, ahol a lánc-elem KELETKEZIK (`EditSession.
_new_op`) — de csak a paraméterszámra, és csak azon az egy úton. Az ini-be
öt-hat különböző vezérlő ír `filters=` értéket (szerkesztő, csoportos
effekt, effekt-vágólap, fotóműveletek, mentés `redo=`-ja, a #644-es napló
visszatöltése), és ezek nyers stringgel is dolgoznak (visszavonás: a
korábbi, nyers érték visszaírása). Ezért az őr a KÖZÖS kapun ül
(`IniDocument.with_value`): amit ott nem engedünk át, az semmilyen hívón
keresztül nem juthat a lemezre.

## A viselkedés — és miért EZ (a jegy kifejezett kérése)

Három lehetőség merült fel; a `.picasa.ini` a felhasználó éles családi
gyűjteményén él, ezért mindkét szélsőség rossz:

1. **A hibás tag néma kihagyása** — ez adatvesztés: a felhasználó (vagy egy
   újabb Picasa-verzió) által beírt bejegyzést dobnánk el szó nélkül,
   miközben a round-trip elv (CLAUDE.md 1. döntés) épp azt írja elő, hogy
   amit nem értünk, azt bitre pontosan megőrizzük. **Elvetve.**
2. **Mindig kivétel** — ez a felhasználó munkáját dobná el: egy idegen
   eredetű, hibás tag miatt a képen többé SEMMILYEN szerkesztés nem lenne
   menthető, pedig a hibát nem mi okoztuk. **Önmagában elvetve.**
3. **A kettő szétválasztása a tag EREDETE szerint** — ez a választott
   megoldás.

**A szabály egy mondatban:** a lánc-írás visszautasított (`FilterWriteError`),
ha a kiírandó lánc olyan hibás tagot tartalmaz, amely a kulcs ELŐZŐ
értékében **nem szerepelt**; a már ott lévő hibás tag változatlan megőrzése
megengedett, de **naplózott** (`logging.WARNING`).

Indoklás:

- *Újonnan keletkező hibás tag* = a MI hibánk. Ilyet a lemezre engedni néma
  adatvesztés lenne a felhasználó szemszögéből (a szerkesztés eltűnik a
  Picasában), ezért a kivétel a helyes: hangosan, a fájl megérintése ELŐTT.
  A hívók az ini-írás eddigi hibáival azonos módon kezelik (`_WRITE_ERRORS`),
  tehát a felhasználó magyar hibaüzenetet kap, nem összeomlást.
- *Már meglévő hibás tag* = nem mi rontottuk el, és a fájl már eddig is
  ebben az állapotban volt. Eldobni adatvesztés, visszautasítani a
  felhasználó munkájának eldobása lenne — megőrizzük, de a napló miatt már
  nem „csendben megy ki a lemezre".

A rövid összefoglaló: **soha nem ADUNK hozzá hibát, és soha nem TÖRLÜNK
egy meglévőt.**

## A `carried` csatorna — a MÁSOLÁS nem szerzőség

A „soha nem adunk hozzá hibát" szabály egy helyen szó szerint nem
alkalmazható: amikor egy láncot **változatlanul átviszünk máshonnan**, és a
célkulcsnak nincs előző értéke. Ilyen a „Copy/Paste All Effects" (#152,
#426), a beillesztés visszavonása, a mentés `filters=` → `redo=` átforgatása
(#21, #444) és a #644-es napló visszatöltése. Ezeknél a hibás tag NEM most
keletkezik — csak más helyre kerül —, és a másolás megtagadása vagy a tag
kiszűrése ugyanaz a két rossz kimenet lenne, mint fent.

Ezért az írási kapunak van egy **kimondott** átviteli csatornája:
`IniDocument.with_value(..., carried=True)`. Ez NEM kikapcsolja az őrt: a
lánc ugyanúgy megvizsgáltatik és a hibák naplóba kerülnek — csak a kivétel
marad el. A hívónak ezzel ki kell MONDANIA, hogy a láncot hordozza, nem
szerzi; az alapértelmezés (`carried=False`) szigorú, tehát minden
szerkesztő-útvonal automatikusan a szigorú ágon van.

Az átvitelt használó helyek szűk, auditálható köre a
`tests/ini/test_roundtrip_guard_643.py`-ban rögzítve van.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

from picasapy.ini.filter_registry import (
    FilterWriteError,
    canonical_filter_name,
    effective_param_count,
    max_param_count,
)

_log = logging.getLogger(__name__)

#: Azok az ini-kulcsok, amelyek értéke `filters=` SZINTAXISÚ szerkesztési
#: lánc, tehát a Picasa ugyanazzal a bejáróval dolgozza fel. A `redo=` a
#: mentéskor félretett verem (`edit/save.py`) — ha az romlik el, a
#: „Mentés visszavonása" (#444) írna vissza halott láncot a `filters=`-be.
CHAIN_KEYS: frozenset[str] = frozenset({"filters", "redo"})


class DefectKind(Enum):
    """A három, MÉRTEN azonos hatású hibamód (#643)."""

    MISSING_EQUALS = "hiányzó `=`"
    UNKNOWN_NAME = "ismeretlen szűrőnév"
    TOO_MANY_PARAMS = "túl sok paraméter"


@dataclass(frozen=True)
class ChainDefect:
    """Egyetlen hibás lánc-tag és a miatta ELVESZŐ hátralévő rész.

    Attributes:
        index: A tag sorszáma a láncban (0-tól).
        entry: A tag nyers szövege (`;` nélkül).
        kind: A hibamód.
        detail: Emberi nyelvű magyarázat (magyarul).
        lost_entries: A tag UTÁN álló tagok — ezek a Picasában NEM futnak le,
            mert a bejáró itt megáll. Ez a #643 lényege: a kár nem a hibás
            tagra korlátozódik.
    """

    index: int
    entry: str
    kind: DefectKind
    detail: str
    lost_entries: tuple[str, ...] = ()

    def describe(self) -> str:
        """A hiba egysoros, magyar leírása — hibaüzenetbe és naplóba.

        A szóhasználat szándékosan „lépés" és nem „tag": ez a szöveg a
        felhasználó elé is kikerül (a mentés hibaüzenetében), ő pedig a
        láncot egymás után alkalmazott szerkesztési lépésekként ismeri."""
        text = (
            f"{self.index + 1}. lépés ({self.entry!r}): "
            f"{self.kind.value} — {self.detail}"
        )
        if self.lost_entries:
            elveszo = ", ".join(repr(entry) for entry in self.lost_entries)
            text += f"; emiatt a Picasában NEM fut le utána: {elveszo}"
        return text


def is_chain_key(key: str) -> bool:
    """Lánc-szintaxisú ini-kulcs-e (kis-nagybetű-tűrően)."""
    return key.casefold() in CHAIN_KEYS


def inspect_chain(value: str) -> tuple[ChainDefect, ...]:
    """A lánc végigjárása a Picasa HÁROM mért szabálya szerint.

    Nem dob és nem módosít — csak leltárt ad. Az `EditSession`/`parse_filters`
    útjától függetlenül, közvetlenül a kiírandó SZÖVEGET vizsgálja, mert az
    őrnek pont azt kell fednie, ami a lemezre kerülne.

    Args:
        value: A `filters=`/`redo=` kulcs kiírandó értéke.

    Returns:
        A hibás tagok leírói, lánc-sorrendben; hibátlan láncnál üres tuple.
    """
    entries = tuple(entry for entry in value.split(";") if entry)
    defects: list[ChainDefect] = []
    for index, entry in enumerate(entries):
        kind_detail = _defect_of(entry)
        if kind_detail is None:
            continue
        kind, detail = kind_detail
        defects.append(
            ChainDefect(
                index=index,
                entry=entry,
                kind=kind,
                detail=detail,
                lost_entries=entries[index + 1 :],
            )
        )
    return tuple(defects)


def guard_chain_write(
    key: str,
    new_value: str,
    previous_value: str | None,
    *,
    where: str = "",
    carried: bool = False,
) -> tuple[ChainDefect, ...]:
    """Az ini-írás kapuja: elvetendő láncot nem enged tovább (#643).

    A döntési szabály és annak indoklása a modul docstringjében. Nem
    lánc-kulcsra (pl. `caption`) azonnal visszatér — ez a függvény a közös
    írási úton fut, tehát olcsónak kell lennie.

    Args:
        key: Az írandó ini-kulcs neve.
        new_value: A kiírandó érték.
        previous_value: A kulcs jelenlegi értéke a dokumentumban, vagy `None`,
            ha a kulcs (vagy a szekció) még nem létezik.
        where: Naplóba/hibaüzenetbe kerülő hely-megjelölés (pl. `[kep.jpg]`).
        carried: A lánc máshonnan, VÁLTOZATLANUL átvitt tartalom (beillesztés,
            visszavonás, `redo=` átforgatás, napló-visszatöltés) — ilyenkor a
            hibás tag nem most keletkezik, ezért nem utasítjuk vissza, csak
            naplózzuk. Ld. a modul „A `carried` csatorna" szakaszát.

    Returns:
        A MEGŐRZÖTT (nem most keletkezett) hibás tagok — a hívónak nem kell
        velük tennie semmit, a naplózás itt megtörtént.

    Raises:
        FilterWriteError: Ha a láncban ÚJ hibás tag jelent meg (és a lánc nem
            `carried`).
    """
    if not is_chain_key(key):
        return ()
    defects = inspect_chain(new_value)
    if not defects:
        return ()

    previous_entries = frozenset(
        entry for entry in (previous_value or "").split(";") if entry
    )
    introduced = tuple(d for d in defects if d.entry not in previous_entries)

    if introduced and not carried:
        raise FilterWriteError(_write_error_message(key, new_value, introduced, where))

    _log.warning(
        "A(z) %s%s lánc %s hibás tagot tartalmaz — az eredeti Picasa itt "
        "megáll, és a lánc hátralévő része nem fut le. Nem dobjuk el "
        "(round-trip elv), de jelezzük: %s",
        key,
        f" {where}" if where else "",
        "ÁTVITT (carried)" if carried else "megőrzött, IDEGEN eredetű",
        "; ".join(defect.describe() for defect in defects),
    )
    return defects


def _defect_of(entry: str) -> tuple[DefectKind, str] | None:
    """Egyetlen lánc-tag megvizsgálása; hibátlan tagnál `None`."""
    name, separator, rest = entry.partition("=")
    if not separator or not name:
        return (
            DefectKind.MISSING_EQUALS,
            "a tagnak `<név>=<flag>[,<paraméter>...]` alakúnak kell lennie",
        )

    canonical = canonical_filter_name(name)
    if canonical is None:
        return (
            DefectKind.UNKNOWN_NAME,
            f"a(z) {name!r} nevű szerkesztést az eredeti Picasa nem ismeri "
            f"(nincs a kanonikus szűrőnév-táblában)",
        )

    limit = max_param_count(name)
    if limit is None:
        # Szándékosan nem validált szűrő (ld. `UNKNOWN_PARAM_COUNT_FILTERS`):
        # a regiszterből nem vezethető le a darabszám, a találgatás valódi
        # szerkesztést utasítana vissza.
        return None

    params = tuple(rest.split(",")) if rest else ()
    count = effective_param_count(params)
    if count > limit:
        return (
            DefectKind.TOO_MANY_PARAMS,
            f"a(z) {canonical!r} legfeljebb {limit} paramétert vár az "
            f"engedélyező flag után, de {count} érkezett",
        )
    return None


def _write_error_message(
    key: str, value: str, introduced: tuple[ChainDefect, ...], where: str
) -> str:
    """A visszautasítás magyar, cselekvésre fordítható indoklása.

    Ez a szöveg **a felhasználó elé kerül** (a szerkesztő mentési hibája és
    a fotóművelet-hibasáv is ezt mutatja), ezért az első két mondat
    hétköznapi nyelvű: mi történt, és mi lett a következménye. A gépi
    részlet (kulcs, nyers lánc) a végére kerül, hogy a hibajelentésbe
    bemásolható legyen, de ne az legyen az első, amit elolvas.

    Új `qsTr()`/`tr()` forrásszöveget SZÁNDÉKOSAN nem vezetünk be: a
    projekt hibaüzenetei (`IniConflictError`, `SaveError`) is magyarul, a
    kivétel szövegében élnek, és egy új fordítandó szöveg a `.ts`
    újragenerálása nélkül pirosra vinné a `test_i18n_completeness`-t.
    """
    hely = f" ({where})" if where else ""
    sorok = "\n".join(f"  • {defect.describe()}" for defect in introduced)
    return (
        f"A szerkesztés nem menthető{hely}: olyan lépés került a "
        f"szerkesztési sorba, amelyet az eredeti Picasa nem tud feldolgozni. "
        f"A Picasa az ilyen lépésnél megáll, ezért nála az utána következő "
        f"szerkesztések sem futnának le — a kép egészen máshogy nézne ki, "
        f"mint itt.\n"
        f"Ezért a mentést visszautasítottuk: a kép korábbi, működő "
        f"szerkesztése érintetlen maradt.\n"
        f"{sorok}\n"
        f"(Technikai részlet: {key}={value!r})"
    )
