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
from collections.abc import Callable
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
    return subprocess.run(args, capture_output=True, text=True, check=False)


def olvasott_verzio(pyproject: Path | None = None) -> str:
    """A verzió a `pyproject.toml`-ból — a projekt EGYETLEN verzióhelye (#642)."""
    forras = pyproject or (_ROOT / "pyproject.toml")
    talalat = re.search(r'^version = "(.+?)"', forras.read_text(encoding="utf-8"), re.M)
    if talalat is None:
        raise ValueError(f"Nincs `version = \"…\"` sor a {forras} fájlban")
    return talalat.group(1)


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
    minta = re.compile(
        rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|\Z)",
        re.S | re.M,
    )
    talalat = minta.search(szoveg)
    if not talalat:
        return ""
    torzs = talalat.group(1).strip()
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
_TARTALEK_JEGYZET = (
    "Ez a kiadás nem hoz felhasználónak látszó változást.\n\n"
    "A benne lévő munka (tesztek, belső javítások, verziólépés) a "
    "korábbi kiadások bejegyzéseihez tartozik — a részletes, emberi "
    "leírás a [CHANGELOG.md]"
    "(https://github.com/sanchomuzax/PicasaPy/blob/main/CHANGELOG.md) "
    "megfelelő szakaszában áll."
)


def tartalek_jegyzet() -> str:
    """A jegyzet, ha a CHANGELOG-ban nincs szakasz ehhez a verzióhoz.

    ⚠️ Ez NEM a gépi lista helyettesítője „jobb híján", hanem szabály: a
    Releases hasáb a tulajdonos egyetlen látható verziókövetése, és
    gépzajt oda kiadni rosszabb, mint egy őszinte egymondatos jegyzet.
    """
    return _TARTALEK_JEGYZET


def _atmeneti(eredmeny: subprocess.CompletedProcess[str]) -> bool:
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

        if _atmeneti(letezik):
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
            parancs += ["--notes", jegyzet or tartalek_jegyzet()]
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
