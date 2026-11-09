"""Lusta függvényhivatkozás: a modul az első HÍVÁSKOR töltődik be (#6688).

## Miért

A `picasapy.render` csomag importja ~70 modult húz be. Az első ablakképhez
egyik sem kell, de a vezérlők (`EditController`, `ThumbnailCache`, a mentés,
az export) modulszinten importálják a render függvényeit, így az indulás
kritikus útján töltődtek be.

    from picasapy.render import apply_filters
        ->
    apply_filters = lazy_callable("picasapy.render", "apply_filters")

A modulszintű név megmarad, csak a hívásig nem tölti be a csomagot. Így a
hívóhelyek és a tesztek `monkeypatch.setattr(modul, "apply_filters", ...)`
foltozása változatlanul működik.

## Miért nem gyorstárazza a megtalált függvényt

Ugyanazért, mint a `lazy_cv2`: ha a helyettes elmentené az első hívás
eredményét, a VALÓDI modul foltozása (`monkeypatch.setattr(render_chain,
"apply_filters", ...)`) nem látszana rajta át. A továbbítás ára egy
szótár-keresés (`sys.modules`) és egy `getattr` hívásonként, ami
elhanyagolható a hívott képfeldolgozó függvényekhez képest.

## Amit ez NEM old meg

Nem függvény jellegű név (konstans, osztály, `isinstance`-ben használt típus)
nem helyettesíthető: azokat a használat helyén, függvényen belül kell
importálni.
"""

from __future__ import annotations

import importlib
import sys
from collections.abc import Callable
from typing import Any

__all__ = ["lazy_callable", "lazy_module"]


class _LazyModule:
    """Attribútum-továbbító helyettes egy modul elé."""

    __slots__ = ("_module_name",)

    def __init__(self, module_name: str) -> None:
        self._module_name = module_name

    def __getattr__(self, name: str) -> Any:
        modul = importlib.import_module(self._module_name)
        return getattr(modul, name)

    def __dir__(self) -> list[str]:
        return dir(importlib.import_module(self._module_name))

    def __repr__(self) -> str:
        betoltve = self._module_name in sys.modules
        allapot = "betöltve" if betoltve else "még nem töltődött be"
        return f"<lusta {self._module_name} — {allapot}>"


def lazy_module(module_name: str) -> _LazyModule:
    """Modulhelyettes, amely csak attribútum-olvasáskor importál.

    A tényleges modult nem másolja és nem gyorstárazza, így a valódi modul
    foltozása minden hivatkozásnál látszik a helyettesen át is.
    """
    return _LazyModule(module_name)


def lazy_callable(module_name: str, attribute: str) -> Callable[..., Any]:
    """Olyan hívható, amely az első hívásakor tölti be a `module_name` modult.

    Minden hívás újra feloldja a `module_name.attribute` nevet, ezért a valódi
    modul foltozása is látszik rajta át. A betöltés a hívó szálán történik.
    """

    def tovabbito(*args: Any, **kwargs: Any) -> Any:
        modul = importlib.import_module(module_name)
        return getattr(modul, attribute)(*args, **kwargs)

    tovabbito.__name__ = attribute
    tovabbito.__qualname__ = attribute
    tovabbito.__doc__ = f"Lusta hivatkozás: {module_name}.{attribute} (#6688)."
    return tovabbito
