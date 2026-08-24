r"""Az „Exportálás mappába" párbeszéd MEGŐRZÖTT beállításai (#1138).

Az eredeti levezetése: `docs/specs/export-parbeszed.md` 4. és 13.7
szakasz. A `0x00738c00` a `Preferences` alól olvassa vissza a kulcsokat, a
`0x00739960` írja ki őket — és a 13.7 mérése szerint **egyetlen menetben,
csak az elfogadáskor**: a közös párbeszéd-lezáró (`0x008d2720`) a
`vt[0x164]`-et hívja, ha a lezárási kód 0. A **Mégse** ága a `vt[0x168]`,
ami az üres tő (`0x00b0d990`, egyetlen `ret`) — Mégsére tehát semmi nem
íródik és semmi nem áll vissza.

Ez a modul szándékosan nem ismeri a Qt-t azon túl, hogy egy
`value()`/`setValue()` párost váró objektumot kap: így a leképezés
(kulcsnév, alapérték, típuskényszerítés) önállóan tesztelhető marad.

⚠️ **Egy KIMONDOTT bizonytalanság.** A spec 10.2 szerint a `sizeradio`
kötés írja a `FileExportSize`-t (`0x00739a01`), a 10.1 szerint viszont
ugyanennek a kulcsnak az **alapértéke 3** (`0x00738c58`) — egy kétállású
rádiócsoport pedig nem lehet 3. A kettő nem hozható közös nevezőre a
meglévő méréssel, ezért nálunk **két** kulcs van: a csúszka állása
(`size`, 0…6, alap 3) és a rádió állása (`resize`, alap hamis — a spec
3.2 szerint az „Eredeti méret használata" az alapértelmezett). A
viselkedés — a párbeszéd mindkettőt megjegyzi — így hű; a registry-kulcsok
egy-az-egyben megfeleltetése nyitva marad.
"""

from __future__ import annotations

from typing import Any

#: A méret-csúszka HÉT fogása (`export.fen` `bind17.list`, spec 3.2).
#: Ugyanez a lista él a felületen — a QML innen kéri el, hogy ne legyen
#: két, némán szétcsúszó igazságforrás.
SIZE_PRESETS: tuple[int, ...] = (320, 480, 640, 800, 1024, 1200, 1600)

#: `FileExportSize` alapértéke 3 (`0x00738c43`/`0x00738c58`) → 800 képpont.
DEFAULT_SIZE_INDEX = 3

#: `FileExportQuality` alapértéke 0x55 = 85 (`0x0073962d`, `0x0073b14a`).
DEFAULT_QUALITY = 85

#: Az egyéni minőség-csúszka 21 fogása (`min=0 max=20 ticks=21`), a
#: minőség = fogás × 5 (`0x00739fe6`).
QUALITY_SLIDER_STEPS = 21
QUALITY_SLIDER_FACTOR = 5

#: A minőség-legördülő öt tétele, a `.fen` sorrendjében — az index maga a
#: `FileExportQualityType` értéke (0…4, `0x00739c0c`).
QUALITY_PRESET_KEYS: tuple[str, ...] = (
    "automatic",
    "normal",
    "maximum",
    "minimum",
    "custom",
)


def _bool(value: Any, alap: bool) -> bool:
    """QSettings-érték logikaivá — a `.ini` háttértárból minden stringként
    jön vissza, a natívból viszont valódi bool/int."""
    if value is None:
        return alap
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() not in ("", "0", "false", "no")
    try:
        return bool(int(value))
    except (TypeError, ValueError):
        return bool(value)


def _int(value: Any, alap: int, *, also: int, felso: int) -> int:
    """QSettings-érték egésszé, a megadott tartományba szorítva — a tárolt
    érték sérülése (kézzel szerkesztett `.ini`) ne borítsa a párbeszédet."""
    try:
        szam = int(value)
    except (TypeError, ValueError):
        return alap
    return max(also, min(felso, szam))


def _str(value: Any, alap: str) -> str:
    return value if isinstance(value, str) else alap


#: mező → (beállítás-kulcs, alapérték, beolvasó)
#:
#: A `path` és a `movieFull` SZÁNDÉKOSAN a #1166 óta élő kulcsnevet
#: használja: két igazságforrás némán szétcsúszna, és a felhasználók
#: meglévő beállításai elvesznének.
_MEZOK: dict[str, tuple[str, Any, Any]] = {
    # `DefaultExportPath`
    "path": ("export/defaultpath", "", _str),
    # `FileExportSize` — a csúszka állása (0…6)
    "size": (
        "export/size",
        DEFAULT_SIZE_INDEX,
        lambda ertek, alap: _int(
            ertek, alap, also=0, felso=len(SIZE_PRESETS) - 1
        ),
    ),
    # `FileExportCustomSize` — a szabadon írható méretmező tartalma
    "customSize": (
        "export/customsize",
        SIZE_PRESETS[DEFAULT_SIZE_INDEX],
        lambda ertek, alap: _int(ertek, alap, also=1, felso=100000),
    ),
    # a méret-rádió: hamis = „Eredeti méret használata" (spec 3.2)
    "resize": ("export/resize", False, _bool),
    # `FileExportQualityType` (0…4)
    #
    # ⚠️ Az ALAPÉRTÉKE a specben nincs kimérve (a kulcs beolvasása
    # `0x00738e3f`, de az átadott alapérték nincs kiolvasva). A 0-t
    # („Automatikus") két, egymást erősítő jel támasztja alá: a
    # tulajdonos képernyőképén az „Megőrzi az eredeti képminőséget"
    # magyarázat áll a legördülő mellett (spec 11.2 képpontmérése ezt a
    # feliratot mérte AKTÍVKÉNT), és mind a három mérőkészlet exportja
    # „Automatikus"-sal készült (11.4). Ellene szól a konstruktor
    # `+0xa40 = 0` értékadása (10.5) — az viszont csak
    # elő-inicializálás, a tényleges választást a beolvasott kulcs adja.
    # Ha egyszer kimérjük, ITT kell javítani.
    "qualityType": (
        "export/qualitytype",
        0,
        lambda ertek, alap: _int(
            ertek, alap, also=0, felso=len(QUALITY_PRESET_KEYS) - 1
        ),
    ),
    # `FileExportQuality` — az egyéni minőség
    "quality": (
        "export/quality",
        DEFAULT_QUALITY,
        lambda ertek, alap: _int(ertek, alap, also=0, felso=100),
    ),
    # `FileExportMovie` — nem nulla → „Teljes film" (spec 11.1)
    "movieFull": ("export/moviefull", False, _bool),
    # `ExportAddNumbers` — alapból ki (spec 12.7)
    "addNumbers": ("export/addnumbers", False, _bool),
    # `ExportWatermark` / `ExportWatermarkText`
    "watermark": ("export/watermark", False, _bool),
    "watermarkText": ("export/watermarktext", "", _str),
}

#: A film-rádió #1166 óta élő kulcsa — a régi slotok is ezt használják.
MOVIE_FULL_SETTINGS_KEY = _MEZOK["movieFull"][0]

#: A célmappa #1166 óta élő kulcsa.
EXPORT_PATH_SETTINGS_KEY = _MEZOK["path"][0]


def read_export_prefs(settings) -> dict[str, Any]:
    """A megőrzött beállítások — hiányzó kulcsnál a spec alapértékével."""
    return {
        nev: beolvaso(settings.value(kulcs), alap)
        for nev, (kulcs, alap, beolvaso) in _MEZOK.items()
    }


def write_export_prefs(settings, values) -> None:
    """A megadott mezők kiírása — EGYETLEN menetben (spec 13.7).

    Részleges térképet is elfogad: ami nincs benne, az érintetlen marad.
    Ismeretlen kulcsot csendben átugrunk — a felület és a tár így nem
    tud véletlenül szemetelni egymásba."""
    for nev, ertek in dict(values or {}).items():
        mezo = _MEZOK.get(nev)
        if mezo is None:
            continue
        kulcs, alap, beolvaso = mezo
        settings.setValue(kulcs, beolvaso(ertek, alap))
