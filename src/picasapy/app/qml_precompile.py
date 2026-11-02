"""A telepített QML-fájlok előfordítása a felhasználói gyorsítótárba (#6374)."""

from __future__ import annotations

from hashlib import sha1
import os
from pathlib import Path, PurePath
import subprocess
import sys
import threading
import time

import PySide6
from PySide6.QtCore import QCoreApplication, QStandardPaths

from .application_location import _qml_import_path

#: Haladásnapló: minden fájl a betöltése ELŐTT ide kerül, így elakadáskor a
#: napló utolsó sora megmondja, hol állt meg (a csomagolt, ablakos exe-nek
#: nincs szabványos kimenete).
NAPLO_ENV = "PICASAPY_QML_ELOFORDIT_NAPLO"
#: Belső határidő: a telepítő (`waituntilterminated`) és az önfrissítés vár
#: rá, ezért elakadás esetén magától kilép.
HATARIDO_ENV = "PICASAPY_QML_ELOFORDIT_HATARIDO"
ALAP_HATARIDO_MP = 120.0
HATARIDO_KOD = 3
KIVETEL_KOD = 4
#: Modulszintű fogantyúk: a tesztek ezeket cserélik, nem a standard modult (#1375).
_Timer = threading.Timer
_os_exit = os._exit
_run = subprocess.run


def _platform() -> str:
    """A futó platform fogantyúja (a tesztek ezt cserélik, nem a `sys.platform`-ot)."""
    return sys.platform


def _azonnali_kilepes(kod: int) -> None:
    """Kilépés a bontás és (Windowson) a DLL-leválasztás nélkül.

    A Package-mérésen a csomagolt exe a gyorsítótár előállítása után az
    `os._exit` hívásnál is elakadt: Windowson az `ExitProcess` minden betöltött
    DLL-t leválaszt, és ez lefagyhat. A `TerminateProcess` ezt kihagyja; a
    gyorsítótár a fordításkor már a lemezen van."""
    if _platform() == "win32":
        import ctypes

        kernel32 = ctypes.windll.kernel32
        kernel32.TerminateProcess(kernel32.GetCurrentProcess(), kod)
    _os_exit(kod)


_kilepes = _azonnali_kilepes


def _naplozz(sor: str) -> None:
    ut = os.environ.get(NAPLO_ENV)
    if not ut:
        return
    try:
        with open(ut, "a", encoding="utf-8") as naplo:
            naplo.write(sor + "\n")
    except OSError:
        pass


def _hatarido_lejart() -> None:
    _naplozz("időtúllépés: az előfordítás nem fejeződött be, kilépés")
    _kilepes(HATARIDO_KOD)


def _inditsd_a_hataridot() -> None:
    try:
        mp = float(os.environ.get(HATARIDO_ENV, ALAP_HATARIDO_MP))
    except ValueError:
        mp = ALAP_HATARIDO_MP
    idozito = _Timer(mp, _hatarido_lejart)
    idozito.daemon = True
    idozito.start()


def _qml_konyvtar() -> Path:
    """A telepített alkalmazáshoz csomagolt QML-fa."""
    return Path(__file__).resolve().parent / "qml"


def _qmlcachegen_exe() -> Path:
    """A csomagba tett vagy a PySide6 mellé telepített Qt cachegenerátor."""
    nev = "qmlcachegen.exe" if _platform() == "win32" else "qmlcachegen"
    pyside = Path(PySide6.__file__).resolve().parent
    # A pyside6-qmlcachegen wrapper ugyanezeket az útvonalakat használja:
    # Windowson a Qt-eszköz közvetlenül a PySide6 könyvtárában, máshol a
    # Qt/libexec alatt található.
    eszkoz = pyside / nev if _platform() == "win32" else pyside / "Qt" / "libexec" / nev
    if not eszkoz.is_file():
        raise FileNotFoundError(f"A Qt QML-cachegenerátor nem található: {eszkoz}")
    return eszkoz


def _qml_cache_konyvtar() -> Path:
    """A Qt futásidejű QML-cache könyvtára."""
    egyedi = os.environ.get("QML_DISK_CACHE_PATH")
    if egyedi:
        return Path(egyedi)
    hely = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.CacheLocation
    )
    if not hely:
        raise RuntimeError("A Qt nem adott QML-cache könyvtárat")
    return Path(hely) / "qmlcache"


def _qml_cache_nev_utbol(ut: PurePath) -> str:
    """A Qt a `QUrl.toLocalFile()` alakot hasheli SHA-1-gyel, ami Windowson is
    perjeles (`C:/...`); a natív, fordított perjeles alakból más név jönne ki."""
    return sha1(ut.as_posix().encode("utf-8")).hexdigest() + ".qmlc"


def _qml_cache_nev(fajl: Path) -> str:
    """A helyi QML-fájl gyorsítótár-neve az abszolút útvonalából."""
    return _qml_cache_nev_utbol(fajl.resolve())


def _forditsd_le(cache_konyvtar: Path, fajlok: list[Path]) -> int:
    """A Qt saját cachegen eszközével készít futásidőben is használható bytecode-ot."""
    hibas = 0
    cache_konyvtar.mkdir(parents=True, exist_ok=True)
    eszkoz = _qmlcachegen_exe()
    kornyezet = os.environ.copy()
    # A qmlcachegen a PySide6 eszközgyökeréből fut; a Qt DLL-ek a Qt/bin
    # könyvtárban vagy közvetlenül mellette vannak.
    pyside = Path(PySide6.__file__).resolve().parent
    qt_bin = pyside / "Qt" / "bin"
    if _platform() == "win32":
        kornyezet["PATH"] = os.pathsep.join(
            (str(qt_bin), str(pyside), kornyezet.get("PATH", ""))
        )
    try:
        hatarido_mp = float(os.environ.get(HATARIDO_ENV, ALAP_HATARIDO_MP))
    except ValueError:
        hatarido_mp = ALAP_HATARIDO_MP
    hatarido = time.monotonic() + max(0.0, hatarido_mp)
    import_path = _qml_import_path()
    for fajl in fajlok:
        _naplozz(f"fordítás: {fajl}")
        cel = cache_konyvtar / _qml_cache_nev(fajl)
        hatralevo = hatarido - time.monotonic()
        if hatralevo <= 0:
            raise subprocess.TimeoutExpired(str(eszkoz), hatarido_mp)
        futtato = {
            "env": kornyezet,
            "stdin": subprocess.DEVNULL,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "timeout": hatralevo,
            "check": False,
            "text": True,
            "encoding": "utf-8",
            "errors": "replace",
        }
        if _platform() == "win32":
            futtato["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            eredmeny = _run(
                [
                    str(eszkoz),
                    "--only-bytecode",
                    "-I",
                    import_path,
                    "-o",
                    str(cel),
                    str(fajl),
                ],
                **futtato,
            )
        except subprocess.TimeoutExpired:
            cel.unlink(missing_ok=True)
            raise
        if eredmeny.returncode != 0 or not cel.is_file():
            hibas += 1
            cel.unlink(missing_ok=True)
            reszlet = (eredmeny.stderr or "").strip()
            if reszlet:
                _naplozz(f"hiba: {fajl}: {reszlet[-800:]}")
    return hibas


def _kiird(sor: str) -> None:
    """Konzolra írás, ami soha nem dob kivételt.

    A csomagolt windowsos exe kimenete cp1252-es: az „ő” betű kiírása
    `UnicodeEncodeError`-t dobott, az ablakos PyInstaller-csomag pedig a
    kezeletlen kivételre hibaablakot nyitott, ami kattintásra várt, ezért
    a folyamat nem lépett ki (Package-mérés, 180 s)."""
    try:
        print(sor, flush=True)
    except (OSError, ValueError, AttributeError):
        pass


def main() -> int:
    """Fordítja a QML-fájlokat, a hibákat összesíti és kilép.

    Kezeletlen kivétel nem hagyhatja el: az ablakos csomagban az hibaablakot
    nyitna, ami a telepítőt és az önfrissítést is megakasztaná."""
    try:
        _fordits()
    except subprocess.TimeoutExpired:
        _hatarido_lejart()
        return HATARIDO_KOD
    except Exception as hiba:  # noqa: BLE001 - lásd a docstringet
        _naplozz(f"kivétel: {type(hiba).__name__}")
        _kilepes(KIVETEL_KOD)
        return KIVETEL_KOD
    _kilepes(0)
    return 0


def _fordits() -> None:
    _inditsd_a_hataridot()
    _naplozz("előfordítás indul")

    QCoreApplication.setOrganizationName("PicasaPy")
    QCoreApplication.setApplicationName("PicasaPy")
    app = QCoreApplication([sys.argv[0]])
    app.setApplicationName("PicasaPy")
    app.setOrganizationName("PicasaPy")

    qml_root = _qml_konyvtar()
    cache_konyvtar = _qml_cache_konyvtar()
    fajlok = sorted(qml_root.rglob("*.qml"))
    started = time.perf_counter()
    hibas = _forditsd_le(cache_konyvtar, fajlok)
    eltelt = time.perf_counter() - started
    osszegzes = f"QML-előfordítás: {len(fajlok)} fájl, {hibas} hibás, {eltelt:.2f} s"
    _naplozz(osszegzes)
    _kiird(osszegzes)
    # A gyorsítótár a fordításkor már a lemezre került; a hívó a Qt-objektumok
    # bontását kihagyva lép ki.


if __name__ == "__main__":
    raise SystemExit(main())
