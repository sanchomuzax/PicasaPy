"""A megőrzött eredeti ini-szekciója is a képpel költözik (#1448).

A #1430 óta a megőrzött eredeti FÁJLJA követi a képet. A hozzá tartozó
`.picasaoriginals/.picasa.ini` szekció viszont a forrásban maradt: a fájl az
új helyen `b.jpg` néven állt, a szekció a régi mappa inijében `[a.jpg]`
néven. A tulajdonos valódi gyűjteményében **52 ilyen ini** van, és nem
üresek — szekciónként `filters=`, `crop=`, `rotate=`, `width/height`,
`moddate`.

Két ára van:

1. A párhuzamosan futó, eredeti (windowsos) Picasa ezt az ini-t olvassa — a
   kétirányú kompatibilitás a projekt élő próbája, ott a beállítások
   elvesznének.
2. Ha később MÁSIK, azonos nevű eredeti kerül a forrás eredeti-mappájába,
   **örökli az elárvult beállításokat** — egy idegen kép adatait kapja meg.
   Ez ugyanaz a hibaosztály, amit a `originals.py` a fájlok szintjén már
   megelőz.

## Sávhatár

Az írás KIZÁRÓLAG az `ini/` csomag API-ján megy (`update_document`), tehát
ütközésbiztosan és backuppal: a párhuzamosan író Picasa közbeírása nem
veszhet el. Közvetlen fájlírás itt sincs.

## A tartalom bitre pontosan megy át

Nem kulcsonként másolunk, hanem a teljes `Section`-t visszük — így az
ismeretlen kulcsok és a kommentsorok is megmaradnak (round-trip elv). Csak a
`[fejléc]` cserélődik, ha a kép neve közben megváltozott.

## A visszagörgetés a CÉLBAN ÁLLT szekciót is megőrzi (#2511)

Ha a célnéven már állt valami — egy korábbi költöztetés árvája —, azt az
odaút felülírja (`_placed`) vagy kiveszi (`_dropped_stale`). A
visszagörgetés viszont VISSZATESZI (`IniSectionMove.previous`): nem a mi
dolgunk eldönteni, hogy egy bukott mozgatás ürügyén a felhasználó régi
adata is elvesszen. A másolás ága (`IniSectionCopy.previous`) ezt már
eddig is így csinálta; a mozgatásé mostantól ugyanígy — mind a három
esetben: azonos fájlon belüli átnevezésnél, fájlok között, és a félig
megtett (`_HalfApplied`) lépésnél is.

## Ami NEM történik meg

Üres ini-t nem hozunk létre: ha a forrás eredeti-mappájában nincs ini, vagy
nincs benne a fájlhoz tartozó szekció, a célban sem keletkezik semmi. Az
üresre fogyott forrás-ini viszont a helyén marad — a törlése önálló döntés
lenne, és a Picasa is békén hagyja.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from collections.abc import Sequence

from picasapy.ini import IniDocument, Section, load_or_empty, update_document
from picasapy.scanner import PICASA_INI_NAME


class IniSectionsFailed(Exception):
    """Az ini-szekciók átvitele félbeszakadt — a `done` a MÁR megtett lépések.

    Enélkül a hívó csak a fájlállapotból tudna következtetni arra, mit
    kell visszavennie, és a következtetés ELDŐLT: a „nincs már a
    forrásban, tehát elment" próba a soha-nem-is-volt esetet is
    átengedte, és a cél inijéből rántott át egy azonos nevű, ÁRVA
    szekciót (#1448 átnézés, 1. lelet). A visszagörgetés KIZÁRÓLAG ebből
    a listából dolgozhat.
    """

    def __init__(self, done: Sequence[object], cause: BaseException) -> None:
        super().__init__(str(cause))
        self.done = tuple(done)
        self.cause = cause


class _HalfApplied(Exception):
    """A szekció-költözés KÖZEPÉN buktunk el: a célba írás megtörtént, a
    forrásból törlés nem (#1448 2. átnézés, 3. lelet).

    Ez a lépés se nem történt meg, se nem maradt el — és épp ezért TARTOZIK
    a `done`-ba: ha kimarad belőle, a visszagörgetés nem tud róla, és a
    célban FRISSEN ÜLTETETT árva szekció marad, amit a következő, azonos
    nevű eredeti örökölne. Pontosan az a hibaosztály, amit ez a jegy
    megszüntet.
    """

    def __init__(self, cause: BaseException, move: IniSectionMove) -> None:
        super().__init__(str(cause))
        self.cause = cause
        #: A félig megtett lépés, a `previous`-szal EGYÜTT (#2511). A hívó
        #: ezt teszi a `done`-ba: a saját, előre gyártott példányában még
        #: nincs benne, mi állt a célnéven, tehát abból a visszagörgetés a
        #: felhasználó árva szekcióját elnyelné.
        self.move = move


@dataclass(frozen=True)
class IniSectionMove:
    """Egy megtörtént ini-szekció-költözés — a visszagörgetés adata.

    Attributes:
        source_ini: A forrás eredeti-mappájának `.picasa.ini`-je.
        target_ini: A cél eredeti-mappájának `.picasa.ini`-je (rename esetén
            ugyanaz a fájl).
        source_name: A szekció neve a forrásban.
        target_name: A szekció neve a célban.
        previous: Ami a CÉLNÉVEN állt a költözés előtt (`None`, ha semmi) —
            a visszagörgetés ezt teszi vissza (#2511). Nélküle a `_placed`
            (fájlok között) és a `_dropped_stale` (fájlon belül) által
            elnyelt, ÁRVA szekció nyomtalanul eltűnt: a másolás ága
            (`IniSectionCopy.previous`) már megőrizte, a mozgatásé nem.
    """

    source_ini: Path
    target_ini: Path
    source_name: str
    target_name: str
    #: Létezett-e a cél ini-je MÁR a költözés előtt. Ha nem, akkor a
    #: visszagörgetés takaríthatja is (`_remove_if_contentless`) — a
    #: mentésbiztonsági `.bak` párjával együtt, mert mindkettő MOST
    #: keletkezett a felhasználó célmappájában.
    target_ini_existed: bool = True
    previous: Section | None = None


@dataclass(frozen=True)
class IniSectionCopy:
    """Egy megtörtént ini-szekció-MÁSOLÁS — a visszavétel adata (#1450).

    Attributes:
        target_ini: A cél eredeti-mappájának `.picasa.ini`-je.
        target_name: A kiírt szekció neve.
        previous: Ami ezen a néven a másolás ELŐTT állt (`None`, ha semmi).
        target_ini_existed: Létezett-e a cél ini-je MÁR a másolás előtt.
            Ha nem, a visszavétel a MOST keletkezett, üresre fogyott fájlt
            el is takarítja (#2511 2. fele) — enélkül a célmappában egy
            `.picasa.ini`-t tartalmazó eredeti-mappa maradt, amit a
            `originals._remove_if_empty` nem tud törölni, és a legacy
            `Originals/` esetben ez LÁTHATÓ mappa.
    """

    target_ini: Path
    target_name: str
    previous: Section | None
    target_ini_existed: bool = True


def ini_path_for(companion: Path) -> Path:
    """A kísérőfájlt tartalmazó eredeti-mappa `.picasa.ini`-je."""
    return companion.parent / PICASA_INI_NAME


def _renamed_section(section: Section, new_name: str) -> Section:
    """A szekció ÚJ néven — a tartalom (kulcsok, kommentek) érintetlen."""
    if section.name == new_name:
        return section
    return replace(
        section,
        name=new_name,
        header=replace(section.header, text=f"[{new_name}]"),
    )


def _placed(document: IniDocument, section: Section, target_name: str) -> IniDocument:
    """A szekció beillesztése `target_name` néven.

    A célnév ott lehet már foglalt egy KORÁBBI költöztetés árva szekciójától.
    Felülírjuk: a fájl helyét ugyanerre a névre az `originals.py` már
    szabadnak találta (különben el sem indult volna a művelet), tehát a
    célban álló szekció gazdátlan — a MOSTANI fájl adatai az érvényesek."""
    return document.with_section(_renamed_section(section, target_name))


def move_original_ini_sections(
    pairs: Sequence[tuple[Path, Path]],
) -> tuple[IniSectionMove, ...]:
    """A kísérőfájlokhoz tartozó ini-szekciók átvitele.

    Args:
        pairs: `(forrás kísérőfájl, cél kísérőfájl)` párok — a
            `fileops.originals.plan_original_moves` eredményéből.

    Returns:
        A ténylegesen végrehajtott szekció-költözések, a visszagörgetéshez.

    Raises:
        IniSectionsFailed: az `ini/` réteg bármely hibájára. A `done`
            mezője a MÁR átvitt szekciókat sorolja fel — a hívó ezekkel (és
            KIZÁRÓLAG ezekkel) hívja az `undo_original_ini_sections`-t.
    """
    done: list[IniSectionMove] = []
    for source, target in pairs:
        target_ini = ini_path_for(target)
        move = IniSectionMove(
            source_ini=ini_path_for(source),
            target_ini=target_ini,
            source_name=source.name,
            target_name=target.name,
            target_ini_existed=target_ini.exists(),
        )
        try:
            megtett = _apply(move)
        except _HalfApplied as felig:
            # A célba írás MEGTÖRTÉNT — a lépés a `done`-ba tartozik, hogy a
            # visszagörgetés eltakarítsa a frissen ültetett szekciót. A
            # kivétel a `previous`-szal KITÖLTÖTT példányt hozza: a fenti,
            # előre gyártott `move`-ban még nincs benne, mi állt a célnéven.
            raise IniSectionsFailed(
                (*done, felig.move), felig.cause
            ) from felig.cause
        except Exception as error:  # noqa: BLE001 — az ini-réteg többfélét dob
            raise IniSectionsFailed(done, error) from error
        if megtett is not None:
            done.append(megtett)
    return tuple(done)


def undo_original_ini_sections(
    moves: Sequence[IniSectionMove],
) -> tuple[IniSectionMove, ...]:
    """A már átvitt szekciók visszatétele — legjobb szándék szerint.

    Egy elem bukása nem akadályozza a többi visszatételét (ugyanaz az elv,
    mint a fájlok `undo_original_moves`-ánál).

    A célnéven korábban állt, ÁRVA szekció is visszakerül (`previous`,
    #2511) — ugyanaz az elv, amit a másolás ága már követett: nem a mi
    dolgunk eldönteni, hogy egy bukott mozgatás ürügyén a felhasználó régi
    adata is elvesszen.

    Returns:
        Azok a költözések, amelyeket NEM sikerült visszacsinálni.
    """
    stranded: list[IniSectionMove] = []
    for move in reversed(list(moves)):
        try:
            _undo(move)
        except Exception:  # noqa: BLE001 — az ini-réteg többféle hibát dob
            stranded.append(move)
            continue
        if not move.target_ini_existed:
            _remove_if_contentless(move.target_ini)
    return tuple(stranded)


def _undo(move: IniSectionMove) -> None:
    """Egy megtett szekció-költözés visszavétele.

    Nem a `_apply` megfordítása: a visszaútnak a célnéven állt, ÁRVA
    szekciót is vissza kell tennie (`previous`, #2511), amit az odaút
    elnyelt.

    A SORREND adatvesztés-kerülő: előbb a forrásba írunk, csak utána
    rendezzük a célt. Fordítva egy közbeeső hiba a szekciót MINDKÉT
    helyről eltüntetné; így legfeljebb duplán marad meg, ami
    helyreállítható.
    """
    if move.source_ini == move.target_ini:
        # Egyetlen írás: két menetben a szekció egy pillanatra eltűnne
        # (ugyanaz az érv, mint a `_apply` azonos-fájlos ágán).
        update_document(
            move.source_ini,
            lambda document: _undone_in_place(document, move),
            backup=True,
        )
        return

    section = _section_of(move.target_ini, move.target_name)
    if section is not None:
        # KIZÁRÓLAG a célból visszaolvasott szekciót visszük — idegen
        # szekciót a forrásba sosem húzunk be (#1448 átnézés, 1. lelet).
        update_document(
            move.source_ini,
            lambda document, sec=section: _placed(
                document, sec, move.source_name
            ),
            backup=True,
        )
    update_document(
        move.target_ini,
        lambda document: _with_previous(document, move),
        backup=True,
    )


def _undone_in_place(document: IniDocument, move: IniSectionMove) -> IniDocument:
    """Az AZONOS fájlon belüli költözés (átnevezés) visszavétele.

    A szekció visszakapja a régi nevét, és a célnéven állt árva is
    visszakerül. Az árva a fájl VÉGÉRE kerül: az odaút a helyéről kivette
    (`_dropped_stale`), a pozíciója nincs meg — a tartalma viszont bitre
    pontosan megvan, és az a felhasználó adata.
    """
    document = document.with_renamed_section(move.target_name, move.source_name)
    if move.previous is None:
        return document
    return document.with_section(move.previous)


def _with_previous(document: IniDocument, move: IniSectionMove) -> IniDocument:
    """A cél inije a költözés ELŐTTI állapotára: vagy az árva szekció áll
    vissza a célnéven, vagy — ha ott korábban semmi nem volt — a frissen
    ültetett szekció tűnik el."""
    if move.previous is None:
        return document.without_section(move.target_name)
    return document.with_section(move.previous)


def _remove_if_contentless(ini: Path) -> None:
    """A visszagörgetés után ÜRESRE fogyott ini eltakarítása.

    KIZÁRÓLAG olyan fájlra hívható, ami a művelet ELŐTT nem létezett
    (`target_ini_existed`), és akkor is csak akkor törlünk, ha a szekció
    kivétele után SEMMI nem maradt benne — se másik szekció, se komment.

    A VISSZAÁLLÍTOTT ÁRVÁT ez KÉTSZERESEN sem törli (#2511): egyrészt egy
    nem létező fájlban nem állhatott korábban semmi, tehát ott a
    `previous` szükségképpen `None`; másrészt ha mégis visszakerülne egy
    szekció, a fájl nem lenne üres, és az alábbi próba nem engedné el.
    A mentésbiztonsági `.bak` párja is megy: az is MOST keletkezett, és
    egyedül maradva ugyanúgy életben tartaná az eredeti-mappát.

    Enélkül a célmappában egy magára maradt `.picasa.ini` tartaná életben
    az eredeti-mappát (a `rmdir` csak ÜRES könyvtárat töröl), miközben a
    felhasználónak azt mondjuk: semmi nem változott."""
    if not ini.is_file():
        return
    try:
        if load_or_empty(ini).serialize().strip():
            return
        ini.unlink()
        ini.with_name(ini.name + ".bak").unlink(missing_ok=True)
    except OSError:
        pass


def copy_original_ini_sections(
    pairs: Sequence[tuple[Path, Path]],
) -> tuple[IniSectionCopy, ...]:
    """Mint a `move_original_ini_sections`, de a forrást MEGTARTJA (#1450).

    A másolt kép megőrzött eredetije a célban ugyanazokat a beállításokat
    kapja meg, miközben a forrás képe és eredetije érintetlen marad.

    Returns:
        A ténylegesen kiírt szekciók — mindegyik megjegyzi, MI állt a
        helyén korábban, hogy a hibaágon pontosan visszaállítható legyen.

    Raises:
        IniSectionsFailed: az `ini/` réteg hibáira; a `done` mezője a már
            kiírt szekciókat sorolja fel. Enélkül egy középen elszálló
            másolás FRISSEN ÜLTETETT árva szekciókat hagyott a cél
            inijében, amiket a következő, azonos nevű eredeti örökölt
            volna (#1450 átnézés, 5. lelet) — a hívó `_discard_copies`
            ugyanis csak a FÁJLOKAT törli.
    """
    done: list[IniSectionCopy] = []
    for source, target in pairs:
        section = _section_of(ini_path_for(source), source.name)
        if section is None:
            continue
        target_ini = ini_path_for(target)
        record = IniSectionCopy(
            target_ini=target_ini,
            target_name=target.name,
            previous=_section_of(target_ini, target.name),
            target_ini_existed=target_ini.exists(),
        )
        try:
            update_document(
                target_ini,
                lambda document, s=section, n=target.name: _placed(document, s, n),
                backup=True,
            )
        except Exception as error:  # noqa: BLE001 — az ini-réteg többfélét dob
            raise IniSectionsFailed(done, error) from error
        done.append(record)
    return tuple(done)


def undo_copied_ini_sections(
    copies: Sequence[IniSectionCopy],
) -> tuple[IniSectionCopy, ...]:
    """A félbemaradt MÁSOLÁS ini-nyomainak visszavétele — legjobb szándék
    szerint.

    A célnéven korábban álló (árva) szekció visszakerül, ha volt ilyen; ha
    nem volt, a frissen kiírt szekció eltűnik. Az árva megtartása
    szándékos: nem a mi dolgunk eldönteni, hogy egy bukott másolás ürügyén
    a felhasználó régi adata is elvesszen.

    Returns:
        Amit NEM sikerült visszavenni.
    """
    stranded: list[IniSectionCopy] = []
    for copy in reversed(list(copies)):
        try:
            update_document(
                copy.target_ini,
                lambda document, c=copy: (
                    document.with_section(c.previous)
                    if c.previous is not None
                    else document.without_section(c.target_name)
                ),
                backup=True,
            )
        except Exception:  # noqa: BLE001 — az ini-réteg többféle hibát dob
            stranded.append(copy)
            continue
        if not copy.target_ini_existed:
            # #2511 2. fele: enélkül a MOST keletkezett, üresre fogyott
            # `.picasa.ini` (és a `.bak` párja) életben tartotta a
            # célmappa eredeti-mappáját — a `_remove_if_empty` csak ÜRES
            # könyvtárat töröl —, miközben az üzenet azt mondja, a
            # másolásból semmi nem maradt.
            _remove_if_contentless(copy.target_ini)
    return tuple(stranded)


def remove_original_ini_sections(companions: Sequence[Path]) -> int:
    """A kísérőfájlokhoz tartozó szekciók törlése (#1451: törléskor).

    Ha a fájl elment (lomtárba vagy véglegesen), a szekciója sem maradhat
    ott: a következő, azonos nevű eredeti örökölné a beállításait.

    Returns:
        A törölt szekciók száma.
    """
    count = 0
    for companion in companions:
        ini = ini_path_for(companion)
        if _section_of(ini, companion.name) is None:
            continue
        update_document(
            ini,
            lambda document, n=companion.name: document.without_section(n),
            backup=True,
        )
        count += 1
    return count


def _section_of(ini: Path, name: str) -> Section | None:
    """A szekció, vagy `None`, ha nincs ini vagy nincs benne ilyen nevű."""
    if not ini.is_file():
        return None
    return load_or_empty(ini).section(name)


def _stale_at(document: IniDocument, move: IniSectionMove) -> Section | None:
    """A célnéven álló, ÁRVA szekció — AZONOS fájlon belüli költözésnél.

    A célnév helyét a fájlok szintjén az `originals.py` már szabadnak
    találta, tehát az ott álló szekció egy korábbi költöztetés árvája — a
    MOSTANI fájl adatai az érvényesek. A magára mutató találat
    (betűzés-javítás, `a.jpg` → `A.JPG`) nem árva: az MAGA a költöző
    szekció, azt békén hagyjuk.

    Ugyanez a próba dönti el, mit KELL a visszagörgetésnek visszatennie
    (#2511): a két helyen külön leírt feltétel némán szétcsúszna, és az
    árva vagy elveszne, vagy megkettőződne.
    """
    allo = document.section(move.target_name)
    if allo is None or allo is document.section(move.source_name):
        return None
    return allo


def _dropped_stale(document: IniDocument, move: IniSectionMove) -> IniDocument:
    """A célnéven álló, ÁRVA szekció eltávolítása az átnevezés elől.

    A `with_renamed_section` ütközésre `ValueError`-t dob (helyesen: néma
    adatvesztés lenne). Amit itt kiveszünk, azt a visszagörgetés az
    `IniSectionMove.previous`-ból teszi vissza."""
    if _stale_at(document, move) is None:
        return document
    return document.without_section(move.target_name)


def _apply(move: IniSectionMove) -> IniSectionMove | None:
    """Egy szekció áthelyezése. `None`, ha nem volt mit vinni.

    Az azonos fájlon belüli eset (átnevezés ugyanabban a mappában) egyetlen
    `update_document`-tel megy: két menetben a szekció egy pillanatra
    eltűnne, és egy közbeeső hiba után nyomtalanul elveszne.

    Returns:
        A MEGTETT lépés, a `previous`-szal kitöltve — ez a visszagörgetés
        adata. A `previous` a fájl beolvasott állapotából jön, nem az
        `update_document` újrajátszott dokumentumából: egy párhuzamos író
        közbeírását itt ugyanúgy nem látjuk, mint a másolás ágán (#1450).
    """
    if not move.source_ini.is_file():
        return None
    source_document = load_or_empty(move.source_ini)
    section = source_document.section(move.source_name)
    if section is None:
        return None

    if move.source_ini == move.target_ini:
        # `with_renamed_section`: a szekció a HELYÉN marad (csak a fejléc
        # cserélődik) — a `without_section` + `with_section` páros a fájl
        # végére dobná, és a kétirányú round-trip diff feleslegesen nőne.
        megtett = replace(move, previous=_stale_at(source_document, move))
        update_document(
            move.source_ini,
            lambda document: _dropped_stale(document, move).with_renamed_section(
                move.source_name, move.target_name
            ),
            backup=True,
        )
        return megtett

    megtett = replace(
        move, previous=_section_of(move.target_ini, move.target_name)
    )
    update_document(
        move.target_ini,
        lambda document: _placed(document, section, move.target_name),
        backup=True,
    )
    try:
        update_document(
            move.source_ini,
            lambda document: document.without_section(move.source_name),
            backup=True,
        )
    except Exception as error:  # noqa: BLE001 — az ini-réteg többfélét dob
        # A két fázis közt buktunk: a szekció MOST mindkét ini-ben ott van.
        # A hívónak tudnia kell róla, különben a célban frissen ültetett
        # árva marad (#1448 2. átnézés, 3. lelet). A `previous`-t is
        # átadjuk, különben a visszagörgetés a felhasználó árváját a
        # frissen ültetettel EGYÜTT törölné (#2511).
        raise _HalfApplied(error, megtett) from error
    return megtett


__all__ = [
    "IniSectionCopy",
    "IniSectionMove",
    "IniSectionsFailed",
    "copy_original_ini_sections",
    "ini_path_for",
    "move_original_ini_sections",
    "remove_original_ini_sections",
    "undo_copied_ini_sections",
    "undo_original_ini_sections",
]
