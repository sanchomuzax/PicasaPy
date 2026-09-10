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
class TrayAlbumToken:
    """ÖSSZECSUKOTT mappa-/album-token — a tálca MÁSIK elemtípusa (#1919).

    Az eredeti tálca egy egész mappát vagy albumot egyetlen elemként is
    tud tartani: bélyegkép-rács helyett egy borítókép, rajta középre
    igazított felirattal („Kiválasztott mappa - 82 fotó"). A rétegkészlet
    a `referencia/tre-eroforrasok/scratch.tre` `scratch/album` családja.

    Amiben ez NEM fotó: nincs `photos.id`-ja, tehát a `photo_ids`, a
    `held_ids`, a `used_ids` és az `unused_ids` nem adja vissza — azok
    kifejezetten fotó-azonosítókat ígérnek. A tokent az `album_tokens`
    kérdezi le.

    A `held` és a `used` viszont UGYANAZT jelenti, mint a képnél: a token
    is tálca-elem, tehát a következő kijelölés elsöpri, ha nincs
    megtartva, és a „Kijelölés megtartása" rá is vonatkozik.
    """

    #: a token KULCSA — a mappa útvonala vagy az album azonosítója. Ez
    #: teszi felismerhetővé (ugyanaz a mappa nem kerülhet be kétszer);
    #: a felirat szándékosan NINCS benne, mert az a nyelvtől függ.
    key: str
    #: hány fotót képvisel — ez kerül a feliratba
    photo_count: int
    #: a borítókép `photos.id`-ja (`scratch/albumcover`), ha van. Üres
    #: mappánál nincs miből venni — az nem hiba.
    cover_photo_id: int | None = None
    #: album (`CThumbUI::UpdateAlbumAlbum` — „Kiválasztott album") vagy
    #: mappa (`CThumbUI::UpdateAlbumFolder` — „Kiválasztott mappa")
    is_album: bool = False
    #: „Kijelölés megtartása" — a következő kijelölés NEM söpri el
    held: bool = False
    #: felhasznált — ugyanaz a jelölő, mint a képnél
    used: bool = False

    def __post_init__(self) -> None:
        """Bemenet-ellenőrzés: ami nem érvényes token, az kimondva
        bukjon el, ne némán rajzolódjon ki üresen."""
        if not isinstance(self.key, str) or not self.key:
            raise ValueError(
                f"a token kulcsa nem üres sztring legyen: {self.key!r}"
            )
        if isinstance(self.photo_count, bool) or not isinstance(
            self.photo_count, int
        ):
            raise TypeError(
                f"a darabszám egész szám legyen: {self.photo_count!r}"
            )
        if self.photo_count < 0:
            raise ValueError(
                f"a darabszám nem lehet negatív: {self.photo_count!r}"
            )
        if self.cover_photo_id is not None and (
            isinstance(self.cover_photo_id, bool)
            or not isinstance(self.cover_photo_id, int)
            or self.cover_photo_id <= 0
        ):
            raise ValueError(
                "a borító azonosítója pozitív egész legyen: "
                f"{self.cover_photo_id!r}"
            )


#: A tálca egy eleme: egyedi kép VAGY összecsukott mappa-/album-token.
TrayEntry = TrayItem | TrayAlbumToken


def _is_photo(entry: TrayEntry) -> bool:
    """Fotó-elem-e (szemben az összecsukott tokennel)."""
    return isinstance(entry, TrayItem)


@dataclass(frozen=True, slots=True)
class TrayState:
    """A tálca teljes állapota."""

    #: az elemek BESZÚRÁSI sorrendben — ez a műveletek sorrendje is.
    #: KÉTFÉLE elem lehet benne (#1919): kép és mappa-/album-token.
    items: tuple[TrayEntry, ...] = ()
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
    """A tálca minden KÉP-eleme, beszúrási sorrendben.

    Az összecsukott mappa-/album-tokent (#1919) szándékosan nem adja
    vissza: annak nincs `photos.id`-ja. Azt az `album_tokens` kérdezi.
    """
    return tuple(item.photo_id for item in state.items if _is_photo(item))


def album_tokens(state: TrayState) -> tuple[TrayAlbumToken, ...]:
    """Az ÖSSZECSUKOTT mappa-/album-tokenek, beszúrási sorrendben (#1919)."""
    return tuple(
        item for item in state.items if isinstance(item, TrayAlbumToken)
    )


def held_ids(state: TrayState) -> tuple[int, ...]:
    """A RÖGZÍTETT képek — a rácsban ezek kapnak jelvényt (`holdadorner`)."""
    return tuple(
        item.photo_id
        for item in state.items
        if _is_photo(item) and item.held
    )


def used_ids(state: TrayState) -> tuple[int, ...]:
    """A FELHASZNÁLT képek (a kollázsra már feltettek)."""
    return tuple(
        item.photo_id
        for item in state.items
        if _is_photo(item) and item.used
    )


def unused_ids(state: TrayState) -> tuple[int, ...]:
    """A FEL NEM HASZNÁLT képek — a Klipek fül `Unused Pictures` listája,
    és a „Klipek (N)" fülfelirat száma."""
    return tuple(
        item.photo_id
        for item in state.items
        if _is_photo(item) and not item.used
    )


def contains(state: TrayState, photo_id: int) -> bool:
    """A fotó a tálcán van-e."""
    return any(
        _is_photo(item) and item.photo_id == photo_id for item in state.items
    )


def is_held(state: TrayState, photo_id: int) -> bool:
    """A fotó RÖGZÍTETT-e (jelvény a rácsban)."""
    return any(
        _is_photo(item) and item.photo_id == photo_id and item.held
        for item in state.items
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
    meglevo = {item.photo_id for item in megmarado if _is_photo(item)}
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
    meglevo = {item.photo_id for item in state.items if _is_photo(item)}
    return replace(
        state,
        items=tuple(
            replace(item, held=True)
            if _is_photo(item) and item.photo_id in kert_halmaz
            else item
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
    lap „–" gombja (*Remove selected clips from the tray*).

    FOTÓ-azonosítókkal dolgozik; az összecsukott token (#1919) marad — azt
    a `without_album_token` viszi el a kulcsával.
    """
    torlendo = set(_ids(selection))
    return replace(
        state,
        items=tuple(
            item
            for item in state.items
            if not (_is_photo(item) and item.photo_id in torlendo)
        ),
    )


def with_album_token(
    state: TrayState, token: TrayAlbumToken
) -> TrayState:
    """Összecsukott mappa-/album-token a tálcára (#1919).

    Ugyanarra a KULCSRA a második hívás felülírja az elsőt, és a token a
    HELYÉN marad: a darabszám frissülése (a mappába új kép került) nem
    művelet, tehát nem is rendezheti át a tálcát.

    ## Mikor mutatja meg ezt az EREDETI (KIMÉRVE, #1919)

    Nem parancs és nem gesztus: **minden képfrissítéskor újraértékelt
    szabály**. A `scratch/album` réteg egy állapot-küldöttet kap
    (a bekötés `0x00572ba4`), és a küldött `0x00563530` függvénye dönt —
    `4` = mutasd, `8` = rejtsd:

    - van album-/mappa-kijelölés (`CThumbUI+0xEAC` nem NULL), ÉS
    - annak a tömbje nem üres, ÉS
    - a KÉP-kijelölés (`CThumbUI+0xEA4`) üres.

    Vagyis amint a felhasználó egyetlen képet is kijelöl, a token eltűnik,
    és a bélyegképek veszik át a helyét.

    ⚙️ **A szabály 2026-09-10 óta FUT (#2741), de csak az ALBUM-kijelölésre**
    (`TrayBar.qml` → `TrayMixin.showSelectedAlbumToken`): a token akkor jár
    ki, ha `currentAlbumToken !== ""` ÉS a kép-kijelölés üres. A megnyitott
    MAPPÁRA szándékosan nem szól — nálunk a „mappa-kijelölés" a megnyitott
    mappa, ott a kép-kijelölés szinte mindig üres, tehát a szó szerinti
    átvétel a tálca MINDENNAPI kinézetét írná át.

    Az így kirakott token **nem `held`**, ezért a következő kép-kijelölést a
    `with_selection` magától elsöpri — pontosan úgy, ahogy az eredetiben a
    bélyegképek átveszik a helyét. A kézzel összecsukott mappa tokenje
    (`collapseFolderIntoTray`) `held`, azt a szabály nem viszi el.
    """
    if not isinstance(token, TrayAlbumToken):
        raise TypeError(f"mappa-/album-token kellene, nem {type(token)!r}")
    csere = False
    ujak: list[TrayEntry] = []
    for item in state.items:
        if isinstance(item, TrayAlbumToken) and item.key == token.key:
            ujak.append(token)
            csere = True
        else:
            ujak.append(item)
    if not csere:
        ujak.append(token)
    return replace(state, items=tuple(ujak))


def without_album_token(state: TrayState, key: str) -> TrayState:
    """Az adott kulcsú összecsukott token eltávolítása (#1919).

    A nem létező kulcs nem hiba — ugyanaz az elv, mint a `without`-nál.
    """
    return replace(
        state,
        items=tuple(
            item
            for item in state.items
            if not (isinstance(item, TrayAlbumToken) and item.key == key)
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
            replace(item, used=used)
            if _is_photo(item) and item.photo_id in jelolendo
            else item
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
