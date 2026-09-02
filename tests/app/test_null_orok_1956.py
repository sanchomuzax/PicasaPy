"""A kontextus-vezérlők őrei a `null`-t is fogják (#1956).

## A hiba, amit ez az őr kizár

A QML-ben a kontextus-objektum (`folderHierarchyController`,
`webExportController`, …) az engine felépítése és leépítése közben
**`null`** lehet — nem `undefined`. A JavaScriptben viszont

    typeof null === "object"

tehát a `typeof x !== "undefined"` vizsgálat a `null`-ra **IGAZ**. Ha
utána a nevet tulajdonságként olvassuk (`x.valami`), a kiértékelés
`TypeError`-ral megszakad.

## Miért nem elméleti — MÉRVE

A `main`-en minden QML-funkcionális futás tele volt ezzel:

```
Main.qml:1170: TypeError: Cannot read property 'treeView' of null
```

Két valódi kára van:

1. **Egy VALÓDI új hiba elveszik benne.** A #1939 körében percekig kellett
   ellenőrizni, hogy nem az új kód okozza-e — és épp abban a körben derült
   ki, hogy ugyanez a hibaosztály (`undefined` egy `Connections`
   `target`-jén) a CI ubuntu-lábát is elbuktatta.
2. **A megszakadt kötés a RÉGI értéken ragad**, tehát a menü pipája és a
   nézetváltó gomb elcsúszhat a vezérlő valódi állapotától.

## KÉT őr kell — ezt a javítás közben mérve tanultuk meg

Először a `typeof`-ot puszta igazságérték-vizsgálatra cseréltük
(`x ? x.valami : alap`). **Ez rosszabb lett:** ha a kontextus-objektum
egyáltalán nincs regisztrálva — például egy szűkített teszt-összeállításban
—, a puszta névre hivatkozás **`ReferenceError`-t** dob. A
`test_qml_hidden` életciklus-őre azonnal el is bukott rajta:

```
Main.qml:1173: ReferenceError: folderHierarchyController is not defined
```

A két őr tehát KÉT KÜLÖNBÖZŐ hiba ellen véd, és egyik sem váltja ki a
másikat:

| őr | mi ellen | mi történik nélküle |
|---|---|---|
| `typeof x !== "undefined"` | a NÉV nincs regisztrálva | `ReferenceError` |
| `&& x` | a név megvan, de az ÉRTÉKE `null` | `TypeError` |

## Mit fogad el az őr

* `typeof x !== "undefined" && x` — **ez a helyes alak**, mindkettőt fogja
* `typeof x !== "undefined" ? x : null` — a `null`-t továbbadja, nem olvas rajta

Amit NEM: a puszta `typeof`-vizsgálatot, ha utána a néven tulajdonságot
vagy metódust olvasunk.
"""
from __future__ import annotations

import re
from pathlib import Path

import picasapy.app

QML_GYOKER = Path(picasapy.app.__file__).parent / "qml"

#: az őr maga — a `typeof <név> !== "undefined"` alak
_OR = re.compile(r'typeof\s+(\w+)\s*!==\s*"undefined"')

#: hány sorral tovább nézzük, mi történik a névvel (a kötések tördeltek)
_ABLAK = 4


def _null_fogo(nev: str, utana: str) -> bool:
    """Kizárja-e a `null`-t is a vizsgálat?"""
    return bool(
        re.search(rf"&&\s*{nev}\b(?!\s*\.)|\?\s*{nev}\s*:|{nev}\s*\?", utana)
    )


def veszelyes_orok() -> list[tuple[str, int, str]]:
    """(fájl, sor, név) minden `null`-ra vak őrhöz, ami tagot is olvas."""
    talalt: list[tuple[str, int, str]] = []
    for f in sorted(QML_GYOKER.rglob("*.qml")):
        sorok = f.read_text(encoding="utf-8").splitlines()
        for i, sor in enumerate(sorok):
            for m in _OR.finditer(sor):
                nev = m.group(1)
                ablak = " ".join(sorok[i : i + _ABLAK])
                utana = ablak[ablak.find(m.group(0)) + len(m.group(0)) :]
                olvas_tagot = re.search(rf"\b{nev}\.\w+", utana)
                if olvas_tagot and not _null_fogo(nev, utana):
                    talalt.append((
                        str(f.relative_to(QML_GYOKER)), i + 1, nev,
                    ))
    return talalt


class TestNincsNullraVakOr:
    def test_egyetlen_typeof_or_sem_vak_a_nullra(self):
        talalt = veszelyes_orok()
        assert talalt == [], (
            "A `typeof` őr a `null`-t NEM fogja (typeof null === 'object'), "
            "és utána tagot olvasunk a néven — ez futásidejű TypeError, "
            "ami a kötést megszakítja:\n"
            + "\n".join(f"  {f}:{sor}  ({nev})" for f, sor, nev in talalt)
            + "\n\nA helyes alak MINDKÉT őrt tartalmazza:\n"
            "    typeof x !== 'undefined' && x  ?  x.valami : alap\n"
            "A `typeof` a NEM REGISZTRÁLT név ellen véd (ReferenceError), "
            "a `&& x` a `null` ÉRTÉK ellen (TypeError). Csak az egyiket "
            "használni MINDKÉT irányban hibás — ezt mérve tanultuk meg."
        )

    def test_az_or_maga_MUKODIK(self):
        """Beültetett hibával: az őrnek FOGA van.

        Enélkül a fenti üres lista azt is jelenthetné, hogy a minta soha
        nem illeszkedik — például mert elgépeltük a reguláris kifejezést.
        """
        nev = "proba"
        vak = 'typeof proba !== "undefined" ? proba.ertek : 0'
        utana = vak[vak.find('"undefined"') + len('"undefined"') :]
        assert not _null_fogo(nev, utana), "az őr nem ismerte fel a vak alakot"

        biztonsagos = 'typeof proba !== "undefined" && proba ? proba.ertek : 0'
        utana2 = biztonsagos[
            biztonsagos.find('"undefined"') + len('"undefined"') :
        ]
        assert _null_fogo(nev, utana2), (
            "az őr a BIZTONSÁGOS alakot is hibásnak jelezné"
        )
