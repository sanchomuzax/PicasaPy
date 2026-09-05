"""A Visszavonás/Újra felirat művelet-nevei (#465).

Az eredeti Picasa szerkesztő-vermének felülete (`CFilterStackUI`) **négy**
feliratot tartott a gombpárhoz — a jegy 5. kommentje szerint:

| kulcs | felirat |
|---|---|
| `undolabel` / `redolabel` | „Visszavonás" / „Újra" |
| `undoname` / `redoname` | „Visszavonás: " / „Újra: " (**záró szóközzel**) |

A záró szóköz árulja el a szerkezetet: a `undoname` után a **visszavonandó
művelet neve** következett, tehát a felhasználó látta, mit fog visszavonni
(„Visszavonás: Vágás"), és nem vaktában nyomkodta a gombot egy hosszú
szerkesztés-láncban. Üres veremnél maradt a puszta „Visszavonás".

Ez a modul a második állapothoz tartozó **névtárat** adja. A név nem
tetszőleges: mindig **ugyanaz a felirat, amit a felhasználó a gombon
látott**, amikor az adott lépést alkalmazta — így a visszavonás nem egy
belső kulcsot mutat („Visszavonás: crossprocess"), hanem az eszköz nevét
(„Visszavonás: Áttűnés").

## Miért nem `qsTr()`, és honnan jön a magyar szöveg

A feliratok **adatok**, nem forráskódba írt szövegek (ugyanaz a helyzet,
mint a `legacyEffects` katalógusnál, `edit_controller.legacyEffects`),
ezért futásidőben, `QCoreApplication.translate()`-tel fordulnak. A
fordítás-kontextus szándékosan a MEGLÉVŐ kontextus, ahol az adott felirat
már le van fordítva:

- `EditorPanel` — a szerkesztő-panel eszköz- és effekt-gombjai,
- `LegacyEffects` — a „Régi effektek" fül katalógusa
  (`picasapy.render.legacy_effects.LEGACY_EFFECTS`).

Így a felirat magyarul jelenik meg ÚJ fordítási bejegyzés nélkül, és nem
keletkezik két, egymástól elcsúszható szövegváltozat ugyanarra az eszközre.
A `tests/app/test_undo_labels_465.py` őrzi, hogy minden bejegyzéshez tartozik
BEFEJEZETT fordítás — ha egy kontextus elgurulna, a teszt megbukik, nem a
felhasználó felülete lesz félig angol.

## Verziós alakok — az eredeti HÁROM párt megkülönbözteti (#2240)

A Picasa több szűrőt verziózott (`glow`/`glow2`, `grain`/`grain2`,
`unsharp`/`unsharp2`, `finetune`/`finetune2`), a vágást pedig `crop64`
néven írja a `.picasa.ini`-be.

Korábban mindegyik pár ugyanazt a nevet kapta. Az eredeti szövegtár
(`filter_*_label0`) szerint ez **három párnál téves**: a régi változat
külön, „(Old)" jelzésű feliratot visel, épp azért, hogy a felhasználó
lássa, régi effektet von vissza.

| kulcs | felirat | magyar |
|---|---|---|
| `unsharp` / `unsharp2` | Sharpen (Old) / Sharpen | Élesítés (régi) / Élesítés |
| `glow` / `glow2` | Glow (Old) / Glow | Ragyogás (régi) / Ragyogás |
| `grain` / `grain2` | Film Grain (Old) / Film Grain | Régi filmszemcse / Filmszemcse |
| `tint` / `picniktint` | Tint (Old) / Tint | Árnyalás (régi) / Árnyalás |
| `finetune` / `finetune2` | Tuning / Tuning | Finomhangolás (AZONOS) |

A `crop64` továbbra is a `crop` alakja — a `.picasa.ini` kulcsa, nem külön
eszköz.
"""

from __future__ import annotations

from PySide6.QtCore import QCoreApplication

from picasapy.render.legacy_effects import LEGACY_EFFECTS

#: A szerkesztő-panel fordítási kontextusa — a `.ts`-ben itt vannak az
#: eszköz- és effekt-gombok magyar feliratai.
_PANEL_CONTEXT = "EditorPanel"

#: A „Régi effektek" katalógusának kontextusa (ld. `legacy_effects.py`).
_LEGACY_CONTEXT = "LegacyEffects"


def _tools() -> dict[str, str]:
    """A szerkesztő-eszközök és az egygombos javítások feliratai."""
    return {
        "crop": "Crop",
        "tilt": "Straighten",
        "retouch": "Retouches",
        "redeye": "Red Eye",
        "text": "Text",
        "enhance": "I'm Feeling Lucky",
        "autolight": "Auto Contrast",
        "autocolor": "Auto Color",
        "finetune": "Tuning",
    }


def _effects() -> dict[str, str]:
    """A szerkesztő Effektek/Kreatív/Művészi/További füleinek gombfeliratai
    — pontosan az a szöveg, amit a felhasználó a gombon lát (a QML-fülek
    `label:` értékei, ld. `EditorEffectsTab1..4.qml`)."""
    return {
        # 1. fül — Effektek
        "unsharp": "Sharpen (Old)",
        "unsharp2": "Sharpen",
        "sepia": "Sepia",
        "bw": "B&W",
        "warm": "Warmify",
        "grain2": "Film Grain",
        "grain": "Film Grain (Old)",
        "tint": "Tint (Old)",
        "sat": "Saturation",
        "radblur": "Soft Focus",
        "glow2": "Glow",
        "glow": "Glow (Old)",
        "ansel": "Filtered B&W",
        # #711: a `desat` UGYANEZ a szűrő egy régebbi kulcs alatt — a
        # renderelése is az `apply_ansel`-re megy. A név nem találgatás: az
        # eredeti `CDesaturateFilter::name` felirata bizonyítottan
        # „Filtered B&W" / „Szűrt FF" (`referencia/stringres-en-hu.tsv`,
        # 282. sor), tehát a felhasználó ugyanazt a nevet látja, mint a régi
        # programban.
        "desat": "Filtered B&W",
        "radsat": "Focal B&W",
        "dir_tint": "Graduated Tint",
        # 2. fül — Kreatív
        "ir": "Infrared Film",
        "lomo": "Lomo-ish",
        "holga": "Holga-ish",
        "hdr": "HDR-ish",
        "cinemascope": "Cinemascope",
        "orton": "Orton-ish",
        "sixties": "1960's",
        "invert": "Invert Colors",
        "heatmap": "Heat Map",
        "crossprocess": "Cross Process",
        "quantizepalette": "Posterize",
        "twotone": "Duo-Tone",
        # 3. fül — Művészi
        "boost": "Boost",
        "soften": "Soften",
        "pixelate": "Pixelate",
        "focalzoom": "Focal Zoom",
        "pencilsketch": "Pencil Sketch",
        "neon": "Neon",
        "comicize": "Comic Book",
        "border": "Border",
        "dropshadow": "Drop Shadow",
        "museummatte": "Museum Matte",
        "polaroid": "Polaroid",
        # 4. fül — További effektek
        "vignette": "Vignette",
        "matte": "Matte",
        "nightvision": "Night Vision",
        "localcontrast": "Local Contrast",
        "roundededges": "Rounded Edges",
        "picnikgrain": "Film Grain",
        # #2141: az 1. fül 6. csempéje ezt hívja. A felirat az EREDETI
        # szövegtárból: `filter_PicnikTint_label0` = Tint / Árnyalás.
        "picniktint": "Tint",
    }


#: Verziós/ini-beli alakok, amelyek ugyanazt az eszközt jelentik. A
#: `crop64` a `.picasa.ini` vágás-kulcsa; a `2`-re végződő párok a Picasa
#: későbbi szűrő-változatai (ld. `render/chain.py`).
_ALIASES: dict[str, str] = {
    "crop64": "crop",
    # A `finetune`/`finetune2` az EGYETLEN verziós pár, amelynek az eredeti
    # szövegtárban is AZONOS a felirata („Tuning" / „Finomhangolás").
    "finetune2": "finetune",
}


def _build_labels() -> dict[str, tuple[str, str]]:
    """Művelet-kulcs → (angol felirat, fordítási kontextus)."""
    labels: dict[str, tuple[str, str]] = {
        key: (label, _PANEL_CONTEXT)
        for key, label in {**_tools(), **_effects()}.items()
    }
    # az örökölt szűrők neve a saját katalógusukból jön — ugyanaz a szöveg,
    # amit a „Régi effektek" fül gombjain lát a felhasználó
    for effect in LEGACY_EFFECTS:
        labels.setdefault(effect.key, (effect.label, _LEGACY_CONTEXT))
    for alias, target in _ALIASES.items():
        labels[alias] = labels[target]
    return labels


#: A teljes névtár: művelet-kulcs → (angol felirat, fordítási kontextus).
ACTION_LABELS: dict[str, tuple[str, str]] = _build_labels()

#: A renderelő által ismert, de NÉV NÉLKÜLI szűrők. Ezekhez az eredeti
#: programban nem tartozik felületi felirat (nincs gombjuk, és a
#: `Picasa3i18n.dll` szótárában sem szerepelnek), ezért a felirat a nyers
#: kulcsot mutatja — találgatott magyar nevet adni nekik félrevezető lenne.
#: Egy valódi Picasa-láncból elvileg előkerülhetnek; ha kiderül a felületi
#: nevük, innen kerülnek át a névtárba.
UNNAMED_CHAIN_KEYS: frozenset[str] = frozenset(
    {
        # (a `picnikfocalpixelate` a #1142-ben KIKERÜLT: a renderelő már nem
        # ismeri, mert a mérés szerint az eredeti Picasa sem futtatja)
        #
        # #2141: a `picniktint` is KIKERÜLT innen. A „szótárban sem
        # szerepelnek" indoklás rá NEM állt: az eredeti szövegtárban ott a
        # felirata (`filter_PicnikTint_label0` = Tint / Árnyalás), és a
        # felület azóta kínálja is — az 1. effekt-fül 6. csempéjén.
        # a vörösszem-javítás belső, szem-szín visszaállító lépése
        "reanimatedeyecolor",
    }
)


def action_label(action: str) -> str:
    """Egy művelet-kulcs olvasható (magyar) neve.

    Ismeretlen kulcsnál a NYERS kulcsot adja vissza: egy valódi Picasa
    írta, számunkra ismeretlen szűrő nevét látni még mindig informatívabb,
    mint egy üres feliratot. Üres kulcsra üres sztringet ad.
    """
    if not action:
        return ""
    entry = ACTION_LABELS.get(action) or ACTION_LABELS.get(action.casefold())
    if entry is None:
        return action
    label, context = entry
    return QCoreApplication.translate(context, label)


def undo_label(action: str) -> str:
    """A Visszavonás gomb felirata — a két eredeti állapot szerint."""
    return _stack_label("Undo", action)


def redo_label(action: str) -> str:
    """Az Újra gomb felirata — a két eredeti állapot szerint."""
    return _stack_label("Redo", action)


def _stack_label(base: str, action: str) -> str:
    """Üres veremnél a puszta felirat (`undolabel`), egyébként a
    „<felirat>: <lépés neve>" alak (`undoname` + a művelet neve)."""
    label = QCoreApplication.translate(_PANEL_CONTEXT, base)
    name = action_label(action)
    return f"{label}: {name}" if name else label


__all__ = [
    "ACTION_LABELS",
    "UNNAMED_CHAIN_KEYS",
    "action_label",
    "redo_label",
    "undo_label",
]
