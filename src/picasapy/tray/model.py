"""A képtálca (`scratch`) FELÜLET-FÜGGETLEN állapotmagja — #455.

Az eredeti Picasa alsó sávjának bal 36,5%-án ült a **képtálca** (belső
neve `scratch`, felirata „Selection"): ide gyűjtötted a képeket böngészés
közben, **mappákon átnyúlóan**, és a tálca tartalmán futott a műveletsor
(`trayexec`).

## Miért Qt-mentes, külön csomagban

Mert **két** felület ül rajta:

1. a főablak alsó sávjának képtálcája (`TrayBar.qml`);
2. a kollázs-szerkesztő **„Klipek" lapja** (#1276, #1153) — a Picasa saját
   szövegforrása szerint ez maga is tálca: a `collagepanel/deleteclips`
   súgója *„Remove selected clips from the **tray**"*, a filmszalag neve
   pedig `collagepanel/filmstrip_title` → **`Unused Pictures`**.

A két nézet ugyanazt mutatja, más szűréssel: a tálca **minden** elemét,
illetve a **fel nem használtakat**. Ezért a „felhasználtság" itt, az
ADATMODELLBEN él, nem a nézetben.

## Amit a modell szándékosan NEM csinál

**Nem tartós.** A tálca tartalma memóriában él, és a program bezárásával
elvész — három független ellenőrzés mondta ki (spec 1.): nincs `]scratch`
token az `albumdata_token.pmp`-ban, nincs tálca-fájl a profilmappában, és
nincs tálca-témájú `Preferences` kulcs. A megőrzés **eltérés** lenne, nem
javítás.

Minden művelet ÚJ állapotot ad vissza; a `TrayState` fagyasztott.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace


@dataclass(frozen=True, slots=True)
class TrayItem:
    """A tálca egy eleme — fotó-azonosító és két jelző.

    A **fotó-azonosító** (`PhotoRecord.id`) a kulcs, nem a rács sor-indexe:
    az utóbbi mappaváltáskor mást jelentene, és a tálca épp attól tálca,
    hogy mappákon átnyúlik.
    """

    #: az index `photos.id`-ja (pozitív egész)
    photo_id: int
    #: „Kijelölés megtartása" — a következő kijelölés NEM söpri el
    held: bool = False
    #: felhasznált (a Klipek fül „Unused Pictures" listája ezt szűri ki);
    #: az eredeti számlálói ugyanezt a jelölőt kérdezik (`[elem+0x5a]`)
    used: bool = False


@dataclass(frozen=True, slots=True)
class TrayState:
    """A tálca teljes állapota."""

    #: az elemek BESZÚRÁSI sorrendben — ez a műveletek sorrendje is
    items: tuple[TrayItem, ...] = ()
    #: a legutóbb megjegyzett elemszám: az `il_ClearFromTray` felkínált
    #: takarítás küszöbe (a bináris `+0x3194` mezője, spec 13.)
    remembered_count: int = 0


#: Az üres tálca — a program indulási állapota.
EMPTY = TrayState()


def _ids(values: Iterable[int]) -> tuple[int, ...]:
    """Bemenet-ellenőrzés: pozitív egész azonosítók, ismétlés nélkül.

    A felület felől QML-tömb (`QVariantList`) érkezik; a hívó vezérlő
    szűri a nyilvánvaló szemetet, ide már csak azonosítók jönnek. Ami
    mégsem az, az programhiba — kimondva bukjon el, ne némán.
    """
    if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
        raise TypeError(f"azonosító-sorozat kellene, nem {type(values)!r}")
    latott: set[int] = set()
    eredmeny: list[int] = []
    for nyers in values:
        if isinstance(nyers, bool) or not isinstance(nyers, int):
            raise TypeError(f"a fotó-azonosító egész szám legyen: {nyers!r}")
        if nyers <= 0:
            raise ValueError(f"a fotó-azonosító pozitív legyen: {nyers!r}")
        if nyers not in latott:
            latott.add(nyers)
            eredmeny.append(nyers)
    return tuple(eredmeny)


# -- lekérdezések ---------------------------------------------------------


def photo_ids(state: TrayState) -> tuple[int, ...]:
    """A tálca MINDEN eleme, beszúrási sorrendben."""
    return tuple(item.photo_id for item in state.items)


def held_ids(state: TrayState) -> tuple[int, ...]:
    """A RÖGZÍTETT elemek — a rácsban ezek kapnak jelvényt (`holdadorner`)."""
    return tuple(item.photo_id for item in state.items if item.held)


def used_ids(state: TrayState) -> tuple[int, ...]:
    """A FELHASZNÁLT elemek (a kollázsra már feltett képek)."""
    return tuple(item.photo_id for item in state.items if item.used)


def unused_ids(state: TrayState) -> tuple[int, ...]:
    """A FEL NEM HASZNÁLT elemek — a Klipek fül `Unused Pictures` listája,
    és a „Klipek (N)" fülfelirat száma."""
    return tuple(item.photo_id for item in state.items if not item.used)


def contains(state: TrayState, photo_id: int) -> bool:
    """A fotó a tálcán van-e."""
    return any(item.photo_id == photo_id for item in state.items)


def is_held(state: TrayState, photo_id: int) -> bool:
    """A fotó RÖGZÍTETT-e (jelvény a rácsban)."""
    return any(
        item.photo_id == photo_id and item.held for item in state.items
    )


# -- műveletek (mind új állapotot ad) -------------------------------------


def with_selection(state: TrayState, selection: Iterable[int]) -> TrayState:
    """A kijelölés a tálcába kerül; a MEGTARTOTT elemek maradnak.

    A Picasa tálcája **a kijelölés meghosszabbítása** volt, nem külön
    kosár: alapból a kijelölést mutatta, és a „Hold" fagyasztotta be, hogy
    máshonnan is lehessen hozzátenni (spec, `single_action_message` köre).

    Amit a kijelölés elsöpör: a se nem rögzített, se nem felhasznált
    elemek. A **felhasznált** elem azért marad, mert a felhasználtság
    olyan állapot, amit a kijelölésből nem lehet visszaállítani —
    elsöpörni néma adatvesztés volna (saját döntés, ld.
    `docs/decisions/keptalca-modell.md`).
    """
    ujak = _ids(selection)
    megmarado = tuple(
        item for item in state.items if item.held or item.used
    )
    meglevo = {item.photo_id for item in megmarado}
    return replace(
        state,
        items=megmarado
        + tuple(
            TrayItem(photo_id=pid) for pid in ujak if pid not in meglevo
        ),
    )


def with_hold(
    state: TrayState, selection: Iterable[int] | None = None
) -> TrayState:
    """„Kijelölés megtartása" (`Tray::ID_PICTURE_HOLDINPICTURETRAY`).

    `selection=None` esetén a tálca MINDEN elemét rögzíti (ez a
    gomb viselkedése: a tálca ilyenkor épp a kijelölést tükrözi).
    Megadott azonosítóknál csak azokat — és ha egy azonosító még nincs a
    tálcán, felveszi. A spec 12. szerint EGY parancs van erre, tehát
    „hozzáadás a tálcához" néven nem épül külön út.
    """
    if selection is None:
        return replace(
            state,
            items=tuple(replace(item, held=True) for item in state.items),
        )
    kertek = _ids(selection)
    kert_halmaz = set(kertek)
    meglevo = {item.photo_id for item in state.items}
    return replace(
        state,
        items=tuple(
            replace(item, held=True) if item.photo_id in kert_halmaz else item
            for item in state.items
        )
        + tuple(
            TrayItem(photo_id=pid, held=True)
            for pid in kertek
            if pid not in meglevo
        ),
    )


def without(state: TrayState, selection: Iterable[int]) -> TrayState:
    """„Kijelölés eltávolítása" (`Tray::ID_REMOVE_SELECTION`), és a Klipek
    lap „–" gombja (*Remove selected clips from the tray*)."""
    torlendo = set(_ids(selection))
    return replace(
        state,
        items=tuple(
            item for item in state.items if item.photo_id not in torlendo
        ),
    )


def cleared(state: TrayState) -> TrayState:
    """Teljes ürítés (`IDS_CLEARTRAY`) — a küszöb is nullázódik."""
    return EMPTY


def with_used(
    state: TrayState, selection: Iterable[int], used: bool = True
) -> TrayState:
    """A „felhasználtság" jelölése — a Klipek lap „+" gombjának hatása.

    A megjelölt elem a tálcán MARAD (a kollázsról levéve újra
    felhasználható lesz), csak a `Unused Pictures` listából esik ki. A
    tálcán nem szereplő azonosítót figyelmen kívül hagyjuk: a jelölés
    meglévő elemre vonatkozik, nem felvételi út.
    """
    jelolendo = set(_ids(selection))
    return replace(
        state,
        items=tuple(
            replace(item, used=used) if item.photo_id in jelolendo else item
            for item in state.items
        ),
    )


# -- a „régóta tartott elemek" felkínált takarítása (spec 13.) ------------


def needs_old_items_prompt(state: TrayState) -> bool:
    """Kell-e felkínálni az `il_ClearFromTray` takarítást.

    **NEM idő-alapú.** A bináris (`0x00571e50`) a NEM KIZÁRT elemek számát
    hasonlítja a legutóbb megjegyzett számhoz, és csak NÖVEKEDÉSKOR
    kérdez; ha nem nőtt, némán frissíti a megjegyzett értéket. „Régóta
    tartott" = ami már a növekedés előtt is bent volt.
    """
    return len(unused_ids(state)) > state.remembered_count


def with_remembered_count(state: TrayState) -> TrayState:
    """A küszöb frissítése a mostani elemszámra (a bináris `+0x3194`-be
    író ága) — ettől a kérdés a következő növekedésig nem tér vissza."""
    return replace(state, remembered_count=len(unused_ids(state)))
