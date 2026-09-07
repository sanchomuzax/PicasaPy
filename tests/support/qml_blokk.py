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

import re


#: Új utasítás kezdete: `nev:` kötés, vagy `Elem {` elemdeklaráció.
_UJ_UTASITAS = re.compile(r"^[A-Za-z_][\w.]*\s*(:|\{)")


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


def tulajdonsag_erteke(forras: str, tulajdonsag: str) -> str:
    """Egy QML-tulajdonság KÖTÉSÉNEK teljes szövege (több sorra is).

    A „mire van kötve ez a tulajdonság?" fajta állításnak sem a sor, sem a
    befoglaló blokk nem a valódi határa:

    * a SOR levágja a többsoros kifejezést (ternárius, sortöréssel írt
      összefűzés) — a mért részlet kicsúszik belőle;
    * a BEFOGLALÓ BLOKK viszont túl tág: a #2575 mérése szerint a
      `FolderPane.qml` küldöttje 7167 karakter, és a `path` szó ott áll
      benne `required property string path`-ként is — vagyis az őr akkor is
      zöld maradt volna, ha a súgó SEMMIT nem mond az útvonalról. Ez a
      vákuum-őr osztálya (#2493).

    Az érték a `tulajdonsag:` utáni első karaktertől addig tart, amíg egy
    sor NULLA zárójel-mélységben új utasítást kezd (`nev:`, `}`, `)`,
    `Elem {`). A kommenteket előbb kivágjuk.

    :raises AssertionError: ha a tulajdonság nincs meg a forrásban.
    """
    tiszta = kommentek_nelkul(forras)
    minta = tulajdonsag + ":"
    hely = tiszta.find(minta)
    assert hely >= 0, f"nincs ilyen tulajdonság a forrásban: {minta!r}"

    i = hely + len(minta)
    sorok: list[str] = []
    melyseg = 0
    for sor in tiszta[i:].splitlines():
        if sorok and melyseg == 0 and _uj_utasitas(sor):
            break
        sorok.append(sor)
        melyseg += sum(sor.count(ny) for ny in "([{")
        melyseg -= sum(sor.count(za) for za in ")]}")
        melyseg = max(melyseg, 0)
    return "\n".join(sorok)


def _uj_utasitas(sor: str) -> bool:
    """Új QML-utasítást kezd-e a sor (tehát az előző kötés itt véget ér)."""
    csupasz = sor.strip()
    if not csupasz:
        return False
    if csupasz[0] in "})]":
        return True
    return bool(_UJ_UTASITAS.match(csupasz))


def _zaro(tiszta: str, nyito: int, horgony: str) -> int:
    """A `nyito` kapcsos zárójel PÁRJÁNAK helye (sztringeket átugorva)."""
    vak = _idezetek_nelkul(tiszta)
    melyseg = 0
    for i in range(nyito, len(vak)):
        if vak[i] == "{":
            melyseg += 1
        elif vak[i] == "}":
            melyseg -= 1
            if melyseg == 0:
                return i
    raise AssertionError(f"a blokk nem záródik: {horgony!r}")


def _idezetek_nelkul(tiszta: str) -> str:
    """Ugyanolyan HOSSZÚ szöveg, a sztringek tartalma szóközzel kitöltve.

    A zárójel-párosítás enélkül hamis: egy `text: "{"` kötés elcsúsztatja a
    számlálót, és a blokk vagy rossz helyen záródik, vagy sehol (mérve
    #2575). A hosszot azért tartjuk meg, hogy az itt talált eltolások a
    tisztított EREDETIRE is érvényesek maradjanak.
    """
    ki: list[str] = []
    idezojel = ""
    i = 0
    while i < len(tiszta):
        jel = tiszta[i]
        if idezojel:
            if jel == "\\" and i + 1 < len(tiszta):
                ki.append("  ")
                i += 2
                continue
            if jel == idezojel:
                idezojel = ""
                ki.append(jel)
            else:
                ki.append("\n" if jel == "\n" else " ")
        elif jel in ("'", '"'):
            idezojel = jel
            ki.append(jel)
        else:
            ki.append(jel)
        i += 1
    return "".join(ki)


def elozo_komment(forras: str, horgony: str) -> str:
    """A `horgony`-t tartalmazó ELEM deklarációja fölötti komment-tömb.

    Van olyan őr, ami szándékosan a KÖRNYEZETET nézi: azt állítja, hogy a
    forrás KIMONDJA az indoklást (ld. „a komment sem hazudhat"). Ennek a
    határa sem karakterszám: a #2575-ben mért alak
    (`forras[forras.find(h) - 1400:][:2200]`) két irányban is hamis — egy
    hosszabb szomszédos indoklás beleszámít, egy rövidebb sajátot pedig
    kilök.

    A határ itt: a horgony fölött felfelé az első `{`-re végződő sor (ez az
    elem deklarációja — a QML-ben az indoklás EZ FÖLÉ kerül), majd az
    afölött álló, megszakítás nélküli `//`-sorok. Üres sor vagy kódsor
    lezárja.

    :raises AssertionError: ha a horgony nincs meg.
    """
    sorok = forras.splitlines()
    horgony_sor = next(
        (i for i, sor in enumerate(sorok) if horgony in sor), -1
    )
    assert horgony_sor >= 0, f"a horgony nincs meg a forrásban: {horgony!r}"

    nyito_sor = horgony_sor
    while nyito_sor >= 0 and not sorok[nyito_sor].rstrip().endswith("{"):
        nyito_sor -= 1
    if nyito_sor < 0:
        nyito_sor = horgony_sor

    gyujtott: list[str] = []
    for sor in reversed(sorok[:nyito_sor]):
        if sor.strip().startswith("//"):
            gyujtott.append(sor.strip())
            continue
        break
    return "\n".join(reversed(gyujtott))


def _befoglalo_nyito(tiszta: str, horgony: str) -> int:
    """A `horgony`-t tartalmazó blokk NYITÓ kapcsos zárójelének helye.

    Visszafelé az első olyan `{`, aminek a párja a horgony UTÁN van.
    """
    hely = tiszta.find(horgony)
    assert hely >= 0, f"a horgony nincs meg a forrásban: {horgony!r}"
    vak = _idezetek_nelkul(tiszta)
    melyseg = 0
    for i in range(hely, -1, -1):
        if vak[i] == "}":
            melyseg += 1
        elif vak[i] == "{":
            if melyseg == 0:
                return i
            melyseg -= 1
    raise AssertionError(
        f"nincs nyitó kapcsos zárójel a horgony előtt: {horgony!r}"
    )


def elem_tipusa(forras: str, horgony: str) -> str:
    """A `horgony`-t tartalmazó QML-elem TÍPUSNEVE (`PicasaMenuItem`).

    A „milyen elem ez?" fajta állítás rögzített ablakkal kétszeresen
    hamis: a `forras[:kezdet][-200:]` alak egy SZOMSZÉD elem típusnevét is
    elfogadja, és egy hosszabb indoklás ki is szoríthatja a valódit. A
    típusnév a blokk nyitó zárójele ELŐTTI azonosító — azt adjuk vissza.

    :raises AssertionError: ha a horgony nincs meg, vagy a nyitó zárójel
        előtt nem áll azonosító.
    """
    tiszta = kommentek_nelkul(forras)
    nyito = _befoglalo_nyito(tiszta, horgony)
    vege = nyito
    while vege > 0 and tiszta[vege - 1].isspace():
        vege -= 1
    kezdet = vege
    while kezdet > 0 and (tiszta[kezdet - 1].isalnum() or tiszta[kezdet - 1] == "."):
        kezdet -= 1
    nev = tiszta[kezdet:vege]
    assert nev, f"a blokk nyitó zárójele előtt nincs típusnév: {horgony!r}"
    return nev


def blokk_horgonyra(forras: str, horgony: str) -> str:
    """A `horgony`-t tartalmazó QML-blokk (`{ … }`) teljes szövege.

    A kommenteket előbb kivágjuk — így egy kommentbe írt sor sem
    elégítheti ki az őrt, és egy hosszú indoklás sem szoríthatja ki a
    mért sorokat.

    :raises AssertionError: ha a horgony nincs meg, vagy a blokk nem
        záródik (elrontott forrás).
    """
    tiszta = kommentek_nelkul(forras)
    nyito = _befoglalo_nyito(tiszta, horgony)
    return tiszta[nyito:_zaro(tiszta, nyito, horgony) + 1]


def blokk_horgony_utan(forras: str, horgony: str) -> str:
    """A `horgony` UTÁN nyíló első `{ … }` blokk teljes szövege.

    Ez a fejlécre horgonyzott eset: `function f() { … }`, `Shortcut { … }`,
    `onValamiChanged: { … }`, `move: Transition { … }`. Ilyenkor a horgony a
    nyitó kapcsos zárójel ELŐTT áll, tehát a `blokk_horgonyra` a BEFOGLALÓ
    blokkot adná vissza — az sokkal tágabb, és az állítás elszürkülne.

    A kommenteket itt is előbb kivágjuk (#2540): enélkül a horgony egy
    kommentbe írt EMLÍTÉSRE illeszkedne, és az őr egy egészen más blokkot
    mérne. (Mérve: a `test_shift_csempek_2146.py` `onActiveTabChanged`
    horgonya egy kommentre esett, és a próba a valódi kezelőt SOSEM nézte.)

    :raises AssertionError: ha a horgony nincs meg, nem követi `{`, vagy a
        blokk nem záródik.
    """
    tiszta = kommentek_nelkul(forras)
    hely = tiszta.find(horgony)
    assert hely >= 0, f"a horgony nincs meg a forrásban: {horgony!r}"

    nyito = _idezetek_nelkul(tiszta).find("{", hely + len(horgony))
    assert nyito >= 0, f"a horgony után nincs nyitó kapcsos zárójel: {horgony!r}"
    return tiszta[nyito:_zaro(tiszta, nyito, horgony) + 1]


def hivas_argumentumai(forras: str, hivas: str) -> str:
    """A `hivas` UTÁNI zárójelpár tartalma — a hívás argumentumlistája.

    Az „eljut-e az érték a hívásig?" fajta állításnak nem `{ … }`, hanem
    `( … )` a valódi határa. Rögzített karakterablakkal ez az állítás két
    irányban is hamis: a többsoros argumentumlista kilóg belőle, a
    SZOMSZÉD hívás argumentumai pedig belelógnak — így egy másik hívásnak
    átadott érték is „bizonyítaná" a bekötést.

    :raises AssertionError: ha a hívás nincs meg, vagy a zárójel nem
        záródik.
    """
    tiszta = kommentek_nelkul(forras)
    hely = tiszta.find(hivas)
    assert hely >= 0, f"a hívás nincs meg a forrásban: {hivas!r}"

    vak = _idezetek_nelkul(tiszta)
    nyito = vak.find("(", hely)
    assert nyito >= 0, f"a hívás után nincs nyitó zárójel: {hivas!r}"

    melyseg = 0
    for i in range(nyito, len(vak)):
        if vak[i] == "(":
            melyseg += 1
        elif vak[i] == ")":
            melyseg -= 1
            if melyseg == 0:
                return tiszta[nyito + 1:i]
    raise AssertionError(f"a hívás zárójele nem záródik: {hivas!r}")
