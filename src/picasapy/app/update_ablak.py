"""A frissítősegéd látható jelzése a csere idejére (#6458).

A tulajdonos gépén (2026-11-03) az „Újraindítás most” után a program eltűnt,
a kicsomagolás 30-120 s-ig tartott, és közben semmi nem látszott: a régi
programot kézzel újraindította, az a fájlokat fogta, és a csere elbukott.
A segéd ezért a munka idejére egy kis ablakot mutat; a végén maga zárja be.
A segédben nincs Qt, ezért a Windows saját üzenetablakát használja.
"""

from __future__ import annotations

import subprocess
import sys
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
#: a segéd ezzel a kapcsolóval csak az ablakot mutatja (külön folyamatként)
ABLAK_KAPCSOLO = "--frissitesi-ablak"


def nyelv(nyelvkod: int | None = None) -> str:
    if nyelvkod is None:
        nyelvkod = _windows_nyelv()
    return "hu" if (nyelvkod & 0x3FF) == _LANG_HUNGARIAN else "en"


def szoveg(nyelvkod: int | None = None) -> str:
    return _SZOVEG[nyelv(nyelvkod)]


class FrissitesiAblak:
    """Kontextuskezelő: belépéskor megnyitja, kilépéskor bezárja az ablakot.

    Az üzenetablak blokkol, ezért KÜLÖN FOLYAMATBAN fut (a segéd önmagát
    indítja `--frissitesi-ablak` kapcsolóval): így a csere szála szabad
    marad, és nyers háttérszál sem kell (#988 őre).
    """

    def __init__(
        self,
        *,
        megjelenit: Callable[[str, str], object] | None = None,
        bezar: Callable[[str, object], None] | None = None,
        windows: bool | None = None,
    ) -> None:
        self._windows = _platform() == "win32" if windows is None else windows
        self._megjelenit = megjelenit or _ablak_folyamat_inditasa
        self._bezar = bezar or _ablak_bezarasa
        self._fogantyu: object | None = None
        self._nyitva = False
        self._cim = CIM["en"]

    def __enter__(self) -> FrissitesiAblak:
        if self._windows:
            kod = nyelv()
            self._cim = CIM[kod]
            try:
                self._fogantyu = self._megjelenit(kod, self._cim)
                self._nyitva = True
            except OSError:
                self._nyitva = False
        return self

    def __exit__(self, *_exc) -> None:
        if self._nyitva:
            try:
                self._bezar(self._cim, self._fogantyu)
            except OSError:
                pass


def _platform() -> str:
    """Platformfogantyú (#1217): a teszt ezt írja át, nem a `sys.platform`-ot."""
    return sys.platform


def ablak_parancs(kod: str) -> list[str]:
    """A segéd önmaga, ablak-üzemmódban (fagyasztva és forrásból futtatva is)."""
    if getattr(sys, "frozen", False):
        return [sys.executable, ABLAK_KAPCSOLO, kod]
    return [sys.executable, "-m", "picasapy.app.update_swap_helper", ABLAK_KAPCSOLO, kod]


def ablak_foprogram(kod: str) -> int:  # pragma: no cover - csak Windowson fut
    """A gyerekfolyamat törzse: megmutatja az ablakot, és bezárásig vár."""
    kod = kod if kod in _SZOVEG else "en"
    _messagebox(_SZOVEG[kod], CIM[kod])
    return 0


def _ablak_folyamat_inditasa(kod: str, _cim: str) -> object:  # pragma: no cover - Windows
    return subprocess.Popen(  # noqa: S603 - saját, rögzített parancs
        ablak_parancs(kod),
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def _windows_nyelv() -> int:  # pragma: no cover - csak Windowson fut
    if _platform() != "win32":
        return 0
    import ctypes

    return int(ctypes.windll.kernel32.GetUserDefaultUILanguage())


def _messagebox(szoveg_: str, cim: str) -> None:  # pragma: no cover - csak Windowson fut
    import ctypes

    ctypes.windll.user32.MessageBoxW(0, szoveg_, cim, _STILUS)


def _ablak_bezarasa(cim: str, folyamat: object) -> None:  # pragma: no cover - Windows
    import ctypes

    user32 = ctypes.windll.user32
    # "#32770": az üzenetablak osztálya; a főablakot így nem találhatja meg
    hwnd = user32.FindWindowW("#32770", cim)
    if hwnd:
        user32.PostMessageW(hwnd, _WM_CLOSE, 0, 0)
    if isinstance(folyamat, subprocess.Popen):
        try:
            folyamat.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            folyamat.terminate()
