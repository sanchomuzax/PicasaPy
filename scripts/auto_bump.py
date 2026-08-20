#!/usr/bin/env python3
"""Verzióemelés a MERGE-kor, hogy egy javítás EGY CI-kört vigyen (#1127).

## Miért

Eddig minden javítás **két** teljes CI-kört fogyasztott: egyet a jegy
PR-jén, egyet a külön verzióemelő PR-en. A tulajdonos szava:

    „Tilos 2-3 órás teszt köröket futni!"

A négygépes felosztás (#1127 1. lépése) a kört 29 percről ~9-re vitte; ez a
lépés a MÁSODIK kört szünteti meg.

## Hogyan

A `main`-re érkező push után: ha a `pyproject.toml` verziójához MÁR van
kiadás, akkor a javítás kiadatlan — emeljük a patch-számot, és a
CHANGELOG „Nem kiadott" szakaszát nevezzük át az új verzióra.

⚠️ **A rekurzió korlátos, nem véletlen:** az emelés utáni push újra
elindítja a workflow-t, de akkor az ÚJ verzióhoz még nincs kiadás, tehát
nem emel többet — pontosan két körben megáll.

⚠️ **A CHANGELOG szövegét EMBER írja**, a jegy PR-jében, a „Nem kiadott"
szakasz alá. Ez a szkript csak a CÍMET cseréli: a felhasználónak szóló
mondatokat nem lehet gépiesíteni, és nem is szabad — azokból tudja meg,
mi változott.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_GYOKER = Path(__file__).resolve().parents[1]

#: A CHANGELOG-ban a még ki nem adott szakasz címe.
KIADATLAN_CIM = "## [Nem kiadott]"

_VERZIO_SOR = re.compile(r'^(version\s*=\s*")([^"]+)(")', re.MULTILINE)


def kovetkezo_verzio(verzio: str) -> str:
    """A patch-szám eggyel emelve: `0.8.28` → `0.8.29`.

    Csak a patch-et emeljük: a minor/major emelés SZÁNDÉK kérdése, nem
    automatizálható — azt továbbra is kézzel kell megtenni."""
    darabok = verzio.strip().split(".")
    if len(darabok) != 3 or not all(d.isdigit() for d in darabok):
        raise ValueError(f"Nem SemVer-alakú verzió: {verzio!r}")
    darabok[2] = str(int(darabok[2]) + 1)
    return ".".join(darabok)


def emeld_a_pyprojectet(ut: Path) -> tuple[str, str]:
    """A `version = "..."` sor emelése; a (régi, új) párost adja vissza."""
    szoveg = ut.read_text(encoding="utf-8")
    talalat = _VERZIO_SOR.search(szoveg)
    if talalat is None:
        raise ValueError(f"Nincs `version = \"...\"` sor: {ut}")
    regi = talalat.group(2)
    uj = kovetkezo_verzio(regi)
    ut.write_text(
        szoveg[: talalat.start(2)] + uj + szoveg[talalat.end(2) :],
        encoding="utf-8",
    )
    return regi, uj


def zard_le_a_changelogot(ut: Path, verzio: str, datum: str) -> bool:
    """A „Nem kiadott" cím átnevezése `## [verzió] – dátum` alakra.

    `False`, ha nincs ilyen szakasz — az nem hiba: egy tisztán belső
    változáshoz nem muszáj felhasználói mondatot írni."""
    if not ut.exists():
        return False
    szoveg = ut.read_text(encoding="utf-8")
    if KIADATLAN_CIM not in szoveg:
        return False
    ut.write_text(
        szoveg.replace(KIADATLAN_CIM, f"## [{verzio}] – {datum}", 1),
        encoding="utf-8",
    )
    return True


def main(argv: list[str] | None = None) -> int:
    elemzo = argparse.ArgumentParser(description=__doc__)
    elemzo.add_argument("--datum", required=True, help="ISO dátum a CHANGELOG-hoz")
    elemzo.add_argument("--gyoker", type=Path, default=_GYOKER)
    args = elemzo.parse_args(argv)

    regi, uj = emeld_a_pyprojectet(args.gyoker / "pyproject.toml")
    volt_szakasz = zard_le_a_changelogot(
        args.gyoker / "CHANGELOG.md", uj, args.datum
    )
    print(f"verzio={uj}")
    print(f"regi={regi}")
    print(f"changelog={'igen' if volt_szakasz else 'nem'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
