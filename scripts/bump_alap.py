#!/usr/bin/env python3
"""Mióta gyűlik a kiadatlan munka? — a verzióemelés ALAPJA (#2488)

## Miért

A `release.yml` verzióemelő lépése eddig abból döntött, hogy **van-e már
kiadás a jelenlegi verzióhoz** (`gh release view v$verzio`). Ez a lekérdezés
UGYANANNAK a futásnak a KIADÓ lépése ELŐTT fut — vagyis a döntés a saját
futása későbbi mellékhatására támaszkodott.

Mért eset (2026-08-23): a #1289 beolvadásakor indult futás **tíz
másodperccel azelőtt** kérdezte meg, hogy ugyanaz a futás létrehozta volna a
`v0.8.58`-at. A válasz „még nincs" lett, a lépés „nincs mit emelni" döntéssel
továbbment, és a #1274 javítása kiadatlan maradt a main-en.

## A szabály

A kérdés valójában nem az, hogy létezik-e egy kiadás, hanem az, hogy
**gyűlt-e kiadatlan munka azóta, hogy a jelenlegi verziószámot beállítottuk.**
Ez a kérdés a git-előzményből, a futás mellékhatásaitól FÜGGETLENÜL
megválaszolható: meg kell keresni azt a commitot, amelyik a `pyproject.toml`
jelenlegi verzióját beállította. A `kiadas_szukseges.py` ezután ehhez a
ponthoz hasonlítja a fejet.

Ettől a döntés determinisztikussá válik: ugyanaz a fa mindig ugyanazt adja,
akkor is, ha a kiadás ebben a másodpercben születik meg.

## Miért az ELSŐ SZÜLŐ mentén

A beolvasztás `--squash` (a `main` védett), tehát a verziót beállító commit a
fővonalon áll. Ha mégis összefésülő commit érkezik, az első szülő útja azt is
a fővonal egyetlen lépésének látja — így a PR SAJÁT emelése nem számít
„azóta gyűlt munkának", és nem születik fölösleges második emelés.

## Melyik irányba tévedjünk?

A `kiadas_szukseges.py`-vel azonos elv: az ELMARADT kiadás a drágább hiba.
Ezért ha a keresés a vizsgált ablakon belül nem talál verzióváltást, a
legrégebbi megnézett commitot adjuk vissza — az ennél tágabb diff legfeljebb
egy fölösleges patch-kiadást okoz. Ha viszont a tájékozódás BUKIK (nem
olvasható a `pyproject.toml`), semmit nem adunk vissza: a munkafolyamat
ilyenkor a korábbi, kiadás-létére épülő útra esik vissza — így a hiba nem
válik VÉGTELEN emelési körré.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ensure_release import verzio_a_szovegbol  # noqa: E402

Runner = Callable[[list[str]], "subprocess.CompletedProcess[str]"]

#: Hány commitot nézünk vissza az első szülő mentén. A verziót beállító
#: commit a gyakorlatban a fej vagy a közvetlen szomszédja; a korlát csak azt
#: akadályozza meg, hogy egy elromlott előzmény ezer `git show`-t futtasson.
ABLAK = 200


def _valodi_futtato(args: list[str]) -> subprocess.CompletedProcess[str]:
    # #2077: `errors="replace"` — az idegen kódolású kimenet ne a DEKÓDOLÁSON
    # ölje meg a tájékozódást.
    return subprocess.run(
        args, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False
    )


def alap_a_verziokbol(commitok: Sequence[tuple[str, str | None]]) -> str | None:
    """Melyik commit állította be a fej verzióját?

    A `commitok` a fejtől visszafelé haladó `(sha, verzió)` párok — a verzió
    `None`, ha az adott commitban nem olvasható (pl. még nem létezett a
    `pyproject.toml`). Tiszta függvény: a git-lekérdezés máshol van, hogy a
    DÖNTÉSRE lehessen állítást írni.

    * üres lista vagy olvashatatlan FEJ → `None` (a tájékozódás bukása);
    * az első olyan commit, ahonnan visszafelé más verzió áll → az ő
      GYERMEKE a keresett pont;
    * ha az ablakon belül nincs verzióváltás → a legrégebbi megnézett commit.
    """
    if not commitok:
        return None
    fej_sha, fej_verzio = commitok[0]
    if fej_verzio is None:
        return None

    elozo = fej_sha
    for sha, verzio in commitok[1:]:
        if verzio != fej_verzio:
            return elozo
        elozo = sha
    return elozo


def _verzio(sha: str, *, futtato: Runner) -> str | None:
    eredmeny = futtato(["git", "show", f"{sha}:pyproject.toml"])
    if eredmeny.returncode != 0:
        return None
    try:
        return verzio_a_szovegbol(eredmeny.stdout or "", forras=f"a {sha} pyproject.toml-ja")
    except ValueError:
        return None


def elso_szulok(head: str, *, ablak: int = ABLAK, futtato: Runner) -> tuple[str, ...]:
    """A fejtől visszafelé az ELSŐ SZÜLŐ útján haladó commitok."""
    eredmeny = futtato(
        ["git", "log", "--first-parent", "--format=%H", f"-n{ablak}", head]
    )
    if eredmeny.returncode != 0:
        return ()
    return tuple(sor.strip() for sor in (eredmeny.stdout or "").splitlines() if sor.strip())


def alap_commit(head: str = "HEAD", *, futtato: Runner = _valodi_futtato) -> str | None:
    """A jelenlegi verziót beállító commit; `None`, ha nem állapítható meg."""
    shak = elso_szulok(head, futtato=futtato)
    if not shak:
        return None
    return alap_a_verziokbol(tuple((sha, _verzio(sha, futtato=futtato)) for sha in shak))


def main(argv: Sequence[str] | None = None, *, futtato: Runner = _valodi_futtato) -> int:
    ertelmezo = argparse.ArgumentParser(
        description="Melyik commit állította be a jelenlegi verziót?"
    )
    ertelmezo.add_argument("--head", default="HEAD", help="a vizsgált fej")
    beallitas = ertelmezo.parse_args(list(argv) if argv is not None else None)

    alap = alap_commit(beallitas.head, futtato=futtato)
    if alap is None:
        # ⚠️ A STDOUT marad üres — a munkafolyamat ebből tudja, hogy vissza
        # kell esnie a korábbi útra (ld. a modul fejlécét).
        print(
            "Nem állapítható meg, melyik commit állította be a jelenlegi verziót.",
            file=sys.stderr,
        )
        return 1
    print(alap)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
