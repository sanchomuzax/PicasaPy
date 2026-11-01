"""A csomagolt windowsos PicasaPy indulási ideje és ablakikonja (#6344, #6345).

## Miért kell

A tulajdonos szerint a telepítővel feltett program **sokkal lassabban**
indul, mint ugyanaz a verzió a Pythonos indítóval (#6344), és futás közben
**nincs ikonja** (#6345). A CI eddig csak azt nézte, hogy a csomagolt
program elindul-e, azt nem, hogy mennyi idő alatt, és milyen ikonnal.

Ez a szkript ugyanazon a gépen, ugyanabban a lépésben futtatja egymás
mellett a forrásból, a PyInstaller-mappából és a telepített programból
indított változatot, így a KÜLÖNBSÉGÜK a lelet, nem a futó gép sebessége.

## Két mód

    python csomag_meres.py ido --futtato forras=@python,picasapy \
        --futtato csomagolt=dist/PicasaPy/PicasaPy.exe

Futtatónként két egymást követő indítás (hideg, majd meleg) ugyanazzal a
profillal. Az indulási szakaszokat a program saját hibanaplójából olvassa
(`errorlog.txt`, a `StartupProgressLog` jelzései), és a folyamat indítása
előtti időbélyeghez méri. Így a PyInstaller-indító és a modulbetöltés ideje
is látszik.

    python csomag_meres.py ikon --futtato telepitett=C:/.../PicasaPy.exe

VALÓDI ablakkal indít (nem `offscreen`), és amíg a program fut, a folyamat
látható felső szintű ablakaitól lekérdezi a Windows ikonját
(`WM_GETICON`, illetve az ablakosztály ikonja). A tálca és az Alt+Tab ezt
mutatja. `--szigoru` mellett bukik, ha egyik ablaknak sincs ikonja.

Ez CI-eszköz, nem termékkód: a csomag nem tartalmazza.
"""

from __future__ import annotations

import argparse
import base64
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

#: a program saját sikerjelzése a hibanaplóban (`_StartupSmokeProbe`)
_SIKER = "A főablak a splash után megjelent"

#: egy hibanapló-sor: `2026-10-31T15:33:14.123+00:00 INFO picasapy.startup: …`
_SOR = re.compile(r"^(\S+) INFO picasapy\.startup: (.*)$")

_IDOKORLAT_MP = 120.0


def _futtatok(ertekek: list[str]) -> list[tuple[str, list[str]]]:
    """`nev=parancs,arg,...` párok. A vessző elválasztó, mert a windowsos
    útvonalban szóköz lehet, vessző nem."""
    eredmeny = []
    for ertek in ertekek:
        nev, _, parancs = ertek.partition("=")
        if not nev or not parancs:
            raise SystemExit(f"hibás --futtato: {ertek!r} (várt: nev=parancs,arg)")
        eredmeny.append((nev, [_resz(resz) for resz in parancs.split(",") if resz]))
    return eredmeny


def _resz(resz: str) -> str:
    """`@python` = a szkriptet futtató értelmező; a létező relatív út
    abszolúttá válik. Így a Git-bash MSYS-útvonalai (`/d/a/...`) sehol nem
    kerülnek a windowsos programok elé."""
    if resz == "@python":
        return sys.executable
    ut = Path(resz)
    return str(ut.resolve()) if not ut.is_absolute() and ut.exists() else resz


def _profil(gyoker: Path) -> tuple[dict[str, str], Path]:
    """Elszigetelt profil és egy üres könyvtár, a CI meglévő füstpróbájának
    mintájára (`package.yml`)."""
    konyvtar = gyoker / "library"
    profil = gyoker / "profile"
    konyvtar.mkdir(parents=True, exist_ok=True)
    (profil / "Temp").mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update(
        {
            "USERPROFILE": str(profil),
            "APPDATA": str(profil / "AppData" / "Roaming"),
            "LOCALAPPDATA": str(profil / "AppData" / "Local"),
            "TEMP": str(profil / "Temp"),
            "TMP": str(profil / "Temp"),
            "XDG_DATA_HOME": str(profil / "xdg-data"),
            "XDG_CONFIG_HOME": str(profil / "xdg-config"),
            "XDG_CACHE_HOME": str(profil / "xdg-cache"),
            "PICASAPY_LANG": "en",
            "PYTHONIOENCODING": "utf-8",
        }
    )
    return env, konyvtar


def _naplo_sorai(profil_gyoker: Path) -> list[tuple[datetime, str]]:
    sorok: list[tuple[datetime, str]] = []
    for naplo in profil_gyoker.rglob("errorlog.txt"):
        for sor in naplo.read_text(encoding="utf-8", errors="replace").splitlines():
            talalat = _SOR.match(sor)
            if talalat is None:
                continue
            try:
                sorok.append((datetime.fromisoformat(talalat.group(1)), talalat.group(2)))
            except ValueError:
                continue
    return sorok


def _egy_inditas(parancs: list[str], gyoker: Path, *, ablakkal: bool) -> dict:
    env, konyvtar = _profil(gyoker)
    if ablakkal:
        env.pop("QT_QPA_PLATFORM", None)
        env.pop("QT_QUICK_BACKEND", None)
    else:
        env["QT_QPA_PLATFORM"] = "offscreen"
        env["QT_QUICK_BACKEND"] = "software"
    korabbi = len(_naplo_sorai(gyoker))
    indult = datetime.now().astimezone()
    kezdet = time.perf_counter()
    folyamat = subprocess.Popen(
        [*parancs, "--indulasellenorzes", str(konyvtar)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return {
        "folyamat": folyamat,
        "indult": indult,
        "kezdet": kezdet,
        "korabbi": korabbi,
        "gyoker": gyoker,
    }


def _bevar(futas: dict) -> dict:
    folyamat = futas["folyamat"]
    try:
        kimenet, _ = folyamat.communicate(timeout=_IDOKORLAT_MP)
    except subprocess.TimeoutExpired:
        folyamat.kill()
        kimenet, _ = folyamat.communicate()
    fal_mp = time.perf_counter() - futas["kezdet"]
    sorok = _naplo_sorai(futas["gyoker"])[futas["korabbi"] :]
    return {
        "kod": folyamat.returncode,
        "fal_mp": fal_mp,
        "indult": futas["indult"],
        "sorok": sorok,
        "kimenet": kimenet.decode("utf-8", errors="replace"),
    }


def _jelentes(nev: str, sorszam: int, eredmeny: dict) -> str:
    sorok = eredmeny["sorok"]
    fej = (
        f"[{nev} #{sorszam}] kilépőkód {eredmeny['kod']}, "
        f"falióra {eredmeny['fal_mp']:.2f} s"
    )
    if not sorok:
        return fej + "\n  (a hibanaplóban nincs indulási jelzés)\n" + eredmeny["kimenet"][-2000:]
    resek = []
    elozo_ido, elozo_nev = eredmeny["indult"], "folyamat indítása"
    for ido, szakasz in sorok:
        resek.append(((ido - elozo_ido).total_seconds() * 1000, elozo_nev, szakasz))
        elozo_ido, elozo_nev = ido, szakasz
    elso = resek[0][0]
    siker = next(
        ((ido - eredmeny["indult"]).total_seconds() for ido, s in sorok if s == _SIKER),
        None,
    )
    sorok_szoveg = [
        fej,
        f"  indítótól az első saját sorig (indító + modulbetöltés): {elso:.0f} ms",
        "  főablak a splash után: "
        + (f"{siker:.2f} s" if siker is not None else "NEM jelent meg"),
        "  a hat leghosszabb szakasz:",
    ]
    for ms, honnan, hova in sorted(resek, reverse=True)[:6]:
        sorok_szoveg.append(f"    {ms:8.0f} ms  {honnan}  →  {hova}")
    for elotag in ("Alkalmazásikon", "A folyamat indulása óta", "PicasaPy-verzió"):
        talalat = [s for _, s in sorok if s.startswith(elotag)]
        if talalat:
            sorok_szoveg.append(f"  {talalat[-1]}")
    return "\n".join(sorok_szoveg)


def ido(futtatok: list[tuple[str, list[str]]], inditasok: int, munka: Path) -> int:
    hiba = 0
    for nev, parancs in futtatok:
        gyoker = munka / f"ido-{nev}"
        for sorszam in range(1, inditasok + 1):
            eredmeny = _bevar(_egy_inditas(parancs, gyoker, ablakkal=False))
            print(_jelentes(nev, sorszam, eredmeny), flush=True)
            if eredmeny["kod"] != 0:
                hiba = 1
    return hiba


# --- ikon: csak Windowson ------------------------------------------------


def _ablakikonok(pid: int) -> dict[int, dict]:
    """A folyamat látható felső szintű ablakai és az ikonjaik."""
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetClassLongPtrW.restype = ctypes.c_size_t
    user32.GetClassLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.SendMessageTimeoutW.restype = ctypes.c_size_t
    user32.SendMessageTimeoutW.argtypes = [
        wintypes.HWND,
        wintypes.UINT,
        wintypes.WPARAM,
        wintypes.LPARAM,
        wintypes.UINT,
        wintypes.UINT,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    wm_geticon, smto_abortifhung = 0x007F, 0x0002
    gclp_hicon, gclp_hiconsm = -14, -34

    talalt: dict[int, dict] = {}

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def bejar(hwnd, _):
        tulaj = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(tulaj))
        if tulaj.value != pid or not user32.IsWindowVisible(hwnd):
            return True

        def uzenet(fajta: int) -> int:
            ered = ctypes.c_size_t(0)
            user32.SendMessageTimeoutW(
                hwnd, wm_geticon, fajta, 0, smto_abortifhung, 1000, ctypes.byref(ered)
            )
            return ered.value

        cim = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, cim, 256)
        osztaly = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, osztaly, 256)
        talalt[int(hwnd)] = {
            "cim": cim.value,
            "osztaly": osztaly.value,
            "kicsi": uzenet(0),
            "nagy": uzenet(1),
            "kicsi2": uzenet(2),
            "osztaly_ikon": user32.GetClassLongPtrW(hwnd, gclp_hicon),
            "osztaly_kicsi": user32.GetClassLongPtrW(hwnd, gclp_hiconsm),
        }
        return True

    user32.EnumWindows(bejar, 0)
    return talalt


def _kepernyokep(hwnd: int | None) -> dict[str, bytes]:
    """A tálca és az ablak címsorának képe PNG-ben (#6345).

    A tulajdonos a TÁLCÁN nem látja az ikont; a `WM_GETICON` csak azt
    mondja meg, mit ad az ablak, azt nem, mit mutat a tálca. Ez a kép
    azt mutatja, amit a felhasználó lát."""
    import ctypes
    import io
    from ctypes import wintypes

    from PIL import ImageGrab

    try:
        teljes = ImageGrab.grab(all_screens=True)
    except OSError as hiba:
        print(f"  ⚠️ képernyőkép nem készült: {hiba}", flush=True)
        return {}
    kepek = {}
    szel, mag = teljes.size
    talca = teljes.crop((0, max(0, mag - 64), szel, mag))
    if szel > 1280:
        talca = talca.resize((1280, round(talca.height * 1280 / szel)))
    for nev, kep in (("talca", talca),):
        puffer = io.BytesIO()
        kep.save(puffer, "PNG", optimize=True)
        kepek[nev] = puffer.getvalue()
    if hwnd is not None:
        teglalap = wintypes.RECT()
        ctypes.WinDLL("user32").GetWindowRect(hwnd, ctypes.byref(teglalap))
        bal, felso = max(0, teglalap.left), max(0, teglalap.top)
        cimsor = teljes.crop((bal, felso, min(szel, bal + 360), min(mag, felso + 48)))
        puffer = io.BytesIO()
        cimsor.save(puffer, "PNG", optimize=True)
        kepek["cimsor"] = puffer.getvalue()
    print(f"  képernyő {szel}×{mag}", flush=True)
    return kepek


def ikon(futtatok: list[tuple[str, list[str]]], munka: Path, szigoru: bool) -> int:
    if sys.platform != "win32":
        print("ikon: csak Windowson mérhető", flush=True)
        return 0
    hiba = 0
    for nev, parancs in futtatok:
        futas = _egy_inditas(parancs, munka / f"ikon-{nev}", ablakkal=True)
        latott: dict[int, dict] = {}
        kepek: dict[str, bytes] = {}
        elso_ablak: float | None = None
        while futas["folyamat"].poll() is None:
            ablakok = _ablakikonok(futas["folyamat"].pid)
            if ablakok and elso_ablak is None:
                elso_ablak = time.perf_counter()
            # a splash legalább 1,5 s-ig áll: ennyi idő után a tálcagomb és
            # a címsor már végleges — ekkor egyszer lefényképezzük
            if elso_ablak is not None and not kepek and time.perf_counter() - elso_ablak > 1.0:
                kepek = _kepernyokep(next(iter(ablakok)) if ablakok else None)
            for hwnd, adat in ablakok.items():
                regi = latott.get(hwnd)
                # egy ablak ikonja menet közben áll be: a LEGJOBB állapot számít
                if regi is None or sum(1 for k in ("kicsi", "nagy") if adat[k]) >= sum(
                    1 for k in ("kicsi", "nagy") if regi[k]
                ):
                    latott[hwnd] = adat
            if time.perf_counter() - futas["kezdet"] > _IDOKORLAT_MP:
                break
            time.sleep(0.05)
        eredmeny = _bevar(futas)
        print(f"[{nev}] kilépőkód {eredmeny['kod']}, {len(latott)} látható ablak", flush=True)
        van_ikon = False
        for hwnd, adat in latott.items():
            ablak_ikon = bool(adat["kicsi"] or adat["kicsi2"]) and bool(adat["nagy"])
            van_ikon = van_ikon or ablak_ikon or bool(adat["osztaly_ikon"])
            print(
                f"  ablak {hwnd:#x} {adat['osztaly']!r} {adat['cim']!r}: "
                f"WM_GETICON kicsi={adat['kicsi']:#x} nagy={adat['nagy']:#x} "
                f"kicsi2={adat['kicsi2']:#x}; osztályikon={adat['osztaly_ikon']:#x} "
                f"osztály-kicsi={adat['osztaly_kicsi']:#x}",
                flush=True,
            )
        ikonsor = [s for _, s in eredmeny["sorok"] if s.startswith("Alkalmazásikon")]
        if ikonsor:
            print(f"  {ikonsor[-1]}", flush=True)
        for resz, png in kepek.items():
            # A kép a naplóba megy, base64-ben: a CI-melléklet letöltéséhez
            # hitelesítés kellene, a napló viszont mindenhonnan olvasható.
            print(f"  KÉP {nev}/{resz} {len(png)} bájt", flush=True)
            print(f"  -----KEP-KEZDET {nev}/{resz}-----", flush=True)
            kodolt = base64.b64encode(png).decode("ascii")
            for i in range(0, len(kodolt), 4000):
                print("  " + kodolt[i : i + 4000], flush=True)
            print(f"  -----KEP-VEGE {nev}/{resz}-----", flush=True)
        if not latott:
            print("  ⚠️ nem láttunk ablakot (nincs asztali munkamenet?)", flush=True)
        elif not van_ikon:
            print(f"  ❌ {nev}: egyik ablaknak sincs ikonja", flush=True)
            if szigoru:
                hiba = 1
        else:
            print(f"  ✅ {nev}: az ablaknak van ikonja", flush=True)
    return hiba


def main(argv: list[str] | None = None) -> int:
    ertelmezo = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ertelmezo.add_argument("mod", choices=("ido", "ikon"))
    ertelmezo.add_argument("--futtato", action="append", required=True)
    ertelmezo.add_argument("--inditasok", type=int, default=2)
    ertelmezo.add_argument("--szigoru", action="store_true")
    ertelmezo.add_argument("--munka", type=Path, default=None)
    args = ertelmezo.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    munka = args.munka or Path(tempfile.mkdtemp(prefix="picasapy-csomag-meres-"))
    futtatok = _futtatok(args.futtato)
    if args.mod == "ido":
        return ido(futtatok, args.inditasok, munka)
    return ikon(futtatok, munka, args.szigoru)


if __name__ == "__main__":
    sys.exit(main())
