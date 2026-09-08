"""A `.picasa.ini` `originhash` kulcsa — a KÉT származás-kulcs szöveges párja.

Megfejtve és valós fájlokon lemérve (2026-09-08, #2675 → #2733); a teljes
bizonyítéklánc: `docs/specs/picasa-tartalomkulcs.md`, „⭐⭐ MEGVAN: az
`originhash` = `originfast` ‖ `originslow`".

```
originhash = hex16(originfast) ‖ hex16(originslow)
```

Mindkét fél a saját MD5-jének első 8 bájtja, 64 bites számként,
`%016I64x` alakban kiírva — vagyis **kisbetűs, nulla-feltöltött 16 hexa
jegy**, és a jegyek sorrendje a digest bájtsorrendjéhez képest MEGFORDUL
(a digestből kis-endiánként vett szám nagy-endián alakban íródik ki).

- `originfast` — fej+farok kulcs, `dedup.fastkey.picasa_fast_key` (#1481);
- `originslow` — a teljes fájl MD5-je, `dedup.slowkey.picasa_slow_key` (#1482).

**Mérés (a valós ini-korpusz és a lemezen lévő fájlok összevetése):** a
tulajdonos saját mappáiban **55/60 = 91,7 %** teljes, 32 jegyes egyezés. A
`Downloaded Albums` alól 3/20 — ott a lemezen a letöltött példány van, nem
az, amit a Picasa hashelt. Minden eltérés MINDKÉT félen bukik, soha nem
csak az egyiken: a fájl változott meg, nem a képlet.

Bináris oldal: a formázást a `FUN_0045c870` végzi (`0x0045cbef` és
`0x0045cc11` `push 0x00c80ce4` = `'%016I64x'`, hozzáfűzés `0x0040ea90`), a
szétszedést a `FUN_00414b40` (`cmp eax, 0x20` — pontosan 32 karaktert vár,
majd `sscanf(..., "%I64x")` mindkét félre).

⛔ **Ez a modul KISZÁMOL, de nem ír.** Az `edit/save.py` ma egy saját alakú
(SHA-256, 64 karakteres) értéket ír, ami az eredetiben SOHA nem fordul elő;
a cserét viszont egy MÉG NYITOTT kérdés blokkolja: **melyik fájl bájtjait**
rögzíti az `originhash` a mentés pillanatában (a most kiírt szerkesztett
képét vagy a szerkesztés előtti eredetiét). A 60-as mintában 44 sor nem
egyezett a MAI fájllal, és ezt sem az mtime, sem szerkesztési kulcs
jelenléte nem magyarázta. Amíg ez nincs eldöntve, rossz választással
bizonyítottan hibás értéket írnánk — ld. `edit/save.py` „`originhash`"
szakasza és a #2675.
"""

from __future__ import annotations

from pathlib import Path

from picasapy.dedup.fastkey import picasa_fast_key
from picasapy.dedup.slowkey import picasa_slow_key

#: A tárolt érték hossza — a bináris szétszedője pontosan ennyit vár
#: (`FUN_00414b40`, `cmp eax, 0x20`). A korpusz 1787 sora közül mind ennyi.
ORIGINHASH_HOSSZ = 32

#: Egy fél hossza hexa jegyekben (`%016I64x`).
FEL_HOSSZ = ORIGINHASH_HOSSZ // 2

_HEXA_JEGYEK = frozenset("0123456789abcdef")


def originhash_szoveg(gyors_kulcs: int, lassu_kulcs: int) -> str:
    """A két 64 bites kulcs `originhash`-alakja (32 kisbetűs hexa jegy).

    A `%016I64x` nulla-feltöltése nem díszítés: a szétszedő fix pozíción
    vágja a szöveget, tehát rövidebb fél elcsúsztatná a másikat."""
    return "%016x%016x" % (gyors_kulcs & 0xFFFFFFFFFFFFFFFF, lassu_kulcs & 0xFFFFFFFFFFFFFFFF)


def originhash_szetszed(szoveg: str) -> tuple[int, int] | None:
    """Egy tárolt `originhash` visszaolvasása a két kulcsra.

    `None`, ha az érték nem a mért alak: nem pontosan 32 jegy, vagy nem
    kisbetűs hexa. **Szándékosan nem találgatunk** — a korpusz 1787 sora
    közül egy sem nagybetűs, és egy idegen alakú értékből képzett kulcspár
    néma hibát vinne a másodpéldány-keresésbe."""
    if len(szoveg) != ORIGINHASH_HOSSZ:
        return None
    if not all(jegy in _HEXA_JEGYEK for jegy in szoveg):
        return None
    return (int(szoveg[:FEL_HOSSZ], 16), int(szoveg[FEL_HOSSZ:], 16))


def origin_hash(path: Path) -> str | None:
    """Egy fájl `originhash`-e a Picasa képlete szerint, vagy `None`.

    `None`, ha a fájl üres vagy nem olvasható — ugyanazokban az esetekben,
    amikor a két kulcs sem áll elő. A fájlt kétszer olvassuk végig (a gyors
    kulcs csak ~33 KB-ot, a lassú a teljes tartalmat)."""
    gyors = picasa_fast_key(path)
    if gyors is None:
        return None
    lassu = picasa_slow_key(path)
    if lassu is None:
        return None
    return originhash_szoveg(gyors, lassu)
