"""A megőrzött eredetik MÁSOLÁSA a kép mellé (#1450).

A `picasapy.fileops.originals` szétbontott része: a `move_preserved_originals`
nem-destruktív párja. A forrás mindenestül a helyén marad; a félbemaradt
másolatot a `_discard_copies` takarítja el.
"""

from __future__ import annotations

import shutil
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from picasapy.fileops.originals_cache import (
    _cache_added,
    _cache_removed,
    _cache_unknown,
)
from picasapy.fileops.originals_move import _remove_if_empty
from picasapy.fileops.originals_plan import (
    OriginalMove,
    _reject_unsafe_targets,
    plan_original_moves,
)

if TYPE_CHECKING:  # a futásidejű import késleltetett (ld. `_copy_ini_sections`)
    from picasapy.fileops.original_ini import IniSectionCopy

#: A `shutil.copy2` MODULSZINTŰ fogantyúja (#1450) - ugyanaz a gondolat.
#:
#: `copy2`, nem `copy`: a megőrzött eredeti mtime-ja a WYSIWYG dátum
#: forrása, és a Picasa a rekord érvényességét is a `moddate`-hez méri.
_copy = shutil.copy2


def _copied(source: Path, target: Path) -> None:
    """A kísérőfájl másolása + a gyorstár könyvelése (#1452)."""
    try:
        _copy(str(source), str(target))
    except BaseException:
        _cache_unknown(target.parent)
        raise
    _cache_added(target.parent, target.name)


def copy_preserved_originals(
    source_photo: str | Path, target_photo: str | Path
) -> tuple[OriginalMove, ...]:
    """A megőrzött eredeti (és a pillanatképek) MÁSOLÁSA a kép mellé (#1450).

    A `move_preserved_originals` nem-destruktív párja: a forrás mindenestül
    a helyén marad. A `copy_photo` hívja, közvetlenül a képfájl másolása
    után.

    Miért kell: enélkül a másolt kép az új helyen nem tudott visszaállni -
    a „Vissza az eredetihez" nem talált semmit, a szerkesztés a példányon
    véglegesnek látszott. Az „After copying: delete" import-módban ez
    ténylegesen adatvesztés volt, mert ott a forrás is törlődik.

    Args:
        source_photo: A másolandó kép jelenlegi útja.
        target_photo: A MÁR ELKÉSZÜLT másolat útja (az ütközés-feloldás
            utáni, végleges néven - a kísérők ezt a nevet veszik fel).

    Returns:
        A ténylegesen elkészült másolatok.

    Raises:
        FileExistsError: ha valamelyik célhely foglalt - ilyenkor semmi nem
            készült el.
        OSError: fájlrendszer-hiba esetén. A már elkészült másolatokat
            eltakarítjuk, hogy ne maradjon fél eredményű célmappa.
    """
    moves = plan_original_moves(source_photo, target_photo)
    if not moves:
        return ()
    _reject_unsafe_targets(moves)

    done: list[OriginalMove] = []
    for move in moves:
        try:
            move.target.parent.mkdir(parents=True, exist_ok=True)
            _copied(move.source, move.target)
        except OSError as error:
            _discard_copies(done)
            _remove_if_empty(move.target.parent)
            raise type(error)(
                f"A képhez megőrzött eredeti változatot nem sikerült ide "
                f"másolni: {move.target} ({error}). A forrás kép és a "
                f"megőrzött változatai érintetlenek."
            ) from error
        done.append(move)

    from picasapy.fileops.original_ini import (
        IniSectionsFailed,
        undo_copied_ini_sections,
    )

    try:
        _copy_ini_sections(done)
    except Exception as error:  # noqa: BLE001 - az ini-réteg többféle hibát dob
        # A `_discard_copies` csak a FÁJLOKAT törli. A már kiírt szekciókat
        # külön kell visszavenni, különben FRISSEN ÜLTETETT árvák maradnak a
        # cél inijében, amiket a következő, azonos nevű eredeti örökölne
        # (#1450 átnézés, 5. lelet).
        if isinstance(error, IniSectionsFailed):
            undo_copied_ini_sections(error.done)
        _discard_copies(done)
        raise OSError(
            f"A képhez megőrzött eredeti beállításait nem sikerült átmásolni "
            f"({error}). A forrás kép és a megőrzött változatai érintetlenek."
        ) from error
    return tuple(done)


def _discard_copies(moves: Sequence[OriginalMove]) -> None:
    """A félbemaradt másolás eltakarítása - csak a MOST készült példányokat
    törli, a forráshoz nem nyúl."""
    for move in reversed(list(moves)):
        try:
            move.target.unlink(missing_ok=True)
        except OSError:
            _cache_unknown(move.target.parent)
            continue
        _cache_removed(move.target.parent, move.target.name)
        _remove_if_empty(move.target.parent)


def _copy_ini_sections(
    moves: Sequence[OriginalMove],
) -> tuple["IniSectionCopy", ...]:
    """A kísérőfájlok ini-szekcióinak MÁSOLÁSA (#1450) - a forrás marad.

    Returns:
        A kiírt szekciók, a visszavételükhöz szükséges előzménnyel együtt.
    """
    from picasapy.fileops.original_ini import copy_original_ini_sections

    return copy_original_ini_sections(
        tuple((move.source, move.target) for move in moves)
    )
