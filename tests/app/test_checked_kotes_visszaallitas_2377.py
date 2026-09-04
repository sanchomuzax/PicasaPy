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

_QML_GYOKER = Path(__file__).resolve().parents[2] / "src/picasapy/app/qml"

#: a `MenuItem { ... }` blokkok — a QML-ben a tételek egy szinten állnak,
#: ezért a nem mohó törzs + a záró kapcsos zárójel elég a felbontáshoz
_TETEL = re.compile(r"MenuItem\s*\{(.*?)\n(\s*)\}", re.S)
_CHECKED = re.compile(r"checked:\s*(.+)")
_OBJNEV = re.compile(r'objectName:\s*"([^"]+)"')


def _kotott_checked_visszaallitas_nelkul() -> list[str]:
    talalatok = []
    for ut in sorted(_QML_GYOKER.rglob("*.qml")):
        szoveg = ut.read_text(encoding="utf-8")
        for talalat in _TETEL.finditer(szoveg):
            torzs = talalat.group(1)
            if "checkable: true" not in torzs or "Qt.binding" in torzs:
                continue
            checked = _CHECKED.search(torzs)
            if checked is None:
                continue
            # a literál `checked: true/false` nem kötés — nincs mit eldobni
            if checked.group(1).strip() in ("true", "false"):
                continue
            nev = _OBJNEV.search(torzs)
            sor = szoveg[: talalat.start()].count("\n") + 1
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
        for talalat in _TETEL.finditer(ut.read_text(encoding="utf-8")):
            if "checkable: true" in talalat.group(1):
                jelolhetok += 1
    assert jelolhetok >= 20, (
        f"csak {jelolhetok} jelölhető menütételt találtam — a minta "
        "valószínűleg elromlott, az őr így semmit nem védene"
    )
