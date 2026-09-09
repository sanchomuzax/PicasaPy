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

#: MODULSZINTŰ fogantyúk (#1375) — a teszt EZEKET cserélje, ne a globális
#: `os`/`shutil` tagjait: azok minden más modulra is átszivárognának.
_rename = os.rename
_copy = shutil.copy2
_unlink = os.unlink


def safe_move(source: str, target: str) -> None:
    """A `source` fájl áthelyezése a `target` ÚTVONALRA, másolat-mentesen.

    A `target` teljes cél-útvonal (nem mappa), a `shutil.move`-tól eltérően —
    a hívóink mindegyike így hívja.
    """
    try:
        _rename(source, target)
        return
    except OSError:
        pass  # más fájlrendszer, vagy a forrás nem mozdítható — másolunk
    _copy(source, target)
    try:
        _unlink(source)
    except OSError:
        # A másolat nem maradhat ott: a forrás megvan, tehát a művelet NEM
        # sikerült — két példány rosszabb, mint egy hibaüzenet.
        try:
            _unlink(target)
        except OSError:
            # A takarítás bukását nem tesszük az eredeti hiba helyére: a
            # hívónak arról kell tudnia, ami a műveletet megállította.
            pass
        raise


__all__ = ["safe_move"]
