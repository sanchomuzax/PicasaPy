#!/usr/bin/env python3
"""Golden kit — 4–5. effekt-fül referencia-csomagja (#190).

A #190 két új effekt-fülének (`Lomo-szerű`, `HDR-szerű`, `Poszterizálás`,
`Neon` stb.) `filters=` kulcsai jelenleg ISMERETLENEK — ellentétben a
`make_golden_kit.py` szűrőivel, itt NEM tudunk előre `.picasa.ini`-t írni.
A módszer megfordul:

  1. ez a szkript effektenként (ahol csúszkája van, 2–3 beállítással)
     KÜLÖN, beszédes nevű referencia-képet készít (a meglévő
     `make_golden_kit.make_charts`/`pick_photos` alapképeit újrahasznosítva),
  2. a felhasználó a Windows-os Picasa 3.9-ben a fájlnév szerinti sorrendben
     ráhúzza a megfelelő effektet/beállítást az egyes képekre,
  3. a keletkező `.picasa.ini` (a `filters=` sorok) ÉS a kiexportált képek
     kerülnek vissza — ebből fejthető meg a kulcs- és paraméterformátum.

Az egyértelmű effekt↔kép megfeleltetéshez minden kép fájlneve tartalmazza
a fület, a sorszámot és az effekt ASCII-sított magyar nevét, csúszkás
effekteknél a beállítást is (pl. `effekt4_04_hdrszeru_eros.jpg`).

Használat:
    make_golden_kit_effects.py <kimenet_dir>
    make_golden_kit_effects.py <fotok_dir> <kimenet_dir>

A `<fotok_dir>` ELHAGYHATÓ: ha megadod és van benne fénykép, a keret-/
vintage-effektekhez egy valódi fotót is beteszünk; ha nincs (vagy üres a
mappa), fotószerű szintetikus képet generálunk. A kit így fényképek nélkül,
pusztán a `<kimenet_dir>` megadásával is elkészül.
"""
from __future__ import annotations

import importlib.util
import shutil
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

_HERE = Path(__file__).resolve().parent


def _load_make_golden_kit():
    """A meglévő `make_golden_kit.py` betöltése fájlútvonalról.

    A `tools/golden/` szándékosan nem csomag (nincs `__init__.py`) — a
    projekt konvenciója szerint (ld. `tests/golden/test_compare_render.py`)
    az egymásra épülő szkriptek `importlib`-bal töltik be egymást, hogy ne
    kelljen a chart-/fotóválasztó logikát duplikálni.
    """
    spec = importlib.util.spec_from_file_location(
        "make_golden_kit", _HERE / "make_golden_kit.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("make_golden_kit", module)
    spec.loader.exec_module(module)
    return module


_mgk = _load_make_golden_kit()


def slugify(name: str) -> str:
    """Magyar effekt-név → ASCII, fájlnév-biztos szeletke (ékezet nélkül)."""
    ascii_form = (
        unicodedata.normalize("NFKD", name)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    ascii_form = ascii_form.lower().replace(" ", "_").replace("-", "")
    return "".join(c for c in ascii_form if c.isalnum() or c == "_").strip("_")


@dataclass(frozen=True)
class Effect:
    """Egy effekt-gomb a 4. vagy 5. fülön."""

    nev: str  # magyar UI-felirat (a Picasában pontosan ez látszik)
    base: str  # melyik alapképen mérhető jól (kulcs a BASES szótárban)
    beallitasok: tuple[str, ...] = ("alap",)  # tuple → biztonságos default


# ------------------------------------------------------ 4. fül effektjei
# Sorrend = a Picasa UI-ban látható sorrend (az issue felsorolása szerint).
# `beallitasok`: ha az effektnek csúszkája van, 2-3 külön kép (alap +
# eltérő beállítás) — a pontos csúszkaérték a felhasználó döntése, csak
# jelölje az UTMUTATO.md táblázatában, mit állított be.
EFFECTS_4 = [
    Effect("Infravörös film", "photo"),
    Effect("Lomo-szerű", "photo"),
    Effect("Holga-szerű", "photo"),
    Effect("HDR-szerű", "photo", ("alap", "gyenge", "eros")),
    Effect("Kinemaszkóp", "photo"),
    Effect("Orton-szerű", "photo", ("alap", "gyenge", "eros")),
    Effect("60-as évek", "photo"),
    Effect("Színinvertálás", "ramp"),
    Effect("Hőtérkép", "ramp"),
    Effect("Áttűnés", "ramp", ("alap", "gyenge", "eros")),
    Effect("Poszterizálás", "ramp", ("alap", "durva", "finom")),
    Effect("Kéttónusú", "ramp", ("alap", "mas_szinpar")),
]

# ------------------------------------------------------ 5. fül effektjei
EFFECTS_5 = [
    Effect("Felpörgetés", "detail", ("alap", "gyenge", "eros")),
    Effect("Lágyítás", "detail", ("alap", "gyenge", "eros")),
    Effect("Képpontnagyítás", "detail", ("alap", "durva", "finom")),
    Effect("Fókusznagyítás", "photo", ("alap", "gyenge", "eros")),
    Effect("Ceruzarajz", "detail", ("alap", "gyenge", "eros")),
    Effect("Neon", "detail", ("alap", "gyenge", "eros")),
    Effect("Képregény", "photo"),
    Effect("Szegély", "photo", ("alap", "keskeny", "szeles")),
    Effect("Árnyékvetés", "photo", ("alap", "eros")),
    Effect("Múzeumi matt", "photo", ("alap", "szeles")),
    Effect("Polaroid", "photo", ("alap", "elforgatva")),
]


def _synthetic_photo(path: Path) -> Path:
    """Fotószerű szintetikus alapkép valódi fénykép HIÁNYÁBAN (#190).

    A keret-/árnyék-/vintage-effektek (Szegély, Polaroid, Lomo, Árnyékvetés
    stb.) elvont charton nem beszédesek — de valódi fotóra sincs feltétlenül
    szükség: egy lágy színátmenetekből, égbolt-/tájszerű sávokból és enyhe
    zajból álló kép bőven elég ahhoz, hogy az effekt hatása látszódjon és a
    `filters=` kulcs kiolvasható legyen. Így a kit fotókönyvtár nélkül is
    legenerálható (a korábbi verzió itt elszállt, ha nem volt fénykép).
    """
    np = _mgk.np
    cv2 = _mgk.cv2
    h, w = 1200, 1600
    img = np.zeros((h, w, 3), np.uint8)
    # függőleges ég→talaj színátmenet (meleg-hideg), hogy tónusa legyen
    top = np.array([210, 170, 120], np.float32)   # BGR: világos, hűvös ég
    bottom = np.array([40, 90, 130], np.float32)   # melegebb, sötétebb talaj
    for y in range(h):
        t = y / (h - 1)
        img[y, :] = (top * (1 - t) + bottom * t).astype(np.uint8)
    # néhány lágy, eltérő tónusú folt (táj-/tárgyszerű régiók)
    rng = np.random.default_rng(190)
    for _ in range(6):
        cx, cy = int(rng.integers(0, w)), int(rng.integers(0, h))
        r = int(rng.integers(120, 340))
        color = rng.integers(30, 220, 3).tolist()
        cv2.circle(img, (cx, cy), r, color, -1)
    img = cv2.GaussianBlur(img, (0, 0), 25)        # lágyítás → természetes
    noise = rng.integers(-12, 12, (h, w, 3), dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    cv2.imwrite(str(path), img, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return path


def _base_images(base_dir: Path, photos_dir: Path | None) -> dict[str, Path]:
    """A négy újrahasznosított alapkép (a meglévő kit chart/fotó-logikájával).

    - `ramp`: `chart_ramp.jpg` — szürke/RGB gradiens, tónusgörbék méréséhez
      (invertálás, hőtérkép-színezés, poszterizálási szintek, kéttónus).
    - `color`: `chart_color.jpg` — HSV-mező + bőrtónusok (itt nem használt
      alapból, de meghagyva bővíthetőségnek).
    - `detail`: `chart_detail.jpg` — sakktáblák/vonalpárok élkereső és
      pixelező effektekhez (Ceruzarajz, Neon, Felpörgetés, Lágyítás,
      Képpontnagyítás).
    - `photo`: kerethez/árnyékhoz/vintage-hatáshoz (Szegély, Polaroid, Lomo
      stb.). Ha a `photos_dir` megvan és van benne fénykép, egy valódi
      fotót használunk; ha nincs (üres mappa vagy nincs megadva), fotószerű
      szintetikus képet generálunk — a kit így fotókönyvtár nélkül is kész.
    """
    charts = _mgk.make_charts(base_dir)
    photo_path = base_dir / "photo00.jpg"
    photos: list = []
    if photos_dir is not None:
        try:
            photos = _mgk.pick_photos(photos_dir, n=1)
        except (IndexError, ValueError):
            # üres/olvashatatlan fotómappa: a pick_photos üres listán
            # indexel — nem hiba, csak nincs valódi fotó, generálunk egyet
            photos = []
    if photos:
        shutil.copy2(photos[0], photo_path)
    else:
        _synthetic_photo(photo_path)
    return {
        "ramp": charts["chart_ramp.jpg"],
        "color": charts["chart_color.jpg"],
        "detail": charts["chart_detail.jpg"],
        "photo": photo_path,
    }


def _build_tab(
    tab_no: int,
    effects: list[Effect],
    bases: dict[str, Path],
    fdir: Path,
) -> list[tuple[str, str, str, str]]:
    """Egy fül (4 vagy 5) referencia-képeinek legyártása.

    Visszaadja a sorokat az UTMUTATO.md táblázatához:
    (fájlnév, effekt neve, beállítás, alapkép-forrás).
    """
    fdir.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, eff in enumerate(effects, start=1):
        slug = slugify(eff.nev)
        base = bases[eff.base]
        for beallitas in eff.beallitasok:
            suffix = "" if beallitas == "alap" and len(eff.beallitasok) == 1 else (
                f"_{beallitas}"
            )
            name = f"effekt{tab_no}_{i:02d}_{slug}{suffix}.jpg"
            shutil.copy2(base, fdir / name)
            rows.append((name, eff.nev, beallitas, eff.base))
    return rows


_ALAPKEP_LEIRAS = {
    "ramp": "szürke/RGB gradiens (chart_ramp.jpg)",
    "color": "HSV-színmező (chart_color.jpg)",
    "detail": "sakktábla + vonalpárok (chart_detail.jpg)",
    "photo": "valódi fénykép",
}

# a fájlnév-szeletke (`slugify`-jal ASCII-sítva) → emberi, ékezetes felirat
# a táblázat "Beállítás" oszlopához (a fájlnévben az ékezet zavarna Windowson)
_BEALLITAS_FELIRAT = {
    "alap": "alap",
    "gyenge": "gyenge",
    "eros": "erős",
    "durva": "durva",
    "finom": "finom",
    "keskeny": "keskeny",
    "szeles": "széles",
    "elforgatva": "elforgatva",
    "mas_szinpar": "más színpár",
}


def _write_utmutato(out: Path, rows4: list, rows5: list) -> None:
    """Magyar nyelvű, lépésenkénti útmutató a Windows-os kézi munkához."""
    lines = [
        "# Útmutató — 4–5. effekt-fül referencia-csomag (#190)",
        "",
        "Ez a mappa a Picasa 3.9 két új effekt-fülének (a #20-as jegy "
        "képernyőképein a zöld és kék ecset ikon) `filters=` kulcsainak "
        "dekódolásához készült. A teendő: minden képre alkalmazd a "
        "fájlnévhez tartozó effektet a Windows-os Picasában, majd hozd "
        "vissza a `.picasa.ini`-t és az exportált képeket.",
        "",
        "## 1. lépés — átvitel a Windows-gépre",
        "",
        "- Másold át ezt a teljes mappát (`golden-kit-effects` vagy amilyen "
        "névre kimásoltad) egy **friss, üres** mappába a Windows-gépen, "
        "pl. `C:\\PicasaPy-teszt-effektek\\`.",
        "- A Picasában: **Mappák → Mappa hozzáadása a Picasához** (vagy "
        "húzd be a Fájlkezelőből), és várd meg, amíg a Picasa beolvassa "
        "(„Scan Once” elég, nem kell folyamatos figyelést kérni rá).",
        "",
        "## 2. lépés — effektek ráhúzása (fájlnév szerinti sorrendben)",
        "",
        "Nyisd meg a képeket egyenként (dupla klikk → szerkesztő nézet), "
        "és a táblázat szerint kattints a megfelelő fülre és effekt-gombra. "
        "Ahol a fájlnév végén beállítás-jelölés van (pl. `_gyenge`, "
        "`_eros`), és az effektnek TÉNYLEG van csúszkája/paramétere a "
        "Picasában, állítsd be úgy, hogy a beállítások jól megkülönböztethetők "
        "legyenek (pl. a csúszka minimumához közel = „gyenge”, maximumához "
        "közel = „eros”) — a pontos számértéket nem kell fejben tartanod, "
        "az a `.picasa.ini`-ből úgyis kiderül. **Ha egy effektnek NINCS "
        "csúszkája/paramétere** (a szkript ezt csak feltételezte), elég csak "
        "az `alap` képre alkalmazni — a többi beállítás-változatot hagyd "
        "figyelmen kívül, arra nincs szükség.",
        "",
        "### 4. fül",
        "",
        "| # | Fájlnév | Effekt neve | Beállítás | Alapkép |",
        "|---|---|---|---|---|",
    ]
    for i, (name, nev, beallitas, base_key) in enumerate(rows4, start=1):
        lines.append(
            f"| {i} | `{name}` | {nev} | "
            f"{_BEALLITAS_FELIRAT[beallitas]} | {_ALAPKEP_LEIRAS[base_key]} |"
        )
    lines += [
        "",
        "### 5. fül",
        "",
        "| # | Fájlnév | Effekt neve | Beállítás | Alapkép |",
        "|---|---|---|---|---|",
    ]
    for i, (name, nev, beallitas, base_key) in enumerate(rows5, start=1):
        lines.append(
            f"| {i} | `{name}` | {nev} | "
            f"{_BEALLITAS_FELIRAT[beallitas]} | {_ALAPKEP_LEIRAS[base_key]} |"
        )
    lines += [
        "",
        "## 3. lépés — mentés, majd a `.picasa.ini` visszahozása",
        "",
        "**Ez a lépés a fontosabb — enélkül a jegy fő célja nem teljesül.**",
        "",
        "- Ha végeztél az összes képpel, **lépj ki a mappából és zárd be a "
        "Picasát** — a `.picasa.ini`-t a Picasa nem mindig azonnal írja ki "
        "lemezre, csak kilépéskor/mappaváltáskor.",
        "- A rejtett fájlok megjelenítése kell hozzá: Fájlkezelő → **Nézet "
        "→ Megjelenítés → Rejtett elemek** bekapcsolása (a `.picasa.ini` "
        "pont miatt rejtett).",
        "- Ha a pontos nevű fájlt (`.picasa.ini`) nem találod, keress "
        "`Picasa.ini`-re is (pont nélkül — régebbi verziók így írták).",
        "- Másold vissza EZT az egy fájlt (a mappa gyökeréből) ide, erre a "
        "gépre — akárhogy is: rávezetéknévvel csatolva, felhő-mappán át, "
        "vagy pendrive-on.",
        "",
        "## 4. lépés — exportálás, majd a képek visszahozása",
        "",
        "- A Picasában jelöld ki mind a képeket (Ctrl+A), majd **Fájl → "
        "Exportálás** (Use Original Size / Maximum méret) — célként az "
        "ebben a mappában lévő `export` alkönyvtárat add meg (vagy ha az "
        "nincs meg Windowson, hozz létre egy `export` nevű almappát).",
        "- Az exportált fájlokat is hozd vissza ugyanúgy, mint a "
        "`.picasa.ini`-t.",
        "",
        "## Sorrend, ha kevés az idő",
        "",
        "Először a `.picasa.ini`-t hozd vissza — ebből már a jegy nagy "
        "része (a `filters=` kulcsok azonosítása) elvégezhető. Az "
        "exportált képek a második, render-kalibrációs körhöz kellenek, "
        "ráérnek.",
        "",
    ]
    (out / "UTMUTATO.md").write_text("\n".join(lines), encoding="utf-8")


def _friss_kimenet(out: Path) -> None:
    """A kimeneti mappa előkészítése Windows-/OneDrive-tűrően (#190).

    A korábbi feltétel nélküli `shutil.rmtree` OneDrive alá szinkronizált
    mappán `PermissionError`-ral (WinError 5) bukott: a szinkronkliens még
    fogja a fájlokat/könyvtárakat. Stratégia:
      1. törlési kísérlet a csak-olvasható attribútum levételével és rövid
         újrapróbálkozással (a OneDrive pár másodperc alatt elenged),
      2. ha a mappa így sem törölhető, NEM állunk le: a generálás a meglévő
         mappába, FELÜLÍRÁSSAL folytatódik (minden fájlt újraírunk; a
         `.picasa.ini`-t és az exportokat a felhasználó teszi bele, azokat
         nem bántjuk).
    """
    import os
    import stat
    import time

    if not out.exists():
        return

    def _irhatova(func, p, _exc):
        os.chmod(p, stat.S_IWRITE)
        func(p)

    for _ in range(3):
        try:
            shutil.rmtree(out, onerror=_irhatova)
            return
        except PermissionError:
            time.sleep(1.0)  # zárolás (OneDrive/víruskereső) — várunk kicsit
    print(
        f"FIGYELEM: a meglévő {out} mappát nem lehetett törölni (zárolja a"
        " OneDrive vagy a víruskereső) — a tartalmát FELÜLÍRVA folytatom."
    )


def main() -> None:
    # Egy argumentum = csak kimeneti mappa (szintetikus fotóval);
    # kettő = fotómappa + kimeneti mappa.
    if len(sys.argv) == 2:
        photos_dir = None
        out = Path(sys.argv[1]).expanduser()
    elif len(sys.argv) == 3:
        photos_dir = Path(sys.argv[1]).expanduser()
        out = Path(sys.argv[2]).expanduser()
    else:
        print(__doc__)
        sys.exit(1)
    _friss_kimenet(out)
    base_dir = out / "00-base"
    base_dir.mkdir(parents=True, exist_ok=True)

    bases = _base_images(base_dir, photos_dir)
    rows4 = _build_tab(4, EFFECTS_4, bases, out / "effekt4")
    rows5 = _build_tab(5, EFFECTS_5, bases, out / "effekt5")
    _write_utmutato(out, rows4, rows5)

    (out / "export").mkdir(exist_ok=True)

    total = len(rows4) + len(rows5)
    print(f"Effekt-kit kész: {out}")
    print(f"  4. fül: {len(EFFECTS_4)} effekt, {len(rows4)} kép")
    print(f"  5. fül: {len(EFFECTS_5)} effekt, {len(rows5)} kép")
    print(f"  összesen {total} referencia-kép, útmutató: UTMUTATO.md")


if __name__ == "__main__":
    main()
