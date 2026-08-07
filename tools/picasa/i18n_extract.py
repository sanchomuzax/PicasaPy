#!/usr/bin/env python3
"""`Picasa3i18n.dll` `<tooltips>` erőforrás-kinyerő.

A `Picasa3i18n.dll` (~26,9 MB) KÉTFÉLE beágyazott XML-erőforrást tartalmaz:

1. `<resources>` blokkok `<stringres id="...">` elemekkel — a menüparancsok
   és a "kis" panelfeliratok táblája (ld. `docs/specs/picasa-hu-terminology.md`).
2. **`<tooltips>` blokkok** `<action type="Text|Tooltip|Label|Text1..4"
   target="panel/elem">` elemekkel — ez a program **teljes felirat- és
   tippkészlete**, panelenként. Ezt dolgozza fel ez az eszköz.

## A blokkok szerkezete

Minden `<tooltips>` blokk egy önálló, jól formált XML dokumentum:

```
<?xml version="1.0" encoding="utf-8" ?>
<tooltips>
 <action type="Tooltip" target="acquirepanel/excludedupesbutton" xmbdesc="...">
  <xmbtext>Exclude photos that are already imported into Picasa</xmbtext>
 </action>
 ...
</tooltips>
```

A DLL-ben **1353 ilyen blokk** van. Ebből **1312 db "egypaneles"** (minden
`target` ugyanazzal a `panel/` előtaggal kezdődik — pl. mind
`acquirepanel/...`), **32 egyedi panelnévvel**, egyenként pontosan **41**
előfordulással. A maradék **41 blokk "vegyes"** (több panel felirata
összefésülve egy blokkba — ezeket az eszköz `__misc__` panelnévvel kezeli).

## Nyelv-azonosítás

A blokkoknak **nincs explicit nyelvjelölésük**. A `<resources>` oldalon az
`options/item27.title` azonosító minden nyelvi blokkban a „System Default
(xx-XX)" szöveget tartalmazza, ami **40 nyelvi blokkot** azonosít egyértelműen
(ld. `picasa-hu-terminology.md`). A `<tooltips>` panelenkénti csoportjai
viszont **41-szer** fordulnak elő (eggyel többször) — ezt egy 41 elemű
"óriás" `<resources>` blokk-csoport (a teljes menüparancs-tábla, `Album::...`
stílusú azonosítókkal) is megerősíti, amelyben **pontosan 41 nyelvi blokk**
van. Az `Abbreviation::May` (hónapnév) tartalma alapján ez a 41 blokk
fájl-eltolás szerinti sorrendben pontosan **egy plusz "alap" angol
példánnyal kiegészített, egyébként az `item27` 40 nyelvével megegyező sorrend**:

    index 0:  en        (alap/duplikált angol — mindig a legkisebb eltolású)
    index 1..39:  a 40, item27-ből azonosított nyelv, ugyanabban a sorrendben
    (a teljes táblázat: ld. LANG_ORDER lent)

**Ellenőrzés (2026-08-07):** ez a sorrend a `<tooltips>` panelcsoportokra is
érvényesnek bizonyult — három egymástól független panelnél (`acquirepanel`,
`oneup`, `headerpanel`) és a `__misc__` csoportnál is a 16. index (0-alapú)
tartalmazott magyar `ő`/`ű` betűket ÉS a 0. index tisztán ASCII angol
szöveget. A tartalmi ellenőrzés emiatt **ténylegesen tartalom alapján**
történik, nem csak a pozíciófeltevésre hagyatkozva:

- **`en`**: az adott panelcsoport legkisebb fájl-eltolású blokkja (0. index),
  megerősítve azzal, hogy szövege túlnyomórészt ASCII.
- **`hu` / `hu-HU`**: az a blokk, amelyik `ő` vagy `ű` betűt tartalmaz
  (ez a két betű Magyar-egyedi az itt előforduló 41 nyelv között). Ha egy
  panel túl rövid ahhoz, hogy ilyen betű előforduljon benne, tartalék
  megoldásként a pozíció (16. index) alapján választ az eszköz.
- A többi nyelv a `LANG_ORDER` táblázat pozíciója alapján (ez az `item27` és
  a hónapnév-azonosítás alapján lett összeállítva, de **nincs mindegyikre
  tartalmi kereszt-ellenőrzés** — csak `en` és `hu` esetén garantált).

## Használat

    python3 tools/picasa/i18n_extract.py <Picasa3i18n.dll> --lang hu --out <fájl.tsv>
    python3 tools/picasa/i18n_extract.py <Picasa3i18n.dll> --list-langs

**Jogi megjegyzés:** a kinyert feliratok/tippek a Google Inc. szerzői
jogvédett fordításai. Ez az eszköz KUTATÁSI célú (a formátum
dokumentálásához készült) — a kimeneti TSV-t **ne** tárold/committold a
projektbe.
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

XML_PROLOG = b'<?xml version="1.0" encoding="utf-8" ?>\n<tooltips>'
XML_CLOSE = b"</tooltips>"

MISC_KEY = "__misc__"

# A nyelvi index -> nyelvkód táblázat. A 0. (en) és a 16. (hu-HU) elem
# tartalmi ellenőrzéssel megerősített; a többi az `options/item27.title`
# (ld. picasa-hu-terminology.md) és a `Abbreviation::May` hónapnév-azonosítás
# alapján összeállított legjobb becslés.
LANG_ORDER: list[str] = [
    "en",  # 0 — alap/duplikált angol (tartalmilag megerősítve)
    "ar-sa",  # 1
    "bg",  # 2
    "ca",  # 3
    "cs",  # 4
    "da-DK",  # 5
    "de",  # 6
    "el",  # 7
    "en-US",  # 8
    "es",  # 9
    "fa",  # 10
    "fi-FI",  # 11
    "en-GB",  # 12
    "fr",  # 13
    "hi",  # 14
    "hr",  # 15
    "hu-HU",  # 16 — tartalmilag megerősítve (ő/ű betű)
    "id",  # 17
    "it",  # 18
    "iw-IL",  # 19
    "ja-JP",  # 20
    "ko",  # 21
    "lt",  # 22
    "lv",  # 23
    "nl-NL",  # 24
    "no",  # 25
    "pl-PL",  # 26
    "pt-BR",  # 27
    "pt-PT",  # 28
    "ro",  # 29
    "ru-RU",  # 30
    "sk",  # 31
    "sl-SI",  # 32
    "sr",  # 33
    "sv",  # 34
    "th",  # 35
    "tr-TR",  # 36
    "uk",  # 37
    "vi-VN",  # 38
    "zh-CN",  # 39
    "zh-TW",  # 40
]

HUNGARIAN_LETTERS = ("ő", "ű", "Ő", "Ű")


class I18nExtractError(Exception):
    """A DLL nem a várt szerkezetű, vagy a kért nyelv nem azonosítható."""


@dataclass(frozen=True)
class Block:
    """Egy `<tooltips>` blokk nyers határai és a benne szereplő panelnév(ek)."""

    offset: int
    raw: bytes
    panel: str  # egypaneles blokknál a panel neve, egyébként MISC_KEY


def find_tooltips_blocks(data: bytes) -> list[Block]:
    """Az összes `<tooltips>...</tooltips>` blokk kikeresése a DLL-ből."""
    blocks: list[Block] = []
    i = 0
    while True:
        i = data.find(XML_PROLOG, i)
        if i < 0:
            break
        j = data.find(XML_CLOSE, i)
        if j < 0:
            raise I18nExtractError(f"Lezáratlan <tooltips> blokk a {i} eltolásnál.")
        end = j + len(XML_CLOSE)
        raw = data[i:end]
        blocks.append(Block(offset=i, raw=raw, panel=_panel_of(raw)))
        i = end
    if not blocks:
        raise I18nExtractError(
            "Egyetlen <tooltips> blokk sem található — nem Picasa3i18n.dll, "
            "vagy a formátum megváltozott."
        )
    return blocks


def _panel_of(raw: bytes) -> str:
    """A blokk `target=` attribútumaiból kiolvasott panelnév(ek).

    Ha minden `target` ugyanazzal a `<panel>/` előtaggal kezdődik, azt adja
    vissza; egyébként `MISC_KEY`-t (vegyes/több paneles blokk).
    """
    root = ET.fromstring(raw)
    panels = set()
    for action in root.findall("action"):
        target = action.get("target", "")
        panel, _, _ = target.partition("/")
        if panel:
            panels.add(panel)
    if len(panels) == 1:
        return next(iter(panels))
    return MISC_KEY


def group_by_panel(blocks: list[Block]) -> dict[str, list[Block]]:
    """Blokkok panelnév szerint csoportosítva, fájl-eltolás szerint rendezve."""
    groups: dict[str, list[Block]] = {}
    for b in blocks:
        groups.setdefault(b.panel, []).append(b)
    for panel in groups:
        groups[panel].sort(key=lambda b: b.offset)
    return groups


def _has_hungarian_letters(raw: bytes) -> bool:
    text = raw.decode("utf-8", errors="replace")
    return any(ch in text for ch in HUNGARIAN_LETTERS)


def resolve_language_index(panel_blocks: list[Block], lang: str) -> int:
    """A kért nyelvhez tartozó blokk indexe a panelcsoporton belül.

    `en` és `hu`/`hu-HU` esetén tartalmi ellenőrzést is végez (ld. modul
    docstring); egyéb nyelvkódnál a `LANG_ORDER` pozícióját használja.
    """
    lang_norm = lang.strip().lower()

    if lang_norm in ("en", "en-us", "en-gb"):
        # A 0. index mindig az alap angol — ellenőrizzük, hogy tényleg
        # túlnyomórészt ASCII-e (ha nem, a fájl szerkezete megváltozott).
        candidate = panel_blocks[0]
        text = candidate.raw.decode("utf-8", errors="replace")
        non_ascii = sum(1 for ch in text if ord(ch) > 127)
        if non_ascii > len(text) * 0.05:
            raise I18nExtractError(
                "A 0. index nem tűnik angol szövegnek (túl sok nem-ASCII "
                "karakter) — a nyelv-hozzárendelés ennél a panelnél "
                "bizonytalan."
            )
        return 0

    if lang_norm in ("hu", "hu-hu"):
        for idx, b in enumerate(panel_blocks):
            if _has_hungarian_letters(b.raw):
                return idx
        # Tartalék: ha a panel túl rövid ő/ű betűs szóhoz, pozíció alapján.
        if len(panel_blocks) > LANG_ORDER.index("hu-HU"):
            return LANG_ORDER.index("hu-HU")
        raise I18nExtractError(
            "Nem található magyar (ő/ű betűs) blokk, és a panelcsoport "
            "túl rövid a pozíció alapú tartalékhoz."
        )

    # Egyéb nyelv: pozíció a LANG_ORDER táblázat alapján.
    try:
        idx = LANG_ORDER.index(lang) if lang in LANG_ORDER else None
    except ValueError:
        idx = None
    if idx is None:
        # engedjünk meg case-insensitive / kötőjel nélküli egyezést is
        for i, code in enumerate(LANG_ORDER):
            if code.lower() == lang_norm or code.lower().split("-")[0] == lang_norm:
                idx = i
                break
    if idx is None:
        raise I18nExtractError(
            f"Ismeretlen nyelvkód: {lang!r}. Használd a --list-langs "
            "kapcsolót az elérhető kódok listázásához."
        )
    if idx >= len(panel_blocks):
        raise I18nExtractError(
            f"A(z) {lang!r} nyelv indexe ({idx}) nagyobb, mint a panelcsoport "
            f"mérete ({len(panel_blocks)}) — ennél a panelnél nincs ennyi "
            "nyelvi blokk."
        )
    return idx


@dataclass(frozen=True)
class Entry:
    """Egy kinyert felirat/tipp: cél-elem, típus és szöveg."""

    target: str
    type: str
    text: str


def extract_language(data: bytes, lang: str) -> list[Entry]:
    """A kért nyelv összes felirata/tippje, panelenként a megfelelő blokkból."""
    blocks = find_tooltips_blocks(data)
    groups = group_by_panel(blocks)

    entries: list[Entry] = []
    skipped_panels: list[str] = []
    for panel, panel_blocks in sorted(groups.items()):
        try:
            idx = resolve_language_index(panel_blocks, lang)
        except I18nExtractError:
            skipped_panels.append(panel)
            continue
        root = ET.fromstring(panel_blocks[idx].raw)
        for action in root.findall("action"):
            target = action.get("target", "")
            atype = action.get("type", "")
            xmbtext = action.find("xmbtext")
            text = xmbtext.text if xmbtext is not None and xmbtext.text else ""
            entries.append(Entry(target=target, type=atype, text=text))

    if skipped_panels:
        print(
            f"Figyelmeztetés: {len(skipped_panels)} panelnél nem sikerült "
            f"azonosítani a(z) {lang!r} nyelvet, kihagyva: "
            f"{', '.join(sorted(skipped_panels))}",
            file=sys.stderr,
        )
    return entries


def _cmd_list_langs(data: bytes) -> int:
    blocks = find_tooltips_blocks(data)
    groups = group_by_panel(blocks)
    sizes = sorted(set(len(v) for v in groups.values()))
    print(f"{len(blocks)} <tooltips> blokk, {len(groups)} panelcsoport.")
    print(f"Panelcsoport-méretek: {sizes}")
    print()
    print("Nyelvi index-táblázat (index: kód — csak en és hu-HU tartalmilag ellenőrzött):")
    for idx, code in enumerate(LANG_ORDER):
        marker = " (tartalmilag ellenőrzött)" if code in ("en", "hu-HU") else ""
        print(f"  {idx:2d}: {code}{marker}")
    return 0


def _cmd_extract(data: bytes, lang: str, out: Path) -> int:
    entries = extract_language(data, lang)
    if not entries:
        raise I18nExtractError(f"Nem sikerült egyetlen bejegyzést sem kinyerni a(z) {lang!r} nyelvhez.")
    with out.open("w", encoding="utf-8", newline="") as f:
        f.write("target\ttype\tszöveg\n")
        for e in entries:
            safe_text = e.text.replace("\t", " ").replace("\n", " ").replace("\r", " ")
            f.write(f"{e.target}\t{e.type}\t{safe_text}\n")
    print(f"{len(entries)} bejegyzés kiírva ide: {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("dll", type=Path, help="a Picasa3i18n.dll elérési útja")
    parser.add_argument("--lang", help="nyelvkód (pl. hu, en, pl-PL, ...)")
    parser.add_argument("--out", type=Path, help="kimeneti TSV fájl")
    parser.add_argument(
        "--list-langs", action="store_true", help="elérhető nyelvi indexek listázása"
    )

    args = parser.parse_args(argv)

    try:
        data = args.dll.read_bytes()
    except OSError as err:
        print(f"Hiba: nem sikerült beolvasni a fájlt: {err}", file=sys.stderr)
        return 1

    try:
        if args.list_langs:
            return _cmd_list_langs(data)
        if not args.lang or not args.out:
            parser.error("--lang és --out kötelező (kivéve --list-langs esetén)")
        return _cmd_extract(data, args.lang, args.out)
    except I18nExtractError as err:
        print(f"Hiba: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
