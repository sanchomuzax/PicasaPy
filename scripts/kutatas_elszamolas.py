#!/usr/bin/env python3
"""Kutatói elszámolás — egyetlen paranccsal, kézi összeszámolás nélkül.

A `picasapy-research` skill minden kör végén elszámoló sort kér:

    Nyitott kérdések: N nyílt · M lezárva · K blokkolt · L hatókörön kívül · 0 csak-nyitva

Eddig ezt kézzel kellett összeszedni — jegyeket olvasva, címkéket
számolva. Ez a szkript **egy futással** kiadja, és mellé a döntéshez
kellő képet is: mi vár a tulajdonosra, mi blokkolt, mit lehet MOST
elővenni, és hol vannak még nyitott kérdések a specekben.

Használat:

    python3 scripts/kutatas_elszamolas.py            # emberi olvasásra
    python3 scripts/kutatas_elszamolas.py --json     # gépi feldolgozásra

Csak OLVAS: `gh issue list` + a repó fájljai. Semmit nem módosít, ezért
korlátlanul ismételhető (7. rögzített döntés).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
INDEX = REPO / "docs" / "specs" / "00-index.md"
#: A privát agent-repó munkasora. Hiányozhat (pl. friss klón, CI) — akkor
#: a szkript ezt a szakaszt kihagyja, nem hibázik.
MUNKASOR = Path.home() / "picasapy-agent" / "memory" / "nyitott-kerdesek-sor.md"

PRIO = ("P0", "P1", "P2", "P3", "P4")


def _gh_issues() -> list[dict]:
    """A nyitott jegyek a `gh` CLI-ből. Hiba esetén üres lista + üzenet."""
    try:
        raw = subprocess.run(
            ["gh", "issue", "list", "--state", "open", "--limit", "500",
             "--json", "number,title,labels,createdAt,updatedAt,comments"],
            cwd=REPO, capture_output=True, text=True, timeout=90, check=True,
        ).stdout
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError) as exc:
        print(f"⚠️  A jegyek nem kérdezhetők le ({exc.__class__.__name__}) — "
              f"a jegy-szakasz kimarad.", file=sys.stderr)
        return []
    return [
        {"number": i["number"], "title": i["title"],
         "labels": {label["name"] for label in i["labels"]},
         "created": i.get("createdAt", "")[:10],
         "updated": i.get("updatedAt", "")[:10],
         "comments": len(i.get("comments") or [])}
        for i in json.loads(raw)
    ]


def _spec_nyitott_kerdesek() -> list[tuple[str, str]]:
    """A `00-index.md` KÉZZEL karbantartott nyitott-kérdés listája.

    A lap fejlécei `### [lap.md](lap.md) — N kérdés` alakúak; a „nincs
    nyitott kérdés" szövegűeket kihagyjuk. A szám a fejlécből jön, nem
    szóelőfordulásból — az index maga figyelmeztet rá, hogy a `Nyitva`
    szavak kétharmada hivatkozás.
    """
    if not INDEX.exists():
        return []
    fej = re.compile(r"^### \[([^\]]+)\]\([^)]+\)\s*—\s*(.+)$", re.M)
    ki: list[tuple[str, str]] = []
    for lap, allapot in fej.findall(INDEX.read_text(encoding="utf-8")):
        # „nincs nyitott kérdés", de „nincs nyitott BINÁRIS kérdés" is —
        # ezért nem szó szerinti egyezést nézünk.
        if re.search(r"nincs nyitott .*kérdés", allapot, re.I):
            continue
        ki.append((lap, allapot.strip()))
    return ki


def _munkasor() -> dict[str, int] | None:
    if not MUNKASOR.exists():
        return None
    szoveg = MUNKASOR.read_text(encoding="utf-8")
    return {
        "nyilt": len(re.findall(r"^- \[ \]", szoveg, re.M)),
        "lezarva": len(re.findall(r"^- \[x\]", szoveg, re.M)),
        "blokkolt": len(re.findall(r"^- \[B\]", szoveg, re.M)),
        "hatokoron_kivul": len(re.findall(r"^- \[-\]", szoveg, re.M)),
    }


def _osszesit(jegyek: list[dict]) -> dict:
    var_rank = [i for i in jegyek if "felhasználóra-vár" in i["labels"]]
    blokkolt = [i for i in jegyek if "blocked" in i["labels"]]
    keszen = [i for i in jegyek
              if "ready" in i["labels"] and "blocked" not in i["labels"]
              and "felhasználóra-vár" not in i["labels"]]
    kovetkezo = [i for i in keszen if "next-up" in i["labels"]]
    prio = Counter()
    for i in jegyek:
        for p in PRIO:
            if p in i["labels"]:
                prio[p] += 1
                break
    return {
        "osszes_nyitott": len(jegyek),
        "felhasznalora_var": var_rank,
        "blokkolt": blokkolt,
        "elovehetp": keszen,
        "next_up": kovetkezo,
        "prioritas": dict(sorted(prio.items())),
    }


def _sor(jegy: dict) -> str:
    cimkek = ",".join(sorted(jegy["labels"]))
    return f"  #{jegy['number']:<5} [{cimkek}]\n        {jegy['title'][:96]}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="gépi kimenet")
    args = ap.parse_args()

    jegyek = _gh_issues()
    ossz = _osszesit(jegyek)
    spec = _spec_nyitott_kerdesek()
    sor = _munkasor()

    if args.json:
        print(json.dumps({
            "jegyek": {k: (v if not isinstance(v, list)
                           else [i["number"] for i in v])
                       for k, v in ossz.items()},
            "spec_nyitott_kerdesek": spec,
            "munkasor": sor,
        }, ensure_ascii=False, indent=2))
        return 0

    print("=" * 72)
    print("KUTATÓI ELSZÁMOLÁS")
    print("=" * 72)

    print(f"\nNyitott jegy összesen: {ossz['osszes_nyitott']}")
    if ossz["prioritas"]:
        print("  prioritás szerint: " +
              " · ".join(f"{p} {n}" for p, n in ossz["prioritas"].items()))

    print(f"\n⛔ FELHASZNÁLÓRA VÁR ({len(ossz['felhasznalora_var'])}) — "
          f"ezeken nem tudunk dolgozni:")
    for i in ossz["felhasznalora_var"] or []:
        print(_sor(i))
    if not ossz["felhasznalora_var"]:
        print("  — egy sincs ✅")

    print(f"\n🚧 BLOKKOLT ({len(ossz['blokkolt'])}):")
    for i in ossz["blokkolt"] or []:
        print(_sor(i))
    if not ossz["blokkolt"]:
        print("  — egy sincs ✅")

    print(f"\n⭐ SORON KÖVETKEZŐ (ready + next-up, {len(ossz['next_up'])}):")
    for i in ossz["next_up"][:12]:
        print(_sor(i))

    print(f"\n✅ ELŐVEHETŐ MOST (ready, nem blokkolt): {len(ossz['elovehetp'])} jegy")

    # A listás jegyek elrohadnak: 2026-08-26-i mérés szerint a 175 nyitott
    # jegyből 87 (49 %) óta senki hozzá sem nyúlt. Ez a szakasz azért van,
    # hogy a rothadás LÁTSZÓDJON — enélkül csendben nő.
    erintetlen = [i for i in jegyek
                  if i.get("created") and i["created"] == i.get("updated")
                  and i.get("comments", 0) <= 1]
    arany = (100 * len(erintetlen) // len(jegyek)) if jegyek else 0
    print(f"\n🕸️  ÉRINTETLEN a nyitás óta: {len(erintetlen)}/{len(jegyek)} ({arany} %)")
    for i in sorted(erintetlen, key=lambda x: x["created"])[:8]:
        print(f"  #{i['number']:<5} {i['created']}  {i['title'][:64]}")
    if len(erintetlen) > 8:
        print(f"  … és még {len(erintetlen) - 8}")

    print(f"\n📄 SPEC-LAPOK NYITOTT KÉRDÉSSEL ({len(spec)}):")
    for lap, allapot in spec:
        print(f"  {lap:44s} {allapot[:60]}")
    if not spec:
        print("  — egy sincs ✅")

    if sor is not None:
        print(f"\n📋 PRIVÁT MUNKASOR: {sor['nyilt']} nyílt · {sor['lezarva']} lezárva · "
              f"{sor['blokkolt']} blokkolt · {sor['hatokoron_kivul']} hatókörön kívül")
    else:
        print("\n📋 PRIVÁT MUNKASOR: nincs meg (a privát repó nincs klónozva)")

    csak_nyitva = sor["nyilt"] if sor else 0
    print("\n" + "-" * 72)
    print(f"Nyitott kérdések: {csak_nyitva} nyílt · —  lezárva · "
          f"{len(ossz['blokkolt'])} blokkolt · — hatókörön kívül · "
          f"{csak_nyitva} csak-nyitva")
    print("-" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
