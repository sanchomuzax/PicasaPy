"""#2377: kötött `checked` + `checkable` ⇒ kötelező a kötés visszaállítása.

## A hibaosztály

A `MenuItem` `checkable: true` esetén kattintáskor ELŐSZÖR maga billenti a
`checked`-et (`AbstractButton.toggle`), és ez az imperatív írás **eldobja**
a `checked: <kifejezés>` deklaratív kötést. Onnantól a pipa nem a valóságot
mutatja, hanem azt, amit a billentés hagyott ott.

Billenő tételnél ez ma nem látszik, mert a művelet úgyis átbillenti az
állapotot — a `toggle` véletlenül ugyanarra az értékre ír. **Ez szerencse,
nem szerkezet:** amint a művelet NEM billent (elutasított beállítás,
hiányzó vezérlő, rádió-jellegű tétel), a pipa hazudik. A #1471-ben pontosan
ez történt a négy fiók-lapnál, ott ki is mérve.

## Miért FORRÁS-őr, és nem futásidejű

A futásidejű mérés csak azt fogná meg, ami ténylegesen elromlott — a nyolc
billenő ma helyes értéket ad. Az őr célja épp az, hogy a **szerkezeti**
hiányt tiltsa, mielőtt egy jövőbeli változás láthatóvá teszi.

## Amit NEM állít

Nem állítja, hogy a `Qt.binding(...)` jelenléte helyes kifejezést ad
vissza — csak azt, hogy a visszaállítás megtörténik. A tartalmi helyességet
a #1471 funkcionális őre méri a fiók-lapokra.
"""

from __future__ import annotations

import re
from pathlib import Path

from tests.support.qml_blokk import blokkok_tipusra

_QML_GYOKER = Path(__file__).resolve().parents[2] / "src/picasapy/app/qml"

#: a `MenuItem {` nyitása — a törzset innen ZÁRÓJEL-PÁROSÍTÁSSAL olvassuk
#: ki, nem mintával.
#:
#: ⚠️ 2026-09-05-ig a törzs a `MenuItem\s*\{(.*?)\n(\s*)\}` nem mohó
#: mintával jött, ami az ELSŐ önálló sorban álló `}`-nál elvágta. Amint egy
#: `onTriggered` törzsébe `if … { … } else { … }` került, a minta a belső
#: ág záró zárójeleénél vágott — a törzs VÉGÉN álló `Qt.binding(...)`
#: visszaállítás kimaradt a szövegből, és az őr HAMIS leletet adott egy
#: helyes tételre (#1637, `menuViewHidden`). A szerkezetet nem szabad
#: mintával közelíteni, ha egyszer beágyazódik.
_CHECKED = re.compile(r"checked:\s*(.+)")
_OBJNEV = re.compile(r'objectName:\s*"([^"]+)"')


def _tetel_torzsek(szoveg: str) -> list[tuple[int, str]]:
    """A `MenuItem` / `PicasaMenuItem` tételek törzse — a KÖZÖS mérővel (#2613).

    ⚠️ Eddig saját, idézőjel-tudatos zárójel-számláló állt itt. Helyes volt,
    de MÁSOLAT: ugyanez a logika öt fájlban élt, és ha az egyik javul (a
    #2575-ben a közös mérő kapott idézőjel-tudatosságot), a többi némán
    marad hibás. A `blokkok_tipusra` ugyanezt adja, egy helyen javíthatóan.

    ⚠️ KÉT típusnevet kérdezünk. A régi minta (`MenuItem\s*\{`) szóhatár
    NÉLKÜL illeszkedett, tehát a `PicasaMenuItem`-et is elkapta; a közös
    mérő szóhatárt használ, ezért a hatókör csak így marad ugyanaz.

    ⚠️ HATÓKÖR-BŐVÜLÉS, kimondva: a közös mérő KIVÁGJA a kommenteket, a régi
    saját számláló nem. Ettől egy kikommentelt `Qt.binding(...)` már nem
    elégíti ki az őrt — ez szigorítás, és pontosan az, amit a projekt kér
    („a komment sem hazudhat").
    """
    return sorted(
        par
        for tipus in ("MenuItem", "PicasaMenuItem")
        for par in blokkok_tipusra(szoveg, tipus)
    )


def _kotott_checked_visszaallitas_nelkul() -> list[str]:
    talalatok = []
    for ut in sorted(_QML_GYOKER.rglob("*.qml")):
        szoveg = ut.read_text(encoding="utf-8")
        for sor, torzs in _tetel_torzsek(szoveg):
            if "checkable: true" not in torzs or "Qt.binding" in torzs:
                continue
            checked = _CHECKED.search(torzs)
            if checked is None:
                continue
            # a literál `checked: true/false` nem kötés — nincs mit eldobni
            if checked.group(1).strip() in ("true", "false"):
                continue
            nev = _OBJNEV.search(torzs)
            talalatok.append(
                f"{ut.name}:{sor} ({nev.group(1) if nev else 'névtelen'})"
            )
    return talalatok


def test_minden_kotott_checked_visszaallitja_a_kotest() -> None:
    hianyzok = _kotott_checked_visszaallitas_nelkul()
    assert not hianyzok, (
        "`checkable: true` + kifejezéssel kötött `checked:` esetén az "
        "`onTriggered` végén kötelező a `checked = Qt.binding(...)` "
        "(minta: FolderListContextMenu.qml). Hiányzik: " + ", ".join(hianyzok)
    )


def test_az_or_talal_is_valamit() -> None:
    """Az őr foga: ha a mintája elromlik, néma zöldet adna.

    Ellenőrizzük, hogy a felbontás egyáltalán lát jelölhető tételeket —
    enélkül a fenti állítás egy ÜRES listán menne át.
    """
    jelolhetok = 0
    for ut in _QML_GYOKER.rglob("*.qml"):
        szoveg = ut.read_text(encoding="utf-8")
        for _sor, torzs in _tetel_torzsek(szoveg):
            if "checkable: true" in torzs:
                jelolhetok += 1
    assert jelolhetok >= 20, (
        f"csak {jelolhetok} jelölhető menütételt találtam — a felbontás "
        "valószínűleg elromlott, az őr így semmit nem védene"
    )


def test_az_or_meglatja_a_beagyazott_ag_utan_allo_visszaallitast() -> None:
    """A 2026-09-05-i hamis lelet fogása: `if … {} else {}` a törzs KÖZEPÉN.

    A régi, nem mohó minta a belső ág záró zárójelénél elvágta a törzset, és
    a törzs VÉGÉN álló `Qt.binding(...)`-ot már nem látta — helyes tételre
    adott leletet. Ez a próba MINDKÉT irányt méri: a beágyazott ág után álló
    visszaállítást el kell fogadni, a hiányzót viszont meg kell találni.
    """
    jo = """
    MenuItem {
        objectName: "proba"
        checkable: true
        checked: ctl.valami
        onTriggered: {
            if (ctl.zarva) {
                ctl.kerdez()
            } else {
                ctl.billent()
            }
            checked = Qt.binding(function () { return ctl.valami })
        }
    }
    """
    rossz = jo.replace(
        "            checked = Qt.binding(function () "
        "{ return ctl.valami })\n", ""
    )
    assert rossz != jo, "a próba mintája elavult — a visszaállítás sora nem illeszkedett"

    def _talal(qml: str) -> bool:
        torzsek = _tetel_torzsek(qml)
        assert torzsek, "a próbaminta nem tartalmaz menütételt"
        torzs = torzsek[0][1]
        return "checkable: true" in torzs and "Qt.binding" not in torzs

    assert not _talal(jo), (
        "a beágyazott ág UTÁN álló visszaállítást nem látja meg az őr — "
        "hamis leletet adna a helyes tételre"
    )
    assert _talal(rossz), (
        "a hiányzó visszaállítást sem találja meg — az őrnek nincs foga"
    )
