"""#1581 — parancsazonosító-térkép. Horgony: a rekord KEZDŐCÍME (a #1409 lelete).

A fordító a menürekord `+0x04`…`+0x10` mezőit a KÖVETKEZŐ rekord feliratának
betöltése UTÁN írja ki, ezért a `push "<kulcs>"` és a rá következő
`mov word ptr [...+0x0a]` NEM tartozik össze. Kétszer ezen bukott meg a gépi
kinyerés; ez a harmadik, javított horgonnyal.

## Miért nem lineáris diszasszemblálás

A `.text` adatszigeteket tartalmaz, amitől a dekódolás elcsúszik (a
környéken `call 0xb8567ea4`-féle képtelenségek jönnek ki). Ehelyett a
menüépítő EGYETLEN, gépiesen ismételt sablonjának BÁJTMINTÁJÁT keressük:

    68 <kulcs>        push  "<Osztály::ID_NEV>"
    B8 <imm32>        mov   eax, <leíró>
    [csak tárolások]  a MEGELŐZŐ rekord +0x04..+0x10 mezői
    E8 <rel32>        call  <betöltő>
    8B 00             mov   eax, [eax]
    83 C4 04          add   esp, 4
    3B C3             cmp   eax, ebx
    74 0A             je    +0x0a
    83 C0 04          add   eax, 4
    A3 <REK>          mov   dword ptr [REK], eax   <- a rekord kezdőcíme

## A szigor SZÁNDÉKOS

A `push`-t csak akkor fogadjuk el, ha a `call`-ig VEZETŐ ÚT kizárólag
tárolásokból áll — vagyis a sablon hiánytalanul kirajzolódik. Ahol nem, ott
a sor ÜRESEN marad. Egy tág „keress visszafelé a legközelebbi push-ig"
heurisztika ugyanis némán társít: kipróbáltam, és három különböző
azonosítót adott UGYANARRA a kulcsra (`eMenuView::ID_VIEW_BW`), ami
találatnak látszik, amíg valaki össze nem veti őket.
"""
import json
import os
import re
import struct

import pefile

EXE = os.environ.get(
    "PICASA_EXE", "research/copy_Picasa_3_7/Picasa3/Picasa3.exe"
)
pe = pefile.PE(EXE, fast_load=True)
BASE = pe.OPTIONAL_HEADER.ImageBase
SZAK = [(BASE + s.VirtualAddress, s.Misc_VirtualSize, s.get_data()) for s in pe.sections]
t = next(s for s in pe.sections if s.Name.startswith(b".text"))
TVA, TD = BASE + t.VirtualAddress, t.get_data()
KULCS = re.compile(r"^[A-Za-z][A-Za-z0-9_]*::[A-Za-z0-9_]+$")


def szoveg(va, maxlen=80):
    for k, m, nyers in SZAK:
        if k <= va < k + m:
            off = va - k
            veg = nyers.find(b"\0", off, off + maxlen)
            if veg <= off:
                return None
            b = nyers[off:veg]
            return b.decode("ascii") if all(32 <= c < 127 for c in b) else None
    return None


def tarolas_hossza(i):
    """A megengedett tároló utasítások hossza az `i` pozíción, vagy None."""
    b = TD[i]
    if b == 0xB8:                                   # mov eax, imm32
        return 5
    if b == 0x89 and TD[i + 1] == 0x1D:             # mov [disp32], ebx
        return 6
    if b == 0xC7 and TD[i + 1] == 0x05:             # mov dword [disp32], imm32
        return 10
    if b == 0x66 and TD[i + 1] == 0x89 and TD[i + 2] == 0x1D:   # mov word [disp32], bx
        return 7
    if b == 0x66 and TD[i + 1] == 0xC7 and TD[i + 2] == 0x05:   # mov word [disp32], imm16
        return 9
    return None


# 1) az AZONOSÍTÓ-térkép — ez teljes és egyértelmű
azonosito = {}
for m in re.finditer(rb"\x66\xc7\x05", TD):
    i = m.start()
    if i + 9 <= len(TD):
        cel = struct.unpack_from("<I", TD, i + 3)[0]
        if cel >= 0xA:
            azonosito.setdefault(cel - 0xA, struct.unpack_from("<H", TD, i + 7)[0])

# 2) a KULCS-térkép — csak a hiánytalan sablonból
FAROK = re.compile(rb"\x8b\x00\x83\xc4\x04\x3b\xc3\x74\x0a\x83\xc0\x04\xa3", re.S)
kulcs = {}
elvetve = 0
for m in FAROK.finditer(TD):
    i = m.start()
    rek = struct.unpack_from("<I", TD, i + 13)[0]
    if i < 5 or TD[i - 5] != 0xE8:                  # a `call` közvetlenül előtte
        continue
    call_i = i - 5
    megvan = False
    for p in range(call_i - 5, max(-1, call_i - 160), -1):
        if TD[p] != 0x68:
            continue
        q, ok = p + 5, True
        while q < call_i:
            h = tarolas_hossza(q)
            if h is None:
                ok = False
                break
            q += h
        if not (ok and q == call_i):
            continue
        s = szoveg(struct.unpack_from("<I", TD, p + 1)[0])
        if s and KULCS.match(s):
            kulcs.setdefault(rek, s)
            megvan = True
        break
    if not megvan:
        elvetve += 1

parok = {r: (k, azonosito[r]) for r, k in kulcs.items() if r in azonosito}
print(f"azonosító-rekord: {len(azonosito)}   sablon-találat kulccsal: {len(kulcs)}"
      f"   ELVETVE (a sablon nem teljes): {elvetve}   PÁR: {len(parok)}")

# ÖNELLENŐRZÉS: a kulcs maga megnevezi a parancsot, az azonosító viszont egy
# TŐLE FÜGGETLEN mezőből (`+0x0a`) jön — az egyezés tehát valódi kontroll.
nev_szerint = {}
for _r, (k, a) in parok.items():
    nev_szerint.setdefault(k.split("::")[-1], set()).add(a)
utkozes = {n: v for n, v in nev_szerint.items() if len(v) > 1}
print(f"ütköző nevek (ugyanaz a név, több azonosító): {len(utkozes)}")
for n, v in sorted(utkozes.items())[:8]:
    print("   ", n, [hex(x) for x in sorted(v)])

VART = {"ID_VIEW_16": 0x9D18, "ID_VIEW_PROJECTOR": 0x9D19, "ID_VIEW_MAC": 0x9D1A,
        "ID_VIEW_SEPIA": 0x9D1B, "ID_VIEW_BW": 0x9D1C, "ID_VIEW_LINEAR": 0x9D1D,
        "ID_VIEW_NORMAL": 0x9D1E, "ID_VIEW_AUTO": 0x9D1F, "ID_VIEW_LCD": 0x9D20,
        "ID_VIEW_OV": 0x9D55, "ID_VIEW_RDESK": 0x9DBC, "ID_VIEW_FOLDERS": 0x9DB6,
        "ID_VIEW_WATCHED": 0x9DB8, "ID_VIEW_ALL": 0x9DB9}
print("\nkontroll — a #1409 / #1454 ismert azonosítói:")
jo = el = hi = 0
for nev, a in sorted(VART.items(), key=lambda x: x[1]):
    kapott = nev_szerint.get(nev)
    if not kapott:
        print(f"  {nev:20} 0x{a:04x}  HIÁNYZIK")
        hi += 1
    elif kapott == {a}:
        print(f"  {nev:20} 0x{a:04x}  ✔")
        jo += 1
    else:
        print(f"  {nev:20} 0x{a:04x}  ELTÉR -> {[hex(x) for x in kapott]}")
        el += 1
print(f"\n{jo} egyezik · {el} eltér · {hi} hiányzik")
json.dump({hex(r): {"kulcs": k, "azonosito": f"0x{a:04x}"} for r, (k, a) in sorted(parok.items())},
          open("terkep.json", "w"), indent=1, ensure_ascii=False)
