"""#1608: a nézetfüggő `Delete` MAGYAR feliratai a HIVATALOS szövegek.

A feliratokat nem mi fogalmazzuk: a Picasa saját magyar erőforrásaiból
valók (`stringres`, a jegyben *megerősített* fokozattal):

| kulcs | angol | magyar |
|---|---|---|
| `IDS_DELETE_FROM_DISK` | `Delete from Disk\tDelete` | `Törlés lemezről\tDelete` |
| `IDS_REMOVE_FROM_LABEL` | `Remove from Album\tDelete` | `Eltávolítás az albumból\tTörlés` |

Az Emberek-album változatát a `docs/specs/picasa-gyorsbillentyuk.md` 4.
szakasza méri (`0x007355c0`): „Eltávolítás az Emberek albumból".

A QML-funkcionális teszt (`qml_functional/test_album_delete_billentyu_1608.py`)
nem tudja ezt mérni: a fixture nem telepít `QTranslator`-t, ott a `qsTr()`
az ANGOL forrásszöveget adja vissza. Ez a fájl ezért közvetlenül a
`picasapy_hu.ts`-t olvassa.

⚠️ A jobb oldali szövegek **kiírt literálok** — szándékosan nem a termék
konstansából származnak (a #1576 első köre épp attól nyelte el a hibát).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

_TS_PATH = (
    Path(__file__).resolve().parents[2]
    / "src" / "picasapy" / "app" / "i18n" / "picasapy_hu.ts"
)

#: (kontextus, forrássztring) -> a HIVATALOS magyar felirat.
HIVATALOS: dict[tuple[str, str], str] = {
    # a menüsáv Fájl ▸ tétele MAPPA-nézetben (IDS_DELETE_FROM_DISK)
    ("PicasaMenuBar", "Delete from Disk"): "Törlés lemezről",
    # ugyanaz a tétel ALBUM-nézetben (IDS_REMOVE_FROM_LABEL)
    ("PicasaMenuBar", "Remove from Album"): "Eltávolítás az albumból",
    # és EMBEREK-albumban (0x007355c0)
    (
        "PicasaMenuBar",
        "Remove from People Album",
    ): "Eltávolítás az Emberek albumból",
    # a helyi menü ugyanezt a két szöveget hozza — a két felület nem
    # csúszhat el egymástól
    ("PhotoContextMenu", "Remove from Album"): "Eltávolítás az albumból",
    (
        "PhotoContextMenu",
        "Remove from People Album",
    ): "Eltávolítás az Emberek albumból",
}


def _forditasok() -> dict[tuple[str, str], str]:
    gyoker = ET.parse(_TS_PATH).getroot()
    ki: dict[tuple[str, str], str] = {}
    for context in gyoker.findall("context"):
        nev = (context.findtext("name") or "").strip()
        for message in context.findall("message"):
            forras = message.findtext("source")
            forditas = message.find("translation")
            if forras is None or forditas is None:
                continue
            ki[(nev, forras)] = forditas.text or ""
    return ki


@pytest.mark.parametrize(("kulcs", "vart"), sorted(HIVATALOS.items()))
def test_a_hivatalos_magyar_felirat_all_a_ts_ben(kulcs, vart):
    forditasok = _forditasok()
    kontextus, forras = kulcs
    assert kulcs in forditasok, (
        f"[{kontextus}] {forras!r} nincs a picasapy_hu.ts-ben"
    )
    assert forditasok[kulcs] == vart, (
        f"[{kontextus}] {forras!r} magyar felirata nem a hivatalos szöveg"
    )


def test_a_harom_felirat_KULONBOZIK():
    """Ha valaki egyetlen szövegre vonja össze a hármat, a nézetfüggés
    láthatatlanná válik a felhasználó számára — ez az őr ezt tiltja."""
    forditasok = _forditasok()
    szovegek = {
        forditasok.get(("PicasaMenuBar", "Delete from Disk")),
        forditasok.get(("PicasaMenuBar", "Remove from Album")),
        forditasok.get(("PicasaMenuBar", "Remove from People Album")),
    }
    assert len(szovegek) == 3, f"a három felirat nem különbözik: {szovegek}"
    assert None not in szovegek, "az egyik felirat hiányzik a .ts-ből"
