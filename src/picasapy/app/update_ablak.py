"""A frissítősegéd folyamatos jelzése (#6508).

A segéd külön folyamat; a kis tkinter ablak egy másik segédfolyamatban fut,
és egy ideiglenes állapotfájlból olvassa a műveletet. Így a másolás és a
Windowsos fájlzárolás-várás alatt is frissül az eltelt idő és a lépés.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Mapping

#: egyedi cím: a bezárás csak ezt az ablakot találhatja meg, a főablakot soha
CIM = {"hu": "PicasaPy frissítése", "en": "PicasaPy update"}
_SZOVEG = {
    "hu": "A PicasaPy frissül. Ne indítsd el közben a programot: a frissítés végén magától újraindul.",
    "en": "PicasaPy is being updated. Please do not start the program meanwhile: "
    "it restarts automatically when the update is finished.",
}
_LEPESEK = {
    "hu": {
        "varakozas": "A régi program kilépésére vár",
        "kicsomagolas": "A frissítési fájlok kicsomagolása",
        "maradek_folyamatok": "Másik futó példány bezárása",
        "csere": "Fájlok cseréje",
        "onellenorzes": "Az új verzió ellenőrzése",
        "qml_cache": "Az indulás előkészítése",
        "qml_grafika": "A grafika előkészítése",
        "inditas": "Az új verzió indítása",
        "ablak_varakozas": "Az új verzió ablakára vár",
    },
    "en": {
        "varakozas": "Waiting for the previous version to exit",
        "kicsomagolas": "Extracting update files",
        "maradek_folyamatok": "Closing another running copy",
        "csere": "Replacing application files",
        "onellenorzes": "Checking the new version",
        "qml_cache": "Preparing startup",
        "qml_grafika": "Preparing graphics",
        "inditas": "Starting the new version",
        "ablak_varakozas": "Waiting for the new version window",
    },
}
_ELTELT = {"hu": "Eltelt idő: {seconds} mp", "en": "Elapsed: {seconds} s"}
_HIBA_CIM = {"hu": "A frissítés nem sikerült", "en": "The update failed"}
_BEZARAS = {"hu": "Bezárás", "en": "Close"}
_ALTALANOS_HIBA = {
    "hu": "Váratlan hiba történt a frissítés közben.",
    "en": "An unexpected error interrupted the update.",
}
_HIBA_RESZLET = {"hu": "Részletek: {details}", "en": "Details: {details}"}
_ELLENORZES_HIBA = {
    "hu": "Az új verzió ellenőrzése nem sikerült. A régi verzió indul.",
    "en": "The new version failed its startup check. The previous version will restart.",
}
_ABLAK_IDOTULEPES = {
    "hu": "Az új verzió 180 másodpercen belül nem nyitott ablakot.",
    "en": "The new version did not show a window within 180 seconds.",
}
_SZOVEG_KULCSOK = (
    "varakozas",
    "kicsomagolas",
    "maradek_folyamatok",
    "csere",
    "onellenorzes",
    "qml_cache",
    "qml_grafika",
    "inditas",
    "ablak_varakozas",
)
#: a segéd ezzel a kapcsolóval csak az ablakot mutatja (külön folyamatként)
ABLAK_KAPCSOLO = "--frissitesi-ablak"


def _platform() -> str:
    """Platformfogantyú (#1217): a teszt ezt írja át, nem a `sys.platform`-ot."""
    return sys.platform


def nyelv(nyelvkod: int | None = None) -> str:
    if nyelvkod is None:
        nyelvkod = _windows_nyelv()
    return "hu" if (nyelvkod & 0x3FF) == 0x0E else "en"


def szoveg(nyelvkod: int | None = None) -> str:
    """A korábbi, statikus üzenet szövege (kompatibilitás a régi hívókkal)."""
    return _SZOVEG[nyelv(nyelvkod)]


def felirat(kulcs: str, kod: str, feliratok: Mapping[str, str] | None = None) -> str:
    """Egy feliratot ad vissza a hívó alkalmazás fordításával vagy tartalékkal."""
    if feliratok is not None and kulcs in feliratok:
        return feliratok[kulcs]
    kod = kod if kod in {"hu", "en"} else "en"
    if kulcs in _LEPESEK[kod]:
        return _LEPESEK[kod][kulcs]
    if kulcs == "elapsed":
        return _ELTELT[kod]
    if kulcs == "error_title":
        return _HIBA_CIM[kod]
    if kulcs == "close":
        return _BEZARAS[kod]
    if kulcs == "unexpected_error":
        return _ALTALANOS_HIBA[kod]
    if kulcs == "error_details":
        return _HIBA_RESZLET[kod]
    if kulcs == "startup_check_failed":
        return _ELLENORZES_HIBA[kod]
    if kulcs == "window_timeout":
        return _ABLAK_IDOTULEPES[kod]
    return kulcs


def lepes_szovege(kulcs: str, kod: str = "en") -> str:
    """A segéd lépésének érthető, alapértelmezett felirata."""
    return felirat(kulcs, kod)


def _windows_nyelv() -> int:
    if _platform() != "win32":
        return 0
    import ctypes

    return int(ctypes.windll.kernel32.GetUserDefaultUILanguage())


def _status_utvonal() -> Path:
    return Path(tempfile.gettempdir()) / f"picasapy-update-{os.getpid()}.json"


def _status_iras(ut: Path, adat: Mapping[str, object]) -> None:
    ideiglenes = ut.with_name(f"{ut.name}.{os.getpid()}.tmp")
    ideiglenes.write_text(json.dumps(adat, ensure_ascii=False), encoding="utf-8")
    ideiglenes.replace(ut)


def _status_olvasas(ut: Path) -> dict:
    try:
        adat = json.loads(ut.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return adat if isinstance(adat, dict) else {}


def ablak_parancs(kod: str, status_ut: Path | None = None) -> list[str]:
    """A segéd önmaga, ablak-üzemmódban (fagyasztva és forrásból futtatva is)."""
    if getattr(sys, "frozen", False):
        parancs = [sys.executable, ABLAK_KAPCSOLO, kod]
    else:
        parancs = [sys.executable, "-m", "picasapy.app.update_swap_helper", ABLAK_KAPCSOLO, kod]
    if status_ut is not None:
        parancs.append(str(status_ut))
    return parancs


class FrissitesiAblak:
    """Kontextuskezelő a frissítés lépéseit és eltelt idejét mutató ablakhoz."""

    def __init__(
        self,
        *,
        megjelenit: Callable[[str, str], object] | None = None,
        bezar: Callable[[str, object], None] | None = None,
        windows: bool | None = None,
        feliratok: Mapping[str, str] | None = None,
    ) -> None:
        self._windows = _platform() == "win32" if windows is None else windows
        self._megjelenit = megjelenit
        self._bezar = bezar or _ablak_bezarasa
        self._fogantyu: object | None = None
        self._nyitva = False
        self._cim = CIM["en"]
        self._kod = "en"
        self._status_ut: Path | None = None
        self._feliratok = dict(feliratok or {})
        self._statusz: dict[str, object] = {"stage": "varakozas", "error": "", "done": False}

    @property
    def van_hibaja(self) -> bool:
        return bool(self._statusz.get("error"))

    def __enter__(self) -> FrissitesiAblak:
        if self._windows:
            self._kod = nyelv()
            self._cim = CIM[self._kod]
            self._status_ut = _status_utvonal()
            self._statusz.update(
                texts=self._feliratok,
                started_at=time.monotonic(),
            )
            try:
                _status_iras(self._status_ut, self._statusz)
                if self._megjelenit is None:
                    self._fogantyu = _ablak_folyamat_inditasa(
                        self._kod, self._cim, self._status_ut
                    )
                else:
                    self._fogantyu = self._megjelenit(self._kod, self._cim)
                self._nyitva = True
            except OSError:
                self._nyitva = False
        return self

    def lepes(self, kulcs: str) -> None:
        self._statusz.update(stage=kulcs, error="", done=False)
        self._frissitsd_a_statuszt()

    def uzenet(self, kulcs: str, **ertekek: object) -> str:
        return felirat(kulcs, self._kod, self._feliratok).format(**ertekek)

    def hiba(self, uzenet: str) -> None:
        self._statusz.update(error=uzenet, done=False)
        self._frissitsd_a_statuszt()

    def _frissitsd_a_statuszt(self) -> None:
        if self._status_ut is not None:
            try:
                _status_iras(self._status_ut, self._statusz)
            except OSError:
                pass

    def __exit__(self, exc_type, exc, _traceback) -> None:
        if exc_type is not None and not self.van_hibaja:
            reszlet = str(exc) if exc is not None else ""
            uzenet = felirat("unexpected_error", self._kod, self._feliratok)
            if reszlet:
                minta = felirat("error_details", self._kod, self._feliratok)
                uzenet += "\n" + minta.format(details=reszlet)
            self.hiba(uzenet)
        if self.van_hibaja:
            # A hibaablak maradjon nyitva, amíg a felhasználó el nem olvassa.
            # A gyermekfolyamat a Bezárás gomb után törli az állapotfájlt.
            return None
        self._statusz["done"] = True
        self._frissitsd_a_statuszt()
        if self._nyitva:
            try:
                self._bezar(self._cim, self._fogantyu)
            except OSError:
                pass
        if self._status_ut is not None:
            self._status_ut.unlink(missing_ok=True)


def _ablak_folyamat_inditasa(kod: str, cim: str, status_ut: Path) -> object:
    del cim
    return subprocess.Popen(
        ablak_parancs(kod, status_ut),
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def _ablak_bezarasa(_cim: str, folyamat: object) -> None:
    if isinstance(folyamat, subprocess.Popen):
        try:
            folyamat.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            folyamat.terminate()


def ablak_foprogram(
    kod: str,
    status_ut: Path | None = None,
) -> int:  # pragma: no cover - a látható ablak Windowson fut
    """A gyermekfolyamat törzse; status fájl nélkül a régi statikus ablakot adja."""
    kod = kod if kod in _SZOVEG else "en"
    if status_ut is None:
        _messagebox(_SZOVEG[kod], CIM[kod])
        return 0
    return _tkinter_ablak(kod, status_ut)


def _tkinter_ablak(kod: str, status_ut: Path) -> int:  # pragma: no cover - Windows
    import tkinter as tk
    from tkinter import ttk

    kezdo = _status_olvasas(status_ut)
    feliratok = kezdo.get("texts") if isinstance(kezdo.get("texts"), dict) else {}
    indulasi_ido = float(kezdo.get("started_at", time.monotonic()))
    root = tk.Tk()
    root.title(CIM[kod])
    root.resizable(False, False)
    root.attributes("-topmost", True)
    root.protocol("WM_DELETE_WINDOW", lambda: None)
    frame = ttk.Frame(root, padding=18)
    frame.pack(fill="both", expand=True)
    stage = tk.StringVar()
    elapsed = tk.StringVar()
    error = tk.StringVar()
    ttk.Label(frame, textvariable=stage, font=("Segoe UI", 11, "bold"), wraplength=430).pack(
        anchor="w", fill="x"
    )
    ttk.Label(frame, textvariable=elapsed, padding=(0, 10, 0, 0)).pack(anchor="w")
    error_label = ttk.Label(frame, textvariable=error, wraplength=430, foreground="#a32020")
    close_button = ttk.Button(
        frame,
        text=felirat("close", kod, feliratok),
        command=root.destroy,
    )
    kezdo_lepes = str(kezdo.get("stage", "varakozas"))
    stage.set(felirat(kezdo_lepes, kod, feliratok))
    elapsed.set(
        felirat("elapsed", kod, feliratok).format(
            seconds=int(max(0.0, time.monotonic() - indulasi_ido))
        )
    )

    def frissitsd() -> None:
        allapot = _status_olvasas(status_ut)
        stage_key = str(allapot.get("stage", "varakozas"))
        stage.set(felirat(stage_key, kod, feliratok))
        elapsed.set(
            felirat("elapsed", kod, feliratok).format(
                seconds=int(max(0.0, time.monotonic() - indulasi_ido))
            )
        )
        hiba = str(allapot.get("error") or "")
        if hiba:
            root.title(f"{CIM[kod]} - {felirat('error_title', kod, feliratok)}")
            error.set(hiba)
            error_label.pack(anchor="w", fill="x", pady=(8, 0))
            close_button.pack(anchor="e", pady=(12, 0))
            root.protocol("WM_DELETE_WINDOW", root.destroy)
        elif allapot.get("done"):
            root.destroy()
            return
        root.after(250, frissitsd)

    root.update_idletasks()
    x = max(0, (root.winfo_screenwidth() - root.winfo_reqwidth()) // 2)
    y = max(0, (root.winfo_screenheight() - root.winfo_reqheight()) // 2)
    root.geometry(f"+{x}+{y}")
    root.lift()
    root.focus_force()
    root.after(0, frissitsd)
    try:
        root.mainloop()
    finally:
        status_ut.unlink(missing_ok=True)
        status_ut.with_name(f"{status_ut.name}.{os.getpid()}.tmp").unlink(missing_ok=True)
    return 0


def _messagebox(szoveg_: str, cim: str) -> None:  # pragma: no cover - Windows
    import ctypes

    ctypes.windll.user32.MessageBoxW(0, szoveg_, cim, 0x0 | 0x40 | 0x10000 | 0x40000)


def van_lathato_ablaka(pid: int) -> bool:
    """Van-e látható felső szintű ablaka a megadott új alkalmazásfolyamatnak."""
    if _platform() != "win32":
        return True
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    talalat = False

    ablak_tipus = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    is_window_visible = user32.IsWindowVisible
    is_window_visible.argtypes = (wintypes.HWND,)
    is_window_visible.restype = wintypes.BOOL
    get_window_thread_process_id = user32.GetWindowThreadProcessId
    get_window_thread_process_id.argtypes = (wintypes.HWND, ctypes.POINTER(wintypes.DWORD))
    get_window_thread_process_id.restype = wintypes.DWORD
    enum_windows = user32.EnumWindows
    enum_windows.argtypes = (ablak_tipus, wintypes.LPARAM)
    enum_windows.restype = wintypes.BOOL

    @ablak_tipus
    def bejar(hwnd, _lparam):
        nonlocal talalat
        if not is_window_visible(hwnd):
            return True
        tulaj = wintypes.DWORD()
        get_window_thread_process_id(hwnd, ctypes.byref(tulaj))
        if tulaj.value == pid:
            talalat = True
            return False
        return True

    enum_windows(bejar, 0)
    return talalat
