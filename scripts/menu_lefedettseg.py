#!/usr/bin/env python3
"""Menü-lefedettség MÉRÉSE — nem kézzel karbantartott lista.

A listás jegyek nálunk elrohadnak: 2026-08-26-i mérés szerint a 175
nyitott jegyből **87 (49 %)** óta senki hozzá sem nyúlt, amióta megnyílt.
Egy 154 tételes pipálható lista egy jegy törzsében ugyanerre a sorsra jut:
senki nem vezeti, és fél év múlva senki nem tudja, mi igaz belőle.

Ez a szkript ezért **méri** a lefedettséget a tényleges melléktermékekből
(a bináris menü-leltárból és a `docs/specs/` lapokból), és **generálja**
a jelentést. Amit generálunk, az nem tud elavulni: minden futás a mai
állapotot adja.

Használat:

    python3 scripts/menu_lefedettseg.py            # emberi olvasásra
    python3 scripts/menu_lefedettseg.py --md       # a jelentés Markdownban
    python3 scripts/menu_lefedettseg.py --json     # gépi feldolgozásra
    python3 scripts/menu_lefedettseg.py --ellenoriz  # CI: nem-nulla, ha ROMLOTT

Csak OLVAS. A `--ellenoriz` a `docs/menu-lefedettseg.md`-ben rögzített
korábbi számokhoz hasonlít: a lefedettség **nem csökkenhet**.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CSV_PATH = REPO / "docs" / "specs" / "picasa-menu-parancsok.csv"
SPEC_DIR = REPO / "docs" / "specs"
REPORT = REPO / "docs" / "menu-lefedettseg.md"

#: A puszta névfelsorolás nem feltárás — ezek a lapok csak LISTÁZNAK.
NEVSOR_LAPOK = {"picasa-menu-leltar.md"}
#: Itt áll a tényleges viselkedés (mit indít, mit ír, mikor).
VISELKEDES_LAP = "picasa-menu-parancsok-viselkedes.md"

#: Parancsok, amelyek viselkedése NEM ezen az egy lapon, hanem egy saját,
#: mélyebb spec-lapon van feltárva.
#:
#: ⚠️ Miért kell ez, és miért KURÁLT lista, nem automatika. A mérés eredetileg
#: EGYETLEN lapot ismert el feltárásnak. Emiatt 2026-08-31-én nyolc
#: megjelenítési mód „feltáratlanként" állt a sorban, miközben a
#: `picasa-megjelenitesi-modok.md` a **képpont-matematikájukat is** méri
#: (LUT-ok bájtra, a tárolás hiánya, az indulási állapot, az export-hatókör).
#: A determinisztikus sor emiatt újra és újra ezeket adta volna ki — a
#: kutatói körök a már elvégzett munkát ismételték volna.
#:
#: Automatikus „bárhol említik" szabály viszont NEM jó: az említés lehet
#: puszta felirat-tábla is (a jobb fiók lapjai például a `jobb-fiok-meretek.md`
#: GEOMETRIA-lapján szerepelnek, a viselkedésük nélkül). Ezért minden sor
#: **kimondott állítás**: „ezen a lapon ennek a parancsnak a VISELKEDÉSE le van
#: írva" — mit indít, mit ír, mikor. Aki felvesz ide egy parancsot, ezt állítja,
#: és greppel ellenőrizhető, hogy igaz-e.
VISELKEDES_MAS_LAPON: dict[str, frozenset[str]] = {
    # A tizenegy megjelenítési mód: algoritmus képpontra, tárolás (NINCS),
    # indulási állapot (`RemoteDesktopCheck`), hatókör (képernyő; export NEM).
    "picasa-megjelenitesi-modok.md": frozenset({
        "ID_VIEW_NORMAL", "ID_VIEW_16", "ID_VIEW_LCD", "ID_VIEW_LINEAR",
        "ID_VIEW_MAC", "ID_VIEW_OV", "ID_VIEW_PROJECTOR", "ID_VIEW_RDESK",
    }),
    # A bal hasáb gyökér-hatókörei: melyik gyökérre vált, és honnan jön a pipa
    # (a `folderviewpopup` kezelő scope-kulcsai: "all" / "mydocs" / "desktop").
    "picasa-konyvtar-eszkoztar-viselkedes.md": frozenset({
        "ID_VIEW_MYCOMPUTER", "ID_VIEW_MYDOCS", "ID_VIEW_DESKTOP",
    }),
}


def _mashol_feltart() -> set[str]:
    """A más lapon feltárt parancsok — CSAK ha a lap tényleg említi is.

    A kurált lista így nem tud némán hazudni: ha egy lapot átneveznek vagy
    egy parancs kikerül belőle, a tétel magától elveszti a hatását.
    """
    lapok = _lapok()
    ki: set[str] = set()
    for lap, parancsok in VISELKEDES_MAS_LAPON.items():
        szoveg = lapok.get(lap, "")
        ki |= {p for p in parancsok if p in szoveg}
    return ki

#: Nem építjük meg — a Picasa Web / Google+ / YouTube szolgáltatások 2016
#: (az `ID_DELETE_EMPTY_ALBUMS` felirata kimondja: „Üres ONLINE albumok törlése";
#:  az `ID_BURNCD` egy szállított windowsos/mac nézőprogramot éget lemezre — #32;
#:  az `ID_EXPORT_SENDTOBLOGGER` a Blogger-feltöltés, a szolgáltatás halott)
#: óta nem léteznek, a CD-írás és a telepítő-kezelés nem a mi dolgunk.
HATOKORON_KIVUL = re.compile(
    r"^ID_(FTPWEB|GETMYSTUFF|TOOLS_BATCH_UPLOAD|TOOLS_COLLAB|TOOLS_YOUTUBE|DELETE_EMPTY_ALBUMS|BURNCD|EXPORT_SENDTOBLOGGER"
    r"|EXPORT_EARTH|HELP_UNINSTALL|HELP_CHECK_FOR_UPDATES|HELP_PICASA_FORUMS"
    r"|HELP_PICASA_README|HELP_RELEASENOTES|HELP_PRIVACY|HELP_DEFAULT)$"
)


def _parancsok() -> list[str]:
    with CSV_PATH.open(encoding="utf-8") as fh:
        sorok = list(csv.reader(fh))
    return sorted({s[1] for s in sorok[1:] if len(s) > 1 and s[1].startswith("ID_")})


#: Ennyi sort nézünk meg a fájl elején a „generált" jelölés keresésekor.
#:
#: ⚠️ A teljes szövegben keresni NEM jó: MÉRVE (2026-09-01) a „generál"
#: szótő 14 lapra illeszkedik, mert a PRÓZA is használja („a Picasa saját
#: generált…", „a lap generált blokkja"). A fejléc első három sorára
#: szűkítve pontosan 2 lap jön ki, hamis pozitív nélkül — és mindkét
#: generált lapunk tényleg ott mondja ki magáról.
_FEJLEC_SOROK = 3

_GENERALT_JELEK = ("generálva", "generált", "ne szerkeszd", "ne írd kézzel")


def _generalt(szoveg: str) -> bool:
    """Gépi lap-e — a FEJLÉCE alapján."""
    fejlec = "\n".join(szoveg.splitlines()[:_FEJLEC_SOROK]).casefold()
    return any(jel in fejlec for jel in _GENERALT_JELEK)


def _lapok() -> dict[str, str]:
    """A `docs/specs/` lapjai — a GENERÁLT lapok NÉLKÜL.

    ⚠️ **Körkörösség-védelem (#1878).** A mérő bizonyítékként olvassa
    ezeket a lapokat. Ha egy generált jelentés is köztük van, a mérő a
    SAJÁT (vagy egy testvér-eszköz) kimenetét hinné el, és a szám némán
    100%-ra ugorhatna.

    Ma két generált lap van a `docs/specs/` alatt — `ui-lefedettseg.md`
    (privát `ui_lefedettseg.py`) és `lanc-szakadasok-leltar.md`
    (`kepesseg_or.py`) —, és egyikben sincs `ID_*` token, tehát a mai
    138/138 nem önhivatkozó. **Ez azonban szerencse, nem szerkezet:** ha
    egy generált lap egyszer parancsneveket sorolna, a szám hazudna. A
    kizárás ezért nem utólagos javítás, hanem a mérés feltétele.

    A testvér-eszköz (#1878) ugyanezt a szabályt kapja — ott a naiv
    névgrep 49 elemből 31 hamis pozitívot adott, mind körkörösségből."""
    return {
        p.name: szoveg
        for p in SPEC_DIR.glob("*.md")
        if not _generalt(szoveg := p.read_text(encoding="utf-8"))
    }


def merd() -> dict:
    parancsok = _parancsok()
    lapok = _lapok()
    viselkedes = lapok.get(VISELKEDES_LAP, "")
    mashol = _mashol_feltart()
    ki: dict[str, list[str]] = {
        "viselkedes": [], "erdemi": [], "csak_nev": [],
        "sehol": [], "hatokoron_kivul": [],
    }
    for cmd in parancsok:
        if HATOKORON_KIVUL.match(cmd):
            ki["hatokoron_kivul"].append(cmd)
            continue
        hol = {nev for nev, szoveg in lapok.items() if cmd in szoveg}
        if not hol:
            ki["sehol"].append(cmd)
        elif cmd in viselkedes or cmd in mashol:
            ki["viselkedes"].append(cmd)
        elif hol <= NEVSOR_LAPOK:
            ki["csak_nev"].append(cmd)
        else:
            ki["erdemi"].append(cmd)
    ki["osszes"] = parancsok
    return ki


def kovetkezo_ot(m: dict) -> list[str]:
    """A soron következő öt — determinisztikusan, hogy ne kelljen VÁLASZTANI.

    Előbb a `sehol` (semmit nem tudunk róla), aztán a `csak_nev`, végül az
    `erdemi` — amiről van valami leírás, de a VISELKEDÉSE nincs feltárva.
    Ezen belül ábécésorrend: bárki futtatja, ugyanazt az ötöt kapja, tehát
    két kör nem ütközik, és nem kell egyeztetni.

    ⚠️ Az `erdemi` NEM hagyható ki. 2026-08-27-én a lista kiürült (a `sehol`
    0-ra, a `csak_nev` 1-re fogyott), miközben **74 parancs viselkedése
    ismeretlen** volt — a mechanizmus pont akkor állt volna le, amikor a
    nehezebb fele kezdődik. A tulajdonos vette észre.
    """
    return (m["sehol"] + m["csak_nev"] + m["erdemi"])[:5]


def markdown(m: dict) -> str:
    n = len(m["osszes"])
    hatokor = n - len(m["hatokoron_kivul"])
    kesz = len(m["viselkedes"])
    sorok = [
        "# Menü-lefedettség — GENERÁLT, ne szerkeszd kézzel",
        "",
        "> Ezt a lapot a `scripts/menu_lefedettseg.py` írja. Kézi lista",
        "> helyett azért mérés, mert a listás jegyeink elrohadnak: a",
        "> 2026-08-26-i mérés szerint a 175 nyitott jegyből **87 (49 %)**",
        "> óta senki hozzá sem nyúlt, amióta megnyílt.",
        "",
        f"## ⛔ {hatokor - kesz} parancs viselkedése ISMERETLEN",
        "",
        f"**{kesz} / {hatokor}** van feltárva (**{100 * kesz // hatokor} %**) — "
        f"vagyis **{hatokor - kesz}** parancsról NEM tudjuk, mit csinál. "
        f"({len(m['hatokoron_kivul'])} tétel hatókörön kívül.)",
        "",
        "> ⚠️ A „csak említve” NEM azt jelenti, hogy ismerjük. Azt jelenti, "
        "> hogy a neve leírva szerepel valahol — a **viselkedése nincs feltárva**.",
        "",
        "| állapot | darab | mit jelent |",
        "|---|---:|---|",
        f"| ✅ **viselkedés feltárva** | {len(m['viselkedes'])} | a `{VISELKEDES_LAP}`-on "
        f"vagy egy saját spec-lapon (`VISELKEDES_MAS_LAPON`): mit indít, mit ír, mikor |",
        f"| 🟡 érdemi lapon szerepel | {len(m['erdemi'])} | valamit tudunk róla, de a viselkedése nincs végigvive |",
        f"| ⚠️ **csak a neve** | {len(m['csak_nev'])} | egyedül a leltárban — a felirata és a helye |",
        f"| ⛔ **sehol** | {len(m['sehol'])} | egyetlen spec sem említi |",
        f"| — hatókörön kívül | {len(m['hatokoron_kivul'])} | megszűnt szolgáltatás vagy nem a mi dolgunk |",
        "",
        "## A soron következő öt",
        "",
        "Determinisztikus sorrend — bárki futtatja, ugyanezt kapja, tehát",
        "két kör nem ütközik és nem kell egyeztetni.",
        "",
    ]
    for cmd in kovetkezo_ot(m):
        sorok.append(f"- [ ] `{cmd}`")
    for cim, kulcs in (("⛔ Sehol nem említett", "sehol"), ("⚠️ Csak a neve ismert", "csak_nev")):
        sorok += ["", f"## {cim} ({len(m[kulcs])})", ""]
        sorok += [f"- `{c}`" for c in m[kulcs]] or ["*(egy sincs)*"]
    return "\n".join(sorok) + "\n"


def _korabbi_kesz() -> int | None:
    if not REPORT.exists():
        return None
    egyezes = re.search(r"\*\*(\d+) / \d+\*\* parancs viselkedése", REPORT.read_text(encoding="utf-8"))
    return int(egyezes.group(1)) if egyezes else None


def _utf8_kimenet() -> None:
    """#2077: a Windows-konzol alapértelmezett kódolása `cp1252`.

    A `✅`/`⚠️`/`⛔` jelek abban nem ábrázolhatók, és a `print` ilyenkor
    `UnicodeEncodeError`-t dob — az őr NEM a leletre, hanem a SAJÁT
    kiírására bukik el. Mérve: `ci.yml` 33693910159, windows 1/4, a
    `cv2_utvonal_or.py` `✅`-jén.

    A `reconfigure` a Python 3.7 óta létezik; ahol mégsem, ott a hiba
    elnyelése a helyes: a kiírás sosem lehet fontosabb az ellenőrzésnél.
    """
    for folyam in (sys.stdout, sys.stderr):
        try:
            folyam.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


def main() -> int:
    _utf8_kimenet()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--md", action="store_true", help="Markdown-jelentés a kimenetre")
    ap.add_argument("--json", action="store_true", help="gépi kimenet")
    ap.add_argument("--ir", action="store_true", help="a jelentés fájlba írása")
    ap.add_argument("--ellenoriz", action="store_true",
                    help="CI: nem-nulla kilépés, ha a lefedettség ROMLOTT")
    args = ap.parse_args()

    m = merd()
    if not m["osszes"]:
        print(f"⛔ A mérés ÜRES: a {CSV_PATH} egyetlen ID_ parancsot sem adott. "
              f"Az őr így akkor is »hibátlant« jelentene, ha semmit nem nézett meg.",
              file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(m, ensure_ascii=False, indent=2))
        return 0
    if args.ellenoriz:
        korabbi = _korabbi_kesz()
        mostani = len(m["viselkedes"])
        if korabbi is not None and mostani < korabbi:
            print(f"⛔ A menü-lefedettség ROMLOTT: {korabbi} → {mostani}", file=sys.stderr)
            return 1
        print(f"✅ Menü-lefedettség: {mostani} parancs viselkedése feltárva"
              + (f" (korábban {korabbi})" if korabbi is not None else ""))
        return 0
    szoveg = markdown(m)
    if args.ir:
        REPORT.write_text(szoveg, encoding="utf-8")
        print(f"megírva: {REPORT.relative_to(REPO)}")
        return 0
    print(szoveg if args.md else
          f"{len(m['viselkedes'])} feltárva · {len(m['erdemi'])} érdemi · "
          f"{len(m['csak_nev'])} csak név · {len(m['sehol'])} sehol · "
          f"{len(m['hatokoron_kivul'])} hatókörön kívül")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
