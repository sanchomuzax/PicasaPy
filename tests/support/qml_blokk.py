"""QML-forrásblokk kivágása MÉRT határok mentén (#2493).

## Miért kell

A forrás-szintű őrök egy része így dolgozott:

```python
kezd = forras.index('objectName: "trayMoreButton"')
blokk = forras[kezd:kezd + 900]      # ⚠️ rögzített ablak
```

A 900 nem jelent semmit: nem a vezérlő határa, hanem egy szám, ami az
íráskor épp elég volt. Amint a vezérlőhöz **indoklás** kerül — pontosan
az, amit a projekt megkövetel —, az ablak vége kicsúszik a mért sorok
alól, és az őr olyasmire panaszkodik, ami ott van a kódban.

Mérve (2026-09-06, #2493): a `trayMoreButton` kapott egy 14 soros
kódkommentet arról, MIÉRT nincs ikonja; a `ToolTip.text` ettől a 900.
karakter mögé került, és két őr bukott el **helyes** kódon.

## A szabály

Az ablak legyen a vezérlő VALÓDI blokkja: a horgonyt tartalmazó `{ … }`
párosítás. Így az őr akkor és csak akkor bukik, ha a mért sor tényleg
hiányzik.

Ld. a memórialapot: „rögzített ablakos forrás-őr".
"""

from __future__ import annotations


def kommentek_nelkul(szoveg: str) -> str:
    """A QML sor- és blokk-kommentjeit kivágja.

    A `//`-t csak akkor tekintjük komment-kezdetnek, ha NEM idézőjelen
    belül áll (`"https://…"` nem komment).
    """
    darabok: list[str] = []
    i = 0
    while True:
        nyit = szoveg.find("/*", i)
        if nyit < 0:
            darabok.append(szoveg[i:])
            break
        darabok.append(szoveg[i:nyit])
        zar = szoveg.find("*/", nyit + 2)
        if zar < 0:
            break
        i = zar + 2
    szoveg = "".join(darabok)

    sorok: list[str] = []
    for sor in szoveg.splitlines():
        idezet = ""
        vag = len(sor)
        j = 0
        while j < len(sor):
            jel = sor[j]
            if idezet:
                if jel == "\\":
                    j += 2
                    continue
                if jel == idezet:
                    idezet = ""
            elif jel in "\"'":
                idezet = jel
            elif jel == "/" and sor[j + 1:j + 2] == "/":
                vag = j
                break
            j += 1
        sorok.append(sor[:vag])
    return "\n".join(sorok)


def blokk_horgonyra(forras: str, horgony: str) -> str:
    """A `horgony`-t tartalmazó QML-blokk (`{ … }`) teljes szövege.

    A kommenteket előbb kivágjuk — így egy kommentbe írt sor sem
    elégítheti ki az őrt, és egy hosszú indoklás sem szoríthatja ki a
    mért sorokat.

    :raises AssertionError: ha a horgony nincs meg, vagy a blokk nem
        záródik (elrontott forrás).
    """
    tiszta = kommentek_nelkul(forras)
    hely = tiszta.find(horgony)
    assert hely >= 0, f"a horgony nincs meg a forrásban: {horgony!r}"

    # a horgonyt tartalmazó blokk NYITÓ kapcsos zárójele: visszafelé az
    # első olyan `{`, aminek a párja a horgony UTÁN van
    melyseg = 0
    nyito = -1
    for i in range(hely, -1, -1):
        if tiszta[i] == "}":
            melyseg += 1
        elif tiszta[i] == "{":
            if melyseg == 0:
                nyito = i
                break
            melyseg -= 1
    assert nyito >= 0, f"nincs nyitó kapcsos zárójel a horgony előtt: {horgony!r}"

    melyseg = 0
    for i in range(nyito, len(tiszta)):
        if tiszta[i] == "{":
            melyseg += 1
        elif tiszta[i] == "}":
            melyseg -= 1
            if melyseg == 0:
                return tiszta[nyito:i + 1]
    raise AssertionError(f"a blokk nem záródik: {horgony!r}")
