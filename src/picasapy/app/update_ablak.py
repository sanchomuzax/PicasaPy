"""A frissítősegéd látható jelzése a csere idejére (#6458).

A tulajdonos gépén (2026-11-03) az „Újraindítás most” után a program eltűnt,
a kicsomagolás 30-120 s-ig tartott, és közben semmi nem látszott: a régi
programot kézzel újraindította, az a fájlokat fogta, és a csere elbukott.
A segéd ezért a munka idejére egy kis ablakot mutat; a végén maga zárja be.
A segédben nincs Qt, ezért a Windows saját üzenetablakát használja.
"""

from __future__ import annotations

import sys
import threading
from collections.abc import Callable

#: egyedi cím: a bezárás csak ezt az üzenetablakot találhatja meg, a főablakot soha
CIM = {"hu": "PicasaPy frissítése", "en": "PicasaPy update"}
_SZOVEG = {
    "hu": "A PicasaPy frissül. Ne indítsd el közben a programot: a frissítés végén magától újraindul.",
    "en": "PicasaPy is being updated. Please do not start the program meanwhile: "
          "it restarts automatically when the update is finished.",
}
#: MB_OK | MB_ICONINFORMATION | MB_SETFOREGROUND | MB_TOPMOST
_STILUS = 0x0 | 0x40 | 0x10000 | 0x40000
_WM_CLOSE = 0x0010
_LANG_HUNGARIAN = 0x0E


def nyelv(nyelvkod: int | None = None) -> str:
    if nyelvkod is None:
        nyelvkod = _windows_nyelv()
    return "hu" if (nyelvkod & 0x3FF) == _LANG_HUNGARIAN else "en"


def szoveg(nyelvkod: int | None = None) -> str:
    return _SZOVEG[nyelv(nyelvkod)]


class FrissitesiAblak:
    """Kontextuskezelő: belépéskor megnyitja, kilépéskor bezárja az ablakot."""

    def __init__(
        self,
        *,
        megjelenit: Callable[[str, str], None] | None = None,
        bezar: Callable[[str], None] | None = None,
        windows: bool | None = None,
    ) -> None:
        self._windows = sys.platform == "win32" if windows is None else windows
        self._megjelenit = megjelenit or _messagebox
        self._bezar = bezar or _ablak_bezarasa
        self._szal: threading.Thread | None = None
        self._cim = CIM["en"]

    def __enter__(self) -> FrissitesiAblak:
        if self._windows:
            kod = nyelv()
            self._cim = CIM[kod]
            self._szal = threading.Thread(
                target=self._megjelenit, args=(_SZOVEG[kod], self._cim), daemon=True
            )
            self._szal.start()
        return self

    def __exit__(self, *_exc) -> None:
        if self._szal is not None:
            try:
                self._bezar(self._cim)
            except OSError:
                pass
            self._szal.join(timeout=2.0)


def _windows_nyelv() -> int:  # pragma: no cover - csak Windowson fut
    if sys.platform != "win32":
        return 0
    import ctypes

    return int(ctypes.windll.kernel32.GetUserDefaultUILanguage())


def _messagebox(szoveg_: str, cim: str) -> None:  # pragma: no cover - csak Windowson fut
    import ctypes

    ctypes.windll.user32.MessageBoxW(0, szoveg_, cim, _STILUS)


def _ablak_bezarasa(cim: str) -> None:  # pragma: no cover - csak Windowson fut
    import ctypes

    user32 = ctypes.windll.user32
    # "#32770": az üzenetablak osztálya; a főablakot így nem találhatja meg
    hwnd = user32.FindWindowW("#32770", cim)
    if hwnd:
        user32.PostMessageW(hwnd, _WM_CLOSE, 0, 0)
