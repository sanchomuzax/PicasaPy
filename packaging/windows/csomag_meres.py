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

## Valósághű indulás (#6355)

    python csomag_meres.py ido --futtato csomagolt=dist/PicasaPy/PicasaPy.exe \
        --kepek 2000 --halozati-export "\\\\192.0.2.1\\picasa\\export" --hatar-mp 5

Üres könyvtáron a csomagolt program 4-5 s alatt indul, a tulajdonos gépén
viszont 30-40 s alatt: az idő az ADATTAL nő. Ez a mód ezért sok képpel
(`--kepek`, mappánként 50) és egy elérhetetlen hálózati exportcéllal
(`--halozati-export`, a tulajdonos NAS-ának mintájára) indít. A
`192.0.2.0/24` dokumentációs címtartomány: oda soha semmi nem válaszol, a
Windows tehát kivárja a hálózati időkorlátot. `--hatar-mp` mellett bukik,
ha a főablak bármelyik indításnál ennél később jelenik meg.

`--indulo-hatar-ms 1000` bekapcsolja a valódi Windows-ablakos mérést is: a
naplójelzésből kiszámolja a külön indulóablak megjelenési idejét, a képernyőből
pedig ellenőrzi a splash ténylegesen kirajzolt, szöveg nélküli alsó sávját.
Alapértelmezésben ez a kapu ki van kapcsolva.

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
_INDULOABLAK = "Az indulóablak megjelent"

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


#: a valósághű könyvtár mappánkénti képszáma (#6355)
_KEP_MAPPANKENT = 50

#: a QSettings windowsos helye (szervezet és alkalmazás: PicasaPy)
_BEALLITAS_KULCS = r"Software\PicasaPy\PicasaPy\export"
_EXPORT_ERTEK = "exportedfolders"


def _kepekkel_tolt(konyvtar: Path, darab: int) -> None:
    """`darab` kis JPEG, mappánként `_KEP_MAPPANKENT`; a meglévőt nem írja újra."""
    if darab <= 0 or (konyvtar / ".kepek-kesz").exists():
        return
    from PIL import Image

    for sorszam in range(darab):
        mappa = konyvtar / f"album-{sorszam // _KEP_MAPPANKENT:03d}"
        mappa.mkdir(parents=True, exist_ok=True)
        szin = (sorszam * 37 % 256, sorszam * 91 % 256, sorszam * 13 % 256)
        Image.new("RGB", (320, 240), szin).save(mappa / f"kep-{sorszam:05d}.jpg", "JPEG")
    (konyvtar / ".kepek-kesz").write_text("", encoding="utf-8")


def _exportcelok_beallitasa(utak: list[str]) -> list[str] | None:
    """A nyilvántartott exportcélok beírása a PicasaPy beállításai közé;
    a korábbi értéket adja vissza (visszaállításhoz). Csak Windowson."""
    import winreg

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _BEALLITAS_KULCS) as kulcs:
        try:
            korabbi, _ = winreg.QueryValueEx(kulcs, _EXPORT_ERTEK)
        except OSError:
            korabbi = None
        winreg.SetValueEx(kulcs, _EXPORT_ERTEK, 0, winreg.REG_MULTI_SZ, list(utak))
    return korabbi


def _exportcelok_visszaallitasa(korabbi: list[str] | None) -> None:
    import winreg

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, _BEALLITAS_KULCS) as kulcs:
        if korabbi is None:
            try:
                winreg.DeleteValue(kulcs, _EXPORT_ERTEK)
            except OSError:
                pass
        else:
            winreg.SetValueEx(kulcs, _EXPORT_ERTEK, 0, winreg.REG_MULTI_SZ, korabbi)


def _profil(gyoker: Path, kepek: int = 0) -> tuple[dict[str, str], Path]:
    """Elszigetelt profil és egy könyvtár, a CI meglévő füstpróbájának
    mintájára (`package.yml`); `kepek` > 0 esetén annyi képpel (#6355)."""
    konyvtar = gyoker / "library"
    profil = gyoker / "profile"
    konyvtar.mkdir(parents=True, exist_ok=True)
    _kepekkel_tolt(konyvtar, kepek)
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


def _egy_inditas(
    parancs: list[str],
    gyoker: Path,
    *,
    ablakkal: bool,
    kepek: int = 0,
    indulo_hatar_ms: float | None = None,
) -> dict:
    env, konyvtar = _profil(gyoker, kepek)
    valodi_ablak = ablakkal or indulo_hatar_ms is not None
    if valodi_ablak:
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
        "indulo_hatar_ms": indulo_hatar_ms,
        "indulo_kep_kotelezo": sys.platform == "win32" and indulo_hatar_ms is not None,
    }


def _bevar(futas: dict) -> dict:
    folyamat = futas["folyamat"]
    indulo_kep = None
    indulo_kep_info = None
    indulo_kep_hiba = None
    induloablak_latszott = False
    if futas["indulo_kep_kotelezo"]:
        hatarido = time.monotonic() + _IDOKORLAT_MP
        while True:
            try:
                kimenet, _ = folyamat.communicate(timeout=0.05)
                break
            except subprocess.TimeoutExpired:
                if not induloablak_latszott:
                    for hwnd, ablak in _ablakikonok(folyamat.pid).items():
                        if not ablak["cim"].casefold().startswith("picasapy startup"):
                            continue
                        induloablak_latszott = True
                        indulo_kep, indulo_kep_info, indulo_kep_hiba = _induloablak_kepe(hwnd)
                        break
                if time.monotonic() >= hatarido:
                    folyamat.kill()
                    kimenet, _ = folyamat.communicate()
                    break
    else:
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
        "indulo_hatar_ms": futas["indulo_hatar_ms"],
        "indulo_kep_kotelezo": futas["indulo_kep_kotelezo"],
        "indulo_kep": indulo_kep,
        "indulo_kep_info": indulo_kep_info,
        "indulo_kep_hiba": indulo_kep_hiba,
    }


def _jelentes(nev: str, sorszam: int, eredmeny: dict) -> str:
    sorok = eredmeny["sorok"]
    fej = (
        f"[{nev} #{sorszam}] kilépőkód {eredmeny['kod']}, "
        f"falióra {eredmeny['fal_mp']:.2f} s"
    )
    if not sorok:
        reszletek = _indulo_jelentes(eredmeny)
        return (
            fej
            + "\n  (a hibanaplóban nincs indulási jelzés)\n"
            + "\n".join(reszletek)
            + "\n"
            + eredmeny["kimenet"][-2000:]
        )
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
        *_indulo_jelentes(eredmeny),
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


def _indulo_jelentes(eredmeny: dict) -> list[str]:
    if eredmeny.get("indulo_hatar_ms") is None:
        return []
    mert = induloablak_ms(eredmeny)
    sor = "  indulóablak megjelenése a folyamatindítástól: "
    sor += f"{mert:.0f} ms" if mert is not None else "NEM jelent meg"
    reszletek = [sor]
    info = eredmeny.get("indulo_kep_info")
    if info is not None:
        width, height, colors = info
        reszletek.append(
            f"  renderelt indulókép ellenőrizve: {width}×{height}, "
            f"az alsó szöveg nélküli sor {colors} színe"
        )
    elif eredmeny.get("indulo_kep_kotelezo"):
        reszletek.append(
            "  renderelt indulókép ellenőrzése sikertelen: "
            + str(eredmeny.get("indulo_kep_hiba") or "nem készült képernyőkép")
        )
    return reszletek


def induloablak_ms(eredmeny: dict) -> float | None:
    """Az indulóablak naplójelzésének ideje a folyamat indításától, ms-ban."""
    return next(
        (
            (ido - eredmeny["indult"]).total_seconds() * 1000
            for ido, szakasz in eredmeny["sorok"]
            if szakasz == _INDULOABLAK
        ),
        None,
    )


def indulo_hatar_hiba(nev: str, eredmeny: dict, hatar_ms: float | None) -> str | None:
    """A korai splash idő- és Windowsos képkapuja."""
    if hatar_ms is None:
        return None
    mert = induloablak_ms(eredmeny)
    if mert is None:
        return f"{nev}: az indulóablak nem jelent meg"
    if mert > hatar_ms:
        return f"{nev}: az indulóablak {mert:.0f} ms alatt jelent meg, a határ {hatar_ms:.0f} ms"
    if eredmeny.get("indulo_kep_kotelezo") and eredmeny.get("indulo_kep_info") is None:
        return (
            f"{nev}: az indulóablak {mert:.0f} ms alatt jelent meg, de a renderelt képe "
            "nem volt ellenőrizhető"
        )
    return None


def indulo_kozepertek_hiba(
    nev: str, eredmenyek: list[dict], hatar_ms: float | None
) -> str | None:
    """Az indulóablak kapuja több indítás KÖZÉPÉRTÉKÉRE (#6367).

    Minden indításnál meg kell jelennie; a határ a középértékre vonatkozik, és
    legalább egy indításnál a renderelt képnek is ellenőrizhetőnek kell lennie
    (Windowson)."""
    if hatar_ms is None or not eredmenyek:
        return None
    idok = [induloablak_ms(eredmeny) for eredmeny in eredmenyek]
    if any(ido is None for ido in idok):
        return f"{nev}: az indulóablak nem jelent meg minden indításnál"
    rendezett = sorted(idok)
    kozep = rendezett[len(rendezett) // 2]
    if kozep > hatar_ms:
        return (
            f"{nev}: az indulóablak középértéke {kozep:.0f} ms, a határ {hatar_ms:.0f} ms"
        )
    if any(e.get("indulo_kep_kotelezo") for e in eredmenyek) and not any(
        e.get("indulo_kep_info") is not None for e in eredmenyek
    ):
        return f"{nev}: az indulóablak renderelt képe egyik indításnál sem volt ellenőrizhető"
    return None


def foablak_mp(eredmeny: dict) -> float | None:
    """A folyamat indításától a főablak megjelenéséig eltelt idő, másodpercben;
    `None`, ha a főablak nem jelent meg."""
    return next(
        (
            (ido - eredmeny["indult"]).total_seconds()
            for ido, szakasz in eredmeny["sorok"]
            if szakasz == _SIKER
        ),
        None,
    )


def hatar_hiba(nev: str, eredmeny: dict, hatar_mp: float | None) -> str | None:
    """Hibaüzenet, ha a főablak a határnál később (vagy egyáltalán nem) jelent
    meg; különben `None`."""
    if hatar_mp is None:
        return None
    mert = foablak_mp(eredmeny)
    if mert is None:
        return f"{nev}: a főablak nem jelent meg"
    if mert > hatar_mp:
        return f"{nev}: a főablak {mert:.2f} s alatt jelent meg, a határ {hatar_mp:.1f} s"
    return None


def ido(
    futtatok: list[tuple[str, list[str]]],
    inditasok: int,
    munka: Path,
    elvart_verzio: str | None = None,
    *,
    kepek: int = 0,
    halozati_export: list[str] | None = None,
    hatar_mp: float | None = None,
    indulo_hatar_ms: float | None = None,
    elso_hatar_mp: float | None = None,
) -> int:
    if indulo_hatar_ms is not None and sys.platform != "win32":
        raise SystemExit("--indulo-hatar-ms csak Windowson mérhető")
    hiba = 0
    korabbi = _exportcelok_beallitasa(halozati_export) if halozati_export else None
    try:
        for nev, parancs in futtatok:
            hiba |= _ido_futtato(
                nev,
                parancs,
                inditasok,
                munka,
                elvart_verzio,
                kepek,
                hatar_mp,
                indulo_hatar_ms,
                elso_hatar_mp,
            )
    finally:
        if halozati_export:
            _exportcelok_visszaallitasa(korabbi)
    return hiba


def _ido_futtato(
    nev: str,
    parancs: list[str],
    inditasok: int,
    munka: Path,
    elvart_verzio: str | None,
    kepek: int,
    hatar_mp: float | None,
    indulo_hatar_ms: float | None,
    elso_hatar_mp: float | None = None,
) -> int:
    hiba = 0
    gyoker = munka / (f"ido-{nev}-{kepek}kep" if kepek else f"ido-{nev}")
    eredmeny: dict = {}
    indulo_eredmenyek: list[dict] = []
    for sorszam in range(1, inditasok + 1):
        eredmeny = _bevar(
            _egy_inditas(
                parancs,
                gyoker,
                ablakkal=False,
                kepek=kepek,
                indulo_hatar_ms=indulo_hatar_ms,
            )
        )
        print(_jelentes(nev, sorszam, eredmeny), flush=True)
        if sorszam == 1 and eredmeny.get("indulo_kep"):
            print(f"  KÉP {nev}/induloablak {len(eredmeny['indulo_kep'])} bájt", flush=True)
            print("  -----KEP-KEZDET induloablak-----", flush=True)
            kodolt = base64.b64encode(eredmeny["indulo_kep"]).decode("ascii")
            for i in range(0, len(kodolt), 4000):
                print("  " + kodolt[i : i + 4000], flush=True)
            print("  -----KEP-VEGE induloablak-----", flush=True)
        if eredmeny["kod"] != 0:
            hiba = 1
        if elvart_verzio is not None:
            # #6348: a csomagolt program 0.0.0+ismeretlen-t mutatott
            sor = f"PicasaPy-verzió: {elvart_verzio}"
            if not any(s == sor for _, s in eredmeny["sorok"]):
                print(f"  ❌ {nev}: a naplóban nincs „{sor}”", flush=True)
                hiba = 1
        # a határ MINDEN indításra vonatkozik: a CI első mérésén épp az első
        # indulás volt 24,9 s (elérhetetlen hálózati gyökér), a többi 4,1 s.
        # Az első indulásnak (friss profil) külön határa lehet: ilyenkor a Qt
        # a felület QML-fájljait egyszer lefordítja és eltárolja (#6374).
        hatar = elso_hatar_mp if sorszam == 1 and elso_hatar_mp is not None else hatar_mp
        uzenet = hatar_hiba(f"{nev} #{sorszam}", eredmeny, hatar)
        if uzenet is not None:
            print(f"  ❌ {uzenet}", flush=True)
            hiba = 1
        indulo_eredmenyek.append(eredmeny)
    # az indulóablak kapuja a mérések KÖZÉPÉRTÉKÉT nézi: a windowsos CI-gép
    # valódi ablakos módban egy-egy indításnál 8 s-os kiugrást mutatott
    # (a többi 0,4-0,8 s), ami a futtatógép zaja, nem a programé
    indulo_uzenet = indulo_kozepertek_hiba(nev, indulo_eredmenyek, indulo_hatar_ms)
    if indulo_uzenet is not None:
        print(f"  ❌ {indulo_uzenet}", flush=True)
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
    return (png, info, hiba) if hiba is None else (None, None, hiba)


def _renderelt_indulokep_ellenorzese(
    png: bytes,
) -> tuple[tuple[int, int, int] | None, str | None]:
    """A szöveg nélküli alsó sáv sorát vizsgálja, betűképpontok nélkül."""
    import io

    from PIL import Image

    try:
        with Image.open(io.BytesIO(png)) as kep:
            kep = kep.convert("RGB")
    except (OSError, ValueError) as hiba:
        return None, f"érvénytelen képernyőkép: {hiba}"
    if kep.width <= 0 or kep.height <= 0:
        return None, "a renderelt indulókép mérete üres"
    sor = [kep.getpixel((x, kep.height - 2)) for x in range(kep.width)]
    szinszam = len(set(sor))
    piros, zold, kek = kep.getpixel((kep.width // 2, kep.height - 2))
    if szinszam < 2 or kek <= max(piros, zold):
        return None, "a renderelt indulókép alsó sávja hiányzik vagy nem kék"
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


def main(argv: list[str] | None = None) -> int:
    ertelmezo = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ertelmezo.add_argument("mod", choices=("ido", "ikon"))
    ertelmezo.add_argument("--futtato", action="append", required=True)
    ertelmezo.add_argument("--inditasok", type=int, default=2)
    ertelmezo.add_argument("--szigoru", action="store_true")
    ertelmezo.add_argument("--elvart-verzio", default=None)
    ertelmezo.add_argument("--munka", type=Path, default=None)
    ertelmezo.add_argument("--kepek", type=int, default=0)
    ertelmezo.add_argument("--halozati-export", action="append", default=None)
    ertelmezo.add_argument("--hatar-mp", type=float, default=None)
    ertelmezo.add_argument("--elso-hatar-mp", type=float, default=None)
    ertelmezo.add_argument("--indulo-hatar-ms", type=float, default=None)
    args = ertelmezo.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    munka = args.munka or Path(tempfile.mkdtemp(prefix="picasapy-csomag-meres-"))
    futtatok = _futtatok(args.futtato)
    if args.mod == "ido":
        return ido(
            futtatok,
            args.inditasok,
            munka,
            args.elvart_verzio,
            kepek=args.kepek,
            halozati_export=args.halozati_export,
            hatar_mp=args.hatar_mp,
            elso_hatar_mp=args.elso_hatar_mp,
            indulo_hatar_ms=args.indulo_hatar_ms,
        )
    return ikon(futtatok, munka, args.szigoru)


if __name__ == "__main__":
    sys.exit(main())
