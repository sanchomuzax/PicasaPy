"""Áthelyezés, ami bukáskor NEM hagy másolatot (#998).

## A baj, amit megszüntet

A `shutil.move` először `os.rename`-t próbál, és ha az elbukik — **más
fájlrendszer, vagy zárolt/nem törölhető forrás** —, átvált
`copy2 + unlink`-re. Ha ekkor az `unlink` bukik, a **másolat már ott van** a
célban, a forrás pedig megmarad: a fájl **megkettőződik**, és a hibaüzenet
erről nem szól.

Mérve (2026-09-09, Linux, írásvédett forrásmappa — POSIX-on a törléshez a
MAPPÁRA kell írásjog): a `move_photo` `PermissionError`-t adott, a forrás
megvolt, ÉS a célban ott maradt egy másolat.

Windowson ugyanez az ág fut a **nyitva tartott** fájlra (ott az `os.rename`
zárolt fájlra bukik) — ez a #998 windowsos leletének
(`assert not copy_path.exists()` a duplikátum-feloldás után)
platformfüggetlen magyarázata. Duplikátum-feloldásnál különösen kellemetlen:
a felhasználó épp duplikátumot akart megszüntetni, és kapott egy újat.

## A szerződés

- sikeres áthelyezés: a forrás eltűnik, a cél megvan;
- bukás: **kivétel** (az EREDETI típusával, mert a hívók osztály szerint
  szűrnek), a forrás megvan, és a célban **nincs** félkész másolat;
- a más-fájlrendszeres áthelyezés jogos `copy2 + unlink` útja változatlan.

⚠️ **Csak FÁJLRA.** Könyvtár áthelyezésénél a `shutil.move` `copytree` +
`rmtree`-t végez; ott a visszagörgetés más probléma (részlegesen átmásolt fa),
ezért a `move_folder.py` szándékosan nem ezt használja — ld. #2785.
"""

from __future__ import annotations

import os
import shutil
import tempfile

#: MODULSZINTŰ fogantyúk (#1375) — a teszt EZEKET cserélje, ne a globális
#: `os`/`shutil` tagjait: azok minden más modulra is átszivárognának.
_rename = os.rename
_copy = shutil.copy2
_unlink = os.unlink


def _link(source: str, target: str) -> None:
    """Hardlink létrehozása a forráskövetés nélküli, atomikus célfoglaláshoz."""
    os.link(source, target, follow_symlinks=False)


def safe_move(source: str, target: str) -> None:
    """A `source` fájl áthelyezése a `target` ÚTVONALRA, másolat-mentesen.

    A `target` teljes cél-útvonal (nem mappa), a `shutil.move`-tól eltérően —
    a hívóink mindegyike így hívja. A cél nem létezhet: ezt atomikus,
    kizárólagos létrehozással tartjuk be, nem előzetes `exists()` vizsgálattal.

    A POSIX `rename` lecserélheti a már létező célfájlt, ezért a gyors út
    atomikus hardlink-létrehozás és forrástörlés. Windowson a `rename`
    eleve nem cserél létező célt, így ott megmarad a natív átnevezés. Ha a
    fájlrendszer-korlát miatt ezek nem működnek, másolatot készítünk egyedi,
    célmappán belüli ideiglenes fájlba, majd a célra kizárólagos hardlinket
    teszünk. Olyan fájlrendszeren, amely hardlinket sem támogat, a cél
    `O_EXCL` megnyitással készül el.
    """

    if os.name == "nt":
        try:
            _rename(source, target)
            return
        except FileExistsError:
            raise
        except OSError:
            pass  # más fájlrendszer vagy zárolt forrás — másolunk
    else:
        try:
            _link(source, target)
        except FileExistsError:
            raise
        except OSError:
            pass  # más fájlrendszer vagy nem támogatott hardlink — másolunk
        else:
            try:
                _unlink(source)
            except OSError:
                _rollback_target(target)
                raise
            return

    _copy_fallback(source, target)


def _copy_fallback(source: str, target: str) -> None:
    """Másolás után csak kizárólagos művelettel teszi véglegessé a célt."""
    cel_mappa = os.path.dirname(os.path.abspath(target))
    fd, ideiglenes = tempfile.mkstemp(
        prefix=f".{os.path.basename(target)}.", suffix=".safe-move", dir=cel_mappa
    )
    os.close(fd)
    try:
        _copy(source, ideiglenes)
        try:
            _link(ideiglenes, target)
        except OSError:
            # A cél létezhetett már, vagy a fájlrendszer tilthatja a
            # hardlinket. Az O_EXCL út az előbbi esetben is hibával áll meg,
            # és sosem nyitja meg írásra a meglévő fájlt.
            _copy_exclusively(ideiglenes, target)

        try:
            _unlink(source)
        except OSError:
            _rollback_target(target)
            raise
    finally:
        try:
            os.unlink(ideiglenes)
        except OSError:
            pass


def _copy_exclusively(source: str, target: str) -> None:
    """Másolat célfájlba úgy, hogy létező útvonalat ne lehessen felülírni."""
    fd = os.open(
        target,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0),
        0o666,
    )
    try:
        with os.fdopen(fd, "wb") as cel:
            with open(source, "rb") as forras:
                shutil.copyfileobj(forras, cel)
            cel.flush()
        shutil.copystat(source, target)
    except BaseException:
        try:
            _unlink(target)
        except OSError:
            pass
        raise


def _rollback_target(target: str) -> None:
    """A saját, már véglegesített cél takarítása; az eredeti hibát megtartja."""
    try:
        _unlink(target)
    except OSError:
        # A takarítás bukását nem tesszük az eredeti hiba helyére.
        pass


__all__ = ["safe_move"]
