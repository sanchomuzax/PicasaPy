"""#2364: az indexkép-nyomtatás menüfelirata az EREDETI erőforrást kövesse.

## A mérés

Az eredeti menüépítő a `0x00559150`-en van, és az
`eMenuLabelFolder::ID_FILE_PRINTCONTACTSHEET` erőforrást teszi a tételre;
annak angol szövege `&Print Contact Sheet...`, a hivatalos magyar
fordítása (`stringres-en-hu.tsv`) `&Indexképek nyomtatása...`. Nálunk a
forrásszöveg `Print Thumbnails...` volt — a mi szavunk, nem az eredetié.

## Amit ez az őr állít, és amit NEM

Állítja, hogy a `PicasaMenuBar.qml` forrásszövege a `Contact Sheet`-es
alak, a magyar fordítása pedig „Indexképek"-kel kezdődik, és hogy a
`Thumbnails` szó ehhez a tételhez nem tér vissza. NEM állít semmit a
funkcióról (azt a #1590 őrei mérik) és a gyorsbillentyűről (azt a
menüsor-audit).

## Helyesbítés a jegyhez képest

A jegy szerint a magyar felület „Bélyegképek nyomtatása…"-t mutatott.
MÉRVE: a `.ts` már a javítás ELŐTT is „Indexképek nyomtatása…"-t adott
erre a forrásszövegre, tehát a magyar felhasználó helyes szöveget látott;
a hiba az ANGOL forrásszövegben és az erőforrás-hűségben állt.
"""

from __future__ import annotations

import re
from pathlib import Path

_GYOKER = Path(__file__).resolve().parents[2]
_QML = _GYOKER / "src/picasapy/app/qml/PicasaPy/PicasaMenuBar.qml"
_TS = _GYOKER / "src/picasapy/app/i18n/picasapy_hu.ts"

#: az eredeti erőforrás angol szövege (az `&` gyorsítójel nélkül, ahogy a
#: QML-ben a többi tételnél is)
FORRAS = "Print Contact Sheet..."
#: a hivatalos magyar fordítás (a `.ts`-ben hármaspont-karakterrel)
MAGYAR = "Indexképek nyomtatása…"


def test_a_menuteel_forrasszovege_az_eredetie() -> None:
    qml = _QML.read_text(encoding="utf-8")
    assert f'qsTr("{FORRAS}") + "\\tCtrl+Shift+P"' in qml


def test_a_thumbnails_szo_nem_ter_vissza_ehhez_a_tetelhez() -> None:
    qml = _QML.read_text(encoding="utf-8")
    assert "Print Thumbnails" not in qml


def test_a_magyar_forditas_indexkepekkel_kezdodik() -> None:
    ts = _TS.read_text(encoding="utf-8")
    talalat = re.search(
        rf"<source>{re.escape(FORRAS)}</source>\s*<translation>(.*?)</translation>",
        ts,
        re.S,
    )
    assert talalat is not None, "a forrásszöveg nincs a magyar .ts-ben"
    assert talalat.group(1) == MAGYAR
