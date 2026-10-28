"""A kép költözéséhez tartozó kísérőfájl-mozgatások TERVE (végrehajtás nélkül).

A `picasapy.fileops.originals` szétbontott része: a `OriginalMove` párok
összeállítása és az ütközés-ellenőrzés, mielőtt bármi elmozdulna. A tényleges
mozgatás (`originals_move`) és a másolás (`originals_copy`) ezt használja.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from picasapy.fileops.originals_messages import _occupied_message
from picasapy.fileops.originals_names import (
    _originals_dir_names,
    _snapshot_dir_name,
    snapshot_numbers,
)


@dataclass(frozen=True)
class OriginalMove:
    """Egy kísérőfájl (megőrzött eredeti vagy pillanatkép) tervezett útja.

    Attributes:
        source: A kísérőfájl jelenlegi helye.
        target: Ahová a kép költözésével kerülnie kell.
    """

    source: Path
    target: Path


def plan_original_moves(
    source_photo: str | Path, target_photo: str | Path
) -> tuple[OriginalMove, ...]:
    """A kép költözéséhez tartozó kísérőfájl-mozgatások - végrehajtás nélkül.

    Args:
        source_photo: A kép jelenlegi, teljes elérési útja.
        target_photo: A kép leendő, teljes elérési útja (átnevezésnél
            ugyanaz a mappa, mozgatásnál a célmappa).

    Returns:
        A mozgatandó párok; üres, ha a képhez nincs megőrzött eredeti.
    """
    source_photo = Path(source_photo)
    target_photo = Path(target_photo)
    moves: list[OriginalMove] = []
    for dir_name in _originals_dir_names():
        source_dir = source_photo.parent / dir_name
        if not source_dir.is_dir():
            continue
        target_dir = target_photo.parent / dir_name
        backup = source_dir / source_photo.name
        if backup.is_file():
            moves.append(OriginalMove(backup, target_dir / target_photo.name))
        for _, sorszam, snapshot in sorted(
            snapshot_numbers(source_dir, source_photo)
        ):
            # A sorszám SZÖVEGÉT visszük át, nem a számértékét: `a.01.jpg`
            # így `b.01.jpg` lesz, nem `b.1.jpg`. Az átszámozás összeejtené
            # az `a.1.jpg`-t és az `a.01.jpg`-t ugyanarra a célnévre, és a
            # `shutil.move` POSIX-on NÉMÁN felülírja a másikat.
            new_name = f"{target_photo.stem}.{sorszam}{target_photo.suffix}"
            # #2512: a pillanatkép a SAJÁT helyén marad - ami a
            # `.picasapy-snapshots`-ból indul, oda érkezik; ami a régi,
            # közös helyről, az oda. Ugyanaz a gondolat, mint a mappanévnél
            # (ld. a modul „A mappanév a költözéskor NEM változik"
            # szakaszát): a régi helyen álló példány a párhuzamosan futó
            # windowsos Picasáé is lehet, azt nem rántjuk be a mi
            # névterünkbe.
            moves.append(
                OriginalMove(
                    snapshot, _target_dir_for(snapshot, target_dir) / new_name
                )
            )
    return tuple(moves)


def _target_dir_for(snapshot: Path, target_dir: Path) -> Path:
    """Egy pillanatkép célkönyvtára: a forrásáéval AZONOS szintű (#2512)."""
    if snapshot.parent.name == _snapshot_dir_name():
        return target_dir / _snapshot_dir_name()
    return target_dir


def _reject_unsafe_targets(moves: Sequence[OriginalMove]) -> None:
    """A terv ellenőrzése MIELŐTT bármi elmozdulna: felülírni sosem írunk
    felül, se meglévő fájlt, se a saját tervünk másik elemét.

    Raises:
        FileExistsError: emberi nyelvű üzenettel arról, MI van útban.
    """
    latott: dict[Path, OriginalMove] = {}
    for move in moves:
        elozo = latott.get(move.target)
        if elozo is not None:
            # A `plan_original_moves` a sorszámot szó szerint viszi át, ezért
            # ez ma nem fordulhat elő. Az őr mégis marad: ha valaha
            # visszakerülne az átszámozás, ez a sor állítja meg - nem a
            # felhasználó adatvesztése.
            raise FileExistsError(
                f"A képhez két megőrzött változat is ugyanarra a névre "
                f"költözne ({elozo.source.name} és {move.source.name} → "
                f"{move.target.name}), így az egyik felülírná a másikat. "
                f"Semmi nem változott: a kép és a megőrzött változatai is a "
                f"régi helyükön maradtak."
            )
        latott[move.target] = move
        if move.target.exists():
            raise FileExistsError(_occupied_message(move))
