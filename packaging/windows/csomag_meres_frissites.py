"""A valódi Windows-frissítési mérés és diagnosztikája."""

from __future__ import annotations

import contextlib

import json
import re
import shutil
import subprocess
import time
from pathlib import Path

from csomag_meres_kozos import (
    _HelyiKiadasszerver,
    _keszits_frissitesi_zip,
    _platform,
)
from csomag_meres_ido import _profil
from csomag_meres_windows import _ablakikonok

def _kovetkezo_verzio(verzio: str) -> str:
    """A tesztkiadás verzióját egy javítási számmal a telepített fölé emeli."""
    match = re.fullmatch(r"v?(\d+(?:\.\d+)*)(?:[-+][0-9A-Za-z.-]+)?", verzio.strip())
    if match is None:
        raise ValueError(f"nem növelhető tesztverzió: {verzio!r}")
    reszek = [int(resz) for resz in match.group(1).split(".")]
    reszek[-1] += 1
    return ".".join(str(resz) for resz in reszek)

def _diagnosztika(diag_mappa: Path) -> list[dict]:
    eredmeny = []
    for fajl in diag_mappa.glob("*.jsonl"):
        try:
            sorok = fajl.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for sor in sorok:
            try:
                adat = json.loads(sor)
            except json.JSONDecodeError:
                continue
            if isinstance(adat, dict):
                eredmeny.append(adat)
    return sorted(eredmeny, key=lambda adat: float(adat.get("at", 0)))

def _objektum(adat: dict, nev: str) -> dict | None:
    return next(
        (
            obj
            for obj in reversed(adat.get("objects", []))
            if obj.get("name") == nev
        ),
        None,
    )

def _lathato_koordinataval(obj: dict | None) -> bool:
    if not obj or not obj.get("visible") or not isinstance(obj.get("rect"), dict):
        return False
    return obj["rect"].get("width", 0) > 0 and obj["rect"].get("height", 0) > 0

def _kilepes_diagnosztika(diag_mappa: Path, pid: int, kattintas: float, profil_gyoker: Path) -> None:
    """Miért nem lépett ki a régi program a Restart now után (#6383).

    A diagnosztika eseményciklus-időzítőről ír: ha a kattintás után nincs új
    pillanat, a program kilépett az eseményciklusból, és a lezárásban akadt
    el; ha van, a kattintás nem ért célba vagy a program várakozik."""
    sajat = [s for s in _diagnosztika(diag_mappa) if s.get("pid") == pid]
    utana = [s for s in sajat if float(s.get("at", 0)) > kattintas]
    utolso = sajat[-1] if sajat else {}
    gomb = _objektum(utolso, "updateDialogRestartButton") if utolso else None
    print(
        f"  kattintás után {len(utana)} pillanat; az utolsó "
        f"{time.time() - float(utolso.get('at', time.time())):.1f} s-a; "
        f"download_state={utolso.get('download_state')}; "
        f"Restart now: {(gomb or {}).get('visible')} {(gomb or {}).get('rect')}",
        flush=True,
    )
    for nev in ("frissites-naplo.txt", "errorlog.txt"):
        for naplo in sorted(profil_gyoker.rglob(nev)):
            sorok = naplo.read_text(encoding="utf-8", errors="replace").splitlines()
            print(f"  --- {nev} (utolsó {min(15, len(sorok))} sor) ---", flush=True)
            for sor in sorok[-15:]:
                print(f"    {sor}", flush=True)

def _uj_folyamat_diagnosztika(diag_mappa: Path, regi_pid: int, profil_gyoker: Path) -> None:
    """Miért nem jelentkezett a frissített program (#6383)."""
    pidek: dict[int, list[dict]] = {}
    for sor in _diagnosztika(diag_mappa):
        if sor.get("pid") != regi_pid:
            pidek.setdefault(int(sor.get("pid", 0)), []).append(sor)
    print(f"  új folyamatok a diagnosztikában: {len(pidek)}", flush=True)
    for pid, sorok in pidek.items():
        cimke = _objektum(sorok[-1], "versionLabel") or {}
        print(
            f"    PID {pid}: {len(sorok)} pillanat, test_mode={sorok[-1].get('test_mode')}, "
            f"verzió={cimke.get('current_version_text')!r}",
            flush=True,
        )
    for nev in ("frissites-naplo.txt", "errorlog.txt"):
        for naplo in sorted(profil_gyoker.rglob(nev)):
            sorok = naplo.read_text(encoding="utf-8", errors="replace").splitlines()
            print(f"  --- {nev} (utolsó {min(25, len(sorok))} sor) ---", flush=True)
            for sor in sorok[-25:]:
                print(f"    {sor}", flush=True)

def _varjon_diagnosztikara(
    diag_mappa: Path,
    feltetel,
    leiras: str,
    *,
    timeout: float = 60.0,
) -> tuple[dict, list[dict]]:
    hatarido = time.monotonic() + timeout
    pillanatok: list[dict] = []
    while time.monotonic() < hatarido:
        pillanatok = _diagnosztika(diag_mappa)
        talalat = feltetel(pillanatok)
        if talalat is not None:
            return talalat, pillanatok
        time.sleep(0.05)
    utolso = pillanatok[-1] if pillanatok else {}
    print(
        "  utolsó diagnosztika: "
        f"{len(pillanatok)} pillanat, update_available={utolso.get('update_available')}, "
        f"download_state={utolso.get('download_state')}, elemek="
        f"{[o.get('name') or o.get('text') for o in utolso.get('objects', [])][:12]}",
        flush=True,
    )
    raise TimeoutError(f"{timeout:.0f} másodpercen belül nem teljesült: {leiras}")

def _eloterbe_hoz(pid: int, *, user32=None, kernel32=None):
    """A PicasaPy ablakát előtérbe hozza, és ellenőrzi is (#6487).

    A Windows előtérzára (foreground lock) a sima `SetForegroundWindow`-t
    megtagadja, ha közben más folyamat kapott valódi bemenetet (például a
    kattintásos telepítőpróba után). Ezért a hívó szálat ideiglenesen az
    előtérben lévő ablak szálához csatoljuk, és megnézzük, sikerült-e.
    """
    import ctypes

    if user32 is None:
        user32 = ctypes.WinDLL("user32", use_last_error=True)
    if kernel32 is None:
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    ablakok = _ablakikonok(pid)
    if not ablakok:
        raise RuntimeError("a PicasaPy-nak nincs látható ablaka, nem hozható előtérbe")
    hwnd = next((h for h, a in ablakok.items() if a["cim"].startswith("PicasaPy")), next(iter(ablakok)))
    if user32.GetForegroundWindow() == hwnd:
        return hwnd
    sajat = kernel32.GetCurrentThreadId()
    for _ in range(20):
        elol = user32.GetForegroundWindow()
        cel = user32.GetWindowThreadProcessId(elol, None)
        user32.AttachThreadInput(sajat, cel, True)
        try:
            user32.ShowWindow(hwnd, 9)
            user32.BringWindowToTop(hwnd)
            user32.SetForegroundWindow(hwnd)
        finally:
            user32.AttachThreadInput(sajat, cel, False)
        if user32.GetForegroundWindow() == hwnd:
            return hwnd
        _szunet(0.1)
    raise RuntimeError("a PicasaPy ablaka 2 s alatt sem hozható előtérbe (előtérzár)")


def _pont_folyamata(user32, x: int, y: int) -> tuple[int, str]:
    """Melyik folyamat ablaka van a képernyő (x, y) pontján, és mi a címe."""
    import ctypes
    from ctypes import wintypes

    user32.WindowFromPoint.argtypes = [wintypes.POINT]
    user32.WindowFromPoint.restype = wintypes.HWND
    hwnd = user32.WindowFromPoint(wintypes.POINT(x, y))
    folyamat = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(folyamat))
    cim = ctypes.create_unicode_buffer(256)
    user32.GetWindowTextW(user32.GetAncestor(hwnd, 2), cim, 256)
    return folyamat.value, cim.value


def _valodi_eger_kattintas(obj: dict, pid: int) -> None:
    """Windows egér-eseménnyel kattint, QML-slotot nem hív közvetlenül."""
    import ctypes

    rect = obj.get("rect")
    if not isinstance(rect, dict):
        raise RuntimeError(f"nincs kattintható koordináta: {obj.get('name')}")
    x = round(rect["x"] + rect["width"] / 2)
    y = round(rect["y"] + rect["height"] / 2)
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    _eloterbe_hoz(pid)
    if not user32.SetCursorPos(x, y):
        raise OSError(ctypes.get_last_error(), "SetCursorPos nem sikerült")
    # #6487: a kattintás csak akkor mehet ki, ha a pont tényleg a PicasaPy ablakára esik
    gazda, cim = _pont_folyamata(user32, x, y)
    if gazda != pid:
        raise RuntimeError(
            f"a kattintási pont ({x}, {y}) nem a PicasaPy ablakára esik, hanem: {cim!r} (PID {gazda})"
        )
    user32.mouse_event(0x0002, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTDOWN
    user32.mouse_event(0x0004, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTUP
    print(f"  valódi egérkattintás: {obj.get('name') or obj.get('text')} ({x}, {y})", flush=True)

_NYUGALOM_MP = 0.7

_falido = time.time

_szunet = time.sleep

def _stabil_kattintas(diag_mappa: Path, pid: int, kivalaszto, leiras: str) -> dict:
    """Akkor kattint, amikor az elem helye már nem változik (#6383).

    A párbeszéd megjelenéskor még a végleges helyére mozog; az első látható
    koordinátára kattintva a próba kétszer is mellé kattintott. A
    diagnosztika 100 ms-onként ír; ha az utolsó `_NYUGALOM_MP` másodperc
    legalább három pillanatában az elem látható és a helye ugyanaz, a
    felület nyugalomban van."""
    hatarido = time.monotonic() + 30.0
    while time.monotonic() < hatarido:
        most = _falido()
        ablak = [
            s
            for s in _diagnosztika(diag_mappa)
            if s.get("pid") == pid and most - float(s.get("at", 0)) <= _NYUGALOM_MP
        ]
        elemek = [kivalaszto(s) for s in ablak]
        if (
            len(elemek) >= 3
            and all(_lathato_koordinataval(e) for e in elemek)
            and len({json.dumps(e.get("rect"), sort_keys=True) for e in elemek}) == 1
        ):
            _valodi_eger_kattintas(elemek[-1], pid)
            return elemek[-1]
        _szunet(0.1)
    raise TimeoutError(f"30 másodpercen belül nem állt meg a felület: {leiras}")

def _elso_inditasi_kerdes_lezarasa(diag_mappa: Path, pid: int, varakozas_mp: float = 20.0) -> bool:
    """Az újraindított programban feljövő első keresési kérdés lezárása (#6383).

    A segéd a frissített programot könyvtár-paraméter nélkül indítja, ezért
    az az első indítás kérdésével nyílik („ready to search for pictures”).
    Ez modális, eltakarja a menüt; a próba úgy zárja le, ahogy a felhasználó:
    a Continue gombbal. Ha 20 s alatt nem jelenik meg, nincs teendő."""
    hatarido = time.monotonic() + varakozas_mp
    while time.monotonic() < hatarido:
        sajat = [s for s in _diagnosztika(diag_mappa) if s.get("pid") == pid]
        if sajat and _lathato_koordinataval(_objektum(sajat[-1], "initialScanContinue")):
            _stabil_kattintas(
                diag_mappa,
                pid,
                lambda s: _objektum(s, "initialScanContinue"),
                "első indítás Continue gombja",
            )
            return True
        _szunet(0.2)
    return False

def _kepernyokep_mentese(cel: Path, pid: int) -> None:
    from PIL import ImageGrab

    _eloterbe_hoz(pid)
    kep = ImageGrab.grab(all_screens=True)
    cel.parent.mkdir(parents=True, exist_ok=True)
    kep.save(cel, "PNG", optimize=True)
    print(f"  képernyőkép: {cel.name} ({kep.width}×{kep.height})", flush=True)

def _help_menu(adat: dict) -> dict | None:
    for obj in reversed(adat.get("objects", [])):
        cimke = str(obj.get("text") or obj.get("title") or "")
        if cimke.replace("&", "").strip().casefold() == "help" and _lathato_koordinataval(obj):
            return obj
    return None

def _about_menu(adat: dict) -> dict | None:
    for obj in reversed(adat.get("objects", [])):
        cimke = str(obj.get("text") or "")
        if (
            cimke.replace("&", "").strip().casefold() == "about picasapy"
            and _lathato_koordinataval(obj)
        ):
            return obj
    return None

def _about_verzio_latszik(adat: dict, verzio: str) -> bool:
    dialog = _objektum(adat, "aboutDialog")
    szoveg = any(
        str(obj.get("text") or "").startswith(f"PicasaPy v{verzio} ")
        for obj in adat.get("objects", [])
    )
    return bool(dialog and dialog.get("visible") and szoveg)

def _csatolt_folyamatok_leallitasa(diag_mappa: Path, kezdo_pid: int) -> None:
    if _platform() != "win32":
        return
    pids = {kezdo_pid}
    pids.update(int(adat["pid"]) for adat in _diagnosztika(diag_mappa) if adat.get("pid"))
    for pid in pids:
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            capture_output=True,
            check=False,
            timeout=10,
        )

def _frissites_utana_indulasi_kapu(naplo: Path) -> int:
    from qml_cache_warmup import frissitesi_indulasi_kapu

    return 0 if frissitesi_indulasi_kapu(naplo) else 1

def frissites(
    futtatok: list[tuple[str, list[str]]],
    munka: Path,
    elvart_verzio: str | None,
    kepernyokep_mappa: Path | None = None,
    valodi_cel_verzio: str | None = None,
    kozben_inditas: bool = False,
) -> int:
    """Teljes, valódi egérkattintásos Windows-frissítési próba (#6383).

    `kozben_inditas` (#6458): a régi program kilépése után a próba azonnal
    újraindítja a régi programot, ahogy a tulajdonos tette, mert a frissítés
    alatt semmi nem látszott. A frissítésnek ekkor is végig kell mennie."""
    if _platform() != "win32":
        print("frissites: csak Windowson mérhető", flush=True)
        return 0
    if len(futtatok) != 1 or not futtatok[0][1]:
        raise SystemExit("frissites: pontosan egy PicasaPy.exe kell")
    if not elvart_verzio:
        raise SystemExit("frissites: az --elvart-verzio megadása kötelező")

    munka = Path(munka).resolve()
    munka.mkdir(parents=True, exist_ok=True)
    exe = Path(futtatok[0][1][0]).resolve()
    telepitesi_mappa = exe.parent
    if exe.name.casefold() != "picasapy.exe":
        raise SystemExit("frissites: a futtatónak PicasaPy.exe útvonalra kell mutatnia")
    # #6458: a tulajdonos útja: a KORÁBBI kiadás Setup-pal telepítve, a valódi
    # GitHub-kiadásból frissít. Ilyenkor nincs helyi ál-szerver és saját zip.
    if valodi_cel_verzio:
        uj_verzio = valodi_cel_verzio
        archive = None
    else:
        uj_verzio = _kovetkezo_verzio(elvart_verzio)
        archive = _keszits_frissitesi_zip(
            telepitesi_mappa,
            munka / "release" / "PicasaPy-windows-x64.zip",
            uj_verzio,
        )
    kepernyokep_mappa = Path(kepernyokep_mappa or munka / "kepernyokepek").resolve()
    diag_mappa = munka / "diagnosztika"
    shutil.rmtree(diag_mappa, ignore_errors=True)
    diag_mappa.mkdir(parents=True)
    env, konyvtar = _profil(munka / "futas")
    env.pop("QT_QPA_PLATFORM", None)
    env.pop("QT_QUICK_BACKEND", None)
    env["PICASAPY_UPDATE_TEST_DIAGNOSTICS"] = "1"
    env["PICASAPY_UPDATE_TEST_DIAGNOSTICS_DIR"] = str(diag_mappa)
    # #6436: a tulajdonos gépén a háttérmunka sosem ért véget; az újraindításnak
    # ilyenkor is meg kell történnie
    env["PICASAPY_UPDATE_TEST_BUSY"] = "1"
    if konyvtar:
        konyvtar.mkdir(parents=True, exist_ok=True)

    folyamat = None
    kozbeni = None
    try:
        szerver_kornyezet = (
            contextlib.nullcontext(None) if archive is None
            else _HelyiKiadasszerver(archive, uj_verzio)
        )
        with szerver_kornyezet as szerver:
            if szerver is not None:
                env["PICASAPY_UPDATE_API"] = szerver.api_url
            folyamat = subprocess.Popen(
                [str(exe), str(konyvtar)],
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.STDOUT,
            )
            print(
                f"[frissites] {elvart_verzio} -> {uj_verzio}; "
                f"API {szerver.api_url if szerver else 'valódi GitHub'}; PID {folyamat.pid}",
                flush=True,
            )
            available, _ = _varjon_diagnosztikara(
                diag_mappa,
                lambda sorok: next(
                    (
                        sor
                        for sor in reversed(sorok)
                        if sor.get("pid") == folyamat.pid
                        and sor.get("update_available")
                        and _objektum(sor, "versionLabel") is not None
                    ),
                    None,
                ),
                "az alkalmazás jelezze az új verziót",
                # a program induláskor 30 s-ot vár a keresés előtt (AUTO_CHECK_DELAY_MS)
                timeout=120.0,
            )
            label = _objektum(available, "versionLabel")
            if not _lathato_koordinataval(label) or not str(label.get("text", "")).startswith("↑"):
                raise RuntimeError("az új verziójelzés nem látható a főablakban")
            _kepernyokep_mentese(kepernyokep_mappa / "01-uj-verzio-jelzese.png", folyamat.pid)

            _stabil_kattintas(
                diag_mappa, folyamat.pid, lambda s: _objektum(s, "versionLabel"), "verziójel"
            )
            dialog_state, _ = _varjon_diagnosztikara(
                diag_mappa,
                lambda sorok: next(
                    (
                        sor
                        for sor in reversed(sorok)
                        if sor.get("pid") == folyamat.pid
                        and (_objektum(sor, "updateDialog") or {}).get("visible")
                        and _lathato_koordinataval(
                            _objektum(sor, "updateDialogDownloadButton")
                        )
                    ),
                    None,
                ),
                "a frissítési ablak és a Frissítés most gomb jelenjen meg",
            )
            _kepernyokep_mentese(
                kepernyokep_mappa / "02-frissites-most-gomb.png", folyamat.pid
            )
            _stabil_kattintas(
                diag_mappa,
                folyamat.pid,
                lambda s: _objektum(s, "updateDialogDownloadButton"),
                "Frissítés most gomb",
            )

            _varjon_diagnosztikara(
                diag_mappa,
                lambda sorok: next(
                    (
                        sor
                        for sor in reversed(sorok)
                        if sor.get("pid") == folyamat.pid
                        and sor.get("download_state") == "downloading"
                    ),
                    None,
                ),
                "a letöltés induljon el",
            )
            _kepernyokep_mentese(
                kepernyokep_mappa / "03-letoltes-folyamatban.png", folyamat.pid
            )
            ready, _ = _varjon_diagnosztikara(
                diag_mappa,
                lambda sorok: next(
                    (
                        sor
                        for sor in reversed(sorok)
                        if sor.get("pid") == folyamat.pid
                        and sor.get("download_state") == "ready"
                        and _lathato_koordinataval(
                            _objektum(sor, "updateDialogRestartButton")
                        )
                    ),
                    None,
                ),
                "a letöltés és az SHA-256 ellenőrzés fejeződjön be",
            )
            _kepernyokep_mentese(
                kepernyokep_mappa / "04-ujrainditasra-kesz.png", folyamat.pid
            )
            kattintas = time.time()
            restart_button = _stabil_kattintas(
                diag_mappa,
                folyamat.pid,
                lambda s: _objektum(s, "updateDialogRestartButton"),
                "Restart now gomb",
            )
            print(f"  Restart now gomb: {restart_button.get('rect')}", flush=True)
            _kepernyokep_mentese(
                kepernyokep_mappa / "05-ujrainditas-kerese.png", folyamat.pid
            )

            kilepett = time.monotonic() + 60
            while folyamat.poll() is None and time.monotonic() < kilepett:
                time.sleep(0.05)
            if folyamat.poll() is None:
                _kilepes_diagnosztika(diag_mappa, folyamat.pid, kattintas, munka / "futas")
                raise TimeoutError("a Frissítés most kattintás után a régi program nem lépett ki")
            time.sleep(3.0)
            _kepernyokep_mentese(
                kepernyokep_mappa / "05b-frissites-folyamatban-ablak.png", 0
            )
            if kozben_inditas:
                kozbeni = subprocess.Popen(
                    [str(exe), str(konyvtar)],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.STDOUT,
                )
                print(
                    f"  a régi program újraindítva a frissítés közben (PID {kozbeni.pid})",
                    flush=True,
                )

            try:
                uj_pid_state, _ = _varjon_diagnosztikara(
                    diag_mappa,
                    lambda sorok: next(
                        (
                            sor
                            for sor in reversed(sorok)
                            if sor.get("pid") != folyamat.pid
                            and not sor.get("test_mode")
                            and _objektum(sor, "versionLabel") is not None
                            and str(
                                (_objektum(sor, "versionLabel") or {}).get(
                                    "current_version_text", ""
                                )
                            ).startswith(f"v{uj_verzio}")
                            and sum(1 for item in sorok if item.get("pid") == sor.get("pid")) >= 5
                        ),
                        None,
                    ),
                    "a frissített program új folyamata induljon el",
                    # a segéd kicsomagolja és lecseréli a telepítést, ez percekig tarthat
                    timeout=180.0,
                )
            except TimeoutError:
                _uj_folyamat_diagnosztika(diag_mappa, folyamat.pid, munka / "futas")
                raise
            uj_pid = int(uj_pid_state["pid"])
            _kepernyokep_mentese(
                kepernyokep_mappa / "06-uj-verzio-elindult.png", uj_pid
            )
            _elso_inditasi_kerdes_lezarasa(diag_mappa, uj_pid)

            help_state, _ = _varjon_diagnosztikara(
                diag_mappa,
                lambda sorok: next(
                    (
                        sor
                        for sor in reversed(sorok)
                        if sor.get("pid") == uj_pid and _help_menu(sor) is not None
                    ),
                    None,
                ),
                "a Súgó menü kattintható területe jelenjen meg",
            )
            _stabil_kattintas(diag_mappa, uj_pid, _help_menu, "Súgó menü")
            about_menu_state, _ = _varjon_diagnosztikara(
                diag_mappa,
                lambda sorok: next(
                    (
                        sor
                        for sor in reversed(sorok)
                        if sor.get("pid") == uj_pid and _about_menu(sor) is not None
                    ),
                    None,
                ),
                "az About PicasaPy menüpont jelenjen meg",
            )
            _stabil_kattintas(diag_mappa, uj_pid, _about_menu, "About PicasaPy menüpont")
            _varjon_diagnosztikara(
                diag_mappa,
                lambda sorok: next(
                    (
                        sor
                        for sor in reversed(sorok)
                        if sor.get("pid") == uj_pid and _about_verzio_latszik(sor, uj_verzio)
                    ),
                    None,
                ),
                "a Névjegy az új verziót mutassa",
            )
            _kepernyokep_mentese(
                kepernyokep_mappa / "07-nevjegy-uj-verzio.png", uj_pid
            )
            from qml_cache_warmup import windows_indulasi_naplo

            if _frissites_utana_indulasi_kapu(windows_indulasi_naplo(env)):
                raise RuntimeError("a frissítés utáni első indulás túllépte az 5 s-os határt")
            print(
                f"✅ frissites: {elvart_verzio} -> {uj_verzio}; "
                f"a Névjegy az új verziót mutatja (PID {uj_pid})",
                flush=True,
            )
            return 0
    except Exception as error:  # noqa: BLE001 - bármelyik lépés hibája piros kapu
        print(f"❌ frissites: {error}", flush=True)
        return 1
    finally:
        if kozbeni is not None and kozbeni.poll() is None:
            kozbeni.terminate()
        kezdo_pid = folyamat.pid if folyamat is not None else 0
        if folyamat is not None and folyamat.poll() is None:
            folyamat.terminate()
        if kezdo_pid:
            _csatolt_folyamatok_leallitasa(diag_mappa, kezdo_pid)

__all__ = (
    "_NYUGALOM_MP",
    "_about_menu",
    "_about_verzio_latszik",
    "_csatolt_folyamatok_leallitasa",
    "_diagnosztika",
    "_eloterbe_hoz",
    "_elso_inditasi_kerdes_lezarasa",
    "_falido",
    "_frissites_utana_indulasi_kapu",
    "_help_menu",
    "_kepernyokep_mentese",
    "_kilepes_diagnosztika",
    "_kovetkezo_verzio",
    "_lathato_koordinataval",
    "_objektum",
    "_stabil_kattintas",
    "_szunet",
    "_uj_folyamat_diagnosztika",
    "_valodi_eger_kattintas",
    "_varjon_diagnosztikara",
    "frissites",
)
