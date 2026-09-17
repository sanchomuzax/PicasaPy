#!/usr/bin/env python3
"""A forrás-szintű kapuk KÖZÖS része (agent#93, agent#94).

Két hibaosztály élt szétszórva a kapukban, és mindkettő **mérten** harapott.
Ezért egy helyen:

## 1. A burkoló-nevek (`BURKOLOK`, `GH`) — agent#93

A projekt szabálya szerint GitHub-műveletet **kizárólag** a saját
bot-burkolóival adunk ki (`gh-bot`, `codex-bot`, `opencode-bot`,
`hermes-bot`) — minden eszköz külön GitHub Appot kap, hogy látszódjon,
melyik mit alkotott. Aki viszont a kaput a csupasz `gh` névre írja, az épp
azt az egy alakot fogja meg, amit tilos használni, és átengedi mindet, amit
tényleg használunk.

Ez a projektben **négyszer** fordult elő: `jegycim_or.py` (#72),
`push_azonossag_kapu.py` (#84), `csupasz_push_or.py` (#87), és a
`release_kapu.py` (agent#93) — ez utóbbi a kiadás-létrehozásra nézve
gyakorlatilag nem létezett. Ezért a lista ITT él, és a kapuk innen veszik.

## 2. A heredoc törzse nem parancs (`adat_nelkul`) — agent#94

A kapuk a Bash-parancs teljes SZÖVEGÉT pásztázzák, és a parancspozíció
újsor után is kezdődhet. Egy `cat > fájl <<'EOF' … EOF` heredoc törzse
viszont **adat**, nem parancs — így a kapu megtiltotta, hogy a saját
szabályát dokumentáljuk, mert a dokumentációban ott áll a tiltott példa.
Egyetlen körön belül négyszer állított meg (agent#94 táblázata).

⚠️ **A törzset csak ADAT-parancsnál hagyjuk ki.** A `bash <<EOF` és a
`python3 - <<PY` alak a törzsét VÉGREHAJTJA, tehát ott a törzs igenis
parancs; ha azt is kihagynánk, a heredoc kapumegkerülő alak lenne. Ezért a
lista **zárt**: `cat` és `tee`. Ami nem ezekkel nyílik, ott minden marad,
ahogy volt.

## Amit ez a modul NEM tud (mérve)

Egy értelmezőnek adott heredoc, amely a törzséből shellel ki
(`python3 - <<PY` + `os.system(...)`), a kapuknak **eddig sem** volt
látható: a program neve nem parancspozícióban áll, hanem egy függvényhívás
paramétereként. Ezt a modul nem javítja, és nem is rontja — kimondva áll
itt, hogy a következő kör ne higgye lefedettnek.
"""

from __future__ import annotations

import os
import re

#: A saját bot-burkolóink. Új eszköz ide kerül — és onnantól MINDEN kapu
#: ismeri, nem csak az, amelyikbe épp beírták.
BURKOLOK = ("gh-bot", "codex-bot", "opencode-bot", "hermes-bot")

#: A GitHub-eszköz minden írásmódja: csupasz `gh`, a burkolók, és bármelyik
#: útvonallal (`./eszkozok/gh-bot`, `~/picasapy-agent/eszkozok/gh-bot`).
GH = (r"(?:[\w.~-]*(?:/[\w.~-]+)*/)?(?:gh|"
      + "|".join(re.escape(b) for b in BURKOLOK) + r")")

#: Parancspozíció: sor eleje vagy shell-elválasztó után, esetleges
#: környezeti-változó előtaggal.
POZICIO = r"(?:^|[;&|]\s*|\n\s*|\$\(\s*|`\s*)(?:\w+=\S*\s+)*"

#: Azok a parancsok, amelyeknél a heredoc törzse ADAT: fájlba írjuk, nem
#: futtatjuk. Szándékosan zárt lista — lásd a modul fejét.
ADAT_PARANCSOK = ("cat", "tee")

#: Heredoc-megnyitó: `<<EOF`, `<<-EOF`, `<<'EOF'`, `<<"EOF"`. A here-STRING
#: (`<<<`) nem illeszkedik, mert a harmadik `<` se a `-?\s*`-ra, se a
#: határoló-alakokra nem jó.
_HEREDOC = re.compile(r"<<-?\s*(?:'([^']*)'|\"([^\"]*)\"|([\w.-]+))")


def _sor_parancsa(sor: str) -> str:
    """A sor UTOLSÓ szakaszának programneve (`cd x && cat > f` → `cat`)."""
    szakasz = re.split(r"[;&|]", sor)[-1]
    for token in szakasz.split():
        if token.startswith("-"):
            continue
        if "=" in token and "/" not in token.split("=", 1)[0]:
            continue  # `KULCS=ertek` előtag
        return os.path.basename(token)
    return ""


def adat_nelkul(cmd: str) -> str:
    """A parancs úgy, hogy az ADAT-heredocok törzse üres sorokra cserélve.

    A sorok SZÁMA nem változik, tehát az útvonal- és sor-alapú leletek
    érvényben maradnak. A megnyitó sor megmarad — az valódi parancs.
    """
    sorok = cmd.split("\n")
    ki: list[str] = []
    i = 0
    while i < len(sorok):
        sor = sorok[i]
        ki.append(sor)
        i += 1
        talalatok = _HEREDOC.findall(sor)
        if not talalatok:
            continue
        adat = _sor_parancsa(sor) in ADAT_PARANCSOK
        for idezett_a, idezett_b, csupasz in talalatok:
            hatarolo = idezett_a or idezett_b or csupasz
            while i < len(sorok) and sorok[i].strip() != hatarolo:
                ki.append("" if adat else sorok[i])
                i += 1
            if i < len(sorok):
                ki.append(sorok[i])  # a záró határoló sora
                i += 1
    return "\n".join(ki)
