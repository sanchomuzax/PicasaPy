"""Külön folyamatú Windows-csomagcsere és visszaállítás (#6340).

A segéd a főfolyamat kilépésére vár. A kicsomagolás külön, szomszédos
mappába történik; a telepített mappa csak teljes staging után cserélődik.
"""

from __future__ import annotations

import argparse
import errno
import getpass
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

from picasapy.perf.tesztuzem import tarolo_tipusa
from picasapy.app import update_ablak, update_eredmeny, update_folyamatok

_kill = os.kill
_run = subprocess.run
_mkdtemp = tempfile.mkdtemp
_POSIX_PATH = re.compile(r"(?<![\w.])/(?:[^\r\n\"']+)")
_QUOTED_WINDOWS_PATH = re.compile(r"(['\"])(?:[A-Za-z]:[\\/]|\\\\).*?\1")
_WINDOWS_PATH = re.compile(r"(?<![\w])(?:[A-Za-z]:[\\/]|\\\\)[^\s\"']+")
_RELATIVE_PATH = re.compile(
    r"(?<![\w.])(?:\.\.?[\\/])?(?:[^\\/\s\"']+[\\/])+[^\\/\s\"']+"
)



# #6508: tesztben cserélhető óra és várakozás (a globális time modult ne írják át)
_monotonic = time.monotonic
_sleep = time.sleep
_chdir = os.chdir
#: #6534: a PyInstaller-bootloader indulóképe a segéd ablak nélküli
#: gyermekfutásaiban ne villanjon fel (PyInstaller: Splash screen)
_SPLASH_TILTAS = "PYINSTALLER_SUPPRESS_SPLASH_SCREEN"


def biztonsagos_munkamappa() -> Path:
    """A segéd és gyermekei munkamappája: a segéd exe mappája, ha az nem érhető el, a %TEMP%.

    #6534: Windowson egy mappa nem nevezhető át, amíg bármely folyamat
    munkamappája benne van; a telepítési mappa ezért senkinek nem lehet az."""
    sajat = Path(sys.executable).resolve().parent
    return sajat if sajat.is_dir() else Path(tempfile.gettempdir())


def gyermek_kornyezet(alap: dict[str, str] | None = None) -> dict[str, str]:
    """A segéd által indított ablak nélküli PicasaPy-futások környezete."""
    env = dict(os.environ if alap is None else alap)
    env[_SPLASH_TILTAS] = "1"
    return env


def _update_log_path() -> Path:
    """A segéd saját, helyi alkalmazásadat-naplója."""
    from .platform_storage import default_storage_paths

    return default_storage_paths(_platform()).data / "frissites-naplo.txt"


def _sanitized_log_message(message: object) -> str:
    """A hiba szövegét megtartja, az útvonalakat és felhasználónevet kiszűri."""
    text = str(message)
    names = {
        getpass.getuser(),
        os.environ.get("USERNAME", ""),
        os.environ.get("USER", ""),
        os.environ.get("LOGNAME", ""),
        os.environ.get("LNAME", ""),
        Path.home().name,
    }
    for name in sorted((name for name in names if name), key=len, reverse=True):
        text = re.sub(re.escape(name), "[felhasználó]", text, flags=re.IGNORECASE)
    text = _QUOTED_WINDOWS_PATH.sub("[útvonal]", text)
    text = _WINDOWS_PATH.sub("[útvonal]", text)
    text = _POSIX_PATH.sub("[útvonal]", text)
    return _RELATIVE_PATH.sub("[útvonal]", text)


def _log_update(message: object, *, include_storage: bool = False) -> None:
    """Egy időbélyeges sort ír; hibanaplóhiba nem szakíthatja meg a cserét."""
    try:
        target = _update_log_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as log:
            if include_storage:
                log.write(
                    f"{time.strftime('%Y-%m-%d %H:%M:%S')} tároló: "
                    f"{tarolo_tipusa(target.parent)}\n"
                )
            log.write(
                f"{time.strftime('%Y-%m-%d %H:%M:%S')} "
                f"{_sanitized_log_message(message)}\n"
            )
    except Exception:  # noqa: BLE001 - a diagnosztika nem állíthatja meg a frissítést
        return


def _safe_member_path(root: Path, member: str) -> Path:
    path = Path(member)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"A frissítési zip érvénytelen útvonalat tartalmaz: {member}")
    destination = (root / path).resolve()
    if root.resolve() not in destination.parents and destination != root.resolve():
        raise ValueError(f"A frissítési zip útvonala kilép a staging mappából: {member}")
    return destination


def extract_update_archive(archive: Path, stage: Path) -> Path:
    """A zipet biztonságosan kicsomagolja, és a program gyökerét adja vissza."""
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    try:
        with zipfile.ZipFile(archive) as source:
            members = source.infolist()
            for member in members:
                destination = _safe_member_path(stage, member.filename)
                if member.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                    continue
                destination.parent.mkdir(parents=True, exist_ok=True)
                with source.open(member) as reader, destination.open("wb") as writer:
                    shutil.copyfileobj(reader, writer)
    except Exception:
        shutil.rmtree(stage, ignore_errors=True)
        raise

    nested = stage / "PicasaPy"
    if nested.is_dir():
        return nested
    if not (stage / "PicasaPy.exe").is_file():
        shutil.rmtree(stage, ignore_errors=True)
        raise ValueError("A frissítési zip nem tartalmaz PicasaPy.exe fájlt")
    return stage


def swap_update_directory(
    staged_dir: Path,
    install_dir: Path,
    *,
    launch,
) -> bool:
    """Mappát cserél, indítást ellenőriz, és hibánál visszaállít.

    A `launch` visszatérési értéke azt jelzi, hogy az új program elérte-e az
    indulási egészségjelzőt. Tesztekben a folyamatindítás helyettesíthető.
    """
    staged_dir = Path(staged_dir).resolve()
    install_dir = Path(install_dir).resolve()
    backup_dir = install_dir.with_name(f"{install_dir.name}.previous")
    failed_dir = install_dir.with_name(f"{install_dir.name}.failed")
    if not staged_dir.is_dir():
        raise ValueError("A staging mappa nem létezik")
    if failed_dir.exists():
        shutil.rmtree(failed_dir)
    if backup_dir.exists():
        # #6354: Program Files-ba telepítve a program induláskor nem írhat a
        # saját mappájába, így egy korábbi csere után az eltávolító a régi
        # mappában maradhatott. Ez a segéd emelt joggal fut: törlés előtt
        # visszamenti, különben végleg elveszne.
        from .update_cleanup import mentsd_at_az_eltavolitot

        mentsd_at_az_eltavolitot(backup_dir, install_dir)
        shutil.rmtree(backup_dir)
    had_previous = install_dir.exists()
    if had_previous:
        # #6458: foglalt fájlnál (víruskereső, indexelő) nem áll vissza azonnal
        update_folyamatok.atnevez_ujraprobalva(
            install_dir,
            backup_dir,
            # #6534: foglalt mappánál a belőle futó folyamatok azonnal leállnak
            foglaltnal=lambda: update_folyamatok.varj_vagy_allitsd_le(
                install_dir, hatarido=0.0
            ),
        )
    try:
        update_folyamatok.atnevez_ujraprobalva(staged_dir, install_dir)
        if not launch():
            if install_dir.exists():
                install_dir.rename(failed_dir)
            if had_previous and backup_dir.exists():
                backup_dir.rename(install_dir)
            if failed_dir.exists():
                shutil.rmtree(failed_dir, ignore_errors=True)
            return False
        if had_previous:
            from .update_cleanup import finalize_successful_update

            finalize_successful_update(install_dir)
    except Exception:
        if install_dir.exists():
            install_dir.rename(failed_dir)
        if had_previous and backup_dir.exists():
            backup_dir.rename(install_dir)
        if failed_dir.exists():
            shutil.rmtree(failed_dir, ignore_errors=True)
        raise
    return True


def wait_for_process(pid: int, *, poll_interval: float = 0.2) -> None:
    """Megvárja a főfolyamat kilépését; a helper külön folyamatban fut."""
    if pid <= 0 or pid == os.getpid():
        raise ValueError("Érvénytelen főfolyamat-azonosító")
    if _platform() == "win32":
        _wait_for_windows_process(pid)
        return
    while True:
        try:
            _kill(pid, 0)
        except ProcessLookupError:
            return
        except PermissionError:
            # Az azonos felhasználó segédjének ez szokatlan, de nem szabad
            # élő folyamatot kilépettnek tekinteni egy hozzáférési hibából.
            time.sleep(poll_interval)
            continue
        except OSError as error:
            if error.errno == errno.ESRCH:
                return
            raise
        time.sleep(poll_interval)


def _platform() -> str:
    """Kis platformfogantyú a folyamatvárás teszteléséhez."""
    return sys.platform


def _wait_for_windows_process(pid: int) -> None:
    """Win32 folyamathandle-en vár; az ``os.kill(pid, 0)`` nem hordozható."""
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    process_synchronize = 0x00100000
    infinite = 0xFFFFFFFF
    wait_object_0 = 0
    wait_failed = 0xFFFFFFFF

    open_process = kernel32.OpenProcess
    open_process.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    open_process.restype = wintypes.HANDLE
    handle = open_process(process_synchronize, False, pid)
    if not handle:
        error_code = ctypes.get_last_error()
        # Windows ERROR_INVALID_PARAMETER: a PID már nem létezik.
        if error_code == 87:
            return
        raise ctypes.WinError(error_code)

    try:
        wait_for_single_object = kernel32.WaitForSingleObject
        wait_for_single_object.argtypes = (wintypes.HANDLE, wintypes.DWORD)
        wait_for_single_object.restype = wintypes.DWORD
        result = wait_for_single_object(handle, infinite)
        if result == wait_failed:
            raise ctypes.WinError(ctypes.get_last_error())
        if result != wait_object_0:
            raise OSError(f"Váratlan Win32 folyamateredmény: {result}")
    finally:
        close_handle = kernel32.CloseHandle
        close_handle.argtypes = (wintypes.HANDLE,)
        close_handle.restype = wintypes.BOOL
        close_handle(handle)


def _onellenorzes(executable: Path, *, timeout: float = 180.0) -> bool:
    """Az új változat felépíti-e a felületét — ablak nélkül (#6340).

    A program saját `--onellenorzes` kapcsolója a teljes indulási utat
    végigjárja (Qt-bővítmények, QML-fa, fordítás), és eseményciklus nélkül
    kilép; ugyanezt futtatja a CI a csomagon. Ablakot nem nyit, tehát a
    rendszergazdai jogú segéd is futtathatja anélkül, hogy a felhasználó
    elé rendszergazdaként futó program kerülne."""
    env = gyermek_kornyezet()
    env["QT_QPA_PLATFORM"] = "offscreen"
    env["QT_QUICK_BACKEND"] = "software"
    started = time.monotonic()
    try:
        eredmeny = _run(
            [str(executable), "--onellenorzes"],
            env=env,
            cwd=str(biztonsagos_munkamappa()),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - started
        _log_update(
            f"Önellenőrzés: IDŐTÚLLÉPÉS; idő: {elapsed:.2f} s; "
            f"határidő: {timeout:.2f} s",
            include_storage=True,
        )
        return False
    except Exception as error:  # noqa: BLE001 - minden önellenőrzési hiba naplózandó
        elapsed = time.monotonic() - started
        _log_update(
            f"Önellenőrzés kivétel; idő: {elapsed:.2f} s; "
            f"hiba: {_sanitized_log_message(error)}",
            include_storage=True,
        )
        return False
    elapsed = time.monotonic() - started
    _log_update(
        f"Önellenőrzés kilépési kód: {eredmeny.returncode}; idő: {elapsed:.2f} s",
        include_storage=True,
    )
    return eredmeny.returncode == 0


def _qml_elofordit(executable: Path, *, timeout: float = 180.0) -> bool:
    """A friss telepítés QML-cache-ét melegíti; hiba esetén csak naplóz."""
    try:
        from .qml_cache_warmup import melegitsd_qml_cache

        output = melegitsd_qml_cache(
            [str(executable)], gyermek_kornyezet(), timeout=timeout
        )
    except Exception as error:  # noqa: BLE001 - a cache-hiba nem vonhatja vissza a cserét
        _log_update(f"QML-gyorsítótár előmelegítése sikertelen: {_sanitized_log_message(error)}")
        return False
    _log_update(f"QML-gyorsítótár előmelegítése kész: {output or 'nincs kimenet'}")
    return True


def _qml_grafika_melegites(executable: Path, *, timeout: float = 180.0) -> bool:
    """A frissítés után előkészíti a Qt Quick grafikus útvonalát, hiba nélkül visszaállva."""
    try:
        from .qml_cache_warmup import melegitsd_qml_grafikat

        output = melegitsd_qml_grafikat(
            [str(executable)], gyermek_kornyezet(), timeout=timeout
        )
    except Exception as error:  # noqa: BLE001 - az előmelegítés nem vonhatja vissza a cserét
        _log_update(
            "QML-grafikai előmelegítés sikertelen: "
            + _sanitized_log_message(error)
        )
        return False
    _log_update(f"QML-grafikai előmelegítés kész: {output or 'nincs kimenet'}")
    return True


def _rendszergazda() -> bool:
    """Rendszergazdai (emelt) jogokkal fut-e a segéd — csak Windowson igaz."""
    if _platform() != "win32":
        return False
    try:
        import ctypes

        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        return False


#: a folyamatindítás fogantyúja — a teszt ezt cseréli (#1375)
_popen = subprocess.Popen


def inditsd_a_felhasznalonak(executable: Path, *, uac_emelt: bool = False) -> None:
    """A frissített program indítása a felhasználó NORMÁL jogaival (#6340).

    Ha a segédet a program UAC-cal emelte rendszergazdává, a közvetlen
    indítás az új PicasaPy-t is rendszergazdaként futtatná: a létrehozott
    fájlok a rendszergazdáé lennének, és az Intézőből húzás sem működne. A
    Windows héja (`explorer.exe`) a bejelentkezett felhasználó jogaival indít.

    #6383: csak akkor, ha MI emeltük (`uac_emelt`). Ha a régi program eleve
    rendszergazdaként futott, a segéd is az, és az Intézőn át indítás
    elvesztené a környezetet (a folyamat nem a mi szülőnktől öröklődne)."""
    if uac_emelt and _rendszergazda():
        _popen(["explorer.exe", str(executable)], close_fds=True)
    else:
        # #6534: úgy indul, ahogy az Intézőből: a munkamappa a program mappája
        _popen([str(executable)], close_fds=True, cwd=str(executable.parent))


def varj_uj_ablakra(
    install_dir: Path,
    *,
    timeout: float = 180.0,
    poll_interval: float = 0.2,
    inditasi_turelem: float = 30.0,
) -> bool:
    """Megvárja, hogy a frissen indított PicasaPy megjelenítsen egy ablakot.

    Ha `inditasi_turelem` másodpercig egyetlen folyamat sem fut a telepítési
    mappából, az új program el sem indult: nem vár tovább a teljes időkorlátig.
    """
    if _platform() != "win32":
        return True
    from . import update_folyamatok

    kezdet = _monotonic()
    hatarido = kezdet + timeout
    latott_folyamatot = False
    while True:
        folyamatok = update_folyamatok.telepitesi_folyamatok(Path(install_dir), os.getpid())
        for pid in folyamatok:
            latott_folyamatot = True
            if update_ablak.van_lathato_ablaka(pid):
                return True
        most = _monotonic()
        if not latott_folyamatot and most - kezdet >= inditasi_turelem:
            return False
        maradek = hatarido - most
        if maradek <= 0:
            return False
        _sleep(min(poll_interval, maradek))


def install_after_exit(
    pid: int,
    archive: Path,
    install_dir: Path,
    executable: str,
    *,
    uac_emelt: bool = False,
    ui_strings: dict[str, str] | None = None,
) -> bool:
    """Vár, kicsomagol, cserél, ellenőriz, szükség esetén visszaáll, majd indít.

    A kis ablak a lépést és az eltelt időt is mutatja; bezárni csak hiba esetén lehet."""
    with update_ablak.FrissitesiAblak(feliratok=ui_strings) as ablak:
        return _telepites(
            pid,
            archive,
            install_dir,
            executable,
            uac_emelt=uac_emelt,
            ablak=ablak,
        )


def _telepites(
    pid: int,
    archive: Path,
    install_dir: Path,
    executable: str,
    *,
    uac_emelt: bool,
    ablak: update_ablak.FrissitesiAblak | None = None,
) -> bool:
    def lepes(kulcs: str) -> None:
        if ablak is not None and not ablak.van_hibaja:
            ablak.lepes(kulcs)

    def hiba(kulcs: str, *, details: str = "") -> None:
        if ablak is None:
            return
        message = ablak.uzenet(kulcs)
        if details:
            message += "\n" + ablak.uzenet("error_details", details=details)
        ablak.hiba(message)

    lepes("varakozas")
    _log_update(
        "A frissítősegéd elindult; várakozás a főfolyamat kilépésére",
        include_storage=True,
    )
    try:
        started = time.monotonic()
        wait_for_process(pid)
        _log_update(f"Várakozás kész; idő: {time.monotonic() - started:.2f} s")
    except Exception as error:
        _log_update("Visszaállás oka: a főfolyamatra várás kivétellel állt le")
        _log_update(f"Kivétel: {_sanitized_log_message(error)}")
        raise
    try:
        install_dir = Path(install_dir).resolve()
    except Exception as error:
        _log_update("Visszaállás oka: a telepítési hely feloldása hibára futott")
        _log_update(f"Kivétel: {_sanitized_log_message(error)}")
        raise
    try:
        stage_root = Path(
            _mkdtemp(prefix="PicasaPy-update-", dir=install_dir.parent)
        )
    except Exception as error:
        _log_update("Visszaállás oka: a frissítési munkamappa nem hozható létre")
        _log_update(f"Kivétel: {_sanitized_log_message(error)}")
        raise
    sikerult = False
    try:
        started = time.monotonic()
        lepes("kicsomagolas")
        _log_update("Kicsomagolás elkezdődött")
        staged = extract_update_archive(Path(archive), stage_root / "new")
        _log_update(f"Kicsomagolás kész; idő: {time.monotonic() - started:.2f} s")
        started = time.monotonic()
        lepes("maradek_folyamatok")
        leallitott = update_folyamatok.varj_vagy_allitsd_le(install_dir)
        _log_update(
            "A telepítési mappa folyamatainak kezelése kész; "
            f"idő: {time.monotonic() - started:.2f} s"
        )
        if leallitott:
            _log_update(f"A telepítési mappából futó maradék folyamatok leállítva: {leallitott}")
        started = time.monotonic()
        lepes("csere")
        _log_update("Csere és önellenőrzés elkezdődött")

        def onellenorzes() -> bool:
            lepes("onellenorzes")
            return _onellenorzes(install_dir / executable)

        sikerult = swap_update_directory(
            staged,
            install_dir,
            launch=onellenorzes,
        )
        elapsed = time.monotonic() - started
        _log_update(
            f"Csere {'sikeres' if sikerult else 'sikertelen'}; idő: {elapsed:.2f} s"
        )
        update_eredmeny.ird(
            update_eredmeny.jelzo_utvonal(),
            siker=sikerult,
            ok="" if sikerult else update_eredmeny.ONELLENORZES,
        )
        if not sikerult:
            _log_update(
                "Visszaállás oka: az új változat önellenőrzése nem jelzett sikert"
            )
            hiba("startup_check_failed")
        elif uac_emelt and _rendszergazda():
            _log_update(
                "Emelt frissítés: a QML-gyorsítótárat az új program első indulása készíti el"
            )
        else:
            started = time.monotonic()
            lepes("qml_cache")
            _qml_elofordit(install_dir / executable, timeout=180.0)
            _log_update(
                "QML-cache előmelegítése befejeződött; "
                f"idő: {time.monotonic() - started:.2f} s"
            )
            started = time.monotonic()
            lepes("qml_grafika")
            _qml_grafika_melegites(install_dir / executable, timeout=180.0)
            _log_update(
                "QML-grafika előmelegítése befejeződött; "
                f"idő: {time.monotonic() - started:.2f} s"
            )
        return sikerult
    except Exception as error:
        update_eredmeny.ird(
            update_eredmeny.jelzo_utvonal(), siker=False, ok=update_eredmeny.ok_kod(error)
        )
        _log_update("Visszaállás oka: a frissítési lépés kivétellel állt le")
        _log_update(f"Kivétel: {_sanitized_log_message(error)}")
        hiba("unexpected_error", details=_sanitized_log_message(error))
        raise
    finally:
        shutil.rmtree(stage_root, ignore_errors=True)
        # sikernél az új, minden más esetben a megmaradt régi változat
        # indul — mindkettő a felhasználó jogaival; a program tehát a
        # frissítés kudarca után sem marad bezárva
        try:
            lepes("inditas")
            inditas_kezdete = time.monotonic()
            inditsd_a_felhasznalonak(install_dir / executable, uac_emelt=uac_emelt)
            _log_update("Az új program elindítva" + (" az Intézőn át" if uac_emelt else ""))
            _log_update(
                "Új program indítása kész; "
                f"idő: {time.monotonic() - inditas_kezdete:.2f} s"
            )
            if sikerult and ablak is not None and not ablak.van_hibaja:
                lepes("ablak_varakozas")
                started = time.monotonic()
                if not varj_uj_ablakra(install_dir, timeout=180.0):
                    hiba("window_timeout")
                else:
                    _log_update(
                        "Az új verzió ablaka megjelent; "
                        f"várakozás: {time.monotonic() - started:.2f} s"
                    )
        except OSError as error:
            _log_update(f"Újraindítási kivétel: {_sanitized_log_message(error)}")
            hiba("unexpected_error", details=_sanitized_log_message(error))


def _munkamappa_a_telepitesen_kivulre() -> None:
    """#6534: a csomagolt segéd legelső lépése; a telepítési mappát ne fogja."""
    if not getattr(sys, "frozen", False):
        return
    try:
        _chdir(biztonsagos_munkamappa())
    except OSError as error:
        _log_update(f"A munkamappa áthelyezése nem sikerült: {_sanitized_log_message(error)}")


def main(argv: list[str] | None = None) -> int:
    _munkamappa_a_telepitesen_kivulre()
    argumentumok = sys.argv[1:] if argv is None else argv
    if argumentumok[:1] == [update_ablak.ABLAK_KAPCSOLO]:
        # #6458: a frissítési ablak a segéd saját gyerekfolyamatában fut
        kod = (argumentumok[1:] or ["en"])[0]
        status_ut = Path(argumentumok[2]) if len(argumentumok) > 2 else None
        return update_ablak.ablak_foprogram(kod, status_ut)
    parser = argparse.ArgumentParser(description="PicasaPy frissítés telepítő segéd")
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--install-dir", type=Path, required=True)
    parser.add_argument("--executable", required=True)
    parser.add_argument("--uac-emelt", action="store_true")
    parser.add_argument("--ui-strings", default="{}")
    args = parser.parse_args(argumentumok)
    try:
        install_after_exit(
            args.pid,
            args.archive,
            args.install_dir,
            args.executable,
            uac_emelt=args.uac_emelt,
            ui_strings=json.loads(args.ui_strings),
        )
    except Exception as error:  # noqa: BLE001 - az elkülönített helper hibája konzolra kerül
        print(f"A PicasaPy-frissítés nem sikerült: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
