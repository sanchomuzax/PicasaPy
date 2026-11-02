"""Windowsos ablak-, ikon- és képernyőkép-segédek."""

from __future__ import annotations

import base64
import sys
import time
from pathlib import Path

from csomag_meres_kozos import _IDOKORLAT_MP
from csomag_meres_ido import _bevar, _egy_inditas

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

def _induloablak_kepe(hwnd: int) -> tuple[bytes | None, tuple[int, int, int] | None, str | None]:
    """A valódi splashablak renderelt képét rögzíti és ellenőrzi."""
    import ctypes
    import io
    from ctypes import wintypes

    from PIL import ImageGrab

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.GetWindowRect.restype = wintypes.BOOL
    teglalap = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(teglalap)):
        return None, None, "a Windows nem adta vissza az ablak helyét"
    bal, felso, jobb, also = (
        teglalap.left,
        teglalap.top,
        teglalap.right,
        teglalap.bottom,
    )
    if jobb <= bal or also <= felso:
        return None, None, "az indulóablak képkockája üres"
    try:
        kep = ImageGrab.grab(bbox=(bal, felso, jobb, also), all_screens=True).convert("RGB")
    except OSError as hiba:
        return None, None, f"képernyőkép nem készült: {hiba}"
    puffer = io.BytesIO()
    kep.save(puffer, "PNG", optimize=True)
    png = puffer.getvalue()
    info, hiba = _renderelt_indulokep_ellenorzese(png)
    # a hibás kép is visszamegy: a jelentés megmutatja, mi látszott (#6426)
    return png, info, hiba

def _renderelt_indulokep_ellenorzese(
    png: bytes,
) -> tuple[tuple[int, int, int] | None, str | None]:
    """A fehér kártyát és a rajta ülő logót vizsgálja (#6378).

    A logó közepén átmenő sorban fehér háttér ÉS attól eltérő, sötétebb
    képpontok (logó, szójel) is vannak."""
    import io

    from PIL import Image

    try:
        with Image.open(io.BytesIO(png)) as kep:
            kep = kep.convert("RGB")
    except (OSError, ValueError) as hiba:
        return None, f"érvénytelen képernyőkép: {hiba}"
    if kep.width <= 0 or kep.height <= 0:
        return None, "a renderelt indulókép mérete üres"
    sor = [kep.getpixel((x, kep.height // 2)) for x in range(kep.width)]
    szinszam = len(set(sor))
    feher = sum(1 for kp in sor if min(kp) >= 240)
    tartalom = sum(1 for kp in sor if min(kp) < 200)
    if feher < kep.width // 3 or tartalom < kep.width // 20:
        return None, "a renderelt indulóképen nincs fehér kártya logóval"
    return (kep.width, kep.height, szinszam), None

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

__all__ = (
    "_ablakikonok",
    "_induloablak_kepe",
    "_kepernyokep",
    "_renderelt_indulokep_ellenorzese",
    "ikon",
)
