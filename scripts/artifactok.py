#!/usr/bin/env python3
"""Az ÖSSZES élő artifact újraszámolása egy paranccsal.

A tulajdonos kérdezett rá (2026-08-27): *„Van már beépített scripted, ami
kényszeríti a bináris artifactok frissítését?"* — nem volt, ez az.

Két lapunk él, és mindkettő MÉRT adatból készül, nem kézzel írva:

* **állapotlap** (`allapotlap.py`) — hol tart a projekt: jegyek, menü-lefedettség
* **bináris térkép** (`binaris_terkep.py`) — mennyit fejtettünk vissza, és hol

    python3 scripts/artifactok.py

Kiírja mindkét lap fájlját ÉS a hozzá tartozó címet. Publikálni ezután kell:
`Artifact` hívás, `file_path` = a generált fájl, **`url` = a kiírt cím**.
Az `url` nélküli publikálás ÚJ lapot hoz létre, és a felhasználó régi linkje
elavul.

Kilépési kód: 0 = mind lefutott · 3 = valamelyik kihagyva (hiányzó forrás,
pl. a privát repóban élő bináris index) · 1 = hiba.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

LAPOK = [
    ("állapotlap", "allapotlap.py", REPO / "docs" / "allapotlap.html",
     "https://claude.ai/code/artifact/4deaf3dd-41c3-4da2-85ec-5fd14a98601e"),
    ("bináris térkép", "binaris_terkep.py", REPO / "docs" / "binaris-terkep.html",
     "https://claude.ai/code/artifact/3e4aac90-5195-45c3-ba94-661d26824f94"),
]


def main() -> int:
    kihagyva, hibas = [], []
    print("=" * 66)
    for nev, szkript, ki, _url in LAPOK:
        print(f"\n▶  {nev}  ({szkript})")
        futas = subprocess.run(
            [sys.executable, str(REPO / "scripts" / szkript), "--ki", str(ki)],
            capture_output=True, text=True,
        )
        print(futas.stdout.rstrip() or futas.stderr.rstrip())
        if futas.returncode == 3:
            kihagyva.append(nev)
        elif futas.returncode != 0:
            hibas.append(nev)

    print("\n" + "=" * 66)
    if hibas:
        print(f"❌ HIBA: {', '.join(hibas)}")
        return 1
    if kihagyva:
        print(f"⚠️  Kihagyva (hiányzó forrás): {', '.join(kihagyva)}")
        print("   A bináris index a PRIVÁT agent-repóban él.")
        return 3
    print("✅ Mindkét lap újraszámolva.")
    print("   Publikáld ŐKET a fent kiírt címekre — url NÉLKÜL új lap jön létre!")
    print()
    print("📬 ÉS KÉRD LE A KOMMENTEKET IS — automatikus értesítés NINCS.")
    print("   Ez az EGYETLEN pillanat, amikor ez rendszeresen megtörténik:")
    for nev, _sz, _ki, url in LAPOK:
        print(f"     Artifact(action=\"comments\", url=\"{url}\")   # {nev}")
    print("   Ha a válasz »comments are not available«, a lap nincs megosztva —")
    print("   ez nem hiba, csak nincs hol kommentelni.")
    print("   Válaszolni CSAK olyan szálba lehet, ahol valaki @claude-ot említett.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
