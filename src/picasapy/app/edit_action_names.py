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

## Verziós alakok

A Picasa több szűrőt verziózott (`glow`/`glow2`, `grain`/`grain2`,
`unsharp`/`unsharp2`, `finetune`/`finetune2`), a vágást pedig `crop64`
néven írja a `.picasa.ini`-be. A felhasználó mindkét alak mögött ugyanazt az
eszközt ismeri, ezért ugyanazt a nevet kapják.
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
        "retouch": "Retouch",
        "redeye": "Redeye",
        "text": "Text",
        "enhance": "I'm Feeling Lucky",
        "autolight": "Auto Contrast",
        "autocolor": "Auto Color",
        "finetune": "Fine Tuning",
    }


def _effects() -> dict[str, str]:
    """A szerkesztő Effektek/Kreatív/Művészi/További füleinek gombfeliratai
    — pontosan az a szöveg, amit a felhasználó a gombon lát (a QML-fülek
    `label:` értékei, ld. `EditorEffectsTab1..4.qml`)."""
    return {
        # 1. fül — Effektek
        "unsharp": "Sharpen",
        "sepia": "Sepia",
        "bw": "B&W",
        "warm": "Warmify",
        "grain2": "Film Grain",
        "tint": "Tint",
        "sat": "Saturation",
        "radblur": "Soft Focus",
        "glow2": "Glow",
        "ansel": "Filtered B&W",
        "radsat": "Focal Saturation",
        "dir_tint": "Graduated Tint",
        # 2. fül — Kreatív
        "ir": "Infrared Film",
        "lomo": "Lomo-ish",
        "holga": "Holga-ish",
        "hdr": "HDR-ish",
        "cinemascope": "Cinemascope",
        "orton": "Orton-ish",
        "sixties": "1960s",
        "invert": "Invert Colors",
        "heatmap": "Heat Map",
        "crossprocess": "Cross Process",
        "quantizepalette": "Posterize",
        "twotone": "Duo-Tone",
        # 3. fül — Művészi
        "boost": "Boost",
        "soften": "Soft Focus",
        "pixelate": "Pixelate",
        "focalzoom": "Focal Zoom",
        "pencilsketch": "Pencil Sketch",
        "neon": "Neon",
        "comicize": "Comicize",
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
        "picnikgrain": "Film Grain (Fine)",
    }


#: Verziós/ini-beli alakok, amelyek ugyanazt az eszközt jelentik. A
#: `crop64` a `.picasa.ini` vágás-kulcsa; a `2`-re végződő párok a Picasa
#: későbbi szűrő-változatai (ld. `render/chain.py`).
_ALIASES: dict[str, str] = {
    "crop64": "crop",
    "finetune2": "finetune",
    "unsharp2": "unsharp",
    "glow": "glow2",
    "grain": "grain2",
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
        # a Picnik (Kreatív Kit) saját szűrői — a felület sosem kínálta őket
        "picnikfocalpixelate",
        "picniktint",
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
