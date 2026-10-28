"""A megőrzött eredetik ÁTHELYEZÉSE, és a sikertelen költözés VISSZAGÖRGETÉSE.

A `picasapy.fileops.originals` szétbontott része: a fájlmozgatás (#1430), az
ini-szekciók utólagos átvitele (#1448), a visszagörgetés, és az
`originals_follow` burkoló, amely a kép saját mozgatását köti a kísérőkhöz.
A sorrend és a visszagörgetés elvei a `originals` modul docstringjében vannak.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from picasapy.fileops.originals_cache import (
    _cache_added,
    _cache_removed,
    _cache_unknown,
)
from picasapy.fileops.originals_messages import (
    _ini_stranded_warning,
    _reassurance,
    _stranded_warning,
)
from picasapy.fileops.originals_names import _snapshot_dir_name
from picasapy.fileops.originals_plan import (
    OriginalMove,
    _reject_unsafe_targets,
    plan_original_moves,
)
from picasapy.fileops.safe_move import safe_move

if TYPE_CHECKING:  # a futásidejű import késleltetett (ld. `_move_ini_sections`)
    from picasapy.fileops.original_ini import IniSectionMove

#: A `shutil.move` MODULSZINTŰ fogantyúja (#1375) - a teszt EZT cserélje.
#:
#: A `"picasapy.fileops.originals.shutil.move"` sztringes rögzítés a GLOBÁLIS
#: `shutil`-t írja át, tehát a „bukjon el a mozgatás" szimuláció a teszt
#: minden más mozgatását is elrontja - a takarítást is.
_move = safe_move  # #998: bukáskor nem marad másolat


def _moved(source: Path, target: Path) -> None:
    """A kísérőfájl mozgatása + a gyorstár könyvelése (#1452)."""
    try:
        _move(str(source), str(target))
    except BaseException:
        # Nem tudjuk, meddig jutott - a két mappa tartalma bizonytalan.
        _cache_unknown(source.parent)
        _cache_unknown(target.parent)
        raise
    _cache_removed(source.parent, source.name)
    _cache_added(target.parent, target.name)


def move_preserved_originals(
    source_photo: str | Path, target_photo: str | Path
) -> tuple[OriginalMove, ...]:
    """A megőrzött eredeti (és a pillanatképek) átköltöztetése.

    A képet MAGÁT nem mozgatja - azt a hívó (`rename_photo`, `move_photo`)
    teszi, közvetlenül utána.

    Args:
        source_photo: A kép jelenlegi, teljes elérési útja.
        target_photo: A kép leendő, teljes elérési útja.

    Returns:
        A ténylegesen végrehajtott mozgatások (a visszagörgetéshez).

    Raises:
        FileExistsError: ha valamelyik célhely foglalt - ilyenkor semmi nem
            mozdult el.
        OSError: ha a másolás/mozgatás fájlrendszer-hibába futott. A már
            elmozdított kísérőket ilyenkor visszatesszük, és a hiba üzenete
            megmondja, hol keresse a felhasználó a fájljait.
    """
    return _move_preserved_originals(source_photo, target_photo)[0]


def _move_preserved_originals(
    source_photo: str | Path, target_photo: str | Path
) -> tuple[tuple[OriginalMove, ...], tuple["IniSectionMove", ...]]:
    """A `move_preserved_originals` MAGJA - a megtett ini-lépéseket is adja.

    A visszagörgetés (`originals_follow`) ezekből dolgozik, és KIZÁRÓLAG
    ezekből: a fájlállapotból következtető őr a soha-nem-is-volt szekciót
    „elmentnek" hitte, és a cél inijéből rántott át egy azonos nevű, ÁRVA
    szekciót (#1448 átnézés, 1. lelet).

    Returns:
        `(megtett fájlmozgatások, megtett ini-szekció-költözések)`.
    """
    moves = plan_original_moves(source_photo, target_photo)
    if not moves:
        return (), ()
    _reject_unsafe_targets(moves)

    done: list[OriginalMove] = []
    for move in moves:
        try:
            move.target.parent.mkdir(parents=True, exist_ok=True)
            _moved(move.source, move.target)
        except OSError as error:
            # Az ini-fázis el sem indult, tehát nincs szekció-lépés, amit
            # vissza kellene venni.
            stranded = undo_original_moves(tuple(done))
            # A célmappa itt akkor is takarítandó, ha a `done` ÜRES (mindjárt
            # az első kísérőnél buktunk): a `mkdir` már lefutott, és egy üres,
            # a legacy esetben LÁTHATÓ `Originals/` maradna a felhasználó
            # célmappájában - miközben az üzenet azt mondja, semmi nem
            # változott.
            _remove_if_empty(move.target.parent)
            raise type(error)(
                f"A képhez megőrzött eredeti változatot nem sikerült átvinni ide: "
                f"{move.target} ({error})."
                f"{_stranded_warning(stranded) or _reassurance()}"
            ) from error
        done.append(move)

    # #1448: a fájlok után a `.picasa.ini` szekcióik is átköltöznek. Azért
    # UTÓLAG, mert így az ini-írás a már véglegesített fájlállapotot
    # könyveli; ha viszont ELBUKIK, mindent visszagörgetünk - egy fél
    # költözés (fájl az új helyen, szekció a régiben) pont az a néma
    # eltérés, amit ez a jegy megszüntet.
    from picasapy.fileops.original_ini import IniSectionsFailed

    try:
        ini_done = _move_ini_sections(done)
    except Exception as error:  # noqa: BLE001 - az ini-réteg többféle hibát dob
        # A MÁR átvitt szekciókat a kivétel hozza magával - a fájlállapotból
        # kikövetkeztetni őket NEM lehet (#1448 átnézés, 1. lelet).
        ini_stranded = _undo_ini_sections(
            error.done if isinstance(error, IniSectionsFailed) else ()
        )
        stranded = undo_original_moves(tuple(done))
        raise OSError(
            f"A képhez megőrzött eredeti beállításait nem sikerült átvinni "
            f"({error})."
            f"{_stranded_warning(stranded)}"
            f"{_ini_stranded_warning(ini_stranded)}"
            f"{_reassurance() if not stranded and not ini_stranded else ''}"
        ) from error
    return tuple(done), ini_done


def _move_ini_sections(
    moves: Sequence[OriginalMove],
) -> tuple["IniSectionMove", ...]:
    """A kísérőfájlok ini-szekcióinak átvitele (#1448).

    Késleltetett import: a `original_ini` az `ini/` csomagot húzza be, amire
    a puszta fájlmozgatás nem szorul rá.

    Returns:
        A ténylegesen megtett szekció-költözések - a visszagörgetés
        EGYETLEN forrása. Korábban ez az érték a padlóra esett, és a
        visszagörgetés a fájlállapotból következtetett; ld. az
        `_undo_ini_sections` docstringjét.
    """
    from picasapy.fileops.original_ini import move_original_ini_sections

    return move_original_ini_sections(
        tuple((move.source, move.target) for move in moves)
    )


def _undo_ini_sections(
    moves: Sequence["IniSectionMove"],
) -> tuple["IniSectionMove", ...]:
    """A MEGTETT ini-szekció-költözések visszavitele (#1448).

    Kizárólag a `_move_ini_sections` által visszaadott listából dolgozik.
    A korábbi változat a fájlállapotból következtetett („ha a szekció már
    nincs a forrásban, akkor elment"), ami a gyakori esetet - hogy soha nem
    is volt ott szekció - átengedte, és a CÉL inijéből rántott át egy
    azonos nevű, ÁRVA szekciót a forrásba (#1448 átnézés, 1. lelet).

    Legjobb szándék szerint dolgozik: a visszatétel bukása nem akadályozhatja
    meg a FÁJLOK visszagörgetését - az a fontosabb, azon múlik a kép
    visszaútja.

    Returns:
        Amit NEM sikerült visszatenni. Ez az érték korábban a padlóra esett,
        és a felhasználó a „minden a helyén maradt" mondatot kapta, miközben
        a beállításai a célmappában ragadtak (#1448 2. átnézés, 3. lelet).
    """
    if not moves:
        return ()
    from picasapy.fileops.original_ini import undo_original_ini_sections

    return undo_original_ini_sections(tuple(moves))


def undo_original_moves(
    moves: Sequence[OriginalMove],
) -> tuple[OriginalMove, ...]:
    """A már elmozdított kísérőfájlok visszatétele a helyükre.

    KIZÁRÓLAG a fájlokkal foglalkozik. Az ini-szekciók visszavitele nem
    következtethető ki a fájlok listájából (#1448 átnézés, 1. lelet), ezért
    azt a hívó végzi, a `_move_ini_sections` visszaadott listájából - a
    fájlok visszagörgetése ELŐTT, mert utána a célmappa már nem létezik.

    Legjobb szándék szerint dolgozik: egy fájl bukása nem akadályozza a
    többi visszatételét.

    Returns:
        Azok a mozgatások, amelyeket NEM sikerült visszacsinálni - a hívó
        ezeket nevezi meg a hibaüzenetében.
    """
    stranded: list[OriginalMove] = []
    for move in reversed(list(moves)):
        try:
            move.source.parent.mkdir(parents=True, exist_ok=True)
            _moved(move.target, move.source)
        except OSError:
            stranded.append(move)
            continue
        # A célmappában közben létrehozott eredeti-mappa ne maradjon ott
        # üresen - a látható `Originals` egy üres, magyarázat nélküli
        # mappaként tűnne fel a felhasználó fájlkezelőjében.
        _remove_if_empty(move.target.parent)
    return tuple(stranded)


def _remove_if_empty(directory: Path) -> None:
    """Üres eredeti-mappa eltakarítása. Az `rmdir` csak ÜRES könyvtárat
    töröl, tehát semmit nem vihet magával.

    A CSAK `.picasa.ini`-t tartalmazó mappát SZÁNDÉKOSAN nem takarítja el
    (#2511): innen nem látszik, hogy azt az ini-t mi hoztuk-e létre, vagy a
    felhasználóé (esetleg a párhuzamosan futó Picasáé) volt már a művelet
    előtt. A törléshez szükséges tudás egy réteggel feljebb van, és ott is
    marad: a `original_ini._remove_if_contentless` KIZÁRÓLAG azt az ini-t
    törli, amelyik a művelet előtt nem létezett (`target_ini_existed`) és
    üresre is fogyott - a `.bak` párjával együtt. Mivel a hívási sorrend
    mindenhol „előbb az ini-fázis visszavétele, utána a fájloké"
    (`originals_follow`, `_move_preserved_originals`, `_discard_copies`
    előtt az `undo_copied_ini_sections`), mire ide érünk, az általunk
    gyártott ini már nincs ott, és a mappa valóban üres.

    Ami marad, az a felhasználó adata: azt a `_ini_stranded_warning`
    mondja ki, nem törli.

    #2512: ha a most eltakarított mappa a `.picasapy-snapshots`
    alkönyvtár volt, a SZÜLŐ eredeti-mappát is megkíséreljük - különben egy
    visszagörgetett költözés után egy üres `.picasaoriginals` (a legacy
    ágon a LÁTHATÓ `Originals`) maradna a felhasználó célmappájában,
    miközben az üzenete azt mondja, semmi nem változott."""
    snapshot_dir = directory.name == _snapshot_dir_name()
    parent = directory.parent
    try:
        directory.rmdir()
    except OSError:
        return
    # A mappa megszűnt: a róla tárolt lista már semmit nem jelent. Nem
    # „üresre" javítjuk, hanem ELFELEJTJÜK - az elfelejtés sosem ad rossz
    # választ, legfeljebb egy listázásba kerül, és nem kell hozzá
    # feltevés arról, mi volt még bent (a `.picasa.ini` például nem a mi
    # könyvelésünk).
    _cache_unknown(directory)
    if snapshot_dir:
        _remove_if_empty(parent)


@contextmanager
def originals_follow(
    source_photo: str | Path, target_photo: str | Path
) -> Iterator[None]:
    """A kép mozgatását a megőrzött eredeti költöztetésébe csomagolja.

    Előbb a kísérőfájlok költöznek, majd lefut a blokk (a kép tényleges
    átnevezése/mozgatása). Ha a blokk fájlrendszer-hibával bukik, a kísérőket
    visszagörgetjük, hogy a kép a régi nevén/helyén se veszítse el a
    visszaútját.

    Használat::

        with originals_follow(path, target):
            path.rename(target)
    """
    moved, ini_moved = _move_preserved_originals(source_photo, target_photo)
    try:
        yield
    except OSError as error:
        # Előbb a szekciók, csak utána a fájlok: fordítva a szekció-
        # visszavitel egy már megszűnt célmappa inijéből olvasna.
        ini_stranded = _undo_ini_sections(ini_moved)
        stranded = undo_original_moves(moved)
        warning = _stranded_warning(stranded) + _ini_stranded_warning(ini_stranded)
        if warning:
            # A típus megőrzése kötelező: a hívók (FileOpsController,
            # PhotoOpsController) kivételosztály szerint szűrnek, egy új
            # osztály némán kicsúszna a szűrőjükön.
            raise type(error)(f"{error}{warning}") from error
        raise
