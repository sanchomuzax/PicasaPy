#!/usr/bin/env python3
"""Paraméter-sweep golden kit — csúszka↔paraméter leképezés (#190 2. kör).

Az 1. körben (docs/specs/filters-decoded.md 5. kör, `tests/ini/test_filters.py`
`TestEffektFulKulcsok190`) mind a 23, a Picasa 3.9 4–5. effekt-fülén élő
`filters=` kulcs AZONOSÍTVA lett — de a paraméterek JELENTÉSE (melyik
csúszkának melyik szám felel meg) még nyitott. Ez a szkript ezt a kört
zárja: a most ismert kulcsokkal ELŐRE megírt `.picasa.ini`-variánsokat
generál, ahol minden paraméteres effekt FŐ (erősség-jellegű) paraméterét
a feltételezett tartományán 5 ponton (min / negyed / fél / háromnegyed /
max) végigléptetjük — a többi paramétert a `filters-decoded.md`-ben
rögzített minta-értéken tartva.

A felhasználónak ezután NEM kell effektet ráhúznia semmire: a
`.picasa.ini` már tartalmazza a `filters=` sorokat, a Windows-os Picasa a
mappa hozzáadásakor automatikusan renderel — a dolga csak a mappák
áthozatala, a Picasához adása és egy TÖMEGES export.

Az egyes effektek feltételezett paraméter-tartománya (0–100 erősség-
százalék, vagy egyedi tartomány, pl. poszterizálási szintszám) NEM
igazolt tény, hanem józan alapértelmezés — a pontos indoklás minden
effektnél a `ParamSweep.megjegyzes` mezőben és az `UTMUTATO.md`-ben áll.
A felhasználó tömeges exportja + a visszahozott `.picasa.ini` (amit a
Picasa esetleg kerekítve ír vissza) adja a tényleges csúszka-értékeket.

Használat:
    make_param_sweep.py <kimenet_dir>
    make_param_sweep.py <fotok_dir> <kimenet_dir>

A `<fotok_dir>` ELHAGYHATÓ (ld. `make_golden_kit_effects.py` — szintetikus
fotó-alapképpel is lefut).
"""
from __future__ import annotations

import importlib.util
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parents[1]

# A tools/ nincs a pythonpath-on — a repo src/-ét kézzel vesszük fel, hogy a
# szkript közvetlenül (python3 tools/golden/make_param_sweep.py) is fusson
# (ugyanaz a minta, mint a `compare_render.py`-ban).
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from picasapy.ini import (  # noqa: E402
    parse_document,
    parse_filters,
    save_document,
    serialize_filters,
)


def _load_module(name: str, filename: str):
    """Fájlútvonalról betöltött szkript-modul (a `tools/golden/` szándékosan
    nem csomag — ld. `make_golden_kit_effects.py` docstringje)."""
    spec = importlib.util.spec_from_file_location(name, _HERE / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules.setdefault(name, module)
    spec.loader.exec_module(module)
    return module


# A `make_golden_kit_effects.py` már tartalmazza az alapkép-előállítást
# (`_base_images`: ramp/color/detail/photo, szükség esetén szintetikus
# fotóval) és a `slugify`-t — ezeket használjuk újra, ne duplikáljuk.
_mgke = _load_module("make_golden_kit_effects", "make_golden_kit_effects.py")
_mgk = _mgke._mgk
slugify = _mgke.slugify


@dataclass(frozen=True)
class ParamSweep:
    """Egy effekt sweep-leírása: a `filters=<key>=1,<params>;` lánc FLAG
    utáni paraméterei pozíciónként rögzítve.

    `template`: a flag utáni ÖSSZES paraméter fix (minta szerinti) alakja —
    a `sweep_index` pozíción lévő érték csak PLACEHOLDER, sweepeléskor
    felülíródik. `sweep_index=None` esetén nincs sweep (pl. `Invert`): a
    `template` ilyenkor üres tuple, egyetlen bejegyzés készül.
    `discrete_ints`: a sweep egész léptékű enum (pl. `Cinemascope`), NEM az
    5-pontos (min/negyed/fél/háromnegyed/max) folytonos tartomány.
    """

    key: str
    nev: str  # magyar UI-felirat (a filters-decoded.md táblázatával egyezik)
    tab: int  # 4 vagy 5 (melyik effekt-fül)
    base: str  # alapkép kulcs: ramp/color/detail/photo
    template: tuple[str, ...]
    sweep_index: int | None
    sweep_min: float = 0.0
    sweep_max: float = 0.0
    discrete_ints: bool = False
    megjegyzes: str = ""


# ---------------------------------------------------------------------
# 4. fül (zöld ecset) — sorrend = filters-decoded.md 5. kör táblázata
# ---------------------------------------------------------------------
EFFECTS_4: list[ParamSweep] = [
    ParamSweep(
        key="IR", nev="Infravörös film", tab=4, base="photo",
        template=("0.000000",), sweep_index=0, sweep_min=0, sweep_max=100,
        megjegyzes="Egyetlen numerikus paraméter; feltételezett tartomány "
        "0–100 (erősség %), a többi hasonló csúszkás effekt mintájára. A "
        "dokumentált minta (0.000000) a Picasa alapértéke, nem feltétlenül "
        "sweep-pont.",
    ),
    ParamSweep(
        key="Lomo", nev="Lomo-szerű", tab=4, base="photo",
        template=("0.000000", "0.000000"), sweep_index=0,
        sweep_min=0, sweep_max=100,
        megjegyzes="p2 (minta 0) fixen — feltehetően járulékos hatás "
        "(vignetta/sávozás); a fő erősség (1. param, minta 50) sweepelve.",
    ),
    ParamSweep(
        key="Holga", nev="Holga-szerű", tab=4, base="photo",
        template=("0.000000", "30.000000", "0.000000"), sweep_index=0,
        sweep_min=0, sweep_max=100,
        megjegyzes="p2=30, p3=0 fixen a minta szerint; a fő erősség "
        "(1. param, minta 70) sweepelve.",
    ),
    ParamSweep(
        key="HDR", nev="HDR-szerű", tab=4, base="photo",
        template=("0.000000", "3.000000", "0.000000"), sweep_index=0,
        sweep_min=0, sweep_max=100,
        megjegyzes="p2=3 (feltehetően finom 'részletesség'-skála), p3=0 "
        "fixen; a fő erősség (1. param, minta 20) sweepelve.",
    ),
    ParamSweep(
        key="Cinemascope", nev="Kinemaszkóp", tab=4, base="photo",
        template=("0",), sweep_index=0, sweep_min=0, sweep_max=3,
        discrete_ints=True,
        megjegyzes="A minta paramétere ('0', TIZEDESJEGY NÉLKÜL — eltér a "
        "szokásos %.6f formátumtól) enum-szerű szelektorra utal (pl. "
        "képarány-előbeállítás), nem folytonos csúszkára; ezért a szokásos "
        "5-pontos sweep helyett 4 egész értéket (0–3) generálunk.",
    ),
    ParamSweep(
        key="Orton", nev="Orton-szerű", tab=4, base="photo",
        template=("0.000000", "50.000000", "0.000000"), sweep_index=0,
        sweep_min=0, sweep_max=100,
        megjegyzes="p2=50 (feltehetően fényesség/elmosás-sugár), p3=0 "
        "fixen; a fő erősség (1. param, minta 25) sweepelve.",
    ),
    ParamSweep(
        key="Sixties", nev="60-as évek", tab=4, base="photo",
        template=("0.000000", "00ffffff", "0"), sweep_index=0,
        sweep_min=0, sweep_max=100,
        megjegyzes="p2 (szín, fehér) és p3 ('0', tizedesjegy nélkül — "
        "szintén enum-gyanús) fixen a minta szerint; a fő erősség "
        "(1. param, minta 20) sweepelve.",
    ),
    ParamSweep(
        key="Invert", nev="Színinvertálás", tab=4, base="ramp",
        template=(), sweep_index=None,
        megjegyzes="Nincs numerikus paramétere (bináris on/off) — egyetlen "
        "bejegyzés elég, sweep nem értelmezhető.",
    ),
    ParamSweep(
        key="HeatMap", nev="Hőtérkép", tab=4, base="ramp",
        template=("0.000000", "0.000000"), sweep_index=0,
        sweep_min=0, sweep_max=100,
        megjegyzes="Mindkét minta-paraméter 0.000000 volt — nincs támpont, "
        "melyik a 'fő'; az 1. paramétert feltételezzük fő erősségnek, a "
        "2.-at fixen 0-n tartjuk.",
    ),
    ParamSweep(
        key="CrossProcess", nev="Áttűnés", tab=4, base="ramp",
        template=("0.000000",), sweep_index=0, sweep_min=0, sweep_max=100,
        megjegyzes="Egyetlen numerikus paraméter; feltételezett tartomány "
        "0–100 (erősség %).",
    ),
    ParamSweep(
        key="QuantizePalette", nev="Poszterizálás", tab=4, base="ramp",
        template=("0.000000", "80.000000", "0.000000"), sweep_index=0,
        sweep_min=2, sweep_max=32,
        megjegyzes="Az 1. param (minta 8) feltehetően a poszterizálási "
        "színszintek száma — tartomány feltételezve 2–32 (NEM 0–100 %, "
        "mert diszkrét szintszámról van szó); p2=80, p3=0 fixen.",
    ),
    ParamSweep(
        key="TwoTone", nev="Kéttónusú", tab=4, base="ramp",
        template=(
            "0.000000", "20.000000", "0.000000", "00004488", "00ffff00",
        ),
        sweep_index=0, sweep_min=-100, sweep_max=100,
        megjegyzes="Az 1. param (minta 0) feltehetően előjeles egyensúly/"
        "küszöb-csúszka (-100..100), mert a minta középálláshoz illő 0; "
        "p2=20, p3=0 és a két szín fixen a minta szerint.",
    ),
]

# ---------------------------------------------------------------------
# 5. fül (kék ecset)
# ---------------------------------------------------------------------
EFFECTS_5: list[ParamSweep] = [
    ParamSweep(
        key="Boost", nev="Felpörgetés", tab=5, base="detail",
        template=("0.000000",), sweep_index=0, sweep_min=0, sweep_max=100,
        megjegyzes="Egyetlen numerikus paraméter; feltételezett tartomány "
        "0–100 (erősség %).",
    ),
    ParamSweep(
        key="Soften", nev="Lágyítás", tab=5, base="detail",
        template=("0.000000", "50.000000"), sweep_index=0,
        sweep_min=0, sweep_max=100,
        megjegyzes="p2=50 (feltehetően lágyítási sugár) fixen; a fő "
        "erősség (1. param, minta 50) sweepelve.",
    ),
    ParamSweep(
        key="Pixelate", nev="Képpontnagyítás", tab=5, base="detail",
        template=("0.000000", "9.000000", "0.000000"), sweep_index=0,
        sweep_min=0, sweep_max=100,
        megjegyzes="p2=9, p3=0 fixen; a fő erősség (cellaméret %, minta "
        "20) sweepelve.",
    ),
    ParamSweep(
        key="FocalZoom", nev="Fókusznagyítás", tab=5, base="photo",
        template=(
            "0.500000", "0.500000", "0.000000",
            "50.000000", "50.000000", "0.000000",
        ),
        sweep_index=2, sweep_min=0, sweep_max=100,
        megjegyzes="p1/p2 (0.5,0.5) feltehetően a fókuszpont relatív x/y-"
        "koordinátája — FIXEN a kép közepén hagyva; a 3. paramétert "
        "(minta 50, feltehetően nagyítás mértéke) sweepeljük, p5/p6 "
        "(sugár/elforgatás, minta 50/0) fixen.",
    ),
    ParamSweep(
        key="PencilSketch", nev="Ceruzarajz", tab=5, base="detail",
        template=("0.000000", "100.000000", "0.000000"), sweep_index=0,
        sweep_min=1, sweep_max=10,
        megjegyzes="Az 1. param (minta 2, kis érték) feltehetően a "
        "ceruzavonal-vastagság — tartomány feltételezve 1–10 (NEM 0–100 "
        "%); p2=100, p3=0 fixen.",
    ),
    ParamSweep(
        key="Neon", nev="Neon", tab=5, base="detail",
        template=("0.000000", "00ff0000"), sweep_index=0,
        sweep_min=0, sweep_max=100,
        megjegyzes="p2 (szín, piros) fixen; a fő erősség (1. param, minta "
        "0) sweepelve.",
    ),
    ParamSweep(
        key="Comicize", nev="Képregény", tab=5, base="photo",
        template=("0.000000", "50.000000", "50.000000"), sweep_index=0,
        sweep_min=0, sweep_max=100,
        megjegyzes="p2=50, p3=50 (feltehetően él-/színszint-részletesség) "
        "fixen; a fő erősség (1. param, minta 20) sweepelve.",
    ),
    ParamSweep(
        key="Border", nev="Szegély", tab=5, base="photo",
        template=(
            "0.000000", "5.000000", "0.000000",
            "00000000", "00ffffff", "0.000000",
        ),
        sweep_index=0, sweep_min=0, sweep_max=100,
        megjegyzes="A szegély szélessége (1. param, minta 20) sweepelve; "
        "a többi (elmosás, sarok, két szín) fixen a minta szerint.",
    ),
    ParamSweep(
        key="DropShadow", nev="Árnyékvetés", tab=5, base="photo",
        template=(
            "0.000000", "90.000000", "10.000000",
            "00000000", "00ffffff", "30.000000",
        ),
        sweep_index=0, sweep_min=0, sweep_max=20,
        megjegyzes="Az 1. param (minta 4, kis érték) feltehetően az "
        "árnyék elmosási/mérethatára — tartomány feltételezve 0–20; szög "
        "(90), távolság (10), színek és átlátszóság (30) fixen. Alternatív "
        "értelmezés (pl. hogy az átlátszóság a fő csúszka) a felhasználói "
        "visszajelzésből pontosítható.",
    ),
    ParamSweep(
        key="MuseumMatte", nev="Múzeumi matt", tab=5, base="photo",
        template=("0.000000", "40.000000", "001a0e03", "00f0eae4"),
        sweep_index=0, sweep_min=0, sweep_max=100,
        megjegyzes="A matt szélessége (1. param, minta 25) sweepelve; "
        "p2=40 és a két szín fixen.",
    ),
    ParamSweep(
        key="Polaroid", nev="Polaroid", tab=5, base="photo",
        template=("0.000000", "00e2e2e2"), sweep_index=0,
        sweep_min=-45, sweep_max=45,
        megjegyzes="Az 1. param (minta 5, kis érték, feltehetően "
        "elforgatás fokban) tartománya feltételezve -45..45°; a "
        "keret-szín fixen.",
    ),
]

EFFECTS: list[ParamSweep] = [*EFFECTS_4, *EFFECTS_5]


def _sweep_values(effect: ParamSweep) -> list[float]:
    """A sweepelt paraméter mintavételi pontjai.

    Folytonos effekteknél 5 pont: min / negyed / fél / háromnegyed / max.
    Diszkrét (`discrete_ints`) effekteknél az egész tartomány MINDEN
    értéke (pl. Cinemascope: 0,1,2,3 — nem csak 5 pont)."""
    if effect.sweep_index is None:
        return [0.0]  # dummy — a _filters_value úgyis figyelmen kívül hagyja
    if effect.discrete_ints:
        lo, hi = int(effect.sweep_min), int(effect.sweep_max)
        return [float(v) for v in range(lo, hi + 1)]
    lo, hi = effect.sweep_min, effect.sweep_max
    return [lo + frac * (hi - lo) for frac in (0.0, 0.25, 0.5, 0.75, 1.0)]


def _format_sweep(effect: ParamSweep, value: float) -> str:
    if effect.discrete_ints:
        return str(int(round(value)))
    return f"{value:.6f}"


def _suffix_label(effect: ParamSweep, idx: int, value: float) -> str:
    """A fájlnév-szeletke a sweep-pozícióhoz.

    Folytonos sweepnél a tartományon belüli SZÁZALÉKOS pozíciót kódolja
    (000/025/050/075/100), NEM a nyers paraméterértéket — negatív/tizedes
    értékek (pl. TwoTone -100..100) így is fájlnév-biztosak maradnak. A
    tényleges paraméterérték a `.picasa.ini`-ben és az UTMUTATO.md
    táblázatában olvasható."""
    if effect.sweep_index is None:
        return ""
    if effect.discrete_ints:
        return str(int(round(value)))
    return ("000", "025", "050", "075", "100")[idx]


def _filters_value(effect: ParamSweep, value: float) -> str:
    """A `<kulcs>=1,<paraméterek>;` lánc a sweepelt pozícióval behelyettesítve."""
    parts = list(effect.template)
    if effect.sweep_index is not None:
        parts[effect.sweep_index] = _format_sweep(effect, value)
    return f"{effect.key}=" + ",".join(("1", *parts)) + ";"


def _build_effect(
    effect: ParamSweep, bases: dict[str, Path], out: Path
) -> tuple[str, list[tuple[str, str]]]:
    """Egy effekt sweep-mappájának legyártása: kép-másolatok + `.picasa.ini`.

    A `.picasa.ini`-t a projekt round-trip ini-rétegén (`parse_document` /
    `with_value` / `save_document`) keresztül írjuk, NEM nyers stringből —
    így a kimenet garantáltan megfelel a dokumentum-modellnek.

    Visszaadja a mappa nevét és a (fájlnév, `filters=` érték) párokat az
    UTMUTATO.md táblázatához."""
    folder_name = f"effekt{effect.tab}_{slugify(effect.nev)}"
    fdir = out / folder_name
    fdir.mkdir(parents=True, exist_ok=True)
    base = bases[effect.base]

    doc = parse_document("")
    rows: list[tuple[str, str]] = []
    for idx, value in enumerate(_sweep_values(effect)):
        label = _suffix_label(effect, idx, value)
        name = f"{effect.key}_{label}.jpg" if label else f"{effect.key}.jpg"
        shutil.copy2(base, fdir / name)
        filt = _filters_value(effect, value)
        # Építés közbeni önellenőrzés (a teszt is lefedi, de itt azonnal
        # kiderül, ha egy template hibás lenne — nem csak CI-n).
        assert serialize_filters(parse_filters(filt)) == filt, filt
        doc = doc.with_value(name, "filters", filt)
        rows.append((name, filt))

    save_document(doc, fdir / ".picasa.ini")
    return folder_name, rows


_ALAPKEP_LEIRAS = {
    "ramp": "szürke/RGB gradiens (chart_ramp.jpg)",
    "color": "HSV-színmező (chart_color.jpg)",
    "detail": "sakktábla + vonalpárok (chart_detail.jpg)",
    "photo": "fénykép (valódi, vagy szintetikus, ha nincs fotómappa)",
}


def _write_utmutato(
    out: Path, built: list[tuple[ParamSweep, str, list[tuple[str, str]]]]
) -> None:
    """Magyar nyelvű útmutató a Windows-os tömeges exporthoz (#190 2. kör)."""
    total_images = sum(len(rows) for _, _, rows in built)
    lines = [
        "# Útmutató — paraméter-sweep golden kit (#190 2. kör)",
        "",
        "Ez a mappa a 4–5. effekt-fül 23 kulcsának CSÚSZKA↔PARAMÉTER "
        "leképezéséhez készült. A képekhez tartozó `.picasa.ini` MÁR "
        "tartalmazza a `filters=` sorokat — nincs kézi effekt-ráhúzás, "
        "csak a mappák áthozatala és egy tömeges export.",
        "",
        f"Összesen **{len(EFFECTS)} effekt**, **{total_images} kép** "
        "(effektenként a feltételezett paramétertartomány 5 pontján — "
        "min / negyed / fél / háromnegyed / max —, kivéve az egyparaméteres "
        "`Invert`-et [1 kép] és a diszkrétnek feltételezett "
        "`Cinemascope`-ot [4 kép, ld. lent]).",
        "",
        "## 1. lépés — átvitel a Windows-gépre",
        "",
        "- Másold át ezt a teljes mappát egy **friss, üres** mappába a "
        "Windows-gépen, pl. `C:\\PicasaPy-parameter-sweep\\`.",
        "- A Picasában: **Mappák → Mappa hozzáadása a Picasához** — mivel "
        "a `.picasa.ini` már készen áll, a Picasa a beolvasáskor RÖGTÖN az "
        "effektekkel renderelve mutatja a képeket (nincs teendőd velük).",
        "",
        "## 2. lépés — tömeges export",
        "",
        "- Jelöld ki AZ ÖSSZES képet (Ctrl+A a teljes fastruktúrán, vagy "
        "mappánként), majd **Fájl → Exportálás** (Use Original Size / "
        "Maximum méret) — célként az ebben a mappában lévő `export` "
        "alkönyvtárat add meg.",
        "",
        "## 3. lépés — visszahozatal",
        "",
        "- Lépj ki a Picasából (a `.picasa.ini` csak kilépéskor/"
        "mappaváltáskor íródik ki biztosan).",
        "- Hozd vissza EBBE a mappába (a struktúrát megtartva) MINDEN "
        "`.picasa.ini`-t (rejtett fájl — Fájlkezelő → Nézet → Rejtett "
        "elemek) és az `export` alkönyvtár tartalmát.",
        "- A visszahozott `.picasa.ini`-kben — ha a Picasa kerekített "
        "vagy módosított egy paramétert — az a TÉNYLEGES csúszka-érték; "
        "ez adja a végleges leképezést a lenti táblázat feltételezett "
        "értékeivel szemben.",
        "",
        "## Effekt → mappa → paraméterérték táblázat",
        "",
        "| Fül | Effekt | Kulcs | Mappa | Fájlnév | `filters=` érték |",
        "|---|---|---|---|---|---|",
    ]
    for effect, folder_name, rows in built:
        for name, filt in rows:
            lines.append(
                f"| {effect.tab} | {effect.nev} | `{effect.key}` | "
                f"`{folder_name}` | `{name}` | `{filt}` |"
            )
    lines += [
        "",
        "## Feltételezések effektenként (mit sweepelünk, mit tartunk fixen)",
        "",
        "**Fontos: ezek NEM igazolt tények, hanem józan alapértelmezések** "
        "— a fenti tömeges export dönti el, helytállóak-e.",
        "",
    ]
    for effect in EFFECTS:
        alapkep = _ALAPKEP_LEIRAS[effect.base]
        lines.append(f"- **{effect.nev}** (`{effect.key}`, alapkép: {alapkep}): "
                     f"{effect.megjegyzes}")
    lines += [
        "",
        "## Kivételek",
        "",
        "- **Színinvertálás (`Invert`)**: nincs numerikus paramétere "
        "(bináris on/off) — a mappában EGYETLEN kép/bejegyzés van.",
        "- **Kinemaszkóp (`Cinemascope`)**: a minta egyetlen paramétere "
        "tizedesjegy nélküli ('0'), ami enum-szerű szelektorra utal — "
        "ezért 4 egész értéket (0,1,2,3) sweepeltünk az 5-pontos "
        "folytonos tartomány helyett.",
        "",
    ]
    (out / "UTMUTATO.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    if len(sys.argv) == 2:
        photos_dir = None
        out = Path(sys.argv[1]).expanduser()
    elif len(sys.argv) == 3:
        photos_dir = Path(sys.argv[1]).expanduser()
        out = Path(sys.argv[2]).expanduser()
    else:
        print(__doc__)
        sys.exit(1)

    _mgk.prepare_out_dir(out)
    base_dir = out / "00-base"
    base_dir.mkdir(parents=True, exist_ok=True)
    bases = _mgke._base_images(base_dir, photos_dir)

    built: list[tuple[ParamSweep, str, list[tuple[str, str]]]] = []
    for effect in EFFECTS:
        folder_name, rows = _build_effect(effect, bases, out)
        built.append((effect, folder_name, rows))

    _write_utmutato(out, built)
    (out / "export").mkdir(exist_ok=True)

    total_images = sum(len(rows) for _, _, rows in built)
    print(f"Paraméter-sweep kit kész: {out}")
    print(f"  {len(EFFECTS)} effekt, {total_images} kép")
    print("  útmutató: UTMUTATO.md")


if __name__ == "__main__":
    main()
