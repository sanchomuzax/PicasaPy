"""A telepített QML-fájlok előfordítása a felhasználói gyorsítótárba (#6374)."""

from __future__ import annotations

import ctypes
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
GRAFIKA_NAPLO_ENV = "PICASAPY_QML_GRAFIKA_MELEGITES_NAPLO"
#: Modulszintű fogantyúk: a tesztek ezeket cserélik, nem a standard modult (#1375).
_Timer = threading.Timer
_os_exit = os._exit
_run = subprocess.run
_windll = getattr(ctypes, "windll", None)


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
        kernel32 = _windll.kernel32
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


def _grafika_naplozz(sor: str) -> None:
    ut = os.environ.get(GRAFIKA_NAPLO_ENV) or os.environ.get(NAPLO_ENV)
    if not ut:
        ideiglenes = os.environ.get("TEMP") or os.environ.get("TMP")
        if ideiglenes:
            ut = str(Path(ideiglenes) / "picasapy-qml-grafika-melegites.txt")
    if not ut:
        _kiird(sor)
        return
    try:
        Path(ut).parent.mkdir(parents=True, exist_ok=True)
        with open(ut, "a", encoding="utf-8") as naplo:
            naplo.write(sor + "\n")
    except OSError:
        pass


def _hatarido_lejart() -> None:
    sor = "időtúllépés: az előfordítás nem fejeződött be, kilépés"
    _naplozz(sor)
    _grafika_naplozz(sor)
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
    hely = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.CacheLocation)
    if not hely:
        raise RuntimeError("A Qt nem adott QML-cache könyvtárat")
    return Path(hely) / "qmlcache"


#: #6436: a gyorsítótárat író változat jele a cache-könyvtárban
CACHE_BELYEG = ".picasapy-verzio"
_FORDITAS_KITERJESZTESEK = (".qmlc", ".jsc")


def ird_be_a_cache_belyeget(verzio: str) -> None:
    """Az előfordítás végén rögzíti, melyik változat írta a gyorsítótárat."""
    konyvtar = _qml_cache_konyvtar()
    konyvtar.mkdir(parents=True, exist_ok=True)
    (konyvtar / CACHE_BELYEG).write_text(verzio, encoding="utf-8")


def torold_az_elavult_cachet(verzio: str) -> int:
    """Más (vagy ismeretlen) változat QML-fordításait törli; a törölt fájlok száma.

    A qmlcachegen-nel fordított `.qmlc` a forrás változása után is érvényes
    marad (mérve, #6436): a régi változat fordítása a régi felületet töltené be.
    Csak a fordításokat törli; a jel ezután a futó változatot mutatja."""
    try:
        konyvtar = _qml_cache_konyvtar()
    except RuntimeError:
        return 0
    if not konyvtar.is_dir():
        return 0
    belyeg = konyvtar / CACHE_BELYEG
    try:
        if belyeg.read_text(encoding="utf-8").strip() == verzio:
            return 0
    except OSError:
        pass
    torolt = 0
    for fajl in konyvtar.iterdir():
        if fajl.suffix.casefold() in _FORDITAS_KITERJESZTESEK and fajl.is_file():
            try:
                fajl.unlink()
                torolt += 1
            except OSError:
                continue
    try:
        belyeg.write_text(verzio, encoding="utf-8")
    except OSError:
        pass
    return torolt


def _qml_cache_nev_utbol(ut: PurePath) -> str:
    """A Qt a perjeles helyi útvonalat SHA-1-gyel hasheli.

    A QML bytecode neve `.qmlc`, az importált JavaScripté `.jsc`; Windowson is
    a `QUrl.toLocalFile()` perjeles alakja adja a cache-kulcsot.
    """
    suffix = {".qml": ".qmlc", ".js": ".jsc"}.get(ut.suffix.casefold())
    if suffix is None:
        raise ValueError(f"Nem támogatott QML-cache forrásfájl: {ut}")
    return sha1(ut.as_posix().encode("utf-8")).hexdigest() + suffix


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
        kornyezet["PATH"] = os.pathsep.join((str(qt_bin), str(pyside), kornyezet.get("PATH", "")))
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
    """Konzolra ír; nem támogatott kódolásnál UTF-8-ra vált.

    A Windows cp1252-es kimenetén az „ő” `UnicodeEncodeError`-t okoz. Ez
    `ValueError`-ból származik, ezért az eddigi széles kivételkezelés némán
    elnyelte az összesítő sort. Az UTF-8-as újrapróbálás megtartja a sort
    pipe-ba irányítva is; ablakos csomagban továbbra is megengedett a
    kimenet hiánya."""
    try:
        print(sor, flush=True)
    except UnicodeEncodeError:
        kimenet = sys.stdout
        ujrakodol = getattr(kimenet, "reconfigure", None)
        if callable(ujrakodol):
            try:
                ujrakodol(encoding="utf-8", errors="strict")
                print(sor, flush=True)
                return
            except (OSError, ValueError, AttributeError):
                pass
        try:
            puffer = getattr(kimenet, "buffer", None)
            if puffer is not None:
                puffer.write((sor + os.linesep).encode("utf-8"))
                puffer.flush()
        except (OSError, ValueError, AttributeError):
            pass
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
    fajlok = sorted((*qml_root.rglob("*.qml"), *qml_root.rglob("*.js")))
    started = time.perf_counter()
    hibas = _forditsd_le(cache_konyvtar, fajlok)
    eltelt = time.perf_counter() - started
    from picasapy import __version__

    ird_be_a_cache_belyeget(__version__)
    osszegzes = f"QML-előfordítás: {len(fajlok)} fájl, {hibas} hibás, {eltelt:.2f} s"
    _naplozz(osszegzes)
    _kiird(osszegzes)
    # A gyorsítótár a fordításkor már a lemezre került; a hívó a Qt-objektumok
    # bontását kihagyva lép ki.


_GRAFIKA_ALAPMODULOK = ("QtQuick", "QtQuick.Controls")
# A főablak fájái ezeket a Qt-modulokat is betöltik. Az első valódi
# indulásnál a hidegen olvasott (és víruskereső által átvizsgált) modul-DLL-ek
# adták a késést, ezért a telepítő ezeket is betölti egyszer.
_GRAFIKA_TOVABBI_MODULOK = (
    "QtQml",
    "QtQuick.Window",
    "QtQuick.Layouts",
    "QtQuick.Dialogs",
    "QtQuick.Templates",
    "QtQuick.Controls.impl",
    "QtQuick.Controls.Fusion",
    "QtMultimedia",
    "QtPositioning",
    "QtLocation",
)


def _grafika_qml(
    *, teljes: bool = True, tovabbi: tuple[str, ...] = _GRAFIKA_TOVABBI_MODULOK
) -> bytes:
    """Qt Quick Controls ablak, amely felállítja az alkalmazás grafikus útját.

    A `teljes` változat a `tovabbi` Qt-modulokat is importálja; a tartalék csak
    az alapmodulokkal melegít.
    """
    modulok = _GRAFIKA_ALAPMODULOK + (tovabbi if teljes else ())
    importok = "".join(f"import {modul}\n" for modul in modulok)
    return (
        importok
        + """ApplicationWindow {
    width: 32
    height: 32
    visible: false
    color: "transparent"
    Button {
        anchors.fill: parent
        text: " "
    }
}
"""
    ).encode("utf-8")


def _betoltheto_modulok(engine, komponens_osztaly, url_osztaly) -> tuple[str, ...]:
    """A további Qt-modulok közül azok, amelyek ebben a csomagban megvannak."""
    megvan = []
    for modul in _GRAFIKA_TOVABBI_MODULOK:
        probe = komponens_osztaly(engine)
        probe.setData(f"import {modul}\nimport QtQml\nQtObject {{}}\n".encode(), url_osztaly())
        if probe.status() == komponens_osztaly.Status.Error:
            _grafika_naplozz(f"grafikai előmelegítés: a(z) {modul} modul nem tölthető be")
        else:
            megvan.append(modul)
    return tuple(megvan)


def _grafika_hatarido_mp() -> float:
    try:
        return max(0.0, float(os.environ.get(HATARIDO_ENV, ALAP_HATARIDO_MP)))
    except ValueError:
        return ALAP_HATARIDO_MP


def _grafika_komponens(engine, komponens_osztaly, url_osztaly):
    """A teljes előmelegítő komponens, hiba esetén az alapmodulos tartalék."""
    tovabbi = _betoltheto_modulok(engine, komponens_osztaly, url_osztaly)
    for teljes in (True, False):
        component = komponens_osztaly(engine)
        component.setData(_grafika_qml(teljes=teljes, tovabbi=tovabbi), url_osztaly())
        if component.status() != komponens_osztaly.Status.Error:
            return component
        hibak = "; ".join(str(hiba.toString()) for hiba in component.errors())
        valtozat = "teljes" if teljes else "tartalék"
        _grafika_naplozz(f"grafikai előmelegítés hibás QML ({valtozat}): {hibak}")
    raise RuntimeError("a grafikai előmelegítő QML nem tölthető be")


def _melegitsd_grafikat() -> None:
    """Rejtett Qt Quick Controls ablakban megvár egy kirajzolt képkockát."""
    from PySide6.QtCore import QEventLoop, QTimer, QUrl, Qt
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent, QQmlEngine
    from PySide6.QtQuick import QQuickWindow

    QCoreApplication.setOrganizationName("PicasaPy")
    QCoreApplication.setApplicationName("PicasaPy")
    app = QGuiApplication.instance()
    if app is None:
        app = QGuiApplication([sys.argv[0]])
    if not isinstance(app, QGuiApplication):
        raise RuntimeError("a grafikai előmelegítéshez QGuiApplication szükséges")

    engine = QQmlEngine()
    engine.addImportPath(_qml_import_path())
    component = _grafika_komponens(engine, QQmlComponent, QUrl)

    ablak = component.create()
    if not isinstance(ablak, QQuickWindow):
        _grafika_naplozz("grafikai előmelegítés: nem jött létre Qt Quick ablak")
        raise RuntimeError("nem jött létre Qt Quick ablak")

    ablak.setFlag(Qt.WindowType.Tool, True)
    ablak.setOpacity(0.0)
    ablak.setPosition(-32000, -32000)
    ciklus = QEventLoop()
    idozito = QTimer()
    idozito.setSingleShot(True)
    kirajzolt = False

    def _kepkesz() -> None:
        nonlocal kirajzolt
        kirajzolt = True
        ciklus.quit()

    ablak.frameSwapped.connect(_kepkesz)
    ablak.show()
    if not kirajzolt:
        idozito.timeout.connect(ciklus.quit)
        idozito.start(max(1, int(_grafika_hatarido_mp() * 1000)))
        ciklus.exec()
    idozito.stop()
    ablak.close()
    if not kirajzolt:
        _grafika_naplozz("grafikai előmelegítés időtúllépés: nem érkezett képkocka")
        raise subprocess.TimeoutExpired("--qml-grafika-melegites", _grafika_hatarido_mp())
    _melegitsd_betukeszleteket()
    _melegitsd_splash_kepet()
    _grafika_naplozz("grafikai előmelegítés kész: 1 képkocka")


def _melegitsd_betukeszleteket(adatbazis=None) -> int:
    """Egyszer betölti a rendszer összes betűkészlet-családját.

    Windowson az első indulásnál a Qt a Main.qml betöltése közben egyenként
    végigjárta a családokat, és ez 4-15 s volt; a második indulástól a
    rendszer betűkészlet-gyorsítótára már meleg (#6426). A hiba nem állítja
    meg a grafikai előmelegítést.
    """
    try:
        if adatbazis is None:
            from PySide6.QtGui import QFontDatabase as adatbazis
        csaladok = list(adatbazis.families())
        for csalad in csaladok:
            adatbazis.styles(csalad)
    except Exception as hiba:  # noqa: BLE001 - csak gyorsítás, nem feltétel
        _grafika_naplozz(f"betűkészlet-előmelegítés kimaradt: {type(hiba).__name__}")
        return 0
    _grafika_naplozz(f"betűkészlet-előmelegítés: {len(csaladok)} betűkészlet-család")
    return len(csaladok)


def _melegitsd_splash_kepet() -> bool:
    """Egyszer elkészíti a splash képét (saját betűkészlet, logó), képernyő nélkül.

    Az első windowsos indulásnál ez 1,5 s volt a szokásos 0,4 s helyett (#6426).
    A hiba nem állítja meg a grafikai előmelegítést.
    """
    try:
        from picasapy import __version__
        from picasapy.app import startup_splash

        kep = startup_splash._create_splash_pixmap(f"v{__version__}")
        # a réteges (áttetsző) splash-ablak első megjelenítése is lassú volt:
        # egyszer, láthatatlanul, a képernyőn kívül megjelenítjük
        ablak = startup_splash.IndulasAblak(kep)
        ablak.setOpacity(0.0)
        ablak.setPosition(-32000, -32000)
        ablak.show()
        from PySide6.QtGui import QGuiApplication

        QGuiApplication.processEvents()
        ablak.close()
    except Exception as hiba:  # noqa: BLE001 - csak gyorsítás, nem feltétel
        _grafika_naplozz(f"splash-előmelegítés kimaradt: {type(hiba).__name__}")
        return False
    _grafika_naplozz("splash-előmelegítés kész")
    return True


def grafika_main() -> int:
    """A telepítő rejtett grafikai előmelegítőjének belépési pontja."""
    try:
        _inditsd_a_hataridot()
        _melegitsd_grafikat()
    except subprocess.TimeoutExpired:
        _hatarido_lejart()
        return HATARIDO_KOD
    except Exception as hiba:  # noqa: BLE001 - ablakos csomagban nem nyílhat hibaablak
        _grafika_naplozz(f"kivétel: {type(hiba).__name__}")
        _kilepes(KIVETEL_KOD)
        return KIVETEL_KOD
    _kiird("QML-grafikai előmelegítés: kész")
    _kilepes(0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
