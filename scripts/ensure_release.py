#!/usr/bin/env python3
"""A GitHub Release pótlása — átmeneti hibát TÚLÉLVE (#896).

## Miért van ez a szkript

A `release.yml` korábban egyetlen `gh release create` hívást tett. 2026-08-17-én
egy GitHub-incidens (~20% hibaarány) alatt ez a hívás **503-ba futott**, és a
**v0.7.65 kiadás elmaradt** — miközben a merge sikeres volt, a CI zöld, a jegy
lezárható. A hiba egy külön workflow-ban keletkezett, amit senki nem néz, és a
következő kiadás visszamenőleg el is fedte volna.

Két dolog véd ez ellen, és a kettő MÁS hibát fog meg:

1. **Újrapróbálkozás** (alapmód) — az átmeneti hibát hidalja át.
2. **`--check-only`** (ütemezett őrfutás) — azt fogja meg, ha a kiadó workflow
   **el sem indult**. Az újrapróbálkozás erre semmit nem ér, mert nincs mit
   újrapróbálni.

## A hívás alakja

    python3 scripts/ensure_release.py --target "$GITHUB_SHA" --repo "$REPO"
    python3 scripts/ensure_release.py --check-only --repo "$REPO"

A verzió alapból a `pyproject.toml`-ból jön (a projekt EGYETLEN verzióhelye,
#642), de `--version`-nel felülírható.

## Idempotencia

A művelet minden körben ELŐSZÖR megnézi, létezik-e már a kiadás, és ha igen,
azonnal kilép. Ezért kétszer lefuttatva sem készül duplikátum — ami nem
elméleti kérdés: a #878 körében kézzel kellett újrafuttatni a workflow-t.

**Egy 503-as létezés-ellenőrzésből NEM következik, hogy nincs kiadás** — a
`gh release view` hibakódja nem különbözteti meg a „nincs ilyen"-t a
„nem érhető el"-től, ezért az átmeneti hibát a hurok következő köre újra
megkérdezi, `create` nélkül.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from collections.abc import Callable, Sequence
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]

#: Hány kísérletet tegyünk, mielőtt zajosan feladjuk.
_ALAP_KISERLET = 5
#: A várakozás alapegysége másodpercben; a kísérlet sorszámával szorzódik.
_VARAKOZAS_EGYSEG = 20.0

#: Amiből átmeneti hibára következtetünk. A `gh` a HTTP-kódot a szöveges
#: hibaüzenetben adja vissza, kilépési kóddal nem különbözteti meg.
_ATMENETI_MINTAK = (
    "http 5",
    "no server is currently available",
    "timeout",
    "timed out",
    "connection reset",
    "temporarily unavailable",
    "bad gateway",
    "service unavailable",
)

Runner = Callable[[list[str]], "subprocess.CompletedProcess[str]"]


def _valodi_gh(args: list[str]) -> subprocess.CompletedProcess[str]:
    # #2077: `errors="replace"` — a `git diff` kimenete NEM feltétlenül
    # érvényes UTF-8 (idegen kódolású fájl, bináris darab). Enélkül az
    # őr a DEKÓDOLÁSON hal meg, nem a leleten, és a CI úgy pirosodik,
    # hogy közben semmi baj nincs a vizsgált tartalommal.
    return subprocess.run(
        args, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False
    )


def verzio_a_szovegbol(szoveg: str, *, forras: str = "a megadott szöveg") -> str:
    """A `version = "…"` sor értéke egy `pyproject.toml` SZÖVEGÉBŐL.

    Azért külön, mert a verziót nem csak a munkafa fájljából olvassuk: a
    kiadás utókövetése (#1338) az `origin/main`-en álló változatot nézi
    (`git show`), ott pedig nincs mit `Path`-ként megnyitni. Két külön
    verzióolvasó előbb-utóbb elcsúszna egymástól."""
    talalat = re.search(r'^version = "(.+?)"', szoveg, re.M)
    if talalat is None:
        raise ValueError(f"Nincs `version = \"…\"` sor ebben: {forras}")
    return talalat.group(1)


def olvasott_verzio(pyproject: Path | None = None) -> str:
    """A verzió a `pyproject.toml`-ból — a projekt EGYETLEN verzióhelye (#642)."""
    forras = pyproject or (_ROOT / "pyproject.toml")
    return verzio_a_szovegbol(
        forras.read_text(encoding="utf-8"), forras=f"a {forras} fájl"
    )


#: A kiadatlan szakasz címkéje — ugyanaz, amit az `auto_bump` keres.
_KIADATLAN_CIMKE = "Nem kiadott"


def _szakasz(szoveg: str, cim_minta: str) -> str | None:
    """Egy `## [<cím>]` szakasz törzse, vagy `None`, ha nincs ilyen."""
    minta = re.compile(
        rf"^## \[{cim_minta}\][^\n]*\n(.*?)(?=^## \[|\Z)",
        re.S | re.M,
    )
    talalat = minta.search(szoveg)
    return talalat.group(1) if talalat else None


def changelog_notes(version: str, changelog: Path | None = None) -> str:
    """A kiadási jegyzet a CHANGELOG verzió-szakaszából (#1167 utómunka).

    A GitHub `--generate-notes` kimenete a bot-PR-ek címeit listázza —
    a tulajdonos szavával „gépzaj": ebből nem derül ki, mi változott.
    A valódi, embernek írt összefoglaló a CHANGELOG-ban él; a kiadás
    jegyzete AZ. Üres/hiányzó szakasznál üres sztringet adunk, és a hívó
    az EMBERI tartalékra vált (`tartalek_jegyzet`) — gépi listára soha.
    """
    utvonal = changelog or Path(__file__).resolve().parents[1] / "CHANGELOG.md"
    try:
        szoveg = utvonal.read_text(encoding="utf-8")
    except OSError:
        return ""
    talalat = _szakasz(szoveg, re.escape(version))
    if talalat is None:
        # #1770 (2. réteg): ha nincs VERZIÓ-szakasz, a „Nem kiadott" alatt
        # álló mondatok pontosan azok, amiket most adunk ki.
        #
        # ⚠️ Miért kell ez: a szakaszt lezáró `auto_bump` CSAK akkor fut, ha
        # a verzió MÁR ki van adva — a mi menetünkben viszont minden PR
        # kézzel emel, tehát a lezárás a gyakorlatban sosem fut le. MÉRVE:
        # 2026-08-31 este TIZENÖT kiadás ment ki egymás után a gépi
        # tartalékkal („nem készült emberi összefoglaló"), pedig mind a
        # tizenöthöz volt megírt magyar bekezdés. A tulajdonos a Releases
        # hasábból követi a fejlődést — épp az nem jutott el hozzá, amit
        # neki írtunk.
        talalat = _szakasz(szoveg, re.escape(_KIADATLAN_CIMKE))
    if talalat is None:
        return ""
    torzs = talalat.strip()
    # a helykitöltő-kommentes szakasz nem jegyzet
    if not torzs or torzs.startswith("*("):
        return ""
    return torzs


#: Kiadás, amihez nincs CHANGELOG-szakasz. MÉRVE (2026-08-23): a
#: verzióemelő lánc körönként egy kiadást csinál, de a CHANGELOG
#: `[Nem kiadott]` szakaszát az ELSŐ emelés elviszi — a többi kiadás
#: szakasz nélkül marad, és a `--generate-notes` bot-PR-címeket listáz.
#: Három egymást követő kiadás (0.8.53–0.8.55) így ment ki gépzajjal,
#: pont azzal, amit a tulajdonos kifogásolt.
#:
#: ⚠️ #1340: a tartalék korábban AZT ÁLLÍTOTTA, hogy „ez a kiadás nem hoz
#: felhasználónak látszó változást". A v0.8.71-ben a letiltott gombok
#: megjelenése javult (#893), a v0.8.72-ben a lasszós kijelölés készült el
#: (#897) — a mondat mindkétszer HAZUDOTT, és a tulajdonos vette észre.
#: A szkript nem tudhatja, hogy nem volt látható változás; azt tudja, hogy
#: nincs hozzá EMBERI MONDAT. Csak ezt szabad kimondania.
_CHANGELOG_LINK = (
    "[CHANGELOG.md]"
    "(https://github.com/sanchomuzax/PicasaPy/blob/main/CHANGELOG.md)"
)

#: Amit az automatika saját magának commitol — a felhasználónak semmit nem mond.
_AUTOMATIKA_ELOTAGOK = ("chore: verzióemelés", "chore: verzioemeles")

#: A conventional-commit típusjelölés: a felhasználót nem érdekli.
_TIPUS_ELOTAG = re.compile(r"^(feat|fix|docs|test|chore|refactor|perf|ci)(\([^)]*\))?: ")


def erdemi_valtozasok(cimek: "Sequence[str]") -> tuple[str, ...]:
    """A beolvadt munkák címei — az automatika saját commitjai nélkül.

    ⚠️ Ez NEM a `--generate-notes` gépi listája: azt a bot-PR-ek címei tették
    zajjá, és pont azért vetettük el (#1167). Ezek EMBER által írt
    commit-címek, és csak akkor kerülnek elő, ha emberi összefoglaló nincs —
    a hamis „nem változott semmi" mondatnál minden esetben többet érnek."""
    tiszta = []
    for cim in cimek:
        szoveg = cim.strip()
        if not szoveg or szoveg.startswith(_AUTOMATIKA_ELOTAGOK):
            continue
        tiszta.append(_TIPUS_ELOTAG.sub("", szoveg))
    return tuple(tiszta)


def valodi_valtozasok(
    target: str, *, version: str, runner: Runner = _valodi_gh
) -> tuple[str, ...] | None:
    """A legutóbbi KORÁBBI kiadás óta beolvadt munkák címei.

    `None`, ha a mérés nem sikerült — és ez NEM ugyanaz, mint az üres lista.
    Az üres lista mért tény („nincs érdemi munka"), a `None` tudatlanság; a
    kettőt összemosni pontosan az a hiba, ami miatt ez a jegy megnyílt.

    ⚠️ A saját címkénket KI KELL zárni: ütemezett futásnál a `v<version>` már
    ott ülhet a célon, és a `git describe` magát adná vissza — a tartomány
    üres lenne, a jegyzet pedig „csak verziólépést" állítana egy valódi
    funkcióról. Éles próbán bukott meg, mielőtt kiment volna."""
    elozo = runner([
        "git", "describe", "--tags", "--abbrev=0",
        "--exclude", f"v{version}", target,
    ])
    if elozo.returncode != 0 or not (elozo.stdout or "").strip():
        return None
    naplo = runner([
        "git", "log", "--pretty=%s", f"{(elozo.stdout or '').strip()}..{target}",
    ])
    if naplo.returncode != 0:
        return None
    return erdemi_valtozasok((naplo.stdout or "").splitlines())


def tartalek_jegyzet(valtozasok: "Sequence[str] | None" = None) -> str:
    """A jegyzet, ha a CHANGELOG-ban nincs szakasz ehhez a verzióhoz.

    Három eset, és egyik sem keverhető össze a másikkal:

    * `None` — a tartalmat nem sikerült megállapítani. Ilyenkor SEMMIT nem
      állítunk róla.
    * üres — mértük, és tényleg nincs benne érdemi munka.
    * van benne — kimondjuk, hogy az emberi összefoglaló hiányzik, és
      felsoroljuk, mi van benne. Csonka, de igaz.
    """
    if valtozasok is None:
        return (
            "⚠️ Ehhez a kiadáshoz **nem készült emberi összefoglaló**, és a "
            "tartalmát sem sikerült megállapítani. Amíg ez pótlásra nem kerül, "
            f"a beolvadt munkák a commit-előzményben és a {_CHANGELOG_LINK}-ben "
            "nézhetők meg."
        )
    if not valtozasok:
        return (
            "Ez a kiadás csak verziólépést tartalmaz — a benne lévő munkák a "
            f"korábbi kiadásokban mentek ki. A részletes leírás a "
            f"{_CHANGELOG_LINK} megfelelő szakaszában áll."
        )
    sorok = "\n".join(f"- {v}" for v in valtozasok)
    return (
        "⚠️ Ehhez a kiadáshoz **nem készült emberi összefoglaló** — az alábbi "
        "lista a beolvadt munkák címéből áll, nem felhasználói leírás.\n\n"
        f"{sorok}\n\n"
        f"A részletes, embernek írt változásleírás a {_CHANGELOG_LINK}-be "
        "utólag kerül be."
    )


def atmeneti_hiba(eredmeny: subprocess.CompletedProcess[str]) -> bool:
    """Átmeneti (újrapróbálható) hibába futott-e a parancs?

    ⚠️ Nyilvános, mert a kiadás utókövetése (#1338) UGYANEZT a kérdést
    teszi fel: egy 503-as létezés-ellenőrzésből nem következik, hogy a
    kiadás hiányzik. Két külön mintalista előbb-utóbb elcsúszna."""
    szoveg = f"{eredmeny.stdout or ''}\n{eredmeny.stderr or ''}".lower()
    return any(minta in szoveg for minta in _ATMENETI_MINTAK)


def ensure_release(
    *,
    version: str,
    target: str,
    repo: str,
    runner: Runner = _valodi_gh,
    sleeper: Callable[[float], None] = time.sleep,
    attempts: int = _ALAP_KISERLET,
    check_only: bool = False,
    changelog: Path | None = None,
) -> int:
    """A `v<version>` kiadás megléte — pótlással vagy csak ellenőrzéssel.

    `0`-t ad, ha a kiadás létezik (vagy sikerült létrehozni), `1`-et, ha a
    kísérletek elfogytak. A bukás MINDIG `::error::`-ral jelez: néma `exit 1`
    a futáslistában nem tűnik fel.
    """
    tag = f"v{version}"

    for kiserlet in range(1, attempts + 1):
        letezik = runner(["gh", "release", "view", tag, "--repo", repo])
        if letezik.returncode == 0:
            print(f"A {tag} kiadás megvan — a Releases hasáb naprakész.")
            return 0

        if check_only:
            print(
                f"::error::A {tag} kiadás HIÁNYZIK, pedig a pyproject.toml már "
                f"ezt a verziót mutatja. A kiadó workflow vagy elbukott, vagy "
                f"el sem indult — nézd meg a Release workflow futásait."
            )
            return 1

        if atmeneti_hiba(letezik):
            # A `gh` nem különbözteti meg a „nincs ilyen"-t a „nem érhető
            # el"-től, ezért ilyenkor NEM hozunk létre semmit, csak újra
            # megkérdezzük a következő körben.
            print(f"A {tag} létezés-ellenőrzése átmeneti hibába futott — újra.")
        else:
            print(f"A {tag} kiadás hiányzik a main mögött — pótlás ({kiserlet}.)…")
            jegyzet = changelog_notes(version, changelog)
            parancs = [
                "gh", "release", "create", tag,
                "--repo", repo,
                "--target", target,
                "--title", f"PicasaPy {version}",
            ]
            # Embernek írt jegyzet a CHANGELOG-ból; ha nincs szakasz,
            # EMBERI tartalék megy ki — gépi lista SOHA (ld.
            # `tartalek_jegyzet`).
            parancs += [
                "--notes",
                jegyzet or tartalek_jegyzet(
                    valodi_valtozasok(target, version=version, runner=runner)
                ),
            ]
            keszult = runner(parancs)
            if keszult.returncode == 0:
                print(f"A {tag} kiadás létrejött.")
                return 0
            print(f"A létrehozás nem sikerült: {(keszult.stderr or '').strip()[:200]}")

        if kiserlet < attempts:
            sleeper(_VARAKOZAS_EGYSEG * kiserlet)

    print(
        f"::error::A {tag} kiadás {attempts} kísérlet után sem jött létre. "
        f"A Releases hasáb LEMARADT a main mögött — kézi pótlás kell."
    )
    return 1


def main(argv: list[str] | None = None) -> int:
    ertelmezo = argparse.ArgumentParser(description=__doc__)
    ertelmezo.add_argument("--repo", required=True, help="tulajdonos/repó")
    ertelmezo.add_argument("--target", default="", help="a kiadás commitja")
    ertelmezo.add_argument("--version", default=None, help="alapból a pyproject.toml-ból")
    ertelmezo.add_argument(
        "--check-only",
        action="store_true",
        help="csak ellenőriz (ütemezett őrfutás), nem hoz létre kiadást",
    )
    ertelmezo.add_argument("--attempts", type=int, default=_ALAP_KISERLET)
    args = ertelmezo.parse_args(argv)

    verzio = args.version or olvasott_verzio()
    if not args.check_only and not args.target:
        ertelmezo.error("a --target kötelező, ha nem csak ellenőrzünk")

    return ensure_release(
        version=verzio,
        target=args.target,
        repo=args.repo,
        attempts=args.attempts,
        check_only=args.check_only,
    )


if __name__ == "__main__":
    sys.exit(main())
