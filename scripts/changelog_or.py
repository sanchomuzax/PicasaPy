#!/usr/bin/env python3
"""A felhasználót érintő PR hozzon CHANGELOG-bejegyzést (#1340).

## Miért

A v0.8.71 és a v0.8.72 ezzel a mondattal jelent meg a Releases hasábon:

    „Ez a kiadás nem hoz felhasználónak látszó változást."

Miközben az egyikben a letiltott gombok megjelenése javult (#893), a
másikban a lasszós kijelölés készült el (#897). A mondat HAZUDOTT — a
tulajdonos vette észre, és joggal háborodott fel: a Releases hasáb az ő
egyetlen látható verziókövetése.

Az ok: a kiadási jegyzet a CHANGELOG szakaszából készül, és egyik PR sem
írt bejegyzést, ezért a tartaléksablon ment ki. A szabály („a CHANGELOG
szövegét EMBER írja, a jegy PR-jében") le volt írva az `auto_bump.py`
fejlécében — de semmi nem őrizte.

## A mérce

Ugyanaz, mint a verzióemelésé (`kiadas_szukseges`): ami eljut a
felhasználóhoz, ahhoz mondat is jár. Két külön megfogalmazású szabály
előbb-utóbb elcsúszna egymástól.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections.abc import Callable, Iterable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from kiadas_szukseges import kiadasra_erdemes  # noqa: E402

Runner = Callable[[list[str]], "subprocess.CompletedProcess[str]"]

#: A még ki nem adott munka szakasza — ide kell írni.
KIADATLAN_CIM = "## [Nem kiadott]"


def _valodi_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    # #2077: `errors="replace"` — a `git diff` kimenete NEM feltétlenül
    # érvényes UTF-8 (idegen kódolású fájl, bináris darab). Enélkül az
    # őr a DEKÓDOLÁSON hal meg, nem a leleten, és a CI úgy pirosodik,
    # hogy közben semmi baj nincs a vizsgált tartalommal.
    return subprocess.run(
        args, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False
    )


#: A `pyproject.toml` verziósora — ezt az automatika írja át, nem ember.
_VERZIO_SOR = re.compile(r"^[+-]version\s*=")


def van_erdemi_valtozas(diff: str) -> bool:
    """Van-e a fájlban a VERZIÓSORON KÍVÜL is változás?

    ⚠️ Enélkül az őr a saját automatikánkat fogná meg: a verzióemelő PR a
    verziósort írja át és a CHANGELOG címét nevezi át, emberi mondatot pedig
    nem hoz — mert nem is neki kell. Ha ezt megfognánk, a verzióemelés soha
    nem tudna beolvadni, és a kiadás állna. Ugyanez a kivétel él a
    `ci.yml` változás-elemzésében is."""
    for sor in diff.splitlines():
        if not sor or sor[0] not in "+-" or sor.startswith(("+++", "---")):
            continue
        if not _VERZIO_SOR.match(sor):
            return True
    return False


#: Fájlkiterjesztés -> a nyelv SORVÉGI megjegyzés-jele. Ami nincs benne,
#: annál a `#` marad az alapértelmezés (a `.py`, `.toml`, `.sh` mind ilyen).
#: A `.qml`/`.js` SZÁNDÉKOSAN külön áll: ott a `#` NEM megjegyzés (szín-
#: literál kezdete lehet), a `//` viszont az (#2042).
_KOMMENT_JEL: dict[str, str] = {".qml": "//", ".js": "//", ".mjs": "//"}

#: Bizonytalanná tevő jelek a `//`-nyelvekben. A `/* */` több sorra nyúlik,
#: tehát egy megváltozott belső sor közönséges kódnak látszik; a backtickes
#: sablonsztring pedig azt teszi lehetővé, hogy egy `//`-kezdetű sor
#: valójában SZTRING belseje legyen. Bármelyik felbukkanása esetén a
#: szigorú ág nyer — a téves riasztás bosszantó, a téves ÁTENGEDÉS néma.
_BIZONYTALAN = ("/*", "*/", "`")


def csak_komment_valtozas(diff: str, fajl: str | None = None) -> bool:
    """Csak `#`-megjegyzés (és üres) sorok változtak a fájlban? (#1875)

    ⚠️ **A szabály SZÁNDÉKOSAN szűk.** Nem tud kódváltozást elrejteni:
    bármely érdemi sor a diffben azonnal kiüti, mert az nem `#`-kezdetű.
    A Python-DOCSTRING-et NEM kezeli (az nem `#`-sor) — ott a szigor
    marad. A téves riasztás bosszantó, a téves ÁTENGEDÉS néma, ezért a
    kétes eset a szigorú oldalra dől.

    **#2042 — a `//`-nyelvek.** A `.qml`/`.js` fájloknál a `#` NEM
    megjegyzés (szín-literál kezdete lehet), a `//` viszont az. A `fajl`
    megadásakor a kiterjesztés dönti el a jelet; fájlnév nélkül a régi,
    `#`-alapú viselkedés marad. Ha a diffben `/*`, `*/` vagy backtick
    bukkan fel, a szigorú ág nyer: az előbbi kettő több sorra nyúló blokk,
    az utóbbi sablonsztring, és mindkettőben egy `//`-kezdetű sor lehet
    NEM megjegyzés. Élesben a #2036 bukott el egyetlen QML-kommenten.

    Üres diff = „nem tudjuk" ⇒ NEM mondjuk kommentnek.

    Miért kell: a projekt elve, hogy a „miért" a kód mellett éljen — a
    `render/` konstansainak `#:` blokkjai tele vannak mért levezetéssel.
    Az őr ezt eddig megadóztatta: a #1873-at (a #1607 mérésének
    beírását a konstans mellé) elbuktatta, holott egyetlen kódsor sem
    változott, és a CHANGELOG-ba nem-felhasználói mondat került volna.
    """
    jel = "#"
    if fajl is not None:
        jel = _KOMMENT_JEL.get(Path(fajl).suffix.lower(), "#")

    latott = False
    for sor in diff.splitlines():
        if not sor or sor[0] not in "+-" or sor.startswith(("+++", "---")):
            continue
        latott = True
        tartalom = sor[1:].strip()
        if jel == "//" and any(x in tartalom for x in _BIZONYTALAN):
            return False
        if tartalom and not tartalom.startswith(jel):
            return False
    return latott


def kell_bejegyzes(fajlok: Iterable[str]) -> bool:
    """Érinti-e a változás a felhasználót? Ugyanaz a mérce, mint a kiadásé."""
    return kiadasra_erdemes(list(fajlok))


def van_uj_bejegyzes(changelog_diff: str) -> bool:
    """Került-e ÚJ felsorolás-elem a naplóba?

    ⚠️ A szakaszcím átnevezése (`[Nem kiadott]` → `[0.8.71]`) NEM bejegyzés:
    azt a verzióemelő automatika végzi, emberi mondat nélkül. Ha ezt
    elfogadnánk, a kapu pont a hibás esetet engedné át."""
    for sor in changelog_diff.splitlines():
        if not sor.startswith("+") or sor.startswith("+++"):
            continue
        tartalom = sor[1:].strip()
        if tartalom.startswith(("- ", "* ")):
            return True
    return False


#: A verzióemelő diff `+version = "X"` sora — ebből tudjuk, MELYIK kiadás
#: születik a beolvadáskor.
_EMELT_VERZIO = re.compile(r'^\+version\s*=\s*"([^"]+)"', re.MULTILINE)


def emelt_verzio(pyproject_diff: str) -> str | None:
    """Melyik verzióra emel ez a PR? `None`, ha nem emel."""
    talalat = _EMELT_VERZIO.search(pyproject_diff)
    return talalat.group(1) if talalat else None


def van_verzio_szakasz(changelog: str, verzio: str) -> bool:
    """Van-e a naplóban a verzióhoz tartozó, MEGNEVEZETT szakasz?

    ⚠️ A `[Nem kiadott]` szakasz NEM számít annak: a kiadási jegyzet a
    `## [X]` címre keres, és a napló verzió-hozzárendelése is ezen múlik.
    A minta a záró `]`-t is megköveteli, különben a `0.8.15` rátalálna a
    `0.8.157`-re."""
    return re.search(
        rf"^##\s*\[{re.escape(verzio)}\]", changelog, re.MULTILINE
    ) is not None


def van_kiadatlan_szakasz(changelog: str) -> bool:
    """Van-e egyáltalán hova írni? A hiányzó szakasz maga is hiba."""
    return KIADATLAN_CIM in changelog


def main(
    argv: list[str] | None = None,
    *,
    runner: Runner = _valodi_git,
) -> int:
    ertelmezo = argparse.ArgumentParser(description="Van-e CHANGELOG-bejegyzés?")
    ertelmezo.add_argument("--base", required=True)
    ertelmezo.add_argument("--head", required=True)
    ertelmezo.add_argument("--changelog", default=None)
    beallitas = ertelmezo.parse_args(argv)

    # #1770: HÁROM PONT — a PR SAJÁT commitjait nézzük, ne a kétirányú
    # diffet. Sűrű kiadásnál a `main` percek alatt előrelép, és a kétirányú
    # alak MÁSOK változásait is a PR-hez számolja: egy ártatlan
    # dokumentáció-PR így kaphat „ez a PR kódot módosít, de nincs
    # CHANGELOG-bejegyzése" hibát. Élesben elő is jött (#1765).
    valtozott = runner(
        ["git", "diff", "--name-only", f"{beallitas.base}...{beallitas.head}"]
    )
    if valtozott.returncode != 0:
        # ⚠️ A sikertelen mérésből SOHA nem lehet zöld út. Éles próbán jött
        # elő: hibás refekkel a diff elbukott, a fájllista üres lett, és az őr
        # „nincs mit ellenőrizni" címén átengedett. Ugyanaz a hibaosztály,
        # ami miatt ez a jegy megnyílt — csak eggyel feljebb.
        print(
            f"::error title=A CHANGELOG-őr nem tudott mérni::"
            f"A `git diff {beallitas.base}...{beallitas.head}` elbukott: "
            f"{(valtozott.stderr or '').strip()[:200]}. Ellenőrzés nélkül nem "
            f"adunk zöld utat."
        )
        return 1
    fajlok = [s for s in (valtozott.stdout or "").splitlines() if s.strip()]

    erdemi = [f for f in fajlok if kell_bejegyzes([f])]

    # #1875: a csak-megjegyzés változás nem jut el a felhasználóhoz. A
    # `kell_bejegyzes` FÁJLNÉV alapján dönt, tehát a kommentet sem tudja
    # megkülönböztetni a kódtól; itt a DIFF dönt.
    csak_kommentesek = [
        f
        for f in erdemi
        if csak_komment_valtozas(
            (runner(["git", "diff", f"{beallitas.base}...{beallitas.head}", "--", f]).stdout or ""),
            f,
        )
    ]
    if csak_kommentesek:
        print(
            "Csak megjegyzés változott ezekben: "
            + ", ".join(csak_kommentesek)
        )
        erdemi = [f for f in erdemi if f not in csak_kommentesek]

    if erdemi == ["pyproject.toml"]:
        pyproject_diff = runner([
            "git", "diff", beallitas.base, beallitas.head, "--", "pyproject.toml",
        ])
        if not van_erdemi_valtozas(pyproject_diff.stdout or ""):
            print("Csak a verziósor változott — ez az automatika saját PR-je.")
            return 0

    if not erdemi:
        print("A változás nem jut el a felhasználóhoz — nem kell CHANGELOG-bejegyzés.")
        return 0

    naplo_ut = Path(beallitas.changelog) if beallitas.changelog else (
        Path(__file__).resolve().parents[1] / "CHANGELOG.md"
    )
    try:
        naplo = naplo_ut.read_text(encoding="utf-8")
    except OSError:
        naplo = ""

    diff = runner([
        "git", "diff", f"{beallitas.base}...{beallitas.head}", "--", "CHANGELOG.md",
    ])
    # #1770 (3. réteg): ha ez a PR verziót emel, a naplóban legyen HOZZÁ
    # tartozó, megnevezett szakasz. A `[Nem kiadott]`-ban hagyott bejegyzést
    # a mi menetünkben SOHA nem zárja le semmi (az `auto_bump.py` lezáró
    # lépése csak automatikus emelésnél futna, nálunk viszont minden kód-PR
    # kézzel emel) — így a következő kiadás jegyzete megismételné, a napló
    # pedig elvesztené a verzió-hozzárendelést. Mérve: a v0.8.156 és a
    # v0.8.157 után is bent maradt a bejegyzés.
    pyproject_diff = runner([
        "git", "diff", f"{beallitas.base}...{beallitas.head}", "--", "pyproject.toml",
    ])
    verzio = emelt_verzio(pyproject_diff.stdout or "")
    if verzio and not van_verzio_szakasz(naplo, verzio):
        print(
            f"::error title=A CHANGELOG szakasza nincs megnevezve::"
            f"Ez a PR a(z) {verzio} verzióra emel, tehát a beolvadáskor "
            f"pontosan ez a kiadás születik — a naplóban viszont nincs "
            f"`## [{verzio}]` szakasz. Nevezd át a `{KIADATLAN_CIM}` "
            f"szakaszt `## [{verzio}] – ÉÉÉÉ-HH-NN` alakra (a bejegyzésekkel "
            f"együtt), és tegyél fölé egy üres `{KIADATLAN_CIM}` címet a "
            f"következő körnek. Enélkül a kiadási jegyzet nem találja meg a "
            f"hozzá írt mondatokat, és a napló elveszti, mi melyik "
            f"verzióban ment ki (#1770)."
        )
        return 1

    if van_uj_bejegyzes(diff.stdout or ""):
        print("Van új CHANGELOG-bejegyzés — rendben.")
        return 0

    if not van_kiadatlan_szakasz(naplo):
        print(
            f"::error title=Hiányzik a CHANGELOG „Nem kiadott” szakasza::"
            f"A bejegyzésnek nincs hova kerülnie. Vedd fel a `{KIADATLAN_CIM}` "
            f"címet a CHANGELOG.md tetejére, és írd alá, mi változott."
        )
        return 1

    print(
        "::error title=Hiányzik a CHANGELOG-bejegyzés::"
        "Ez a PR a felhasználóhoz eljutó kódot módosít, de nem ír hozzá "
        "mondatot a CHANGELOG „Nem kiadott” szakaszába. Enélkül a kiadási "
        "jegyzet tartaléksablonra vált — a v0.8.71 és a v0.8.72 így állította "
        "magáról valótlanul, hogy nem hoz látható változást (#1340)."
    )
    print("A programot érintő fájlok:")
    for f in erdemi:
        print(f"  {f}")
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
