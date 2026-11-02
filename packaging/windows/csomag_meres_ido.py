"""Csomagolt PicasaPy-program indulási idejének mérése."""

from __future__ import annotations

import base64
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from csomag_meres_kozos import (
    _BEALLITAS_KULCS,
    _EXPORT_ERTEK,
    _IDOKORLAT_MP,
    _INDULOABLAK,
    _KEP_MAPPANKENT,
    _SIKER,
    _SOR,
)

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
    ablakikonok = globals().get("_ablakikonok")
    induloablak_kepe = globals().get("_induloablak_kepe")
    if ablakikonok is None or induloablak_kepe is None:
        from csomag_meres_windows import _ablakikonok as ablakikonok
        from csomag_meres_windows import _induloablak_kepe as induloablak_kepe

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
                    for hwnd, ablak in ablakikonok(folyamat.pid).items():
                        if not ablak["cim"].casefold().startswith("picasapy startup"):
                            continue
                        induloablak_latszott = True
                        indulo_kep, indulo_kep_info, indulo_kep_hiba = induloablak_kepe(hwnd)
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
) -> int:
    hiba = 0
    gyoker = munka / (f"ido-{nev}-{kepek}kep" if kepek else f"ido-{nev}")
    # Az önálló előfordítás ugyanazzal a profillal modellezi az Inno Setup
    # futását, közvetlenül az első mért indítás előtt.
    from qml_cache_warmup import melegitsd_qml_cache

    profil_env, _konyvtar = _profil(gyoker, kepek)
    melegitsd_qml_cache(parancs, profil_env)
    eredmeny: dict = {}
    indulo_eredmenyek: list[dict] = []
    for sorszam in range(1, inditasok + 1):
        inditas_elott = time.time()
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
        if sorszam == 1:
            from profil_valtozas import uj_fajlok

            for sor in uj_fajlok(gyoker / "profile", inditas_elott):
                print(f"  profilba írt: {sor}", flush=True)
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
        uzenet = hatar_hiba(f"{nev} #{sorszam}", eredmeny, hatar_mp)
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

__all__ = (
    "_bevar",
    "_egy_inditas",
    "_exportcelok_beallitasa",
    "_exportcelok_visszaallitasa",
    "_ido_futtato",
    "_indulo_jelentes",
    "_jelentes",
    "_kepekkel_tolt",
    "_naplo_sorai",
    "_profil",
    "foablak_mp",
    "hatar_hiba",
    "ido",
    "indulo_hatar_hiba",
    "indulo_kozepertek_hiba",
    "induloablak_ms",
)
