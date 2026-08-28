#!/usr/bin/env python3
"""Nyelvi ellenőrzés a felhasználónak látszó magyar szövegekre.

Miért: a tesztek a viselkedést őrzik, a szöveg helyességét semmi. Bizonyítottan
ment ki zöld teszt mellett "Többválaszás", "Modellek fülöt" és magyar mondatba
tévedt spanyol szó. 2026-08-18-tól volt egy helyi (commit utáni) őr, de az a
munkamásolatok és a szerveroldali beolvasztás miatt a szövegek zömét nem látta:
16 óra alatt 11 magyar szöveget hozó commitból egyet sem. Ezért az ellenőrzés
ide, a PR-be költözött, ahol MINDEN változás áthalad.

⚠️ MIT NEM ELLENŐRIZ (#1708). Ez az őr a változásban megjelenő MAGYAR
SZÖVEGEK helyességét nézi — NEM azt, hogy minden felirathoz VAN-E fordítás.
A kettő külön kérdés, és a „nincs új magyar felületi szöveg" válasz nem
jelenti, hogy nincs lefordítatlan felirat.

Bizonyíték (#1614, 2026-08-28): két új `qsTr()` felirat lefordítatlanul ment
volna ki, mert MINDKÉT szöveg szerepelt már a `.ts`-ben — csak MÁS
kontextusban (a Qt fordítási egységei kontextushoz kötöttek). Ez az őr
jelentette: „nincs új felhasználónak látszó szöveg" — és igaza is volt, mert
a szöveg nem volt új, csak a helye. A hiányt a
`tests/app/test_i18n_completeness.py` fogta meg a CI-n.

⇒ A teljességet MINDIG a `test_i18n_completeness.py` mondja meg. Ez az őr és
az a teszt nem helyettesíti egymást.

Szándékosan tanácsadó: sosem bukatja el a build-et. A hunspell a nem létező
szóalakokat és az idegen szavakat fogja meg; a nyelvhelyesség finomabb
kérdéseit (stílus, egyeztetés) nem — arra az emberi olvasás való.

Használat:
    python3 scripts/nyelvi_ellenorzes.py --proba          # öntesz
    python3 scripts/nyelvi_ellenorzes.py --tartomany A..B  # diff-ellenőrzés
"""

from __future__ import annotations

import argparse
import html
import pathlib
import re
import shutil
import subprocess
import sys

EKEZET = re.compile(r"[áéíóöőúüűÁÉÍÓÖŐÚÜŰ]")
IDEZETT = re.compile(r'"([^"\\]{2,})"' + r"|'([^'\\]{2,})'")
FORDITAS = re.compile(r"<(?:translation|source)[^>]*>([^<]+)<")
# helykitöltők és jelölők, amiket ki kell venni a szó elé/mögé
ZAJ = re.compile(r"(%\d*[sdfl]?|\{\d+\}|&\w+;|</?[a-zA-Z][^>]*>)")
# A Qt gyorsbillentyű-jelölője a szó KÖZEPÉN is állhat, ráadásul a .ts-ben
# XML-entitásként: "S&amp;zerkesztés". Előbb entitás-feloldás kell, aztán a
# jelölő NYOMTALAN törlése — szóközre cserélve kettévágja a szót, és a fél
# szó minden körben vaklármát ad (2026-08-19-i kalibrálás: 6 ilyen).
MNEMONIK = re.compile(r"&(?=\w)")
SZOHATAR = re.compile(r"[^0-9A-Za-zÁÉÍÓÖŐÚÜŰáéíóöőúüű-]+")

SZOTAR = pathlib.Path(__file__).with_name("nyelvi_szotar.txt")

# Az öntesz: a saját, dokumentált hibáink és a hozzájuk tartozó helyes alakok.
PROBA_HIBAS = ["Többválaszás", "fülöt", "orden"]
PROBA_HELYES = ["fület", "mentés", "vászon", "kollázs", "bélyegkép", "nagyítás"]


def _sajat_szavak() -> set[str]:
    if not SZOTAR.exists():
        return set()
    return {
        s.strip().lower()
        for s in SZOTAR.read_text(encoding="utf-8").splitlines()
        if s.strip() and not s.startswith("#")
    }


def _hunspell(szavak: list[str]) -> list[str]:
    """A hunspell által ismeretlennek jelölt szavak (sorrendtartóan)."""
    if not szavak or not shutil.which("hunspell"):
        return []
    r = subprocess.run(
        ["hunspell", "-d", "hu_HU", "-l"],
        input="\n".join(szavak), capture_output=True, text=True, timeout=120,
    )
    return list(dict.fromkeys(r.stdout.split()))


def _szavak(szovegek: list[str]) -> list[str]:
    ki: list[str] = []
    for sz in szovegek:
        tiszta = MNEMONIK.sub("", html.unescape(sz))
        for szo in SZOHATAR.split(ZAJ.sub(" ", tiszta)):
            if len(szo) > 2 and EKEZET.search(szo) and not szo.isupper():
                ki.append(szo)
    return list(dict.fromkeys(ki))


def magyar_szovegek(diff: str) -> list[str]:
    """A diffben HOZZÁADOTT, felhasználónak látszó magyar szövegek."""
    talalatok: list[str] = []
    for sor in diff.splitlines():
        if not sor.startswith("+") or sor.startswith("+++"):
            continue
        tartalom = sor[1:]
        jeloltek = [m.group(1) for m in FORDITAS.finditer(tartalom)]
        kod = re.split(r"(?://|#)", tartalom, maxsplit=1)[0]  # komment nem UI
        jeloltek += [a or b for a, b in IDEZETT.findall(kod)]
        talalatok += [j.strip() for j in jeloltek if EKEZET.search(j)]
    return list(dict.fromkeys(t for t in talalatok if t))


def _diff(tartomany: str) -> str:
    return subprocess.run(
        # CSAK a felhasználónak látszó felület: Qt-fordítások és QML-feliratok.
        # A .py szándékosan kimarad: ott a magyar szöveg zöme docstring és
        # tesztadat — a kalibráláskor (2026-08-19) mind a 25 találat onnan
        # jött, egy sem volt valódi felirat. A tesztfák sem UI-k.
        ["git", "diff", tartomany, "--unified=0", "--",
         "*.ts", "*.qml", ":(exclude)tests/**"],
        capture_output=True, text=True, timeout=60,
    ).stdout


def _jelentes(gyanus: list[str], szovegek: list[str]) -> None:
    print(f"::warning title=Nyelvi ellenőrzés::{len(gyanus)} gyanús szóalak "
          "a most hozzáadott magyar szövegekben")
    for szo in gyanus:
        pelda = next((s for s in szovegek if szo in s), "")
        print(f"  • {szo}" + (f"   ← „{pelda[:70]}”" if pelda else ""))
    print("\nHa valós hiba, javítsd a PR-ben. Ha helyes szó, vedd fel a "
          "scripts/nyelvi_szotar.txt fájlba.")


def proba() -> int:
    """Öntesz: a CI-naplóban bizonyítja, hogy a szótár tényleg működik."""
    if not shutil.which("hunspell"):
        print("HIBA: nincs hunspell — az ellenőrzés vak lenne.")
        return 1
    hibasnak_latszik = set(_hunspell(PROBA_HIBAS))
    helyesnek_latszik = set(PROBA_HELYES) - set(_hunspell(PROBA_HELYES))
    print("Öntesz — ismert hibás alakok:",
          {sz: ("FELISMERVE" if sz in hibasnak_latszik else "ÁTCSÚSZOTT")
           for sz in PROBA_HIBAS})
    print("Öntesz — ismert helyes alakok:",
          {sz: ("rendben" if sz in helyesnek_latszik else "VAKLÁRMA")
           for sz in PROBA_HELYES})
    hibak = [sz for sz in PROBA_HIBAS if sz not in hibasnak_latszik]
    vaklarma = [sz for sz in PROBA_HELYES if sz not in helyesnek_latszik]
    if hibak or vaklarma:
        print(f"Az öntesz megbukott (át: {hibak}, vaklárma: {vaklarma})")
        return 1
    print("Az öntesz rendben — az ellenőrzés valóban lát.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--proba", action="store_true", help="öntesz futtatása")
    ap.add_argument("--tartomany", help="git diff tartomány, pl. main...HEAD")
    args = ap.parse_args()

    if args.proba:
        return proba()
    if not args.tartomany:
        ap.error("--tartomany vagy --proba kell")

    szovegek = magyar_szovegek(_diff(args.tartomany))
    if not szovegek:
        # #1708: a válasz félreérthető volt — az agent ebből arra jutott,
        # hogy nincs fordítanivaló, holott két felirat lefordítatlan maradt
        # (más kontextusban már létező szöveg). Mondjuk ki a hatókört.
        print("Nincs új magyar felületi szöveg ebben a változásban.")
        print("  (Ez NEM jelenti, hogy minden felirat le van fordítva — "
              "azt a tests/app/test_i18n_completeness.py mondja meg.)")
        return 0
    gyanus = [sz for sz in _hunspell(_szavak(szovegek))
              if sz.lower() not in _sajat_szavak()]
    if not gyanus:
        print(f"{len(szovegek)} magyar szöveg ellenőrizve — nincs gyanús szóalak.")
        return 0
    _jelentes(gyanus, szovegek)
    return 0  # tanácsadó: sosem bukatja el a build-et


if __name__ == "__main__":
    sys.exit(main())
